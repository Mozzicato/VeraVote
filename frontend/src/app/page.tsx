"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PollingUnit, StatusKey } from "@/lib/types";
import { StatusMark, statusTitle } from "@/components/Status";
import { ErrorText } from "@/components/ui";

type Summary = {
  polling_units: number;
  status_counts: Partial<Record<StatusKey, number>>;
  units: { id: number; code: string; name: string; lga: string; status: StatusKey }[];
};
type Opt = { id: number; name: string; code: string };

const ORDER: StatusKey[] = [
  "consistent_evidence", "discrepancy_detected", "review_completed", "under_review",
  "insufficient_evidence", "evidence_received", "no_evidence",
];

export default function Home() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<PollingUnit[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    api<Summary>("/public/summary").then(setSummary).catch(() => {});
  }, []);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (q.trim().length < 2) return setError("Type at least two letters of the name, code or a landmark.");
    try {
      setResults(await api<PollingUnit[]>(`/polling-units/search?q=${encodeURIComponent(q.trim())}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed. Check your connection and try again.");
    }
  }

  return (
    <div className="space-y-14">
      <section className="space-y-6">
        <h1 className="text-3xl sm:text-[3.25rem] sm:leading-[1.02] font-bold tracking-tight max-w-[16ch]">
          What happened at your polling unit?
        </h1>
        <p className="text-lg max-w-measure">
          See the result-sheet evidence we hold, who it came from, and whether the records agree with each other and
          with the official copy. You don&apos;t need an account.
        </p>

        <form onSubmit={search} role="search" className="max-w-2xl">
          <div className="flex items-end gap-3 border-b-2 border-ink pb-1 focus-within:border-violet">
            <label htmlFor="q" className="text-lg font-bold whitespace-nowrap pb-1.5">
              Polling unit:
            </label>
            <input
              id="q"
              aria-label="Search by polling-unit name, code, community or landmark"
              className="flex-1 min-w-0 bg-transparent text-xl py-1 outline-none placeholder:text-ink-soft/70"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="name or landmark"
              autoComplete="off"
            />
            <button className="mb-1 rounded-[3px] bg-violet text-on-violet px-4 py-2 font-bold hover:bg-violet-strong">
              Find
            </button>
          </div>
          <p className="mt-2 text-sm text-ink-soft">Try “Town Mosque”, “Jetty” or a code like <span className="whitespace-nowrap">SIM-01-01-001</span>.</p>
          <div className="mt-2"><ErrorText error={error} /></div>
        </form>

        {results && <Results results={results} />}

        <details className="max-w-2xl text-sm">
          <summary className="cursor-pointer text-violet underline">Choose from a list instead</summary>
          <Cascade />
        </details>
      </section>

      {summary && <Coverage summary={summary} />}

      <section className="grid sm:grid-cols-3 gap-8 sm:gap-10 border-t-2 border-ink pt-8 text-sm">
        <div className="space-y-1">
          <h2 className="text-lg font-bold">Seen a result sheet?</h2>
          <p className="text-ink-soft">Send a photo of a result that was displayed in public. You don&apos;t need to be an observer.</p>
          <Link href="/submit" className="inline-block font-bold text-violet underline">Send evidence</Link>
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-bold">Want to help?</h2>
          <p className="text-ink-soft">Train as a VeraVote community contributor and cover a polling unit near you.</p>
          <Link href="/volunteer" className="inline-block font-bold text-violet underline">Become a volunteer</Link>
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-bold">How we check</h2>
          <p className="text-ink-soft">We compare records line by line. We never decide who won.</p>
          <Link href="/about" className="inline-block font-bold text-violet underline">Read the method</Link>
        </div>
      </section>
    </div>
  );
}

/** One box per polling unit, like the boxes on a result form. Empty boxes are units with no evidence. */
function Coverage({ summary }: { summary: Summary }) {
  const present = ORDER.filter((k) => summary.status_counts[k]);
  const units = [...summary.units].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status));
  return (
    <section aria-labelledby="coverage" className="space-y-4">
      <h2 id="coverage" className="text-lg font-bold">
        Evidence across {summary.polling_units} demo polling units
      </h2>
      <ul className="flex flex-wrap gap-1.5" aria-label="Each polling unit and its evidence status">
        {units.map((u) => (
          <li key={u.id}>
            <Link href={`/pu/${u.id}`} title={`${u.name}: ${statusTitle(u.status)}`} className="block text-[1.75rem] leading-none hover:opacity-80">
              <StatusMark status={u.status} />
              <span className="sr-only">{u.name}, {statusTitle(u.status)}</span>
            </Link>
          </li>
        ))}
      </ul>
      <ul className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
        {present.map((k) => (
          <li key={k} className="flex items-center gap-2">
            <StatusMark status={k} />
            <span>{statusTitle(k)}</span>
            <span className="font-bold">{summary.status_counts[k]}</span>
          </li>
        ))}
      </ul>
      <p className="text-sm text-ink-soft max-w-measure">
        Units with no evidence are counted and shown, not hidden. A unit counts as covered only once evidence arrives.
      </p>
    </section>
  );
}

function Results({ results }: { results: PollingUnit[] }) {
  if (!results.length)
    return (
      <p className="text-sm max-w-measure">
        No polling unit matched. Try a nearby landmark or the ward name, or choose from the list below.
      </p>
    );
  return (
    <div className="max-w-2xl">
      {results.length > 1 && <p className="text-sm text-ink-soft mb-2">{results.length} units match. Pick yours.</p>}
      <ul className="border-t border-rule">
        {results.map((r) => (
          <li key={r.id} className="border-b border-rule">
            <Link href={`/pu/${r.id}`} className="block py-3 hover:bg-sheet">
              <span className="text-lg font-bold text-violet underline decoration-1 underline-offset-2">{r.official_name}</span>
              <span className="block text-sm text-ink-soft">
                {r.official_code}, {r.ward.name}, {r.lga.name}
                {r.matched_alias && <>. Known locally as “{r.matched_alias}”</>}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Cascade() {
  const [states, setStates] = useState<Opt[]>([]);
  const [lgas, setLgas] = useState<Opt[]>([]);
  const [wards, setWards] = useState<Opt[]>([]);
  const [units, setUnits] = useState<PollingUnit[]>([]);
  useEffect(() => {
    api<Opt[]>("/states").then(setStates).catch(() => {});
  }, []);
  const sel = "rounded-[3px] border border-ink/30 bg-sheet px-2 py-2 text-base w-full";
  return (
    <div className="grid sm:grid-cols-3 gap-2 mt-3">
      <select className={sel} aria-label="State" defaultValue=""
        onChange={(e) => { setWards([]); setUnits([]); api<Opt[]>(`/lgas?state_id=${e.target.value}`).then(setLgas); }}>
        <option value="" disabled>State</option>
        {states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <select className={sel} aria-label="LGA" defaultValue="" disabled={!lgas.length}
        onChange={(e) => { setUnits([]); api<Opt[]>(`/wards?lga_id=${e.target.value}`).then(setWards); }}>
        <option value="" disabled>LGA</option>
        {lgas.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <select className={sel} aria-label="Ward" defaultValue="" disabled={!wards.length}
        onChange={(e) => api<PollingUnit[]>(`/polling-units?ward_id=${e.target.value}`).then(setUnits)}>
        <option value="" disabled>Ward</option>
        {wards.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      {units.length > 0 && (
        <ul className="sm:col-span-3 border-t border-rule">
          {units.map((u) => (
            <li key={u.id} className="border-b border-rule">
              <Link href={`/pu/${u.id}`} className="block py-2 text-violet underline">
                {u.unit_number}. {u.official_name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
