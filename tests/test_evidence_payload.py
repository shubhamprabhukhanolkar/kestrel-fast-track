import json
from backend.database import db
from backend.services.agent_graph import demo_extract, source_payload
from backend.services.evidence_payload import critique_payload, compact_cells
from backend.services.intake_rules import reconcile


def test_compact_critique_preserves_every_value_and_independent_source_quote(client):
    with db() as conn:
        docs = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM documents WHERE case_id='KF-2026-0892'"
            )
        ]
    cells = demo_extract(docs)["cells"]
    reconciliation = reconcile(cells, 10)
    payload = critique_payload(cells, docs, reconciliation, 10, [])
    assert len(payload["cells"]) == 60
    decoded = [dict(zip(payload["cell_columns"], row)) for row in payload["cells"]]
    sources = {(r[0], r[1], r[2]): r[3] for r in payload["source_quotes"]}
    for cell, row in zip(cells, decoded):
        assert row["value"] == cell["value"] and row["month"] == cell["month"]
        assert (
            payload["document_aliases"][row["document_alias"]]
            == cell["citation"]["source_doc"]
        )
        assert (
            row["raw_text_quote"]
            == sources[(row["document_alias"], row["page_number"], row["line_ref"])]
        )
    full = {
        "cells": cells,
        "documents": source_payload(docs),
        "reconciliation": reconciliation,
    }
    assert len(json.dumps(payload)) < len(json.dumps(full)) * 0.7
    # A forged extraction must not overwrite what the model sees as the original source.
    cells[0]["citation"]["raw_text_quote"] = "invented quote"
    forged = critique_payload(cells, docs, reconciliation, 10, ["Ungrounded quote"])
    first = dict(zip(forged["cell_columns"], forged["cells"][0]))
    actual = {(r[0], r[1], r[2]): r[3] for r in forged["source_quotes"]}
    assert (
        actual[(first["document_alias"], first["page_number"], first["line_ref"])]
        != "invented quote"
    )
    memo = compact_cells(cells, include_quotes=False)
    assert len(memo["cells"]) == 60 and "raw_text_quote" not in memo["cell_columns"]
    assert "page_number" in memo["cell_columns"] and "line_ref" in memo["cell_columns"]
