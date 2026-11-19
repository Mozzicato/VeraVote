import Link from "next/link";
import type { Receipt } from "@/lib/types";
import { fmtTime } from "./ui";

/** A submission receipt, styled as a tear-off slip: it is the one thing the contributor keeps. */
export function ReceiptCard({ r }: { r: Receipt }) {
  return (
    <section aria-label="Submission receipt" className="max-w-xl bg-sheet border-2 border-ink">
      <div className="p-4 sm:p-5 space-y-1 border-b-2 border-dashed border-ink/40">
        <p className="text-sm">Your submission reference</p>
        <p className="text-3xl font-bold font-mono tracking-wider">{r.receipt_code}</p>
        {r.duplicate_retry && <p className="text-sm text-ink-soft">We had already received this. This is the original receipt.</p>}
      </div>
      <dl className="p-4 sm:p-5 grid sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
        <Row k="Polling unit" v={`${r.polling_unit.name} (${r.polling_unit.code})`} />
        <Row k="Recorded as" v={r.classification_label} />
        <Row k="Received by our server" v={fmtTime(r.server_received_time)} />
        <Row k="Your phone's clock said" v={r.device_reported_time ? fmtTime(r.device_reported_time) : "not recorded"} />
        <Row k="Status" v={r.status.replace(/_/g, " ")} />
        {r.file_size != null && <Row k="File size" v={`${Math.round(r.file_size / 1024)} KB`} />}
      </dl>
      {r.file_sha256 && (
        <div className="px-4 sm:px-5 pb-4 space-y-1 text-sm">
          <p className="font-bold">SHA-256 fingerprint</p>
          <code className="block font-mono text-xs break-all bg-paper p-2">{r.file_sha256}</code>
          <p className="text-xs text-ink-soft">{r.hash_note}</p>
        </div>
      )}
      <p className="px-4 sm:px-5 pb-4 text-xs text-ink-soft">
        {r.device_time_note} Keep this reference. You can{" "}
        <Link className="underline" href={`/receipt/${r.receipt_code}`}>
          check its progress
        </Link>{" "}
        at any time.
      </p>
    </section>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-soft">{k}</dt>
      <dd className="font-bold">{v}</dd>
    </div>
  );
}
