// ---------------------------------------------------------------------------
// Device store (F55): outing records and journal photos in IndexedDB, so they
// survive a reload and never leave the phone. Plain IndexedDB, no library.
//
//   activity_record  keyPath id     one row per completed outing
//   journey_photo    keyPath id     one row per photo, the image as a Blob;
//                    index runId    links a photo to its outing
//
// The schema is versioned from the first release (DB_VERSION). Every call
// resolves even when IndexedDB is missing or fails (private mode, jsdom in
// unit tests): the stores then simply keep working in memory for the session.
// ---------------------------------------------------------------------------

const DB_NAME = 'active-together'
const DB_VERSION = 1
export const RECORDS = 'activity_record'
export const PHOTOS = 'journey_photo'

let dbPromise = null

function openDb() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve) => {
    if (typeof indexedDB === 'undefined') return resolve(null)
    let req
    try {
      req = indexedDB.open(DB_NAME, DB_VERSION)
    } catch {
      return resolve(null)
    }
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(RECORDS)) db.createObjectStore(RECORDS, { keyPath: 'id' })
      if (!db.objectStoreNames.contains(PHOTOS)) {
        db.createObjectStore(PHOTOS, { keyPath: 'id' }).createIndex('runId', 'runId', { unique: false })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => resolve(null)
    req.onblocked = () => resolve(null)
  })
  return dbPromise
}

// Run one transaction; resolves with fn's IDBRequest result, or null on any failure.
async function tx(store, mode, fn) {
  const db = await openDb()
  if (!db) return null
  return new Promise((resolve) => {
    try {
      const t = db.transaction(store, mode)
      const req = fn(t.objectStore(store))
      t.oncomplete = () => resolve(req?.result ?? true)
      t.onerror = () => resolve(null)
      t.onabort = () => resolve(null)
    } catch {
      resolve(null)
    }
  })
}

export const getAll = (store) => tx(store, 'readonly', (s) => s.getAll()).then((r) => (Array.isArray(r) ? r : []))
export const put = (store, value) => tx(store, 'readwrite', (s) => s.put(value))
export const remove = (store, id) => tx(store, 'readwrite', (s) => s.delete(id))

// Delete every photo of one outing (D11 abandoned run, D15 deleted record).
export function removeByRun(runId) {
  return tx(PHOTOS, 'readwrite', (s) => {
    const req = s.index('runId').openCursor(IDBKeyRange.only(runId))
    req.onsuccess = () => {
      const c = req.result
      if (c) {
        c.delete()
        c.continue()
      }
    }
    return req
  })
}

// Ask the browser not to clear this site's storage under pressure. Asked once,
// on the first write; the answer only changes how safe the data is.
let persistAsked = false
export function askPersist() {
  if (persistAsked) return
  persistAsked = true
  try {
    navigator.storage?.persist?.()
  } catch {
    /* not supported */
  }
}
