"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, getDemoUser, post } from "@/lib/api";
import type { DemoUser, StatusKey } from "@/lib/types";
import { StatusBadge } from "@/components/Status";
import { Button, Card, ErrorText, Loading, Notice, fmtTime } from "@/components/ui";

type Coverage = {
  organisation: { id: number; name: string; verification_status: string };
  totals: Record<string, number>;
  units: { polling_unit: { id: number; code: string; name: string; lga: string; ward: string }; assignments: { id: number; status: string; contributor: string; is_primary: boolean }[]; submissions: number; unit_status: StatusKey; observed: boolean }[];
  members: number;
  note: string;
};
type Req = { id: number; contributor: string; polling_unit: string; polling_unit_code: string; requested_at: string };

const TOTALS: [string, string][] = [
  ["in_scope", "Polling units in scope"],
  ["assigned", "With an approved contributor"],
  ["unassigned", "Unassigned"],
  ["awaiting_approval", "Requests awaiting approval"],
  ["accepted", "Accepted assignments"],
  ["evidence_received", "Units with evidence received"],
  ["evidence_pending", "Assigned, no evidence yet"],
  ["incomplete", "Units with incomplete review"],
  ["discrepancies", "Units with discrepancies"],
];

export default function Organisation() {
  const [orgId, setOrgId] = useState<number | null>(null);
  const [orgs, setOrgs] = useState<{ id: number; name: string }[]>([]);
  const [cov, setCov] = useState<Coverage | null>(null);
  const [reqs, setReqs] = useState<Req[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pick = async () => {
      const [users, list] = await Promise.all([api<DemoUser[]>("/demo/users"), api<{ id: number; name: string }[]>("/organisations")]);
      setOrgs(list);
      const me = users.find((u) => u.id === getDemoUser());
      setOrgId(me?.organisation_id ?? list[0]?.id ?? null);
    };
    pick().catch(() => {});
    window.addEventListener("veravote:user", pick);
    return () => window.removeEventListener("veravote:user", pick);
  }, []);

  const load = useCallback(() => {
    if (!orgId) return;
    setError(null);
    api<Coverage>(`/organisations/${orgId}/coverage`).then(setCov).catch((e) => { setCov(null); setError(e.message); });
    api<Req[]>(`/organisations/${orgId}/requests`).then(setReqs).catch(() => setReqs([]));
  }, [orgId]);
  useEffect(load, [load]);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">Coverage</h1>
          {cov && <p className="text-sm text-ink-soft">{cov.organisation.name}, {cov.organisation.verification_status === "verified" ? "verified organisation" : "self-declared (not yet verified)"}, {cov.members} members</p>}
        </div>
        {orgs.length > 1 && (
          <select className="rounded border border-rule bg-sheet px-2 py-1.5 text-sm" value={orgId ?? ""} onChange={(e) => setOrgId(Number(e.target.value))} aria-label="Organisation">
            {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        )}
      </header>
      {error && <Notice tone="warn">{error}. Choose the coordinator (Funke Adebayo) or an admin in “Viewing as”.</Notice>}
      {!cov && !error && <Loading />}
      {cov && (
        <>
          <Notice>{cov.note}</Notice>
          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {TOTALS.map(([k, l]) => (
              <Card key={k} className="!p-3">
                <dt className="text-xs text-ink-soft">{l}</dt>
                <dd className="text-2xl font-semibold tabular-nums">{cov.totals[k] ?? 0}</dd>
              </Card>
            ))}
          </dl>

          {reqs.length > 0 && (
            <Card className="space-y-2">
              <h2 className="font-semibold">Assignment requests</h2>
              <ul className="divide-y divide-rule text-sm">
                {reqs.map((r) => (
                  <li key={r.id} className="py-2 flex flex-wrap items-center justify-between gap-2">
                    <span>{r.contributor} asks to cover {r.polling_unit}<span className="block text-xs text-ink-soft">{r.polling_unit_code}, {fmtTime(r.requested_at)}</span></span>
                    <span className="flex gap-2">
                      <Button className="!px-2 !py-1" onClick={async () => { await post(`/assignments/${r.id}/decide`, { approve: true }); load(); }}>Approve</Button>
                      <Button variant="secondary" className="!px-2 !py-1" onClick={async () => { await post(`/assignments/${r.id}/decide`, { approve: false }); load(); }}>Decline</Button>
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card>
            <h2 className="font-semibold mb-2">Polling units</h2>
            <div className="overflow-x-auto -mx-4 sm:mx-0">
              <table className="min-w-full text-sm">
                <thead className="text-xs text-ink-soft text-left">
                  <tr><th className="py-2 px-4 sm:pl-0 font-medium">Unit</th><th className="py-2 px-3 font-medium">Contributors</th><th className="py-2 px-3 font-medium">Submissions</th><th className="py-2 px-3 font-medium">Evidence status</th></tr>
                </thead>
                <tbody>
                  {cov.units.map((u) => (
                    <tr key={u.polling_unit.id} className="border-t border-rule align-top">
                      <td className="py-2 px-4 sm:pl-0"><Link className="underline" href={`/pu/${u.polling_unit.id}`}>{u.polling_unit.name}</Link><span className="block text-xs text-ink-soft">{u.polling_unit.code}, {u.polling_unit.ward}</span></td>
                      <td className="py-2 px-3">{u.assignments.length ? u.assignments.map((a) => <span key={a.id} className="block text-xs">{a.contributor} — {a.status}{a.is_primary ? " (primary)" : ""}</span>) : <span className="text-xs text-ink-soft">none</span>}</td>
                      <td className="py-2 px-3 tabular-nums">{u.submissions}{!u.observed && u.assignments.length > 0 && <span className="block text-xs text-wait">not observed yet</span>}</td>
                      <td className="py-2 px-3"><StatusBadge status={u.unit_status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
      <ErrorText error={null} />
    </div>
  );
}
