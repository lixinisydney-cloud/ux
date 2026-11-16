"""Restore committed Codex results and rebuild static artifacts without AI calls.

An existing result is validated and preserved byte for byte. If missing, recover
it from local Git HEAD. Never substitute offline fixtures or generate decisions.
"""
import json
from pathlib import Path
import runpy
import subprocess

from classify_notes import load_dataset, validate_envelope, atomic_write
from build_data_bundle import build

ROOT = Path(__file__).resolve().parents[1]


def restore():
    target = ROOT / 'data/classifications.precomputed.json'
    payload = target.read_bytes() if target.exists() else subprocess.run(
        ['git', '-C', str(ROOT), 'show', 'HEAD:data/classifications.precomputed.json'],
        check=True, capture_output=True,
    ).stdout
    notes, groups = load_dataset(ROOT / 'data/notes.json', ROOT / 'data/groups.json')
    validate_envelope(json.loads(payload.decode('utf-8-sig')), notes, groups,
                      expected_mode='precomputed')
    if not target.exists():
        atomic_write(target, payload)
    build()
    runpy.run_path(str(ROOT / 'tests/export_standalone.py'), run_name='__main__')
    print('Validated/recovered saved Codex classification; no reclassification or network request.')


if __name__ == '__main__':
    restore()
