"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, getDemoUser, post, setDemoUser } from "@/lib/api";
import { Button, Card, ErrorText, Field, Loading, Notice, inputCls } from "@/components/ui";

type Me = {
  user: { id: number; name: string; role: string };
  application_status: string | null;
  next_step: string;
  training_modules_completed: string[];
  assessment_status: string | null;
  assessment_score: number | null;
  classification: string;
  classification_label: string;
  official: { role: string; status: string; reference: string | null; party: string | null; note: string } | null;
  organisation: { id: number; name: string } | null;
  can_submit_field_evidence: boolean;
  simulated_otp_hint?: string;
};
type Module = { id: string; title: string; points: string[]; completed: boolean };
type Question = { id: string; kind: string; text: string; options: string[] };

const STEPS = ["Apply", "Verify phone", "Training", "Assessment", "Approved"];
const STEP_INDEX: Record<string, number> = {
  identity_verification_pending: 1, training_pending: 2, assessment_pending: 3, approved: 4,
};

export default function Volunteer() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [hint, setHint] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    if (!getDemoUser()) {
      setMe(null);
      setLoading(false);
      return;
    }
    try {
      setMe(await api<Me>("/volunteers/me"));
    } catch {
      setMe(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    window.addEventListener("veravote:user", load);
    return () => window.removeEventListener("veravote:user", load);
  }, [load]);

  if (loading) return <Loading />;
  const status = me?.application_status;
  const step = status ? STEP_INDEX[status] ?? 0 : 0;

  return (
    <div className="space-y-5 max-w-2xl">
      <h1 className="text-2xl font-bold">Become a VeraVote volunteer</h1>
      <ol className="flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Progress">
        {STEPS.map((s, i) => (
          <li key={s} className={i <= step && status ? "text-violet font-semibold" : "text-ink-soft"} aria-current={i === step ? "step" : undefined}>
            {i + 1}. {s}
          </li>
        ))}
      </ol>
      {hint && <Notice>{hint}</Notice>}

      {!me || !status ? (
        me && me.user.role !== "volunteer" ? (
          <Notice>
            You are viewing as <strong>{me.user.name}</strong> ({me.user.role}). Switch to &quot;Public visitor&quot; to
            start a new application.
          </Notice>
        ) : (
          <ApplyForm onDone={(m) => { setHint(m.simulated_otp_hint ?? null); setMe(m); }} />
        )
      ) : status === "identity_verification_pending" ? (
        <VerifyPhone onDone={(m) => { setHint(null); setMe(m); }} />
      ) : status === "training_pending" ? (
        <Training me={me} onDone={setMe} />
      ) : status === "assessment_pending" ? (
        <Assessment onDone={setMe} />
      ) : (
        <StatusCard me={me} onChange={setMe} />
      )}
    </div>
  );
}

function ApplyForm({ onDone }: { onDone: (m: Me) => void }) {
  const [states, setStates] = useState<{ id: number; name: string }[]>([]);
  const [lgas, setLgas] = useState<{ id: number; name: string }[]>([]);
  const [f, setF] = useState({ name: "", phone: "", email: "", state_id: "", lga_id: "", accept: false });
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ id: number; name: string }[]>("/states").then(setStates);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const me = await post<Me>("/volunteers/apply", {
        name: f.name, phone: f.phone, email: f.email || null, state_id: Number(f.state_id),
        lga_id: Number(f.lga_id), accept_code_of_conduct: f.accept,
      });
      setDemoUser(me.user.id);
      onDone(me);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not apply");
    }
  }

  return (
    <form onSubmit={submit}>
      <Card className="space-y-4">
        <p className="text-sm text-ink-soft">
          Open to any eligible Nigerian. You don&apos;t need to belong to an organisation. Training takes about 20
          minutes.
        </p>
        <Field label="Full name"><input className={inputCls} required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Phone number" hint="We send a one-time code to confirm it."><input className={inputCls} required inputMode="tel" placeholder="+234…" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
        <Field label="Email (optional)"><input className={inputCls} type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="State">
            <select className={inputCls} required value={f.state_id} onChange={(e) => { setF({ ...f, state_id: e.target.value, lga_id: "" }); api<{ id: number; name: string }[]>(`/lgas?state_id=${e.target.value}`).then(setLgas); }}>
              <option value="">Choose…</option>
              {states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="LGA you'd like to cover">
            <select className={inputCls} required value={f.lga_id} onChange={(e) => setF({ ...f, lga_id: e.target.value })}>
              <option value="">Choose…</option>
              {lgas.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
        </div>
        <details className="text-sm rounded-md border border-rule p-3">
          <summary className="cursor-pointer font-medium">Volunteer code of conduct</summary>
          <ul className="list-disc pl-5 mt-2 space-y-1 text-ink-soft">
            <li>Stay neutral. No campaigning, party colours or telling people how to vote.</li>
            <li>Never interfere with voters, officials, counting or security personnel.</li>
            <li>Your safety comes first. Leave if you feel unsafe; you can withdraw at any time.</li>
            <li>Submit original, unedited evidence only.</li>
            <li>Keep other people&apos;s personal information confidential.</li>
          </ul>
        </details>
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1" checked={f.accept} onChange={(e) => setF({ ...f, accept: e.target.checked })} />
          I accept the volunteer code of conduct.
        </label>
        <ErrorText error={error} />
        <Button disabled={!f.accept}>Apply</Button>
      </Card>
    </form>
  );
}

function VerifyPhone({ onDone }: { onDone: (m: Me) => void }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <Card className="space-y-3">
      <h2 className="font-semibold">Confirm your phone number</h2>
      <p className="text-sm text-ink-soft">Enter the 6-digit code we sent you. (Demo mode: the code is 123456.)</p>
      <input aria-label="One-time code" autoComplete="one-time-code" className={`${inputCls} max-w-40 font-mono tracking-widest`} inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
      <ErrorText error={error} />
      <Button onClick={async () => {
        try { onDone(await post<Me>("/volunteers/verify-phone", { code })); } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
      }}>Verify</Button>
    </Card>
  );
}

function Training({ me, onDone }: { me: Me; onDone: (m: Me) => void }) {
  const [modules, setModules] = useState<Module[]>([]);
  useEffect(() => {
    api<Module[]>("/volunteers/training").then(setModules);
  }, [me.training_modules_completed.length]);
  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-soft">Read each module, then mark it done. All five are needed before the assessment.</p>
      {modules.map((m, i) => (
        <Card key={m.id} className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-semibold">Module {i + 1}: {m.title}</h2>
            {m.completed && <span className="text-xs text-agree font-medium">✓ Done</span>}
          </div>
          <ul className="list-disc pl-5 text-sm space-y-1">
            {m.points.map((p) => <li key={p}>{p}</li>)}
          </ul>
          {!m.completed && (
            <Button variant="secondary" onClick={async () => onDone(await post<Me>(`/volunteers/training/${m.id}/complete`))}>
              I&apos;ve read this
            </Button>
          )}
        </Card>
      ))}
    </div>
  );
}

function Assessment({ onDone }: { onDone: (m: Me) => void }) {
  const [qs, setQs] = useState<Question[]>([]);
  const [passMark, setPassMark] = useState(0.8);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<{ score: number; passed: boolean; incorrect: string[]; attempts_left: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ questions: Question[]; pass_mark: number }>("/volunteers/assessment").then((a) => { setQs(a.questions); setPassMark(a.pass_mark); });
  }, []);
  const kindLabel: Record<string, string> = { knowledge: "Knowledge", practical: "Reading a result sheet", exercise: "Submission exercise" };

  async function submit() {
    setError(null);
    try {
      const r = await post<Me & { score: number; passed: boolean; incorrect: string[]; attempts_left: number }>("/volunteers/assessment", { answers });
      setResult(r);
      if (r.passed) onDone(r);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-soft">Pass mark: {Math.round(passMark * 100)}%. You have up to three attempts.</p>
      {result && !result.passed && (
        <Notice tone="warn">
          You scored {Math.round(result.score * 100)}%. Review the questions marked below and try again ({result.attempts_left} attempt{result.attempts_left === 1 ? "" : "s"} left).
        </Notice>
      )}
      {qs.map((q, i) => (
        <Card key={q.id} className={result?.incorrect.includes(q.id) ? "border-differ/50" : ""}>
          <fieldset className="space-y-2">
            <legend className="text-sm">
              <span className="block text-xs text-ink-soft">{kindLabel[q.kind]}</span>
              <span className="font-medium">{i + 1}. {q.text}</span>
            </legend>
            {q.options.map((o, j) => (
              <label key={o} className="flex items-start gap-2 text-sm">
                <input type="radio" name={q.id} className="mt-1" checked={answers[q.id] === j} onChange={() => setAnswers({ ...answers, [q.id]: j })} />
                {o}
              </label>
            ))}
          </fieldset>
        </Card>
      ))}
      <ErrorText error={error} />
      <Button onClick={submit} disabled={Object.keys(answers).length < qs.length}>Submit answers</Button>
    </div>
  );
}

function StatusCard({ me, onChange }: { me: Me; onChange: (m: Me) => void }) {
  const [claim, setClaim] = useState({ role: "accredited_observer", reference: "", party: "" });
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="space-y-4">
      <Card className="space-y-2">
        <p className="text-sm text-ink-soft">You are recorded as</p>
        <p className="text-lg font-semibold">{me.classification_label}</p>
        {me.assessment_score != null && <p className="text-sm">Assessment score: {Math.round(me.assessment_score * 100)}%</p>}
        {me.organisation && <p className="text-sm">Organisation: {me.organisation.name}</p>}
        <p className="text-sm">{me.next_step}</p>
        {me.can_submit_field_evidence && (
          <Link href="/contributor" className="inline-block text-violet underline text-sm">Go to my assignments</Link>
        )}
      </Card>
      <Card className="space-y-3">
        <h2 className="font-semibold">Official status</h2>
        <p className="text-xs text-ink-soft">{me.official?.note}</p>
        {me.official && me.official.role !== "none" ? (
          <p className="text-sm">
            {me.official.role === "party_agent" ? `Party agent (${me.official.party})` : "INEC-accredited observer"} —{" "}
            <strong>{me.official.status === "claimed" ? "waiting for a reviewer to check" : me.official.status}</strong>
            {me.official.reference && <>, ref {me.official.reference}</>}
          </p>
        ) : (
          <>
            <p className="text-sm">Are you also an INEC-accredited observer or an authorised party agent? Tell us so a reviewer can check it.</p>
            <select className={inputCls} value={claim.role} onChange={(e) => setClaim({ ...claim, role: e.target.value })}>
              <option value="accredited_observer">INEC-accredited observer</option>
              <option value="party_agent">Authorised party agent</option>
            </select>
            <input className={inputCls} placeholder="Accreditation or authorisation reference" value={claim.reference} onChange={(e) => setClaim({ ...claim, reference: e.target.value })} />
            {claim.role === "party_agent" && (
              <input className={inputCls} placeholder="Party you represent" value={claim.party} onChange={(e) => setClaim({ ...claim, party: e.target.value })} />
            )}
            <ErrorText error={error} />
            <Button variant="secondary" onClick={async () => {
              try { onChange(await post<Me>("/volunteers/official-status", { role: claim.role, reference: claim.reference, party: claim.party || null })); }
              catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
            }}>Submit for checking</Button>
          </>
        )}
      </Card>
    </div>
  );
}
