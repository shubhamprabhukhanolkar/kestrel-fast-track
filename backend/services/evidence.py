from backend.services.intake_rules import reconcile


def evidence_snapshot(case, cells, threshold):
    """Rebuild authoritative facts from CURRENT verified values, never a stale LLM memo."""
    rows = reconcile(cells, threshold)
    exceptions = [r for r in rows if r["flagged"]]
    totals = {
        f: sum(c["value"] for c in cells if c["field"] == f)
        for f in ("credits", "debits", "gstr1", "gstr3b")
    }
    balances = [c["value"] for c in cells if c["field"] == "average_balance"]
    corrected = sum(c["value"] != c["original_value"] for c in cells)
    verified = sum(bool(c["verified_by"]) for c in cells)
    text = f"{case['id']} | {case['business']} | {case['city']}\nRequested facility: INR {case['loan_amount']:,.0f}. Evidence window: Jan-Dec 2025.\n"
    text += f"Analyst verified {verified}/{len(cells)} source fields; {corrected} distinct cells corrected. Case revision {case['revision']}.\n"
    text += f"CIBIL score: {case.get('cibil_score') if case.get('cibil_score') is not None else 'not provided'}; source: {case.get('cibil_source', 'not provided')}. Analyst note: {case.get('cibil_note', '')}\n"
    text += (
        "Annual totals: "
        + "; ".join(f"{f} INR {value:,.2f}" for f, value in totals.items())
        + ".\n"
    )
    text += f"Mean monthly balance: INR {sum(balances) / max(1, len(balances)):,.2f}. Policy tolerance: {threshold}%.\n"
    text += "Reconciliation formula: abs(bank credits - GST turnover) / bank credits x 100.\n"
    if exceptions:
        text += (
            "Exceptions requiring explicit human judgement:\n"
            + "\n".join(
                f"{r['month']}: bank INR {r['bank_credits'] or 0:,.2f}; GSTR1 delta {r['gstr1_variance_pct']}%; GSTR3B delta {r['gstr3b_variance_pct']}%."
                for r in exceptions
            )
            + "\n"
        )
    else:
        text += "All 12 months within reconciliation tolerance. This is not a credit approval.\n"
    text += f"RM notes (reported explanation, not automatically accepted): {case['gap_notes']}\n"
    # A few real anchors; complete per-cell provenance stays in the case audit record.
    anchors = []
    for c in cells:
        if c["month"] == "2025-11" and c["field"] in ("credits", "gstr1", "gstr3b"):
            citation = c["citation"]
            if isinstance(citation, str):
                import json

                citation = json.loads(citation)
            anchors.append(
                f"{citation['source_doc']} p.{citation['page_number']} {citation['line_ref']}"
            )
    text += (
        "Evidence anchors: "
        + "; ".join(anchors)
        + ".\nNO MODEL APPROVES CREDIT. Named human credit manager signature and rationale required."
    )
    return text
