// Offline-first evidence queue (PRD §8). Captures live in IndexedDB until the server issues a receipt.
import { ApiError, post } from "./api";
import type { Receipt } from "./types";

export type SyncState = "saved" | "waiting" | "uploading" | "received" | "failed" | "rejected";

export type Capture = {
  client_id: string;
  polling_unit_id: number;
  polling_unit_name: string;
  contest_id: number;
  device_time: string;
  captured_offline: boolean;
  blob: Blob;
  filename: string;
  state: SyncState;
  attempts: number;
  error?: string;
  receipt?: Receipt;
};

export const SYNC_LABEL: Record<SyncState, string> = {
  saved: "Saved on this phone",
  waiting: "Waiting for connection",
  uploading: "Uploading…",
  received: "Received by server",
  failed: "Upload failed — will retry",
  rejected: "Not accepted",
};

const DB = "veravote";
const STORE = "captures";

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "client_id" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function tx<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const req = fn(db.transaction(STORE, mode).objectStore(STORE));
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export const listCaptures = () => tx<Capture[]>("readonly", (s) => s.getAll() as IDBRequest<Capture[]>);
export const putCapture = (c: Capture) => tx("readwrite", (s) => s.put(c));
export const removeCapture = (id: string) => tx("readwrite", (s) => s.delete(id));

export function newClientId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** Upload one capture. The client id makes retries safe: the server returns the original receipt. */
export async function syncOne(c: Capture): Promise<Capture> {
  if (c.state === "received" || c.state === "rejected") return c;
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    const next = { ...c, state: "waiting" as const };
    await putCapture(next);
    return next;
  }
  await putCapture({ ...c, state: "uploading" });
  const fd = new FormData();
  fd.set("client_submission_id", c.client_id);
  fd.set("polling_unit_id", String(c.polling_unit_id));
  fd.set("contest_id", String(c.contest_id));
  fd.set("device_reported_time", c.device_time);
  fd.set("captured_offline", String(c.captured_offline));
  fd.set("file", c.blob, c.filename);
  try {
    const receipt = await post<Receipt>("/evidence", fd);
    const next = { ...c, state: "received" as const, receipt, attempts: c.attempts + 1, error: undefined };
    await putCapture(next);
    return next;
  } catch (e) {
    const permanent = e instanceof ApiError && e.status >= 400 && e.status < 500;
    const next = {
      ...c,
      attempts: c.attempts + 1,
      state: (permanent ? "rejected" : "failed") as SyncState,
      error: e instanceof Error ? e.message : "Upload failed",
    };
    await putCapture(next);
    return next;
  }
}

export async function syncAll(): Promise<Capture[]> {
  const all = await listCaptures();
  const out: Capture[] = [];
  for (const c of all) out.push(await syncOne(c));
  return out;
}
