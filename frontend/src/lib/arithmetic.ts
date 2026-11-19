// Client-side copy of backend/app/services/arithmetic.py, so reviewers see the checks update as they type.
// The server remains the source of truth; keep the two in step.
export type Check = { check: string; message: string };

export function checkFigures(values: Record<string, number | null>): Check[] {
  const flags: Check[] = [];
  const cands = Object.entries(values).filter(([k]) => k.startsWith("cand:")).map(([, v]) => v);
  const { total_valid: valid, rejected, total_cast: cast, accredited } = values;
  const sum = cands.reduce<number>((a, v) => a + (v ?? 0), 0);
  if (cands.length && cands.every((v) => v != null) && valid != null && sum !== valid)
    flags.push({ check: "candidate_sum", message: `The candidates' votes add up to ${sum}, but the form says total valid votes is ${valid}.` });
  if (valid != null && rejected != null && cast != null && valid + rejected !== cast)
    flags.push({ check: "valid_plus_rejected", message: `Valid votes plus rejected votes is ${valid + rejected}, but the form says total votes cast is ${cast}.` });
  if (cast != null && accredited != null && cast > accredited)
    flags.push({ check: "cast_exceeds_accredited", message: `The form records ${cast} votes cast but only ${accredited} accredited voters.` });
  return flags;
}
