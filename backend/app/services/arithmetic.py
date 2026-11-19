"""Arithmetic validation of a result form (PRD §9.3).

A failed check raises a review flag. It is never treated as proof of misconduct.
"""


def check(values: dict[str, int | None]) -> list[dict]:
    flags = []
    cands = [v for k, v in values.items() if k.startswith("cand:")]
    valid, rejected, cast, accredited = (values.get(k) for k in ("total_valid", "rejected", "total_cast", "accredited"))

    if cands and None not in cands and valid is not None and sum(cands) != valid:
        flags.append({
            "check": "candidate_sum", "expected": sum(cands), "found": valid,
            "message": f"The candidates' votes add up to {sum(cands)}, but the form says total valid votes is {valid}.",
        })
    if None not in (valid, rejected, cast) and valid + rejected != cast:
        flags.append({
            "check": "valid_plus_rejected", "expected": valid + rejected, "found": cast,
            "message": f"Valid votes plus rejected votes is {valid + rejected}, but the form says total votes cast is {cast}.",
        })
    if None not in (cast, accredited) and cast > accredited:
        flags.append({
            "check": "cast_exceeds_accredited", "expected": f"≤ {accredited}", "found": cast,
            "message": f"The form records {cast} votes cast but only {accredited} accredited voters.",
        })
    return flags
