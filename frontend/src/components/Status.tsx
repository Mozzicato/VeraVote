import type { StatusKey } from "@/lib/types";

// A status is a small boxed mark (like a tick-box on the result form) plus words. Never colour alone.
const STYLE: Record<StatusKey, { glyph: string; box: string; text: string; title: string }> = {
  no_evidence: { glyph: "", box: "border-ink-soft", text: "text-ink-soft", title: "No evidence yet" },
  evidence_received: { glyph: "•", box: "border-violet text-violet", text: "text-violet", title: "Evidence received" },
  under_review: { glyph: "…", box: "border-wait text-wait", text: "text-wait", title: "Under review" },
  consistent_evidence: { glyph: "✓", box: "border-agree bg-agree text-sheet", text: "text-agree", title: "Records agree" },
  discrepancy_detected: { glyph: "≠", box: "border-differ bg-differ text-sheet", text: "text-differ", title: "Records differ" },
  insufficient_evidence: { glyph: "1", box: "border-ink text-ink", text: "text-ink", title: "Not enough to compare" },
  review_completed: { glyph: "■", box: "border-done text-done", text: "text-done", title: "Review completed" },
};

export function StatusMark({ status, className = "" }: { status: StatusKey; className?: string }) {
  const s = STYLE[status] ?? STYLE.no_evidence;
  return (
    <span
      aria-hidden
      className={`inline-grid place-items-center w-[1.15em] h-[1.15em] border-2 text-[0.8em] leading-none font-bold shrink-0 ${s.box} ${className}`}
    >
      {s.glyph}
    </span>
  );
}

export function StatusBadge({ status, size = "sm" }: { status: StatusKey; size?: "sm" | "lg" }) {
  const s = STYLE[status] ?? STYLE.no_evidence;
  return (
    <span className={`inline-flex items-center gap-2 font-bold ${s.text} ${size === "lg" ? "text-lg" : "text-sm"}`}>
      <StatusMark status={status} />
      {s.title}
    </span>
  );
}

export function statusTitle(status: StatusKey) {
  return STYLE[status]?.title ?? status;
}
