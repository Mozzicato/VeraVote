"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, post } from "@/lib/api";
import type { StatusKey } from "@/lib/types";
import { StatusBadge } from "@/components/Status";
import { Button, Card, ErrorText, Loading, Notice, fmtTime, inputCls } from "@/components/ui";

type Item = {
  id: number; receipt_code: string; category: string; classification_label: string; evidence_type: string;
  status: string; extraction_status: string; server_received_time: string; captured_offline: boolean;
  polling_unit: { id: number; code: string; name: string; lga: string; ward: string }; contest_id: number;
  unit_status: StatusKey | null; low_confidence_fields: number; arithmetic_flags: number;
};
type Claim = { user_id: number; name: string; official_role: string; official_reference: string; party: string | null; organisation: string | null; classification_label: string };
type Inv = { id: number; status: string; outcome: string | null; contest_id: number; polling_unit: { id: number; code: string; name: string } };

const STATUSES = ["awaiting_review", "under_review", "info_requested", "accepted", "rejected", "unresolved_lead"];

export default function VerifyQueue() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [status, setStatus] = useState("awaiting_review");
  const [category, setCategory] = useState("");
  const [discOnly, setDiscOnly] = useState(false);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [invs, setInvs] = useState<Inv[]>([]);
  const [chain, setChain] = useState<{ intact: boolean; first_broken_event_id: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const p = new URLSearchParams();
    if (status) p.set("status", status);
    if (category) p.set("category", category);
    if (discOnly) p.set("discrepancy_only", "true");
    setError(null);
    api<Item[]>(`/verification/queue?${p}`).then(setItems).catch((e) => { setItems([]); setError(e.message); });
    api<Claim[]>("/verification/contributors?official_status=claimed").then(setClaims).catch(() => {});
    api<Inv[]>("/verification/investigations").then(setInvs).catch(() => {});
    api<typeof chain>("/verification/audit/verify").then(setChain).catch(() => {});
  }, [status, category, discOnly]);

  useEffect(() => {
    load();
    window.addEventListener("veravote:user", load);
    return () => window.removeEventListener("veravote:user", load);
  }, [load]);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">Verification</h1>
          <p className="text-sm text-ink-soft">Review evidence, correct extracted figures, compare sources.</p>
        </div>
        {chain && (
          <span className={`text-xs rounded px-2 py-1 ${chain.intact ? "bg-agree-tint text-agree" : "bg-differ-tint text-differ"}`}>
            {chain.intact ? "✓ Audit log intact" : `✗ Audit log broken at event ${chain.first_broken_event_id}`}
          </span>
        )}
      </header>
      {error && <Notice tone="warn">{error}. Choose a verification officer (e.g. Chika Umeh) in “Viewing as”.</Notice>}

      <Card className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
          <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </select>
          <select className={inputCls} value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Source">
            <option value="">Field evidence and citizen leads</option>
            <option value="field">Field evidence only</option>
            <option value="citizen_lead">Citizen leads only</option>
          </select>
          <label className="flex items-center gap-2"><input type="checkbox" checked={discOnly} onChange={(e) => setDiscOnly(e.target.checked)} /> Only units with discrepancies</label>
        </div>
        {!items ? <Loading /> : items.length === 0 ? <p className="text-sm text-ink-soft">Nothing here.</p> : (
          <ul className="divide-y divide-rule">
            {items.map((i) => (
              <li key={i.id}>
                <Link href={`/verify/submission/${i.id}`} className="block py-3 hover:bg-paper -mx-2 px-2 rounded">
                  <div className="flex flex-wrap items-center gap-2 justify-between">
                    <span className="font-medium">{i.polling_unit.name}</span>
                    {i.unit_status && <StatusBadge status={i.unit_status} />}
                  </div>
                  <div className="text-xs text-ink-soft flex flex-wrap gap-x-3 gap-y-1 mt-1">
                    <span className="font-mono">{i.receipt_code}</span>
                    <span>{i.classification_label}</span>
                    <span>{i.polling_unit.code}</span>
                    <span>Received {fmtTime(i.server_received_time)}</span>
                    {i.captured_offline && <span>captured offline</span>}
                    <span>status: {i.status.replace(/_/g, " ")}</span>
                    <span>extraction: {i.extraction_status}</span>
                    {i.low_confidence_fields > 0 && <span className="text-wait">{i.low_confidence_fields} low-confidence field(s)</span>}
                    {i.arithmetic_flags > 0 && <span className="text-wait">arithmetic flag</span>}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="space-y-2">
          <h2 className="font-semibold">Official status claims to check</h2>
          <p className="text-xs text-ink-soft">Check each claim against INEC&apos;s or the party&apos;s own records before verifying.</p>
          {claims.length === 0 && <p className="text-sm text-ink-soft">No pending claims.</p>}
          <ul className="divide-y divide-rule text-sm">
            {claims.map((c) => <ClaimRow key={c.user_id} c={c} onDone={load} />)}
          </ul>
        </Card>
        <Card className="space-y-2">
          <h2 className="font-semibold">Investigations</h2>
          {invs.length === 0 && <p className="text-sm text-ink-soft">None yet. Open one from a polling unit&apos;s workspace.</p>}
          <ul className="divide-y divide-rule text-sm">
            {invs.map((i) => (
              <li key={i.id} className="py-2">
                <Link className="underline" href={`/verify/unit/${i.polling_unit.id}/${i.contest_id}`}>{i.polling_unit.name}</Link>
                <span className="block text-xs text-ink-soft">{i.status.replace(/_/g, " ")}{i.outcome && `, ${i.outcome.replace(/_/g, " ")}`}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

function ClaimRow({ c, onDone }: { c: Claim; onDone: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const act = async (status: string) => {
    try { await post(`/verification/contributors/${c.user_id}/official-status`, { status }); onDone(); }
    catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
  };
  return (
    <li className="py-2 space-y-1">
      <p>
        <strong>{c.name}</strong> claims {c.official_role === "party_agent" ? `party agent (${c.party})` : "INEC accreditation"}
        <span className="block text-xs text-ink-soft">ref {c.official_reference}{c.organisation && `, ${c.organisation}`}, now: {c.classification_label}</span>
      </p>
      <div className="flex gap-2">
        <Button className="!px-2 !py-1" onClick={() => act("verified")}>Verified</Button>
        <Button variant="secondary" className="!px-2 !py-1" onClick={() => act("rejected")}>Could not verify</Button>
      </div>
      <ErrorText error={error} />
    </li>
  );
}
