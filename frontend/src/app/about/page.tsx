import { StatusBadge } from "@/components/Status";
import type { StatusKey } from "@/lib/types";

const STATUSES: [StatusKey, string][] = [
  ["no_evidence", "We have not received any usable evidence for this polling unit."],
  ["evidence_received", "At least one submission has arrived but has not finished review."],
  ["under_review", "A verification officer is examining the evidence."],
  ["consistent_evidence", "At least two independent, reviewed records show the same figures."],
  ["discrepancy_detected", "Two or more reviewed records show different figures. A person must look at it."],
  ["insufficient_evidence", "There is only one usable record, so there is nothing independent to compare it with."],
  ["review_completed", "The verification team has finished and published its documented review."],
];

const SOURCES: [string, string][] = [
  ["Citizen leads", "Anyone can share a photo or a link. Leads are reviewed before they count."],
  ["VeraVote-trained community contributors", "Volunteers who passed our training and assessment. This is not INEC accreditation."],
  ["INEC-accredited observers", "People designated through an INEC-accredited observer group. We record this only after checking it."],
  ["Party agents", "People authorised by a party or candidate. Their party is shown on every record they submit."],
  ["Official documents", "Copies of results published on official platforms such as IReV. In this demo they are simulated, and there is no live IReV link."],
];

export const metadata = { title: "How VeraVote works" };

export default function About() {
  return (
    <article className="space-y-12 max-w-3xl">
      <header className="space-y-4">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">How VeraVote works</h1>
        <p className="text-xl max-w-[34ch] font-bold">
          VeraVote does not ask you to trust another authority. It shows you the evidence so you can inspect it yourself.
        </p>
        <ul className="list-disc pl-5 space-y-1 max-w-measure">
          <li>We collect and keep photos of polling-unit result forms from several kinds of contributor.</li>
          <li>We check where each record came from and whether the records agree.</li>
          <li>We do not run elections, replace INEC, certify results or declare winners. VeraVote is independent and is not an INEC platform.</li>
        </ul>
      </header>

      <section className="space-y-4">
        <h2 className="text-lg font-bold">What each status means</h2>
        <dl className="border-t-2 border-ink">
          {STATUSES.map(([k, t]) => (
            <div key={k} className="grid sm:grid-cols-[15rem_1fr] gap-1 sm:gap-4 py-3 border-b border-rule">
              <dt><StatusBadge status={k} /></dt>
              <dd className="text-sm">{t}</dd>
            </div>
          ))}
        </dl>
        <p className="text-sm text-ink-soft max-w-measure">
          These labels describe the evidence we hold. They are not a ruling on whether a result is legally valid.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-bold">Who sends evidence</h2>
        <dl className="space-y-3 max-w-measure">
          {SOURCES.map(([k, t]) => (
            <div key={k}>
              <dt className="font-bold">{k}</dt>
              <dd className="text-sm text-ink-soft">{t}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-bold">How we check a record, step by step</h2>
        <ol className="space-y-3 max-w-measure">
          {[
            "We keep the original file untouched and record its SHA-256 fingerprint and the time our server received it.",
            "Figures are read from the form. That reading is only a proposal.",
            "A reviewer checks every figure against the original and records the reason for any correction.",
            "We check the arithmetic. Candidate votes should add up to valid votes, and valid plus rejected votes to votes cast.",
            "We compare the records with each other and with the official copy, line by line.",
            "We check independence. Several photos of one sheet, or from one organisation, are not several independent sources.",
            "Every step is written to an audit log that shows if anything is later changed.",
          ].map((step, i) => (
            <li key={i} className="grid grid-cols-[2rem_1fr] gap-2 text-sm">
              <span className="grid place-items-center h-7 w-7 border-2 border-ink font-bold">{i + 1}</span>
              <span className="pt-0.5">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-3 border-l-4 border-wait pl-4 max-w-measure">
        <h2 className="text-lg font-bold">Limits you should know</h2>
        <ul className="list-disc pl-5 space-y-1 text-sm">
          <li>A fingerprint shows a file has not changed since we received it. It does not prove where or when a photo was taken.</li>
          <li>Phone clocks can be wrong, so we show phone times as &quot;device-reported&quot;.</li>
          <li>An arithmetic error or a difference between records is a reason to look closer, not proof of misconduct.</li>
          <li>A polling unit with a volunteer assigned is not counted as covered until evidence arrives.</li>
        </ul>
      </section>
    </article>
  );
}
