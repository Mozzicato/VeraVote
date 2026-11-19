"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { PollingUnit } from "@/lib/types";
import { inputCls } from "./ui";

/** Search-and-confirm polling-unit chooser (PRD §5.3: show candidates, user confirms). */
export function UnitPicker({ value, onChange }: { value: PollingUnit | null; onChange: (pu: PollingUnit | null) => void }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<PollingUnit[]>([]);
  const [searched, setSearched] = useState(false);

  if (value)
    return (
      <div className="flex items-start justify-between gap-3 rounded-md border border-rule bg-paper px-3 py-2 text-sm">
        <div>
          <p className="font-medium">{value.official_name}</p>
          <p className="text-xs text-ink-soft">
            {value.official_code}, {value.ward.name}, {value.lga.name}
          </p>
        </div>
        <button type="button" className="text-violet underline text-xs" onClick={() => onChange(null)}>
          Change
        </button>
      </div>
    );

  async function go() {
    if (q.trim().length < 2) return;
    setResults(await api<PollingUnit[]>(`/polling-units/search?q=${encodeURIComponent(q.trim())}`));
    setSearched(true);
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          className={inputCls}
          value={q}
          placeholder="Unit name, code or landmark"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              go();
            }
          }}
        />
        <button type="button" onClick={go} className="rounded-md border border-rule px-3 text-sm">
          Find
        </button>
      </div>
      {searched && !results.length && <p className="text-xs text-ink-soft">No match. Try another name.</p>}
      {results.length > 0 && (
        <ul className="divide-y divide-rule border border-rule rounded-md text-sm">
          {results.map((r) => (
            <li key={r.id}>
              <button type="button" className="w-full text-left px-3 py-2 hover:bg-paper" onClick={() => onChange(r)}>
                {r.official_name}
                <span className="block text-xs text-ink-soft">
                  {r.official_code}, {r.ward.name}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
