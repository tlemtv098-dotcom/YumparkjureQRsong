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

initStorage();

export class PlaylistManager {
  static getAll() {
    return getAllFromStorage();
  }

  static save(name, songs) {
    const all = this.getAll();
    all[name] = songs;
    setAllToStorage(all);
  }

  static load(name) {
    return this.getAll()[name] || [];
  }

  static delete(name) {
    const all = this.getAll();
    delete all[name];
    setAllToStorage(all);
  }

  static rename(oldName, newName) {
    const all = this.getAll();
    if (all[oldName]) {
      all[newName] = all[oldName];
      delete all[oldName];
      setAllToStorage(all);
    }
  }

  static exportJSON() {
    return JSON.stringify(this.getAll(), null, 2);
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

// Expose for non-module inline scripts
if (typeof window !== 'undefined') {
  window.PlaylistManager = PlaylistManager;
}