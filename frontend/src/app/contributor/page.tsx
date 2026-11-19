"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, post } from "@/lib/api";
import { type Capture, SYNC_LABEL, listCaptures, newClientId, putCapture, removeCapture, syncAll, syncOne } from "@/lib/offline";
import type { Contest, PollingUnit, Receipt } from "@/lib/types";
import { ReceiptCard } from "@/components/ReceiptCard";
import { Button, Card, ErrorText, Hash, Loading, Notice, fmtTime, inputCls } from "@/components/ui";

type Assignment = { id: number; status: string; is_primary: boolean; polling_unit: PollingUnit; note: string; election_id: number };
type Me = { classification_label: string; can_submit_field_evidence: boolean; user: { name: string } };
type Avail = { polling_unit: PollingUnit; active_assignments: number; has_primary: boolean; mine: string | null };

export default function Contributor() {
  const [me, setMe] = useState<Me | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [contest, setContest] = useState<Contest | null>(null);
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [history, setHistory] = useState<Receipt[]>([]);
  const [online, setOnline] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [m, a, s] = await Promise.all([
        api<Me>("/volunteers/me"),
        api<Assignment[]>("/assignments/mine"),
        api<{ contests: Contest[] }>("/public/summary"),
      ]);
      setMe(m);
      setAssignments(a);
      setContest(s.contests[0] ?? null);
      setHistory(await api<Receipt[]>("/evidence/mine"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load");
    }
    setCaptures(await listCaptures().catch(() => []));
    setLoading(false);
  }, []);

  const sync = useCallback(async () => {
    setCaptures(await syncAll());
    api<Receipt[]>("/evidence/mine").then(setHistory).catch(() => {});
  }, []);

  useEffect(() => {
    setOnline(navigator.onLine);
    load();
    const on = () => { setOnline(true); sync(); };
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    window.addEventListener("veravote:user", load);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      window.removeEventListener("veravote:user", load);
    };
  }, [load, sync]);

  if (loading) return <Loading />;
  if (error) return <div className="space-y-2"><ErrorText error={error} /><p className="text-sm">Choose a volunteer in “Viewing as” at the top, e.g. Tunde or Ngozi.</p></div>;
  if (!me) return null;

  const accepted = assignments.filter((a) => a.status === "accepted");
  const pendingSync = captures.filter((c) => c.state !== "received");

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">My assignments</h1>
          <p className="text-sm text-ink-soft">{me.user.name}, {me.classification_label}</p>
        </div>
        <SafetyButton onDone={load} />
      </header>

      {!online && <Notice tone="warn">You are offline. You can still capture evidence. It is saved on this phone and uploads when you have signal again.</Notice>}
      {!me.can_submit_field_evidence && (
        <Notice>
          Finish your <Link className="underline" href="/volunteer">volunteer training</Link> before you can submit field evidence.
          You can still <Link className="underline" href="/submit">submit a citizen lead</Link>.
        </Notice>
      )}

      {accepted.map((a) => contest && (
        <CaptureCard key={a.id} a={a} contest={contest} onSaved={async (c) => { setCaptures(await listCaptures()); if (navigator.onLine) { await syncOne(c); setCaptures(await listCaptures()); api<Receipt[]>("/evidence/mine").then(setHistory); } }} />
      ))}

      {captures.length > 0 && (
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">On this phone</h2>
            {pendingSync.length > 0 && <Button variant="secondary" onClick={sync} disabled={!online}>Sync now</Button>}
          </div>
          <ul className="divide-y divide-rule text-sm">
            {captures.map((c) => (
              <li key={c.client_id} className="py-2 flex flex-wrap items-center gap-2 justify-between">
                <span>
                  {c.polling_unit_name}
                  <span className="block text-xs text-ink-soft">Captured {fmtTime(c.device_time)} by the phone's clock. Upload attempts: {c.attempts}</span>
                  {c.error && <span className="block text-xs text-differ">{c.error}</span>}
                </span>
                <span className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${c.state === "received" ? "text-agree" : c.state === "rejected" ? "text-differ" : "text-wait"}`}>{SYNC_LABEL[c.state]}</span>
                  {c.state === "received" && <span className="font-mono text-xs">{c.receipt?.receipt_code}</span>}
                  {(c.state === "received" || c.state === "rejected") && (
                    <button className="text-xs underline text-ink-soft" onClick={async () => { await removeCapture(c.client_id); setCaptures(await listCaptures()); }}>Clear</button>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="space-y-3">
        <h2 className="font-semibold">All my assignments</h2>
        {assignments.length === 0 && <p className="text-sm text-ink-soft">No assignments yet.</p>}
        <ul className="divide-y divide-rule text-sm">
          {assignments.map((a) => (
            <li key={a.id} className="py-2 flex flex-wrap gap-2 justify-between items-center">
              <span>
                <Link className="font-medium underline" href={`/pu/${a.polling_unit.id}`}>{a.polling_unit.official_name}</Link>
                <span className="block text-xs text-ink-soft">{a.polling_unit.official_code}, {a.is_primary ? "Primary contributor" : "Additional contributor"}</span>
              </span>
              <span className="flex items-center gap-2">
                <span className="text-xs rounded bg-paper px-2 py-0.5">{a.status}</span>
                {a.status === "approved" && (
                  <>
                    <Button className="!px-2 !py-1" onClick={async () => { await post(`/assignments/${a.id}/respond`, { accept: true }); load(); }}>Accept</Button>
                    <Button variant="secondary" className="!px-2 !py-1" onClick={async () => { await post(`/assignments/${a.id}/respond`, { accept: false }); load(); }}>Decline</Button>
                  </>
                )}
                {["requested", "approved", "accepted"].includes(a.status) && (
                  <button className="text-xs underline text-ink-soft" onClick={async () => { await post(`/assignments/${a.id}/withdraw`); load(); }}>Withdraw</button>
                )}
              </span>
            </li>
          ))}
        </ul>
        <p className="text-xs text-ink-soft">Assignments are VeraVote coverage arrangements, not INEC accreditation.</p>
        {me.can_submit_field_evidence && contest && <RequestAssignment electionId={contest.election.id} onDone={load} />}
      </Card>

      <Card className="space-y-3">
        <h2 className="font-semibold">My submissions</h2>
        {history.length === 0 && <p className="text-sm text-ink-soft">Nothing submitted yet.</p>}
        <ul className="divide-y divide-rule text-sm">
          {history.map((r) => (
            <li key={r.receipt_code} className="py-2 flex flex-wrap justify-between gap-2">
              <span>
                <span className="font-mono">{r.receipt_code}</span>, {r.polling_unit.name}
                <span className="block text-xs text-ink-soft">Received {fmtTime(r.server_received_time)}, <Hash value={r.file_sha256} /></span>
                {r.review_note && <span className="block text-xs">Reviewer note: {r.review_note}</span>}
              </span>
              <span className="text-xs rounded bg-paper px-2 py-0.5 h-fit">{r.status.replace(/_/g, " ")}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function CaptureCard({ a, contest, onSaved }: { a: Assignment; contest: Contest; onSaved: (c: Capture) => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [warn, setWarn] = useState<string | null>(null);
  const [last, setLast] = useState<Receipt | null>(null);
  const [inputKey, setInputKey] = useState(0); // remount the file input to clear it after saving

  function choose(f: File | null) {
    setFile(f);
    setWarn(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(f && f.type.startsWith("image/") ? URL.createObjectURL(f) : null);
    // Simple quality check (PRD §7.2 step 4): tiny files are usually unreadable.
    if (f && f.size < 30 * 1024) setWarn("This image is very small and may be unreadable. Retake it if it is safe to do so.");
  }

  async function save() {
    if (!file) return;
    const c: Capture = {
      client_id: newClientId(), polling_unit_id: a.polling_unit.id, polling_unit_name: a.polling_unit.official_name,
      contest_id: contest.id, device_time: new Date().toISOString(), captured_offline: !navigator.onLine,
      blob: file, filename: file.name || "capture.jpg", state: navigator.onLine ? "saved" : "waiting", attempts: 0,
    };
    await putCapture(c);
    choose(null);
    setInputKey((k) => k + 1);
    await onSaved(c);
    const after = (await listCaptures()).find((x) => x.client_id === c.client_id);
    if (after?.receipt) setLast(after.receipt);
  }

  return (
    <Card className="space-y-3">
      <div>
        <p className="text-xs text-ink-soft">Assigned polling unit</p>
        <h2 className="font-semibold">{a.polling_unit.official_name}</h2>
        <p className="text-xs text-ink-soft">{a.polling_unit.official_code}, {a.polling_unit.location_description}</p>
      </div>
      <p className="text-sm">{contest.office}, {contest.election.name}</p>
      <ul className="text-xs text-ink-soft list-disc pl-5">
        <li>Photograph the whole result form, flat, with all four corners visible.</li>
        <li>Do not crop, filter or edit. Never block voters or officials.</li>
      </ul>
      <input key={inputKey} type="file" accept="image/*" capture="environment" aria-label={`Result form photo for ${a.polling_unit.official_name}`} onChange={(e) => choose(e.target.files?.[0] ?? null)} className="text-sm" />
      {/* eslint-disable-next-line @next/next/no-img-element -- local blob preview */}
      {preview && <img src={preview} alt="Preview of the captured result form" className="max-h-64 rounded border border-rule" />}
      {warn && <Notice tone="warn">{warn}</Notice>}
      <Button disabled={!file} onClick={save}>Save and submit</Button>
      {last && <ReceiptCard r={last} />}
    </Card>
  );
}

function RequestAssignment({ electionId, onDone }: { electionId: number; onDone: () => void }) {
  const [wards, setWards] = useState<{ id: number; name: string; lga: string }[]>([]);
  const [ward, setWard] = useState("");
  const [avail, setAvail] = useState<Avail[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const states = await api<{ id: number }[]>("/states");
      const out: { id: number; name: string; lga: string }[] = [];
      for (const s of states)
        for (const l of await api<{ id: number; name: string }[]>(`/lgas?state_id=${s.id}`))
          for (const w of await api<{ id: number; name: string }[]>(`/wards?lga_id=${l.id}`)) out.push({ ...w, lga: l.name });
      setWards(out);
    })().catch(() => {});
  }, []);

  useEffect(() => {
    if (ward) api<Avail[]>(`/assignments/availability?ward_id=${ward}&election_id=${electionId}`).then(setAvail);
  }, [ward, electionId]);

  return (
    <details className="text-sm border-t border-rule pt-3">
      <summary className="cursor-pointer text-violet">Request another polling unit</summary>
      <div className="space-y-2 mt-2">
        <select className={inputCls} value={ward} onChange={(e) => setWard(e.target.value)}>
          <option value="">Choose a ward…</option>
          {wards.map((w) => <option key={w.id} value={w.id}>{w.name}, {w.lga}</option>)}
        </select>
        <ul className="divide-y divide-rule">
          {avail.map((u) => (
            <li key={u.polling_unit.id} className="py-2 flex justify-between items-center gap-2">
              <span>
                {u.polling_unit.official_name}
                <span className="block text-xs text-ink-soft">{u.has_primary ? "Has a primary contributor" : "No primary contributor yet"}, {u.active_assignments} active</span>
              </span>
              {u.mine ? (
                <span className="text-xs text-ink-soft">{u.mine}</span>
              ) : (
                <Button variant="secondary" className="!px-2 !py-1" onClick={async () => {
                  setError(null);
                  try { await post("/assignments/request", { polling_unit_id: u.polling_unit.id, election_id: electionId }); onDone(); setWard(""); setAvail([]); }
                  catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
                }}>Request</Button>
              )}
            </li>
          ))}
        </ul>
        <ErrorText error={error} />
      </div>
    </details>
  );
}

function SafetyButton({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState("threat");
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <div>
      <Button variant="danger" onClick={() => setOpen(!open)} aria-expanded={open}>Safety: withdraw or report</Button>
      {open && (
        <Card className="mt-2 space-y-2 max-w-sm">
          {msg ? (
            <p className="text-sm">{msg}</p>
          ) : (
            <>
              <p className="text-sm">Your safety matters more than any submission. This withdraws you from all your assignments.</p>
              <select className={inputCls} value={kind} onChange={(e) => setKind(e.target.value)}>
                <option value="threat">I was threatened</option>
                <option value="asked_to_leave">I was asked to leave</option>
                <option value="access_denied">I could not access the polling unit</option>
                <option value="other">Other</option>
              </select>
              <Button variant="danger" onClick={async () => {
                const r = await post<{ message: string }>("/safety/report", { kind, withdraw: true });
                setMsg(r.message);
                onDone();
              }}>Withdraw now</Button>
            </>
          )}
        </Card>
      )}
    </div>
  );
}
