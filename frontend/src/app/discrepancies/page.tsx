"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Contest, PollingUnit } from "@/lib/types";
import { StatusMark } from "@/components/Status";
import { ErrorText, Loading, fmtTime } from "@/components/ui";

type Row = {
  polling_unit: PollingUnit;
  contest: Contest;
  explanation: string;
  largest_difference: number;
  fields_affected: string[];
  since: string;
};

export default function Discrepancies() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Row[]>("/public/discrepancies").then(setRows).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Where records differ</h1>
        <p className="text-lg max-w-measure">
          At these polling units, the records we hold show different figures. A difference is a reason to look closer.
          It is not, by itself, proof of wrongdoing.
        </p>
      </header>
      <ErrorText error={error} />
      {!rows && !error && <Loading />}
      {rows?.length === 0 && (
        <p className="max-w-measure">
          No polling unit has an open difference right now. <Link className="text-violet underline" href="/">Find a polling unit</Link> to see its evidence.
        </p>
      )}
      <ul className="border-t-2 border-ink">
        {rows?.map((r) => (
          <li key={`${r.polling_unit.id}-${r.contest.id}`} className="border-b border-rule py-5 grid sm:grid-cols-[1fr_auto] gap-x-8 gap-y-2">
            <div className="space-y-1">
              <Link href={`/pu/${r.polling_unit.id}`} className="text-lg font-bold text-violet underline decoration-1 underline-offset-2">
                {r.polling_unit.official_name}
              </Link>
              <p className="text-sm text-ink-soft">
                {r.polling_unit.official_code}, {r.polling_unit.lga.name}. {r.contest.office} election.
              </p>
              <p className="text-sm">Lines that differ: {r.fields_affected.join(", ")}.</p>
              <p className="text-xs text-ink-soft">Flagged {fmtTime(r.since)}</p>
            </div>
            <p className="flex items-center gap-3 sm:justify-end sm:text-right">
              <StatusMark status="discrepancy_detected" className="text-xl" />
              <span>
                <span className="block text-3xl font-bold leading-none text-differ">{r.largest_difference}</span>
                <span className="text-sm">votes apart, at most</span>
              </span>
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
