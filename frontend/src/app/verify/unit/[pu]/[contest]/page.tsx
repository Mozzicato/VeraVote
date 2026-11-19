"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { api, getDemoUser, post } from "@/lib/api";
import type { Contest, DemoUser, Evaluation, PollingUnit } from "@/lib/types";
import { StatusBadge } from "@/components/Status";
import { ComparisonList, FigureMatrix, SourceTag } from "@/components/Evidence";
import { Button, Card, ErrorText, Field, Hash, Loading, Notice, inputCls } from "@/components/ui";

type Inv = { id: number; status: string; outcome: string | null; findings: string; public_summary: string; assigned_reviewer_id: number | null };
type Data = { polling_unit: PollingUnit; contest: Contest; evaluation: Evaluation; investigation: Inv | null };

const OUTCOMES = [
  ["discrepancy_confirmed", "Discrepancy confirmed (needs senior approval)"],
  ["discrepancy_unresolved", "Discrepancy unresolved"],
  ["insufficient_evidence", "Insufficient evidence"],
  ["referred", "Referred for further investigation (needs senior approval)"],
  ["consistent", "Records consistent"],
  ["no_discrepancy_found", "No discrepancy found"],
];

export default function UnitWorkspace({ params }: { params: Promise<{ pu: string; contest: string }> }) {
  const { pu, contest } = use(params);
  const [d, setD] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);

  const load = useCallback(() => {
    api<Data>(`/verification/units/${pu}/${contest}`).then(setD).catch((e) => setError(e.message));
    api<DemoUser[]>("/demo/users").then((us) => setRole(us.find((u) => u.id === getDemoUser())?.role ?? null)).catch(() => {});
  }, [pu, contest]);
  useEffect(load, [load]);

  if (error && !d) return <ErrorText error={error} />;
  if (!d) return <Loading />;
  const ev = d.evaluation;

  return (
    <div className="space-y-5">
      <Link href="/verify" className="text-sm underline">← Queue</Link>
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">{d.polling_unit.official_name}</h1>
          <p className="text-sm text-ink-soft">{d.polling_unit.official_code}, {d.contest.office}</p>
        </div>
        <StatusBadge status={ev.status} size="lg" />
      </header>
      <Card className="space-y-2">
        <p>{ev.explanation}</p>
        {ev.notes.map((n) => <Notice key={n}>{n}</Notice>)}
        <Link href={`/pu/${d.polling_unit.id}`} className="text-sm underline">See the public page</Link>
      </Card>

      {ev.documents.length > 0 && (
        <Card className="space-y-3">
          <h2 className="font-semibold">Figures by distinct document</h2>
          <FigureMatrix ev={ev} />
          <ComparisonList comparisons={ev.comparisons} documents={ev.documents} />
        </Card>
      )}

      <Card className="space-y-2">
        <h2 className="font-semibold">Sources and independence</h2>
        <p className="text-sm">
          {ev.independence.submissions} submissions, {ev.independence.distinct_contributors} contributors,{" "}
          {ev.independence.distinct_organisations} organisations, {ev.independence.distinct_documents} distinct files,{" "}
          {ev.independence.official_documents} official
        </p>
        {ev.independence.notes.map((n) => <Notice key={n} tone="warn">{n}</Notice>)}
        <ul className="divide-y divide-rule text-sm">
          {ev.sources.map((s) => (
            <li key={s.ref} className="py-2 flex flex-wrap items-center gap-2 justify-between">
              <span className="flex flex-wrap items-center gap-2">
                <SourceTag s={s} />
                <Hash value={s.file_hash} />
                <span className="text-xs text-ink-soft">{s.status.replace(/_/g, " ")}{s.comparable ? ", in comparison" : ""}</span>
              </span>
              {s.kind === "submission" && <Link className="text-xs underline" href={`/verify/submission/${s.id}`}>Review</Link>}
            </li>
          ))}
        </ul>
      </Card>

      <OfficialDocForm data={d} onDone={load} />
      <InvestigationPanel data={d} role={role} onDone={load} />
    </div>
  );
}

function OfficialDocForm({ data, onDone }: { data: Data; onDone: () => void }) {
  const fields = data.evaluation.fields;
  const [vals, setVals] = useState<Record<string, string>>({});
  const [ref, setRef] = useState(`simulated://irev/${data.polling_unit.official_code}/ec8a`);
  const [version, setVersion] = useState("v1");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const hasOfficial = data.evaluation.independence.official_documents > 0;

  return (
    <Card>
      <details>
        <summary className="cursor-pointer font-semibold">{hasOfficial ? "Attach a newer official document version" : "Attach the official result document"}</summary>
        <div className="space-y-3 mt-3">
          <Notice tone="warn">Demo: enter figures from a simulated IReV record. There is no live IReV integration.</Notice>
          <div className="grid sm:grid-cols-2 gap-2">
            <Field label="Source reference"><input className={inputCls} value={ref} onChange={(e) => setRef(e.target.value)} /></Field>
            <Field label="Version"><input className={inputCls} value={version} onChange={(e) => setVersion(e.target.value)} /></Field>
          </div>
          <div className="grid sm:grid-cols-2 gap-2">
            {fields.map((f) => (
              <label key={f.key} className="flex items-center gap-2 text-sm">
                <span className="flex-1">{f.label}</span>
                <input className={`${inputCls} !w-24 font-mono text-right`} inputMode="numeric" value={vals[f.key] ?? ""} onChange={(e) => setVals({ ...vals, [f.key]: e.target.value.replace(/\D/g, "") })} />
              </label>
            ))}
          </div>
          <ErrorText error={error} />
          {msg && <p className="text-sm text-agree">{msg}</p>}
          <Button onClick={async () => {
            setError(null);
            try {
              const values = Object.fromEntries(Object.entries(vals).filter(([, v]) => v !== "").map(([k, v]) => [k, Number(v)]));
              const r = await post<{ unit_status: string }>("/verification/official-documents", {
                polling_unit_id: data.polling_unit.id, contest_id: data.contest.id, source_reference: ref, version_reference: version, values,
              });
              setMsg(`Attached. Unit status is now: ${r.unit_status.replace(/_/g, " ")}`);
              onDone();
            } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
          }}>Attach document</Button>
        </div>
      </details>
    </Card>
  );
}

function InvestigationPanel({ data, role, onDone }: { data: Data; role: string | null; onDone: () => void }) {
  const inv = data.investigation;
  const [findings, setFindings] = useState(inv?.findings ?? "");
  const [outcome, setOutcome] = useState("discrepancy_unresolved");
  const [summary, setSummary] = useState(inv?.public_summary ?? "");
  const [error, setError] = useState<string | null>(null);
  const isSenior = role === "senior_reviewer" || role === "admin";
  const base = `/verification/units/${data.polling_unit.id}/${data.contest.id}/investigation`;
  const act = async (fn: () => Promise<unknown>) => {
    setError(null);
    try { await fn(); onDone(); } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
  };

  return (
    <Card className="space-y-3">
      <h2 className="font-semibold">Investigation</h2>
      {!inv || inv.status === "closed" ? (
        <>
          {inv && <p className="text-sm">Completed: <strong>{inv.outcome?.replace(/_/g, " ")}</strong>. {inv.public_summary}</p>}
          {!inv ? (
            <Button variant="secondary" onClick={() => act(() => post(base, { action: "open" }))}>Open investigation</Button>
          ) : isSenior ? (
            <Button variant="secondary" onClick={() => act(() => post(base, { action: "reopen" }))}>Reopen (senior reviewer)</Button>
          ) : null}
        </>
      ) : inv.status === "awaiting_approval" ? (
        <div className="space-y-2">
          <Notice>Outcome “{inv.outcome?.replace(/_/g, " ")}” is waiting for a senior reviewer to approve it.</Notice>
          <p className="text-sm">Public summary: {inv.public_summary}</p>
          {isSenior && <Button onClick={() => act(() => post(`/verification/investigations/${inv.id}/approve`))}>Approve and publish</Button>}
        </div>
      ) : (
        <div className="space-y-3">
          <Field label="Findings (internal)">
            <textarea className={inputCls} rows={4} value={findings} onChange={(e) => setFindings(e.target.value)} />
          </Field>
          <Button variant="secondary" onClick={() => act(() => post(base, { action: "record", findings }))}>Save findings</Button>
          <div className="border-t border-rule pt-3 space-y-2">
            <Field label="Outcome">
              <select className={inputCls} value={outcome} onChange={(e) => setOutcome(e.target.value)}>
                {OUTCOMES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
            <Field label="Public summary" hint="Plain language. Describe the evidence, not who is to blame.">
              <textarea className={inputCls} rows={3} value={summary} onChange={(e) => setSummary(e.target.value)} />
            </Field>
            <Button onClick={() => act(() => post(base, { action: "close", findings, outcome, public_summary: summary }))}>Complete review</Button>
          </div>
        </div>
      )}
      <ErrorText error={error} />
    </Card>
  );
}
