import json
import math
import re
from backend.database import MONTHS
from backend.models import FIELDS
from backend.services.document_index import extract_periods, cited_lines, FIELD_LABELS


def intake_check(case, documents):
    checks = [
        {
            "label": "Facility below INR 25 lakh",
            "passed": 0 < case["loan_amount"] < 2500000,
            "detail": f"INR {case['loan_amount']:,.0f}",
        }
    ]
    for kind, label in [
        ("bank", "Bank statements"),
        ("gstr1", "GSTR-1 returns"),
        ("gstr3b", "GSTR-3B returns"),
    ]:
        docs = [d for d in documents if d["kind"] == kind]
        covered = set(m for d in docs for m in json.loads(d["months"]))
        missing = sorted(set(MONTHS) - covered)
        checks.append(
            {
                "label": f"12-month {label}",
                "passed": not missing,
                "detail": "Jan–Dec 2025 complete"
                if not missing
                else "Missing: " + ", ".join(missing),
            }
        )
    native = bool(documents) and all(
        d["native_text"] and json.loads(d["pages"]) for d in documents
    )
    checks.append(
        {
            "label": "Native text-based PDFs only (A2)",
            "passed": native,
            "detail": "Text layer available on every page"
            if native
            else "Scanned/image-only or empty pages rejected; request native PDFs",
        }
    )
    checks.append(
        {
            "label": "Structured cash-share & gap notes",
            "passed": case["cash_share"] is not None
            and 0 <= case["cash_share"] <= 100
            and len(case["gap_notes"].strip()) >= 10,
            "detail": f"Cash share: {case['cash_share']}% · {case['gap_notes']}",
        }
    )
    return {
        "passed": all(c["passed"] for c in checks),
        "checks": checks,
        "coverage_window": MONTHS,
    }


def reconcile(cells, threshold):
    rows = []
    for month in MONTHS:
        values = {c["field"]: c["value"] for c in cells if c["month"] == month}
        bank = values.get("credits")
        result = {"month": month, "bank_credits": bank, "threshold_pct": threshold}
        for field in ("gstr1", "gstr3b"):
            gst = values.get(field)
            variance = (
                None
                if bank is None or gst is None
                else (
                    0.0
                    if bank == gst == 0
                    else (None if bank == 0 else abs(bank - gst) / abs(bank) * 100)
                )
            )
            result[field] = gst
            result[field + "_variance_pct"] = (
                round(variance, 3) if variance is not None else None
            )
            result[field + "_flagged"] = variance is None or variance > threshold
        result["flagged"] = result["gstr1_flagged"] or result["gstr3b_flagged"]
        rows.append(result)
    return rows


def citation_issues(cells, documents):
    issues = []
    expected = {(month, field) for month in MONTHS for field in FIELDS}
    actual = [(c["month"], c["field"]) for c in cells]
    if set(actual) != expected or len(actual) != len(expected):
        issues.append(
            "Extraction must have exactly one value per field per month (60 unique cells)"
        )
    docs = {d["name"]: d for d in documents}
    for cell in cells:
        cite = cell["citation"]
        tag = f"{cell['month']}/{cell['field']}"
        doc = docs.get(cite["source_doc"])
        try:
            if not doc or not doc["native_text"]:
                raise ValueError()
            expected_kind = (
                "bank"
                if cell["field"] in ("credits", "debits", "average_balance")
                else cell["field"]
            )
            if doc["kind"] != expected_kind:
                raise ValueError()
            pages = json.loads(doc["pages"])
            line = cited_lines(pages, cite["page_number"], cite["line_ref"])
            quote = cite["raw_text_quote"]
            quote_periods = extract_periods(quote)
            page_periods = extract_periods("\n".join(pages[cite["page_number"] - 1]))
            month_grounded = cell["month"] in quote_periods or (
                not quote_periods and page_periods == [cell["month"]]
            )
            if (
                quote != line
                or not month_grounded
                or not re.search(FIELD_LABELS[cell["field"]], quote, re.I)
            ):
                raise ValueError()
            amounts = re.findall(r"(?<![\d.-])\d[\d,]*(?:\.\d{1,2})?(?![\d.-])", line)
            if not any(
                math.isclose(
                    float(a.replace(",", "")), cell["value"], rel_tol=0, abs_tol=0.005
                )
                for a in amounts
            ):
                raise ValueError()
        except (ValueError, IndexError, AttributeError, KeyError, TypeError):
            issues.append(
                f"{tag}: number, month, field or exact page/line citation is ungrounded"
            )
    return issues
