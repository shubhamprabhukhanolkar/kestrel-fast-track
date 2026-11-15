"""Compact model inputs without dropping evidence or weakening backend validation."""

import json
from backend.services.document_index import cited_lines, extract_periods


def compact_cells(cells, include_quotes=True):
    names = list(dict.fromkeys(c["citation"]["source_doc"] for c in cells))
    aliases = {name: f"D{i + 1}" for i, name in enumerate(names)}
    columns = [
        "month",
        "field",
        "value",
        "document_alias",
        "page_number",
        "line_ref",
        "confidence",
        "analyst_verified_by",
    ]
    if include_quotes:
        columns.append("raw_text_quote")
    rows = []
    for cell in cells:
        citation = cell["citation"]
        row = [
            cell["month"],
            cell["field"],
            cell["value"],
            aliases[citation["source_doc"]],
            citation["page_number"],
            citation["line_ref"],
            citation["confidence"],
            cell.get("verified_by"),
        ]
        if include_quotes:
            row.append(citation["raw_text_quote"])
        rows.append(row)
    return {
        "document_aliases": {alias: name for name, alias in aliases.items()},
        "cell_columns": columns,
        "cells": rows,
    }


def compact_reconciliation(rows):
    columns = [
        "month",
        "bank_credits",
        "gstr1",
        "gstr3b",
        "gstr1_variance_pct",
        "gstr3b_variance_pct",
        "threshold_pct",
        "flagged",
    ]
    return {
        "columns": columns,
        "rows": [[row[column] for column in columns] for row in rows],
    }


def critique_payload(cells, documents, reconciliation, threshold, issues):
    payload = compact_cells(cells)
    docs = {d["name"]: d for d in documents}
    aliases = {name: alias for alias, name in payload["document_aliases"].items()}
    originals = {}
    for cell in cells:
        citation = cell["citation"]
        name = citation["source_doc"]
        alias = aliases[name]
        key = (alias, citation["page_number"], citation["line_ref"])
        try:
            pages = json.loads(docs[name]["pages"])
            quote = cited_lines(pages, citation["page_number"], citation["line_ref"])
            months = extract_periods("\n".join(pages[citation["page_number"] - 1]))
        except (KeyError, IndexError, ValueError, TypeError):
            quote, months = None, []
        originals[key] = [
            alias,
            citation["page_number"],
            citation["line_ref"],
            quote,
            months,
        ]
    payload.update(
        source_columns=[
            "document_alias",
            "page_number",
            "line_ref",
            "actual_source_text",
            "page_periods",
        ],
        source_quotes=list(originals.values()),
        reconciliation=compact_reconciliation(reconciliation),
        threshold_pct=threshold,
        deterministic_issues=issues,
        variance_formula="abs(bank_credits - gst_turnover) / abs(bank_credits) * 100; zero bank/nonzero GST unresolved",
        instructions="Compare every extracted quote/value with actual_source_text independently. Expand document_aliases for source identity. Model confidence is metadata, not a PDF-extracted amount.",
    )
    return payload
