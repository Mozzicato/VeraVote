// API client. Auth is SIMULATED: the chosen demo user's id is sent as X-Demo-User.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const USER_KEY = "veravote.demoUser";

export function getDemoUser(): number | null {
  try {
    const v = localStorage.getItem(USER_KEY);
    return v ? Number(v) : null;
  } catch {
    return null;
  }
}

export function setDemoUser(id: number | null) {
  try {
    if (id === null) localStorage.removeItem(USER_KEY);
    else localStorage.setItem(USER_KEY, String(id));
  } catch {
    /* storage unavailable: the switcher still works for this page view */
  }
  window.dispatchEvent(new Event("veravote:user"));
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const d = (body as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => x?.msg ?? String(x)).join("; ");
  }
  return "Something went wrong";
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const uid = typeof window !== "undefined" ? getDemoUser() : null;
  if (uid) headers.set("X-Demo-User", String(uid));
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, detail(body));
  return body as T;
}

export const post = <T = unknown>(path: string, data?: unknown) =>
  api<T>(path, { method: "POST", body: data instanceof FormData ? data : JSON.stringify(data ?? {}) });

/** Fetch a protected file with the demo header and return an object URL for <img>. */
export async function fileUrl(path: string): Promise<string> {
  const headers = new Headers();
  const uid = getDemoUser();
  if (uid) headers.set("X-Demo-User", String(uid));
  const res = await fetch(`${API_URL}${path}`, { headers });
  if (!res.ok) throw new ApiError(res.status, "File not available");
  return URL.createObjectURL(await res.blob());
}
