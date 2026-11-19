import type { ReactNode } from "react";

/** A working panel. Used for tools and forms, not as a wrapper for every section. */
export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-[3px] border border-rule bg-sheet p-4 sm:p-5 ${className}`}>{children}</section>;
}

/** An unboxed page section: a heading and content separated by space, not borders. */
export function Section({ title, children, className = "", aside }: { title: string; children: ReactNode; className?: string; aside?: ReactNode }) {
  return (
    <section className={`space-y-3 ${className}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-bold tracking-tight">{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** A marginal note: a coloured rule on the left, like a reviewer's note beside a form. */
export function Notice({ tone = "info", children }: { tone?: "info" | "warn" | "bad" | "ok"; children: ReactNode }) {
  const cls = {
    info: "border-violet bg-done-tint",
    warn: "border-wait bg-wait-tint",
    bad: "border-differ bg-differ-tint",
    ok: "border-agree bg-agree-tint",
  }[tone];
  return <div className={`border-l-4 px-3 py-2 text-sm max-w-measure ${cls}`}>{children}</div>;
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  const cls = {
    primary: "bg-violet text-on-violet hover:bg-violet-strong border border-violet",
    secondary: "bg-sheet border border-ink/25 text-ink hover:border-ink/60",
    danger: "bg-differ text-on-violet border border-differ hover:opacity-90",
  }[variant];
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[3px] px-4 py-2 text-sm font-bold disabled:opacity-45 disabled:cursor-not-allowed ${cls} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-bold">{label}</span>
      {children}
      {hint && <span className="text-xs text-ink-soft">{hint}</span>}
    </label>
  );
}

export const inputCls =
  "rounded-[3px] border border-ink/30 bg-sheet px-3 py-2 text-base w-full placeholder:text-ink-soft/80 focus:border-violet";

export function Hash({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-ink-soft">none</span>;
  return (
    <code className="font-mono text-xs break-all" title={value}>
      {value.slice(0, 12)}…{value.slice(-6)}
    </code>
  );
}

export function fmtTime(iso: string | null | undefined) {
  if (!iso) return "not recorded";
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
  return d.toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });
}

export function Loading() {
  return <p className="text-ink-soft text-sm py-8">Loading…</p>;
}

export function ErrorText({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <p role="alert" className="text-sm text-differ font-bold">
      {error}
    </p>
  );
}

/** Small separated facts, as a real list rather than a dot-joined string. */
export function Meta({ items, className = "" }: { items: (ReactNode | null | false | undefined)[]; className?: string }) {
  const shown = items.filter(Boolean);
  return (
    <ul className={`flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-soft ${className}`}>
      {shown.map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </ul>
  );
}
