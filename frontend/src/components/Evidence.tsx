import type { Comparison, Evaluation, Source } from "@/lib/types";
import { API_URL } from "@/lib/api";
import { Hash, Meta, fmtTime } from "./ui";

const letter = (i: number) => String.fromCharCode(65 + i);

const KIND_TAG: Record<string, string> = {
  official_document: "border-done text-done",
  accredited_observer: "border-violet text-violet",
  trained_community: "border-ink/40 text-ink",
  party_agent: "border-wait text-wait",
  citizen: "border-ink/30 text-ink-soft",
};

export function SourceTag({ s }: { s: Pick<Source, "classification" | "label"> }) {
  return (
    <span className={`inline-block border px-1.5 py-px text-xs font-bold ${KIND_TAG[s.classification] ?? ""}`}>
      {s.label}
    </span>
  );
}

/** A reviewer's hand-drawn ellipse around a figure that disagrees with another record. */
function InkCircle({ i }: { i: number }) {
  return (
    <svg
      aria-hidden
      className="ink-circle pointer-events-none absolute -left-2 -top-1.5 h-[calc(100%+0.75rem)] w-[calc(100%+1rem)] overflow-visible text-differ"
      viewBox="0 0 100 40"
      preserveAspectRatio="none"
      style={{ ["--i" as string]: i }}
    >
      <path
        d="M78 5C60 0 22 1 8 10C-3 18 4 32 26 36C50 40 86 37 95 26C102 17 92 6 70 4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

/**
 * The comparison laid out like the result form: one row per line of the form, one column per distinct
 * record, every figure in its own box. In a row where records differ, the minority figure is circled.
 */
export function FigureMatrix({ ev }: { ev: Evaluation }) {
  const docs = ev.documents;
  if (!docs.length) return null;
  const differing = new Set(
    ev.comparisons.filter((c) => c.result === "differ").flatMap((c) => c.differences.map((d) => d.field_key)),
  );
  const oddOut = (key: string, value: number | null | undefined) => {
    if (!differing.has(key) || value == null) return false;
    const vals = docs.map((d) => d.values[key]);
    const same = vals.filter((v) => v === value).length;
    const firstIdx = docs.findIndex((d) => d.values[key] === value);
    // Minority value; on a tie, circle every value except the first record's.
    return same < vals.length - same || (same === vals.length - same && firstIdx > 0);
  };
  let circle = 0;
  const pinned = "sticky left-0 z-10 bg-paper";

  return (
    <figure className="space-y-2">
      {docs.length > 2 && (
        <p className="text-xs text-ink-soft sm:hidden">{docs.length} records side by side. Scroll sideways to see them all.</p>
      )}
      <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
        <table className="border-separate border-spacing-x-2 border-spacing-y-1.5 -ml-2">
          <caption className="sr-only">Figures from each reviewed record, line by line as on the result form</caption>
          <thead>
            <tr className="text-left">
              <th scope="col" className={`${pinned} pr-2 pb-1 text-xs font-normal text-ink-soft align-bottom`}>Line on the form</th>
              {docs.map((d, i) => (
                <th key={d.key} scope="col" className="pb-1 w-[9.5rem] min-w-[7.5rem] font-normal align-top">
                  <span className="block text-xl font-bold leading-none">Record {letter(i)}</span>
                  <span className="block text-xs text-ink-soft mt-1">{d.label}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ev.fields.map((f) => {
              const diff = differing.has(f.key);
              const isTotal = f.key.startsWith("total");
              return (
                <tr key={f.key}>
                  <th scope="row" className={`${pinned} pr-3 text-left text-sm min-w-[8.5rem] sm:min-w-[13rem] ${isTotal ? "font-bold" : "font-normal"}`}>
                    {f.label}
                    {diff && <span className="block text-xs font-bold text-differ">records differ</span>}
                  </th>
                  {docs.map((d) => {
                    const v = d.values[f.key];
                    const odd = oddOut(f.key, v);
                    return (
                      <td key={d.key}>
                        <span
                          className={`relative flex justify-end w-full max-w-[7rem] px-2 py-1 text-lg tabular-nums bg-sheet ${
                            isTotal ? "border-2 border-ink font-bold" : "border border-ink/40"
                          } ${odd ? "text-differ font-bold" : ""}`}
                        >
                          {v ?? <span className="text-sm text-ink-soft">unreadable</span>}
                          {odd && <InkCircle i={circle++} />}
                          {odd && <span className="sr-only"> (differs from the other records)</span>}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

function sentence(c: Comparison, name: (k: string, l: string) => string) {
  const a = name(c.a, c.a_label);
  const b = name(c.b, c.b_label);
  if (c.result === "agree") return <><strong>{a} and {b}</strong> show the same figures.</>;
  if (c.result === "not_comparable") return <><strong>{a} and {b}</strong> have no readable figures in common.</>;
  const n = c.differences.length;
  return <><strong>{a} and {b}</strong> differ on {n} line{n > 1 ? "s" : ""}.</>;
}

export function ComparisonList({ comparisons, documents }: { comparisons: Comparison[]; documents?: Evaluation["documents"] }) {
  if (!comparisons.length)
    return <p className="text-sm text-ink-soft">There is nothing to compare yet. Comparison needs at least two reviewed records.</p>;
  const name = (key: string, label: string) => {
    const i = documents?.findIndex((d) => d.key === key) ?? -1;
    return i >= 0 ? `Record ${letter(i)}` : label;
  };
  return (
    <ul className="space-y-3 max-w-measure">
      {comparisons.map((c, i) => (
        <li key={i} className="text-sm">
          <p>
            <span aria-hidden className={`inline-block w-4 font-bold ${c.result === "agree" ? "text-agree" : c.result === "differ" ? "text-differ" : "text-ink-soft"}`}>
              {c.result === "agree" ? "=" : c.result === "differ" ? "≠" : "?"}
            </span>
            {sentence(c, name)}
          </p>
          {!documents && <p className="ml-4 text-xs text-ink-soft">{c.a_label} and {c.b_label}</p>}
          {c.differences.length > 0 && (
            <ul className="ml-4 mt-1 text-ink-soft">
              {c.differences.map((d) => (
                <li key={d.field_key}>
                  {d.label}: {d.a} against {d.b} ({d.difference > 0 ? "+" : ""}{d.difference})
                </li>
              ))}
            </ul>
          )}
          {!c.independent && c.result !== "not_comparable" && (
            <p className="ml-4 text-xs text-wait font-bold">These two records may not be independent of each other.</p>
          )}
        </li>
      ))}
    </ul>
  );
}

const STATUS_WORDS: Record<string, string> = {
  accepted: "Reviewed and used in the comparison",
  awaiting_review: "Waiting for review",
  under_review: "Being reviewed",
  rejected: "Reviewed and not used",
  info_requested: "More information requested",
  unresolved_lead: "Kept on file as an unresolved lead",
};

export function SourceList({ sources, documents }: { sources: Source[]; documents?: Evaluation["documents"] }) {
  const recordOf = (ref: string) => {
    const i = documents?.findIndex((d) => d.sources?.includes(ref)) ?? -1;
    return i >= 0 ? letter(i) : null;
  };
  return (
    <ol className="space-y-5">
      {sources.map((s) => {
        const rec = recordOf(s.ref);
        return (
          <li key={s.ref} className="grid grid-cols-[2.25rem_1fr] gap-x-3">
            <span
              title={rec ? `Record ${rec}` : "Not in the comparison yet"}
              className={`grid place-items-center h-9 w-9 border-2 text-lg font-bold ${rec ? "border-ink" : "border-dashed border-ink/30 text-ink-soft"}`}
            >
              <span className="sr-only">{rec ? `Record ${rec}` : "Not in the comparison yet"}</span>
              <span aria-hidden>{rec ?? ""}</span>
            </span>
            <div className="space-y-1 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <SourceTag s={s} />
                {s.organisation_name && <span className="text-ink-soft">{s.organisation_name}</span>}
              </div>
              <p>
                {s.kind === "official"
                  ? s.status === "current" ? "Current version" : "Replaced by a newer version"
                  : STATUS_WORDS[s.status] ?? s.status}
              </p>
              <Meta
                items={[
                  `${s.kind === "official" ? "Retrieved" : "Received by our server"} ${fmtTime(s.received_at)}`,
                  <>Fingerprint <Hash value={s.file_hash} /></>,
                  s.version_reference && `Version ${s.version_reference}`,
                  s.is_forwarded_copy === "yes" && <span className="text-wait font-bold">Sent in as a forwarded copy</span>,
                ]}
              />
              {s.arithmetic_flags.map((f) => (
                <p key={f.check} className="text-xs text-wait font-bold">{f.message}</p>
              ))}
              {s.file_available && (
                <a className="inline-block text-violet underline" href={`${API_URL}/public/files/${s.kind}/${s.id}`} target="_blank" rel="noreferrer">
                  View the original document
                </a>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
