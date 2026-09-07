const STORAGE_KEY = 'ym_playlists_v1';

let storage = localStorage;
let useMemoryFallback = false;
const memoryStore = new Map();

function initStorage() {
  try {
    const testKey = '__storage_test__';
    storage.setItem(testKey, testKey);
    storage.removeItem(testKey);
    useMemoryFallback = false;
  } catch (e) {
    useMemoryFallback = true;
    console.warn('localStorage unavailable (private mode?), falling back to in-memory storage. Playlists will not persist across reloads.');
  }
}

function getStorage() {
  if (useMemoryFallback) {
    return memoryStore;
  }
  return storage;
}

function getAllFromStorage() {
  const store = getStorage();
  if (useMemoryFallback) {
    const data = store.get(STORAGE_KEY);
    return data ? JSON.parse(data) : {};
  }
  try {
    const raw = store.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    console.warn('Failed to read playlists from localStorage:', e);
    return {};
  }
}

function setAllToStorage(data) {
  const store = getStorage();
  const json = JSON.stringify(data);
  if (useMemoryFallback) {
    store.set(STORAGE_KEY, json);
  } else {
    try {
      store.setItem(STORAGE_KEY, json);
    } catch (e) {
      console.warn('Failed to write playlists to localStorage:', e);
    }
  }
}

function getCSRFToken() {
  try {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  } catch (e) {
    return '';
  }
}

function isAuthFailure(res) {
  if (!res) return false;
  if (res.status === 401 || res.status === 403 || res.status === 302) return true;
  if (res.redirected && res.url && res.url.includes('/accounts/login')) return true;
  const ct = res.headers ? (res.headers.get('content-type') || '') : '';
  if (ct.includes('text/html') && res.url && res.url.includes('/accounts/login')) return true;
  return false;
}

initStorage();

export class PlaylistManager {
  static _idMap = {};
  static _apiAvailable = null;

  static async _fetchJson(url, opts = {}) {
    const headers = opts.headers || {};
    if (opts.method && opts.method !== 'GET' && !headers['X-CSRFToken']) {
      const token = getCSRFToken();
      if (token) headers['X-CSRFToken'] = token;
    }
    const res = await fetch(url, { credentials: 'same-origin', ...opts, headers });
    return res;
  }

  static async getAll() {
    try {
      const res = await fetch('/api/playlists/', { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (res.ok) {
        if (res.redirected && res.url.includes('/accounts/login')) {
          this._apiAvailable = false;
          return getAllFromStorage();
        }
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('text/html')) {
          this._apiAvailable = false;
          return getAllFromStorage();
        }
        const data = await res.json();
        const playlists = data.playlists || [];
        const map = {};
        const idMap = {};
        for (const p of playlists) {
          map[p.name] = p.songs || [];
          idMap[p.name] = p.id;
        }
        this._idMap = idMap;
        this._apiAvailable = true;
        return map;
      }
      if (isAuthFailure(res)) {
        this._apiAvailable = false;
        return getAllFromStorage();
      }
      // other error -> fallback
      this._apiAvailable = false;
      return getAllFromStorage();
    } catch (e) {
      this._apiAvailable = false;
      return getAllFromStorage();
    }
  }

  static async save(name, songs) {
    // try API first
    try {
      const res = await this._fetchJson('/api/playlists/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        body: JSON.stringify({ name, songs }),
      });
      if (res.ok) {
        const data = await res.json();
        this._idMap[name] = data.id;
        this._apiAvailable = true;
        return data;
      }
      if (isAuthFailure(res)) {
        this._apiAvailable = false;
        const all = getAllFromStorage();
        all[name] = songs;
        setAllToStorage(all);
        return { fallback: true };
      }
      if (res.status === 400) {
        const data = await res.json().catch(() => ({}));
        const err = new Error(data.error || 'duplicate');
        err.status = 400;
        err.data = data;
        throw err;
      }
      // other non-ok -> fallback to local as generic
      const all = getAllFromStorage();
      all[name] = songs;
      setAllToStorage(all);
      return { fallback: true };
    } catch (e) {
      if (e.status === 400) throw e;
      // network or other -> fallback local if not already handled
      // Check if e is TypeError (Failed to fetch)
      const all = getAllFromStorage();
      // Avoid overwriting if already API succeeded? but we are here due to catch, so do local fallback
      // Only fallback if not duplicate error
      if (!e.status || e.status !== 400) {
        // if we haven't already saved locally in try branch, save now
        // but try branch already saved for auth failure; this catch will second-save for network error
        // ensure idempotent
        try {
          // don't double-save if already saved? just ensure
          const current = getAllFromStorage();
          // if this is network error, we haven't saved yet (since fetch threw)
          // so save
          if (!current[name] || JSON.stringify(current[name]) !== JSON.stringify(songs)) {
            current[name] = songs;
            setAllToStorage(current);
          }
          return { fallback: true };
        } catch (_) {
          return { fallback: true };
        }
      }
      throw e;
    }
  }

  static async load(name) {
    try {
      const res = await fetch('/api/playlists/', { credentials: 'same-origin' });
      if (res.ok) {
        if (res.redirected && res.url.includes('/accounts/login')) {
          return getAllFromStorage()[name] || [];
        }
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('text/html')) {
          return getAllFromStorage()[name] || [];
        }
        const data = await res.json();
        const pl = (data.playlists || []).find((p) => p.name === name);
        if (pl) {
          this._apiAvailable = true;
          // update idMap
          this._idMap[name] = pl.id;
          return pl.songs || [];
        }
        // not found in API, fallback to local check
        return getAllFromStorage()[name] || [];
      }
      if (isAuthFailure(res)) {
        return getAllFromStorage()[name] || [];
      }
      return getAllFromStorage()[name] || [];
    } catch (e) {
      return getAllFromStorage()[name] || [];
    }
  }

  static async delete(name) {
    try {
      const resList = await fetch('/api/playlists/', { credentials: 'same-origin' });
      if (resList.ok) {
        if (resList.redirected && resList.url.includes('/accounts/login')) {
          const all = getAllFromStorage();
          delete all[name];
          setAllToStorage(all);
          return { fallback: true };
        }
        const ct = resList.headers.get('content-type') || '';
        if (ct.includes('text/html')) {
          const all = getAllFromStorage();
          delete all[name];
          setAllToStorage(all);
          return { fallback: true };
        }
        const data = await resList.json();
        const pl = (data.playlists || []).find((p) => p.name === name);
        if (pl) {
          const delRes = await this._fetchJson(`/api/playlists/${pl.id}/`, {
            method: 'DELETE',
          });
          if (delRes.ok) {
            delete this._idMap[name];
            this._apiAvailable = true;
            return { status: 'deleted' };
          }
          if (isAuthFailure(delRes)) {
            const all = getAllFromStorage();
            delete all[name];
            setAllToStorage(all);
            return { fallback: true };
          }
          if (delRes.status === 404) {
            const all = getAllFromStorage();
            delete all[name];
            setAllToStorage(all);
            return { fallback: true };
          }
          // other error fallback
          const all = getAllFromStorage();
          delete all[name];
          setAllToStorage(all);
          return { fallback: true };
        } else {
          // not found in API, delete locally
          const all = getAllFromStorage();
          delete all[name];
          setAllToStorage(all);
          return { fallback: true };
        }
      }
      if (isAuthFailure(resList)) {
        const all = getAllFromStorage();
        delete all[name];
        setAllToStorage(all);
        return { fallback: true };
      }
      const all = getAllFromStorage();
      delete all[name];
      setAllToStorage(all);
      return { fallback: true };
    } catch (e) {
      const all = getAllFromStorage();
      delete all[name];
      setAllToStorage(all);
      return { fallback: true };
    }
  }

  static async rename(oldName, newName) {
    try {
      const resList = await fetch('/api/playlists/', { credentials: 'same-origin' });
      if (resList.ok) {
        if (resList.redirected && resList.url.includes('/accounts/login')) {
          const all = getAllFromStorage();
          if (all[oldName]) {
            all[newName] = all[oldName];
            delete all[oldName];
            setAllToStorage(all);
          }
          return { fallback: true };
        }
        const ct = resList.headers.get('content-type') || '';
        if (ct.includes('text/html')) {
          const all = getAllFromStorage();
          if (all[oldName]) {
            all[newName] = all[oldName];
            delete all[oldName];
            setAllToStorage(all);
          }
          return { fallback: true };
        }
        const data = await resList.json();
        const pl = (data.playlists || []).find((p) => p.name === oldName);
        if (pl) {
          const putRes = await this._fetchJson(`/api/playlists/${pl.id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ name: newName }),
          });
          if (putRes.ok) {
            const out = await putRes.json();
            delete this._idMap[oldName];
            this._idMap[newName] = pl.id;
            this._apiAvailable = true;
            return out;
          }
          if (isAuthFailure(putRes)) {
            const all = getAllFromStorage();
            if (all[oldName]) {
              all[newName] = all[oldName];
              delete all[oldName];
              setAllToStorage(all);
            }
            return { fallback: true };
          }
          if (putRes.status === 400) {
            const d = await putRes.json().catch(() => ({}));
            const err = new Error(d.error || 'duplicate');
            err.status = 400;
            err.data = d;
            throw err;
          }
          const all = getAllFromStorage();
          if (all[oldName]) {
            all[newName] = all[oldName];
            delete all[oldName];
            setAllToStorage(all);
          }
          return { fallback: true };
        } else {
          const all = getAllFromStorage();
          if (all[oldName]) {
            all[newName] = all[oldName];
            delete all[oldName];
            setAllToStorage(all);
          }
          return { fallback: true };
        }
      }
      if (isAuthFailure(resList)) {
        const all = getAllFromStorage();
        if (all[oldName]) {
          all[newName] = all[oldName];
          delete all[oldName];
          setAllToStorage(all);
        }
        return { fallback: true };
      }
      const all = getAllFromStorage();
      if (all[oldName]) {
        all[newName] = all[oldName];
        delete all[oldName];
        setAllToStorage(all);
      }
      return { fallback: true };
    } catch (e) {
      if (e.status === 400) throw e;
      const all = getAllFromStorage();
      if (all[oldName]) {
        all[newName] = all[oldName];
        delete all[oldName];
        setAllToStorage(all);
      }
      return { fallback: true };
    }
  }

  static async addSongToPlaylist(playlistId, song) {
    const res = await this._fetchJson(`/api/playlists/${playlistId}/add-song/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify({ song }),
      credentials: 'same-origin',
    });
    if (res.ok) {
      const data = await res.json();
      this._apiAvailable = true;
      return data;
    }
    if (isAuthFailure(res)) {
      this._apiAvailable = false;
      const err = new Error('Unauthorized');
      err.status = 401;
      throw err;
    }
    if (res.status === 404) {
      const err = new Error('Playlist not found');
      err.status = 404;
      throw err;
    }
    if (res.status === 400) {
      const d = await res.json().catch(() => ({}));
      const err = new Error(d.error || 'Bad request');
      err.status = 400;
      err.data = d;
      throw err;
    }
    const err = new Error('Failed to add song');
    err.status = res.status;
    throw err;
  }

  static exportJSON() {
    return JSON.stringify(getAllFromStorage(), null, 2);
  }

  static importJSON(json) {
    try {
      const data = JSON.parse(json);
      if (data && typeof data === 'object') {
        setAllToStorage(data);
        return true;
      }
    } catch (e) {
      console.warn('Failed to import playlists:', e);
    }
    return false;
  }
}

const MIGRATED_KEY = 'ym_migrated_v1';
const LAST_PLAYLIST_KEY = 'ym_last_playlist';

async function migrateLocalToAccount() {
  try {
    if (useMemoryFallback) return;
    const store = getStorage();
    // already migrated - guarded via ym_migrated_v1
    try {
      if (store.getItem('ym_migrated_v1') || store.getItem(MIGRATED_KEY)) return;
    } catch (e) {
      return;
    }
    let raw = null;
    try {
      raw = store.getItem('ym_playlists_v1') || store.getItem(STORAGE_KEY);
    } catch (e) {
      return;
    }
    if (!raw) return;
    let localData;
    try {
      localData = JSON.parse(raw);
    } catch (e) {
      try { store.setItem('ym_migrated_v1', '1'); } catch (_) {}
      return;
    }
    if (!localData || typeof localData !== 'object' || Array.isArray(localData)) return;
    const entries = Object.entries(localData);
    if (entries.length === 0) {
      try { store.setItem('ym_migrated_v1', '1'); } catch (_) {}
      return;
    }
    // check auth: 200 means authenticated
    let authRes;
    try {
      authRes = await fetch('/api/playlists/', { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    } catch (e) {
      return;
    }
    if (!authRes) return;
    if (isAuthFailure(authRes)) return;
    if (!authRes.ok) return;
    if (authRes.redirected && authRes.url && authRes.url.includes('/accounts/login')) return;
    const ct = authRes.headers ? (authRes.headers.get('content-type') || '') : '';
    if (ct.includes('text/html')) return;
    // authenticated - sync each entry via POST /api/playlists/create/
    for (const [name, songs] of entries) {
      try {
        const res = await fetch('/api/playlists/create/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
          credentials: 'same-origin',
          body: JSON.stringify({ name, songs }),
        });
        if (res.ok) continue;
        if (res.status === 400) {
          // duplicate - ignore
          try { await res.json(); } catch (_) {}
          continue;
        }
        if (isAuthFailure(res)) return;
        // other errors ignore and continue
      } catch (e) {
        continue;
      }
    }
    try {
      store.removeItem('ym_playlists_v1');
      store.removeItem('ym_last_playlist');
      store.removeItem(STORAGE_KEY);
      store.removeItem(LAST_PLAYLIST_KEY);
      store.setItem('ym_migrated_v1', '1');
      store.setItem(MIGRATED_KEY, '1');
    } catch (e) {}
  } catch (e) {}
}

// trigger once on load, guarded by MIGRATED_KEY
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { migrateLocalToAccount(); });
  } else {
    migrateLocalToAccount();
  }
  // also attempt after first getAll() to cover cases where DOMContentLoaded already fired before script load
  const _origGetAll = PlaylistManager.getAll.bind(PlaylistManager);
  let _migrateAttempted = false;
  PlaylistManager.getAll = async function() {
    const result = await _origGetAll();
    if (!_migrateAttempted) {
      _migrateAttempted = true;
      try { await migrateLocalToAccount(); } catch (_) {}
    }
    return result;
  };
  // expose for testing
  PlaylistManager.migrateLocalToAccount = migrateLocalToAccount;
}

// Expose for non-module inline scripts
if (typeof window !== 'undefined') {
  window.PlaylistManager = PlaylistManager;
  window.migrateLocalToAccount = migrateLocalToAccount;
}
