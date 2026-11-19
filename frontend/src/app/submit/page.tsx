"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, post } from "@/lib/api";
import { newClientId } from "@/lib/offline";
import type { Contest, PollingUnit, Receipt, UnitPage } from "@/lib/types";
import { ReceiptCard } from "@/components/ReceiptCard";
import { UnitPicker } from "@/components/UnitPicker";
import { Button, Card, ErrorText, Field, Notice, inputCls } from "@/components/ui";

export default function SubmitPage() {
  return (
    <Suspense>
      <SubmitForm />
    </Suspense>
  );
}

const TYPES = [
  ["result_poster_photo", "Photo of a result sheet displayed in public"],
  ["result_sheet_photo", "Photo or scan of a result form"],
  ["public_link", "Link to a publicly available document"],
  ["other_info", "Information about a conflicting result record"],
] as const;

function SubmitForm() {
  const params = useSearchParams();
  const [pu, setPu] = useState<PollingUnit | null>(null);
  const [contests, setContests] = useState<Contest[]>([]);
  const [contestId, setContestId] = useState<number | null>(null);
  const [type, setType] = useState<string>("result_poster_photo");
  const [file, setFile] = useState<File | null>(null);
  const [link, setLink] = useState("");
  const [desc, setDesc] = useState("");
  const [forwarded, setForwarded] = useState("no");
  const [contact, setContact] = useState("");
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [clientId] = useState(newClientId);

  useEffect(() => {
    api<{ contests: Contest[] }>("/public/summary").then((s) => {
      setContests(s.contests);
      const wanted = Number(params.get("contest"));
      setContestId(s.contests.find((c) => c.id === wanted)?.id ?? s.contests[0]?.id ?? null);
    });
    const puId = params.get("pu");
    if (puId) api<UnitPage>(`/public/polling-units/${puId}`).then((p) => setPu(p.polling_unit)).catch(() => {});
  }, [params]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!pu || !contestId) return setError("Choose the polling unit.");
    setBusy(true);
    const fd = new FormData();
    fd.set("polling_unit_id", String(pu.id));
    fd.set("contest_id", String(contestId));
    fd.set("evidence_type", type);
    fd.set("description", desc);
    fd.set("is_forwarded_copy", forwarded);
    fd.set("accepted_notice", String(agree));
    fd.set("client_submission_id", clientId);
    if (link) fd.set("source_url", link);
    if (contact) fd.set("follow_up_contact", contact);
    if (file) fd.set("file", file, file.name);
    try {
      setReceipt(await post<Receipt>("/public/evidence-leads", fd));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  if (receipt)
    return (
      <div className="space-y-4 max-w-2xl">
        <h1 className="text-2xl font-bold">We received your evidence</h1>
        <p className="text-sm text-ink-soft">
          Your evidence is a <strong>citizen lead</strong>. Our verification team will review it before it is
          compared with other records. It is not published as verified.
        </p>
        <ReceiptCard r={receipt} />
      </div>
    );

  const needsFile = type === "result_poster_photo" || type === "result_sheet_photo";
  return (
    <form onSubmit={submit} className="space-y-5 max-w-2xl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold">Submit evidence</h1>
        <p className="text-sm text-ink-soft">
          Anyone can share evidence. You don&apos;t need an account or observer status.
        </p>
      </header>
      <Notice tone="warn">
        Only photograph what is openly displayed or what you are allowed to see. Never enter restricted areas,
        interfere with officials, or put yourself in danger to get a photo.
      </Notice>
      <Card className="space-y-4">
        <div className="flex flex-col gap-1 text-sm" role="group" aria-labelledby="pu-label">
          <span id="pu-label" className="font-medium">Polling unit</span>
          <UnitPicker value={pu} onChange={setPu} />
        </div>
        {contests.length > 1 && (
          <Field label="Election and contest">
            <select className={inputCls} value={contestId ?? ""} onChange={(e) => setContestId(Number(e.target.value))}>
              {contests.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.office}, {c.election.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <fieldset className="space-y-1 text-sm">
          <legend className="font-medium mb-1">What are you sharing?</legend>
          {TYPES.map(([v, l]) => (
            <label key={v} className="flex items-center gap-2">
              <input type="radio" name="type" value={v} checked={type === v} onChange={() => setType(v)} /> {l}
            </label>
          ))}
        </fieldset>
        {needsFile && (
          <Field label="Photo or scan" hint="Send the original photo. Please don't crop, filter or edit it.">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              capture="environment"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm"
            />
          </Field>
        )}
        {type === "public_link" && (
          <Field label="Link">
            <input className={inputCls} type="url" value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://" />
          </Field>
        )}
        <Field label="Anything we should know? (optional)">
          <textarea className={inputCls} rows={3} value={desc} onChange={(e) => setDesc(e.target.value)} maxLength={2000} />
        </Field>
        <fieldset className="text-sm space-y-1">
          <legend className="font-medium mb-1">Did you take this photo yourself?</legend>
          {[["no", "Yes, I took it myself"], ["yes", "No, someone sent it to me"], ["unknown", "Not sure"]].map(([v, l]) => (
            <label key={v} className="flex items-center gap-2">
              <input type="radio" name="fwd" checked={forwarded === v} onChange={() => setForwarded(v)} /> {l}
            </label>
          ))}
        </fieldset>
        <Field label="Phone or email for follow-up (optional)" hint="Kept private. Never shown publicly.">
          <input className={inputCls} value={contact} onChange={(e) => setContact(e.target.value)} maxLength={200} />
        </Field>
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} className="mt-1" />
          <span>
            I understand this is shared as a citizen lead, will be reviewed before use, and that I obtained it lawfully
            and safely.
          </span>
        </label>
        <ErrorText error={error} />
        <Button disabled={busy || !agree}>{busy ? "Sending…" : "Submit evidence"}</Button>
      </Card>
    </form>
  );
}
