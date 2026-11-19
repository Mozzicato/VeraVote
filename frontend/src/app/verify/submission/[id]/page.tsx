"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { api, post } from "@/lib/api";
import { checkFigures } from "@/lib/arithmetic";
import type { Evaluation, Flag, StatusKey } from "@/lib/types";
import { StatusBadge } from "@/components/Status";
import { DocViewer } from "@/components/DocViewer";
import { ComparisonList } from "@/components/Evidence";
import { Button, Card, ErrorText, Hash, Loading, Notice, fmtTime, inputCls } from "@/components/ui";

type F = { id: number; key: string; label: string; extracted_value: number | null; corrected_value: number | null; value: number | null; confidence: number; status: string; method: string; correction_reason: string | null; needs_attention: boolean };
type Detail = {
  id: number; receipt_code: string; category: string; classification_label: string; status: string; extraction_status: string;
  server_received_time: string; device_reported_time: string | null; captured_offline: boolean; sync_attempts: number;
  polling_unit: { id: number; code: string; name: string; lga: string; ward: string }; contest_id: number; unit_status: StatusKey | null;
  contributor: { id: number; name: string } | null; organisation: { name: string } | null;
  file_sha256: string | null; file_url: string | null; integrity_ok: boolean | null; source_url: string | null; description: string;
  follow_up_contact: string | null; is_forwarded_copy: string; review_note: string; fields: F[]; arithmetic: Flag[];
  unit: Evaluation; is_own_submission: boolean; history: { at: string; action: string; by: string; new: Record<string, unknown> | null }[];
};
type Edit = { value: string; unreadable: boolean; reason: string };

export default function SubmissionReview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [d, setD] = useState<Detail | null>(null);
  const [edits, setEdits] = useState<Record<number, Edit>>({});
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const apply = (det: Detail) => {
    setD(det);
    setEdits(Object.fromEntries(det.fields.map((f) => [f.id, { value: f.value?.toString() ?? "", unreadable: f.status === "unreadable", reason: f.correction_reason ?? "" }])));
  };
  const load = useCallback(() => {
    api<Detail>(`/verification/submissions/${id}`).then(apply).catch((e) => setError(e.message));
  }, [id]);
  useEffect(load, [load]);

  if (error && !d) return <ErrorText error={error} />;
  if (!d) return <Loading />;
  const locked = d.extraction_status === "confirmed" || d.is_own_submission;
  // Checks run on what the reviewer currently sees, including unsaved edits.
  const liveFlags = checkFigures(Object.fromEntries(d.fields.map((f) => {
    const e = edits[f.id];
    return [f.key, !e || e.unreadable || e.value === "" ? null : Number(e.value)];
  })));

  async function run(fn: () => Promise<unknown>, msg: string) {
    setError(null);
    setSaved(null);
    try {
      const r = await fn();
      if (r && typeof r === "object" && "fields" in r && "receipt_code" in r) apply(r as Detail);
      else load();
      setSaved(msg);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  }

  const saveFields = () =>
    run(() => post(`/verification/submissions/${d.id}/fields`, {
      fields: d.fields.map((f) => {
        const e = edits[f.id];
        return { id: f.id, value: e.unreadable || e.value === "" ? null : Number(e.value), unreadable: e.unreadable, reason: e.reason || null };
      }),
    }), "Figures saved. Every change is in the audit log.");

  return (
    <div className="space-y-5">
      <Link href="/verify" className="text-sm underline">← Queue</Link>
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">{d.polling_unit.name}</h1>
          <p className="text-sm text-ink-soft">{d.polling_unit.code}, {d.polling_unit.ward}, {d.polling_unit.lga}</p>
        </div>
        {d.unit_status && <StatusBadge status={d.unit_status} size="lg" />}
      </header>
      {d.is_own_submission && <Notice tone="warn">This is your own submission. Someone else must review it.</Notice>}

      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <Card className="space-y-3">
          <h2 className="font-semibold">Original document</h2>
          <DocViewer path={d.file_url} alt={`Original result document submitted for ${d.polling_unit.name}`} />
          <dl className="text-xs grid grid-cols-2 gap-2">
            <div><dt className="text-ink-soft">Receipt</dt><dd className="font-mono">{d.receipt_code}</dd></div>
            <div><dt className="text-ink-soft">Source</dt><dd>{d.classification_label}{d.organisation && `, ${d.organisation.name}`}</dd></div>
            <div><dt className="text-ink-soft">Contributor</dt><dd>{d.contributor?.name ?? "Anonymous"}</dd></div>
            <div><dt className="text-ink-soft">Follow-up contact</dt><dd>{d.follow_up_contact ?? "—"}</dd></div>
            <div><dt className="text-ink-soft">Server received</dt><dd>{fmtTime(d.server_received_time)}</dd></div>
            <div><dt className="text-ink-soft">Device time (unverified)</dt><dd>{fmtTime(d.device_reported_time)}</dd></div>
            <div><dt className="text-ink-soft">Upload</dt><dd>{d.captured_offline ? "Captured offline" : "Online"}, {d.sync_attempts} attempt(s)</dd></div>
            <div><dt className="text-ink-soft">Forwarded copy?</dt><dd>{d.is_forwarded_copy}</dd></div>
            <div className="col-span-2"><dt className="text-ink-soft">SHA-256</dt><dd><Hash value={d.file_sha256} /> {d.integrity_ok === true ? <span className="text-agree">✓ file unchanged</span> : d.integrity_ok === false ? <span className="text-differ">✗ integrity check failed</span> : null}</dd></div>
            {d.source_url && <div className="col-span-2"><dt className="text-ink-soft">Link</dt><dd className="break-all">{d.source_url}</dd></div>}
            {d.description && <div className="col-span-2"><dt className="text-ink-soft">Contributor note</dt><dd>{d.description}</dd></div>}
          </dl>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Extracted figures</h2>
            <span className="text-xs text-ink-soft">extraction: {d.extraction_status}</span>
          </div>
          {d.fields.length === 0 ? <p className="text-sm text-ink-soft">No figures (not an image of a result form).</p> : (
            <>
              <p className="text-xs text-ink-soft">Simulated extraction. Check every figure against the original. Corrections need a reason.</p>
              <ul className="space-y-2">
                {d.fields.map((f) => {
                  const e = edits[f.id];
                  const changed = !e.unreadable && e.value !== "" && Number(e.value) !== f.extracted_value;
                  return (
                    <li key={f.id} className={`rounded border p-2 ${f.needs_attention ? "border-wait bg-wait-tint" : "border-rule"}`}>
                      <div className="flex items-center gap-2">
                        <label className="text-sm flex-1" htmlFor={`f${f.id}`}>{f.label}</label>
                        <input id={`f${f.id}`} className={`${inputCls} !w-24 font-mono text-right`} inputMode="numeric" disabled={locked || e.unreadable}
                          value={e.value} onChange={(ev) => setEdits({ ...edits, [f.id]: { ...e, value: ev.target.value.replace(/\D/g, "") } })} />
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 text-xs text-ink-soft mt-1">
                        <span>read as {f.extracted_value ?? "nothing"}, {Math.round(f.confidence * 100)}% confidence</span>
                        {f.needs_attention && <span className="text-wait font-medium">check this</span>}
                        {f.status !== "proposed" && <span>{f.status}</span>}
                        <label className="flex items-center gap-1 ml-auto">
                          <input type="checkbox" disabled={locked} checked={e.unreadable} onChange={(ev) => setEdits({ ...edits, [f.id]: { ...e, unreadable: ev.target.checked } })} /> unreadable
                        </label>
                      </div>
                      {(changed || e.unreadable) && (
                        <input className={`${inputCls} mt-1 !text-xs`} placeholder={e.unreadable ? "Why is it unreadable?" : "Reason for correction"} disabled={locked}
                          value={e.reason} onChange={(ev) => setEdits({ ...edits, [f.id]: { ...e, reason: ev.target.value } })} />
                      )}
                    </li>
                  );
                })}
              </ul>
              {liveFlags.map((a) => <Notice key={a.check} tone="warn">⚠ {a.message} This is a review flag, not proof of misconduct.</Notice>)}
              {liveFlags.length === 0 && d.fields.some((f) => f.value != null) && <p className="text-xs text-agree">✓ The figures above add up.</p>}
              {!locked && (
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={saveFields}>Save figures</Button>
                  <Button onClick={() => run(() => post(`/verification/submissions/${d.id}/extraction`, { action: "confirm" }), "Extraction confirmed.")}>Confirm extraction</Button>
                </div>
              )}
            </>
          )}
        </Card>
      </div>

      <Card className="space-y-3">
        <h2 className="font-semibold">Decision</h2>
        <p className="text-sm">Current status: <strong>{d.status.replace(/_/g, " ")}</strong>{d.review_note && `. Note: “${d.review_note}”`}</p>
        <textarea className={inputCls} rows={2} placeholder="Note (required to reject, request information or keep as unresolved lead)" value={note} onChange={(e) => setNote(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          {d.status !== "under_review" && <Button variant="secondary" disabled={d.is_own_submission} onClick={() => run(() => post(`/verification/submissions/${d.id}/decision`, { decision: "start_review", note }), "Marked as under review.")}>Start review</Button>}
          <Button disabled={d.is_own_submission} onClick={() => run(() => post(`/verification/submissions/${d.id}/decision`, { decision: "accept", note }), "Accepted for comparison.")}>Accept for comparison</Button>
          <Button variant="secondary" disabled={d.is_own_submission} onClick={() => run(() => post(`/verification/submissions/${d.id}/decision`, { decision: "request_info", note }), "Information requested.")}>Request information</Button>
          {d.category === "citizen_lead" && <Button variant="secondary" disabled={d.is_own_submission} onClick={() => run(() => post(`/verification/submissions/${d.id}/decision`, { decision: "unresolved_lead", note }), "Kept as unresolved lead.")}>Keep as unresolved lead</Button>}
          <Button variant="danger" disabled={d.is_own_submission} onClick={() => run(() => post(`/verification/submissions/${d.id}/decision`, { decision: "reject", note }), "Rejected.")}>Reject as unusable</Button>
        </div>
        {d.category === "citizen_lead" && <p className="text-xs text-ink-soft">Accepted citizen leads stay labelled as citizen leads; they are never relabelled as observer evidence.</p>}
        <ErrorText error={error} />
        {saved && <p className="text-sm text-agree" role="status">{saved}</p>}
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold">Other records for this polling unit</h2>
          <Link className="text-sm underline" href={`/verify/unit/${d.polling_unit.id}/${d.contest_id}`}>Open the unit workspace</Link>
        </div>
        <p className="text-sm">{d.unit.explanation}</p>
        <ComparisonList comparisons={d.unit.comparisons} />
      </Card>

      <Card>
        <h2 className="font-semibold mb-2">History</h2>
        <ol className="text-xs space-y-1">
          {d.history.map((h, i) => <li key={i}><span className="text-ink-soft">{fmtTime(h.at)}</span>, {h.action.replace(/_/g, " ")}, {h.by}</li>)}
        </ol>
      </Card>
    </div>
  );
}
