/* Static classification files only. This module never contacts an AI service. */
(function (root) {
  'use strict';
  const VERSION = 1;
  const PROMPT = 're-fold-text-v1';
  const FIELDS = ['id', 'title', 'description', 'tags'];
  const GROUP_IDS = ['design', 'travel', 'career', 'food', 'home', 'life'];
  const CACHE_KEY = 'refold-classification-cache-v1';
  const MAX_CACHE_AGE = 7 * 24 * 60 * 60 * 1000;
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const text = (value, max = 2000) => typeof value === 'string' && value.trim().length > 0 && Array.from(value).length <= max;
  const exactKeys = (value, names) => object(value) && Object.keys(value).sort().join('|') === names.slice().sort().join('|');
  function demand(condition, message) { if (!condition) throw new Error(message); }
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (object(value)) return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    return JSON.stringify(value);
  }
  function validateDataset(bundle) {
    demand(object(bundle) && Array.isArray(bundle.notes) && Array.isArray(bundle.groups), 'Missing dataset');
    const ids = new Set();
    for (const n of bundle.notes) {
      demand(object(n) && text(n.id, 80) && !ids.has(n.id), 'Invalid or duplicate note ID');
      ids.add(n.id);
      demand(text(n.title, 200) && text(n.description) && Array.isArray(n.tags) && n.tags.length <= 20 && n.tags.every(t => text(t, 80)), 'Invalid note text');
      demand(text(n.originalAlbum, 100) && typeof n.savedAt === 'string' && Number.isFinite(Date.parse(n.savedAt)), 'Invalid note metadata');
      demand(text(n.cover, 80) && /^[a-zA-Z0-9_]+$/.test(n.cover), 'Invalid cover');
      demand(['initial', 'simulated'].includes(n.availability), 'Invalid note availability');
    }
    demand(ids.size > 0 && ids.size <= 500, 'Invalid dataset size');
    demand(bundle.groups.length === GROUP_IDS.length, 'Unexpected group count');
    const groups = new Set();
    for (const g of bundle.groups) {
      demand(object(g) && GROUP_IDS.includes(g.id) && !groups.has(g.id), 'Unknown or duplicate group ID');
      demand(text(g.name, 80) && text(g.description) && /^[a-zA-Z0-9_]+$/.test(g.cover), 'Invalid group');
      groups.add(g.id);
    }
    return bundle;
  }
  function modelInput(bundle) {
    return {
      notes: bundle.notes.map(n => ({ id: n.id, title: n.title, description: n.description, tags: n.tags })),
      groups: bundle.groups.map(g => ({ id: g.id, name: g.name, description: g.description }))
    };
  }
  async function datasetHash(bundle) {
    demand(root.crypto && root.crypto.subtle, 'SHA-256 unavailable; use HTTPS or localhost');
    const bytes = new TextEncoder().encode(canonical(modelInput(bundle)));
    const digest = await root.crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('');
  }
  function validateResult(result, bundle, hash, expectedMode) {
    const keys = ['schemaVersion','mode','provider','model','generatedAt','datasetHash','promptVersion','inputFields','notesCount','assignments'];
    demand(exactKeys(result, keys), 'Unexpected classification fields');
    demand(result.schemaVersion === VERSION && result.promptVersion === PROMPT, 'Unsupported result version');
    demand(result.mode === expectedMode && ['real','offline','precomputed'].includes(result.mode), 'Incorrect result mode');
    demand(result.datasetHash === hash && /^[a-f0-9]{64}$/.test(hash), 'Classification dataset mismatch');
    demand(JSON.stringify(result.inputFields) === JSON.stringify(FIELDS), 'Unexpected model input fields');
    demand(result.notesCount === bundle.notes.length && Number.isInteger(result.notesCount), 'Incorrect note count');
    const generated = typeof result.generatedAt === 'string' ? Date.parse(result.generatedAt) : NaN;
    demand(Number.isFinite(generated) && generated <= Date.now() + 5 * 60 * 1000, 'Invalid generation date');
    if (expectedMode === 'real') demand(result.provider === 'openai' && text(result.model, 160), 'Invalid real result provenance');
    else if (expectedMode === 'precomputed') demand(result.provider === 'codex' && result.model === 'Codex', 'Invalid precomputed provenance');
    else demand(result.provider === 'offline-fixture' && result.model === null, 'Invalid offline provenance');
    demand(Array.isArray(result.assignments) && result.assignments.length === bundle.notes.length, 'Incomplete assignments');
    const ids = new Set(bundle.notes.map(n => n.id));
    const seen = new Set();
    for (const row of result.assignments) {
      demand(exactKeys(row, ['noteId','memberships','unclassifiedReason']) && ids.has(row.noteId) && !seen.has(row.noteId), 'Invalid or duplicate assigned note');
      seen.add(row.noteId);
      demand(Array.isArray(row.memberships) && row.memberships.length <= GROUP_IDS.length, 'Invalid memberships');
      const groupSet = new Set();
      for (const m of row.memberships) {
        demand(exactKeys(m, ['groupId','reason']) && GROUP_IDS.includes(m.groupId) && !groupSet.has(m.groupId) && text(m.reason, 400), 'Invalid group or explanation');
        groupSet.add(m.groupId);
      }
      demand(row.memberships.length ? row.unclassifiedReason === null : text(row.unclassifiedReason, 400), 'Invalid unclassified explanation');
    }
    return result;
  }
  async function createStore(rawBundle, options = {}) {
    const bundle = validateDataset(rawBundle);
    const hash = await datasetHash(bundle);
    const offline = validateResult(bundle.offline, bundle, hash, 'offline');
    let precomputed = null;
    if (bundle.precomputed) {
      try { precomputed = validateResult(bundle.precomputed, bundle, hash, 'precomputed'); }
      catch (_) { /* A stale or invalid preclassification must never be displayed. */ }
    }
    let storage = options.storage;
    if (!storage) {
      try { storage = root.localStorage; } catch (_) { /* Disabled storage is supported. */ }
      storage = storage || { getItem: () => null, setItem: () => {}, removeItem: () => {} };
    }
    const fetcher = options.fetcher || root.fetch.bind(root);
    const forceOffline = options.forceOffline === true;
    const fallback = !forceOffline && precomputed ? precomputed : offline;
    const fallbackSource = fallback.mode === 'precomputed' ? 'precomputed' : 'offline';
    let result = fallback;
    let source = fallbackSource;
    let status = forceOffline ? 'offline_requested' : precomputed ? 'precomputed_loaded' : 'not_generated';
    let byNote = new Map(result.assignments.map(row => [row.noteId, row]));
    function apply(value, origin) {
      result = value;
      source = origin;
      byNote = new Map(result.assignments.map(row => [row.noteId, row]));
    }
    function readCache() {
      try {
        const cached = JSON.parse(storage.getItem(CACHE_KEY) || 'null');
        demand(exactKeys(cached, ['cachedAt','result']), 'Invalid cache');
        demand(Number.isFinite(cached.cachedAt) && cached.cachedAt <= Date.now() && Date.now() - cached.cachedAt <= MAX_CACHE_AGE, 'Expired cache');
        return validateResult(cached.result, bundle, hash, 'real');
      } catch (_) {
        try { storage.removeItem(CACHE_KEY); } catch (_) { /* Storage can be disabled. */ }
        return null;
      }
    }
    function writeCache(value) {
      try { storage.setItem(CACHE_KEY, JSON.stringify({ cachedAt: Date.now(), result: value })); } catch (_) { /* The page still works without caching. */ }
    }
    async function refresh() {
      if (forceOffline) return false;
      try {
        let incoming;
        if (Object.prototype.hasOwnProperty.call(bundle, 'real')) incoming = bundle.real;
        else if (root.location.protocol === 'file:') { status = 'file_offline'; return false; }
        else {
          const response = await fetcher('data/classifications.real.json', { cache: 'no-store' });
          demand(response.ok, 'Result file unavailable');
          incoming = await response.json();
        }
        if (object(incoming) && incoming.mode === 'unavailable') {
          // An explicit not-generated marker must not resurrect an old real cache.
          try { storage.removeItem(CACHE_KEY); } catch (_) {}
          apply(fallback, fallbackSource); status = precomputed ? 'precomputed_loaded' : 'not_generated'; return false;
        }
        const checked = validateResult(incoming, bundle, hash, 'real');
        apply(checked, 'file'); writeCache(checked); status = 'loaded'; return true;
      } catch (_) {
        const cached = readCache();
        if (cached) { apply(cached, 'cache'); status = 'cached_result'; return true; }
        apply(fallback, fallbackSource); status = 'invalid_or_unavailable'; return false;
      }
    }
    return {
      notes: bundle.notes, groups: bundle.groups, hash, refresh,
      get result() { return result; },
      get mode() { return result.mode; },
      get source() { return source; },
      get status() { return status; },
      memberships(id) { return byNote.get(id)?.memberships || []; },
      reason(id, groupId) {
        const row = byNote.get(id);
        return row?.memberships.find(m => m.groupId === groupId)?.reason || row?.memberships.map(m => m.reason).join('；') || row?.unclassifiedReason || '暂无分类依据';
      },
      label() {
        if (result.mode === 'precomputed') return 'Codex AI 语义预分类 · 未调用付费 API';
        if (result.mode === 'offline') return '离线模拟分类 · 非真实模型输出';
        return '真实 AI 文本分类 · ' + result.model + (source === 'cache' ? ' · 本地缓存' : '');
      }
    };
  }
  root.REClassification = { createStore, validateDataset, validateResult, modelInput, datasetHash, canonical, CACHE_KEY };
})(globalThis);
