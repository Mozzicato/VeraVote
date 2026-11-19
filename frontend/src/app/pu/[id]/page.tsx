"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Evaluation, UnitPage } from "@/lib/types";
import { StatusBadge } from "@/components/Status";
import { ComparisonList, FigureMatrix, SourceList } from "@/components/Evidence";
import { ErrorText, Hash, Loading, Notice, Section, fmtTime } from "@/components/ui";

const WORDS = ["No", "One", "Two", "Three", "Four", "Five"];

/** The finding, written as the page's headline. */
function finding(ev: Evaluation): string {
  const gaps = ev.comparisons.flatMap((c) => c.differences.map((d) => Math.abs(d.difference)));
  const docs = ev.documents.length;
  switch (ev.status) {
    case "discrepancy_detected":
      return `These records differ by up to ${Math.max(...gaps)} votes.`;
    case "consistent_evidence":
      return `${WORDS[docs] ?? docs} independent records show the same figures.`;
    case "insufficient_evidence":
      return "We have one usable record, and nothing yet to compare it with.";
    case "evidence_received":
      return "Evidence has arrived and is waiting for review.";
    case "under_review":
      return "Our verification team is examining the evidence.";
    case "review_completed":
      return "Our review of this polling unit is complete.";
    default:
      return "We have no evidence for this polling unit yet.";
  }
}

export default function PollingUnitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<UnitPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<UnitPage>(`/public/polling-units/${id}`).then(setData).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  const pu = data.polling_unit;

  return (
    <article className="space-y-12">
      <header className="space-y-1">
        <p className="text-sm text-ink-soft">
          {pu.ward.name}, {pu.lga.name}, {pu.state.name}
        </p>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{pu.official_name}</h1>
        <p className="text-sm">
          Polling unit <span className="font-bold">{pu.official_code}</span>. {pu.location_description}.
        </p>
        {pu.aliases.length > 0 && <p className="text-sm text-ink-soft">Also known as {pu.aliases.join(", ")}.</p>}
      </header>

      {data.contests.map((c) => (
        <div key={c.contest.id} className="space-y-12">
          <section aria-labelledby={`finding-${c.contest.id}`} className="space-y-4 border-l-4 border-ink pl-4 sm:pl-6">
            <p className="text-sm text-ink-soft">
              {c.contest.office}, {c.contest.election.name}
            </p>
            <StatusBadge status={c.status} size="lg" />
            <h2 id={`finding-${c.contest.id}`} className="text-2xl sm:text-3xl font-bold tracking-tight max-w-[24ch]">
              {finding(c)}
            </h2>
            <p className="max-w-measure text-lg">{c.explanation}</p>
            {c.notes.length > 0 && (
              <ul className="space-y-1 max-w-measure">
                {c.notes.map((n) => (
                  <li key={n} className={`font-bold ${c.status === "discrepancy_detected" ? "text-differ" : "text-violet"}`}>
                    {n}
                  </li>
                ))}
              </ul>
            )}
            <p className="text-xs text-ink-soft max-w-measure">{c.disclaimer}</p>
          </section>

          {c.documents.length > 0 && (
            <Section title="Line by line">
              <p className="text-sm text-ink-soft max-w-measure">
                Each column is a separate document. Several photos of the same sheet count as one.
              </p>
              <FigureMatrix ev={c} />
              <ComparisonList comparisons={c.comparisons} documents={c.documents} />
            </Section>
          )}

          <Section title="Where the evidence came from">
            <p className="text-sm max-w-measure">
              {c.independence.submissions === 0 && c.independence.official_documents === 0 ? (
                "No one has sent evidence for this polling unit yet."
              ) : (
                <>
                  <strong>{c.independence.submissions}</strong> submission{c.independence.submissions === 1 ? "" : "s"} from{" "}
                  <strong>{c.independence.distinct_contributors}</strong> contributor{c.independence.distinct_contributors === 1 ? "" : "s"} in{" "}
                  <strong>{c.independence.distinct_organisations}</strong> organisation{c.independence.distinct_organisations === 1 ? "" : "s"}, and{" "}
                  <strong>{c.independence.official_documents}</strong> official document{c.independence.official_documents === 1 ? "" : "s"}.
                  Contributors&apos; identities are kept private.
                </>
              )}
            </p>
            {c.independence.notes.map((n) => (
              <Notice key={n} tone="warn">{n}</Notice>
            ))}
            {c.sources.length > 0 && <SourceList sources={c.sources} documents={c.documents} />}
            <p>
              <Link href={`/submit?pu=${pu.id}&contest=${c.contest.id}`} className="text-violet underline font-bold">
                Send evidence for this polling unit
              </Link>
            </p>
          </Section>
        </div>
      ))}

      <Section title="What happened, in order">
        {data.timeline.length === 0 ? (
          <p className="text-sm text-ink-soft">Nothing has been recorded yet.</p>
        ) : (
          <ol className="space-y-4 border-l-2 border-rule pl-5 max-w-measure">
            {data.timeline.map((t, i) => (
              <li key={i} className="relative text-sm">
                <span aria-hidden className="absolute -left-[1.65rem] top-1.5 h-2.5 w-2.5 bg-ink" />
                <p className="font-bold">{t.event}</p>
                <p className="text-xs text-ink-soft">
                  {fmtTime(t.at)}, recorded by {t.by === "VeraVote" ? "VeraVote" : t.by.toLowerCase()}. Audit record <Hash value={t.event_hash} />
                </p>
              </li>
            ))}
          </ol>
        )}
      </Section>

      <p className="text-xs text-ink-soft max-w-measure">
        Polling-unit details come from the {pu.dataset_source}, version {pu.dataset_version}, last checked{" "}
        {fmtTime(pu.last_verified)}. <Link href="/about" className="underline">How we check evidence</Link>
      </p>
    </article>
  );
}
