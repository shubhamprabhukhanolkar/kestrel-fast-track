"""Deterministic period normalization; original page/line text is preserved."""

import re

MONTH_NAMES = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def extract_periods(text):
    months = set(re.findall(r"\b(20\d{2}-(?:0[1-9]|1[0-2]))(?:-\d{2})?\b", text))
    for month, year in re.findall(
        r"\b(?:\d{1,2}[/.-])?(0?[1-9]|1[0-2])[/.-](20\d{2})\b", text
    ):
        months.add(f"{year}-{int(month):02d}")
    for name, year in re.findall(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s,/-]+(20\d{2})\b",
        text,
        re.I,
    ):
        months.add(f"{year}-{MONTH_NAMES.index(name[:3].lower()) + 1:02d}")
    return sorted(months)


def cited_lines(pages, page_number, line_ref):
    match = re.fullmatch(r"L(\d+)(?:-L?(\d+))?", line_ref)
    if not match:
        raise ValueError("Use L01 or L01-L05")
    start = int(match[1]) - 1
    end = int(match[2] or match[1])
    if (
        page_number < 1
        or page_number > len(pages)
        or start < 0
        or end <= start
        or end > len(pages[page_number - 1])
        or end - start > 30
    ):
        raise ValueError("Citation range outside the indexed page")
    return "\n".join(pages[page_number - 1][start:end])


FIELD_LABELS = {
    "credits": r"\bcredits?\b|\bdeposits?\b|credit turnover|cr\.?\s*total",
    "debits": r"\bdebits?\b|\bwithdrawals?\b|debit turnover|dr\.?\s*total",
    "average_balance": r"average[_\s]+balance|average monthly balance|monthly average balance|\bAMB\b|\bMAB\b",
    "gstr1": r"\bgstr1\b|turnover|taxable value|outward supplies",
    "gstr3b": r"\bgstr3b\b|turnover|taxable value|outward supplies",
}
