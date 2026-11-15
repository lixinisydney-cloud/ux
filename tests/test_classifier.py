"""Pipeline tests with explicitly fabricated transport responses, never real AI.

Run: python3 -m unittest discover -s tests -p test_classifier.py -v
The mocked OpenAI response fixtures below do not establish model quality.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("classify_notes", ROOT / "scripts/classify_notes.py")
classifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(classifier)


class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "data/classifications.real.json"
        self.cache = self.root / ".cache/re-fold"
        self.now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        self.notes = [
            {"id": "note-a", "title": "一张纸的变化", "description": "在纸面上尝试不同字距与颜色。",
             "tags": ["纸面实验"], "originalAlbum": "随手收藏", "savedAt": "2026-01-01T10:00:00Z",
             "cover": "design_type", "availability": "initial"},
            {"id": "note-b", "title": "求职作品集排版技巧", "description": "准备岗位作品展示的叙述和文字层次。",
             "tags": ["项目讲述"], "originalAlbum": "个人资料", "savedAt": "2026-01-01T11:00:00Z",
             "cover": "career_resume", "availability": "simulated"},
        ]
        self.groups = [
            {"id": group_id, "name": group_id, "description": f"{group_id} topic", "cover": "design_type"}
            for group_id in ("design", "travel", "career", "food", "home", "life")
        ]
        self.payload = {"assignments": [
            {"noteId": "note-a", "memberships": [{"groupId": "design", "reason": "单元测试夹具中的理由，并非真实模型输出"}], "unclassifiedReason": None},
            {"noteId": "note-b", "memberships": [
                {"groupId": "career", "reason": "单元测试夹具：作品准备"},
                {"groupId": "design", "reason": "单元测试夹具：文字层次"},
            ], "unclassifiedReason": None},
        ]}

    def raw_response(self, payload=None, **changes):
        response = {"id": "fabricated-test-response", "model": "fixture-model", "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(payload or self.payload)}}
        ]}
        response.update(changes)
        return json.dumps(response).encode()

    def run_mock(self, **options):
        options.setdefault("api_key", "unit-test-not-a-real-key")
        options.setdefault("now", self.now)
        return classifier.classify(self.notes, self.groups, self.output, self.cache, **options)

    def cache_file(self, model="gpt-4.1-mini"):
        return self.cache / (classifier.cache_key(self.notes, self.groups, model) + ".json")

    def test_read_json_accepts_windows_utf8_bom(self):
        path = self.root / "含中文的数据.json"
        path.write_bytes(b'\xef\xbb\xbf' + json.dumps(
            {"title": "中文笔记与收藏"}, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(classifier.read_json(path), {"title": "中文笔记与收藏"})

    def generated_envelope(self):
        with patch.object(classifier, "send_request", return_value=self.raw_response()):
            self.run_mock()
        return json.loads(self.output.read_text())

    def test_model_input_has_explicit_allowlist_without_answers(self):
        self.notes[0].update(groups=["secret-preset"], reason="preset answer", apiKey="should-not-be-sent")
        projected = classifier.model_input(self.notes, self.groups)
        for note in projected["notes"]:
            self.assertEqual(set(note), {"id", "title", "description", "tags"})
        for group in projected["groups"]:
            self.assertEqual(set(group), {"id", "name", "description"})
        request = classifier.request_payload(self.notes, self.groups, "gpt-4.1-mini")
        contents = json.loads(request["messages"][1]["content"])
        self.assertEqual(contents, projected)
        self.assertNotIn("secret-preset", json.dumps(request))
        self.assertTrue(request["response_format"]["json_schema"]["strict"])

    def test_hash_uses_only_semantic_inputs_and_canonical_json(self):
        expected = classifier.dataset_hash(self.notes, self.groups)
        self.notes[0].update(originalAlbum="另一个专辑", cover="other_cover", savedAt="2026-01-02T00:00:00Z", groups=["wrong"], reason="wrong")
        self.groups[0]["cover"] = "other_cover"
        self.assertEqual(classifier.dataset_hash(self.notes, self.groups), expected)
        self.notes[0]["description"] += " 改了语义内容"
        self.assertNotEqual(classifier.dataset_hash(self.notes, self.groups), expected)

    def test_multi_label_and_uncertain_records_are_valid(self):
        classifier.validate_assignments(self.payload, self.notes, self.groups)
        self.payload["assignments"][0].update(memberships=[], unclassifiedReason="内容不足，不能确定主题")
        classifier.validate_assignments(self.payload, self.notes, self.groups)

    def test_unknown_and_duplicate_note_ids_and_missing_records_rejected(self):
        cases = []
        wrong = deepcopy(self.payload); wrong["assignments"][0]["noteId"] = "invented"; cases.append(wrong)
        duplicate = deepcopy(self.payload); duplicate["assignments"][1]["noteId"] = "note-a"; cases.append(duplicate)
        missing = deepcopy(self.payload); missing["assignments"].pop(); cases.append(missing)
        for case in cases:
            with self.subTest(payload=case), self.assertRaises(classifier.ClassificationError):
                classifier.validate_assignments(case, self.notes, self.groups)

    def test_unknown_duplicate_group_and_invalid_reasons_rejected(self):
        for modifier in ("unknown", "duplicate", "empty", "extra", "wrong-null"):
            case = deepcopy(self.payload)
            assignment = case["assignments"][0]
            if modifier == "unknown": assignment["memberships"][0]["groupId"] = "made-up"
            elif modifier == "duplicate": assignment["memberships"] *= 2
            elif modifier == "empty": assignment["memberships"][0]["reason"] = " "
            elif modifier == "extra": assignment["memberships"][0]["originalAlbum"] = "do not modify"
            else: assignment["unclassifiedReason"] = "wrong for a classified note"
            with self.subTest(modifier=modifier), self.assertRaises(classifier.ClassificationError):
                classifier.validate_assignments(case, self.notes, self.groups)

    def test_uncertain_records_need_an_explanation(self):
        self.payload["assignments"][0].update(memberships=[], unclassifiedReason=None)
        with self.assertRaises(classifier.ClassificationError):
            classifier.validate_assignments(self.payload, self.notes, self.groups)

    def test_reason_limit_matches_browser_at_400_characters(self):
        for uncertain in (False, True):
            payload = deepcopy(self.payload)
            assignment = payload["assignments"][0]
            if uncertain:
                assignment.update(memberships=[], unclassifiedReason="测" * 400)
            else:
                assignment["memberships"][0]["reason"] = "测" * 400
            classifier.validate_assignments(payload, self.notes, self.groups)
            if uncertain:
                assignment["unclassifiedReason"] += "试"
            else:
                assignment["memberships"][0]["reason"] += "试"
            with self.subTest(uncertain=uncertain), self.assertRaises(classifier.ClassificationError):
                classifier.validate_assignments(payload, self.notes, self.groups)

    def test_local_dataset_ids_dates_and_tags_are_validated(self):
        classifier.validate_dataset(self.notes, self.groups)
        for modifier in ("duplicate-id", "naive-date", "tag-type", "missing-description", "bad-group"):
            notes, groups = deepcopy(self.notes), deepcopy(self.groups)
            if modifier == "duplicate-id": notes[1]["id"] = notes[0]["id"]
            elif modifier == "naive-date": notes[0]["savedAt"] = "2026-01-01"
            elif modifier == "tag-type": notes[0]["tags"] = [4]
            elif modifier == "missing-description": notes[0].pop("description")
            else: groups[0]["id"] = "new-group"
            with self.subTest(modifier=modifier), self.assertRaises(classifier.ClassificationError):
                classifier.validate_dataset(notes, groups)

    def test_missing_key_does_not_call_network_or_create_real_output(self):
        with patch.object(classifier, "send_request") as network:
            with self.assertRaisesRegex(classifier.ClassificationError, "OPENAI_API_KEY is missing"):
                self.run_mock(api_key=None)
        network.assert_not_called()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.cache.exists())

    def test_mock_response_is_validated_before_cache_and_publication(self):
        with patch.object(classifier, "send_request", return_value=self.raw_response()) as network:
            result = self.run_mock()
        self.assertEqual(result["status"], "generated")
        network.assert_called_once()
        envelope = classifier.validate_envelope(json.loads(self.output.read_text()), self.notes, self.groups, expected_mode="real")
        self.assertEqual(envelope["notesCount"], 2)
        self.assertTrue(self.cache_file().exists())
        self.assertEqual(len(list(self.cache.glob("*.raw-response.json"))), 1)
        self.assertNotIn("unit-test-not-a-real-key", self.output.read_text())
        request = next(self.cache.glob("*.request.json")).read_text()
        self.assertNotIn("unit-test-not-a-real-key", request)
        self.assertEqual(set(json.loads(json.loads(request)["messages"][1]["content"])["notes"][0]), {"id", "title", "description", "tags"})

    def test_valid_cache_can_be_reused_without_key_or_second_charge(self):
        with patch.object(classifier, "send_request", return_value=self.raw_response()) as network:
            self.run_mock()
            first_output = self.output.read_bytes()
            self.output.unlink()
            result = self.run_mock(api_key=None, now=self.now + timedelta(hours=1))
            self.assertEqual(result["status"], "cached")
            self.assertEqual(self.output.read_bytes(), first_output)
            network.assert_called_once()

    def test_stale_cache_requires_new_request_and_changed_content_misses_cache(self):
        self.generated_envelope()
        with patch.object(classifier, "send_request", return_value=self.raw_response()) as network:
            result = self.run_mock(now=self.now + timedelta(days=8))
            self.assertEqual(result["status"], "generated")
            network.assert_called_once()
        self.notes[0]["description"] += " content changed"
        with patch.object(classifier, "send_request") as network:
            with self.assertRaisesRegex(classifier.ClassificationError, "missing"):
                self.run_mock(api_key=None)
        network.assert_not_called()

    def test_cache_model_and_prompt_version_affect_identity(self):
        original = classifier.cache_key(self.notes, self.groups, "model-a")
        self.assertNotEqual(original, classifier.cache_key(self.notes, self.groups, "model-b"))
        with patch.object(classifier, "PROMPT_VERSION", "next-version"):
            self.assertNotEqual(original, classifier.cache_key(self.notes, self.groups, "model-a"))

    def test_tampered_cache_is_revalidated_and_not_silently_reused(self):
        envelope = self.generated_envelope()
        envelope["assignments"][0]["memberships"][0]["groupId"] = "invented"
        self.cache_file().write_text(json.dumps(envelope))
        original_output = self.output.read_bytes()
        with patch.object(classifier, "send_request") as network:
            with self.assertRaises(classifier.ClassificationError): self.run_mock()
        network.assert_not_called()
        self.assertEqual(self.output.read_bytes(), original_output)

    def test_force_bypasses_valid_cache(self):
        self.generated_envelope()
        with patch.object(classifier, "send_request", return_value=self.raw_response()) as network:
            self.assertEqual(self.run_mock(force=True)["status"], "generated")
        network.assert_called_once()

    def test_refusal_truncation_and_invalid_json_never_publish(self):
        cases = [
            b'not json',
            json.dumps({"choices": [{"finish_reason": "stop", "message": {"refusal": "fixture refusal"}}]}).encode(),
            json.dumps({"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}).encode(),
            json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": "not JSON"}}]}).encode(),
            json.dumps({"choices": [{"finish_reason": "stop", "message": "invalid"}]}).encode(),
        ]
        for raw in cases:
            with self.subTest(raw=raw), patch.object(classifier, "send_request", return_value=raw):
                with self.assertRaises(classifier.ClassificationError): self.run_mock(force=True)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.cache_file().exists())

    def test_invalid_classification_preserves_existing_output(self):
        self.output.parent.mkdir()
        self.output.write_text("existing valid result should stay untouched")
        bad = deepcopy(self.payload); bad["assignments"][0]["noteId"] = "invented"
        with patch.object(classifier, "send_request", return_value=self.raw_response(bad)):
            with self.assertRaises(classifier.ClassificationError): self.run_mock()
        self.assertEqual(self.output.read_text(), "existing valid result should stay untouched")

    def test_envelope_rejects_wrong_hash_model_mode_prompt_and_note_count(self):
        envelope = self.generated_envelope()
        changes = [{"datasetHash": "0" * 64}, {"promptVersion": "old"}, {"notesCount": True}, {"mode": "offline"}, {"inputFields": ["groups"]}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(classifier.ClassificationError):
                classifier.validate_envelope(envelope | change, self.notes, self.groups)
        with self.assertRaises(classifier.ClassificationError):
            classifier.validate_envelope(envelope, self.notes, self.groups, expected_model="other")

    def test_http_errors_omit_provider_body_and_key(self):
        fake_opener = unittest.mock.MagicMock()
        fake_opener.open.side_effect = urllib.error.HTTPError(
            classifier.API_URL, 401, "secret-body-must-not-be-printed", {}, io.BytesIO(b"unit-test-not-a-real-key"))
        with patch.object(classifier.urllib.request, "build_opener", return_value=fake_opener):
            with self.assertRaisesRegex(classifier.ClassificationError, "HTTP 401") as caught:
                classifier.send_request({}, "unit-test-not-a-real-key", 1)
        self.assertNotIn("unit-test-not-a-real-key", str(caught.exception))
        self.assertNotIn("secret-body", str(caught.exception))

    def test_offline_envelope_requires_explicit_fixture_metadata(self):
        envelope = self.generated_envelope()
        envelope.update(mode="offline", provider="offline-fixture", model=None)
        classifier.validate_envelope(envelope, self.notes, self.groups)
        with self.assertRaises(classifier.ClassificationError):
            classifier.validate_envelope(envelope, self.notes, self.groups, expected_mode="real")

    def test_future_result_timestamps_are_rejected(self):
        envelope = self.generated_envelope()
        envelope["generatedAt"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(classifier.ClassificationError, "future timestamp"):
            classifier.validate_envelope(envelope, self.notes, self.groups)

    def test_key_prompt_requires_a_real_terminal(self):
        notes_file, groups_file = self.root / 'notes.json', self.root / 'groups.json'
        notes_file.write_text(json.dumps(self.notes)); groups_file.write_text(json.dumps(self.groups))
        with patch.object(classifier.sys.stdin, 'isatty', return_value=False), patch.object(classifier.getpass, 'getpass') as prompt, patch('sys.stderr', new_callable=io.StringIO) as err:
            code = classifier.main(['--input', str(notes_file), '--groups', str(groups_file), '--ask-key'])
        self.assertEqual(code, 2)
        prompt.assert_not_called()
        self.assertIn('interactive terminal', err.getvalue())

    def test_project_dataset_and_offline_file_match_shared_contract(self):
        if not (ROOT / "data/notes.json").exists(): self.skipTest("project dataset is not available yet")
        notes, groups = classifier.load_dataset(ROOT / "data/notes.json", ROOT / "data/groups.json")
        offline = classifier.read_json(ROOT / "data/classifications.offline.json")
        classifier.validate_envelope(offline, notes, groups, expected_mode="offline")
        self.assertEqual(len(notes), 38)
        self.assertEqual(sum(n["availability"] == "initial" for n in notes), 35)
        self.assertEqual(sum(n["availability"] == "simulated" for n in notes), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
