import { useEffect, useState } from "react";
import { send } from "../api/client";
import { Panel, Badge } from "./shared";

export default function CibilPanel({ active, user, refresh, notify }) {
  const [score, setScore] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setScore(active.cibil_score ?? "");
    setNote(active.cibil_note || "");
    setError("");
  }, [active.id, active.cibil_score, active.cibil_note]);
  const editable = user.persona === "meena" && !active.decision;
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await send(
        `/cases/${active.id}/cibil`,
        { score: score === "" ? null : Number(score), note },
        "PUT",
      );
      await refresh();
      notify("CIBIL information saved with its source and audit trail.");
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Panel
      title="CIBIL score"
      className="cibil-compact"
      action={
        <div className="cibil-headline">
          <strong>{active.cibil_score ?? "—"}</strong>
          <span>/ 900</span>
        </div>
      }
    >
      <div className="cibil-compact-summary">
        <Badge type="purple">
          {active.cibil_source === "manual"
            ? "Manually supplied"
            : "Example case"}
        </Badge>
        <span title={active.cibil_note}>
          {active.cibil_note || "Score not provided"}
        </span>
      </div>
      {editable && (
        <details className="cibil-edit">
          <summary>Edit score & source</summary>
          <form className="panel-body cibil-form" onSubmit={save}>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <div className="cibil-fields">
              <label>
                CIBIL score
                <input
                  type="number"
                  min="300"
                  max="900"
                  step="1"
                  value={score}
                  onChange={(e) => setScore(e.target.value)}
                  placeholder="300–900 or leave blank"
                  disabled={!editable || busy}
                />
              </label>
              <label>
                Score source / analyst note
                <input
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  minLength={5}
                  maxLength={1000}
                  required
                  placeholder="For example: supplied report dated 16 November 2026"
                  disabled={!editable || busy}
                />
              </label>
            </div>
            {active.cibil_updated_by && (
              <p className="helper">
                Last updated by {active.cibil_updated_by} ·{" "}
                {new Date(active.cibil_updated_at).toLocaleString("en-IN")}
              </p>
            )}
            {editable && (
              <button
                type="submit"
                className="secondary"
                disabled={busy || note.trim().length < 5}
              >
                {busy ? "Saving…" : "Save CIBIL information"}
              </button>
            )}
            <p className="helper">
              Score range 300–900. Record the source when entering a supplied
              score. The score does not automatically approve or decline a case.{" "}
              <a
                href="https://www.cibil.com/faq/understand-your-credit-score-and-report"
                target="_blank"
                rel="noreferrer"
              >
                About CIBIL scores
              </a>
            </p>
          </form>
        </details>
      )}
    </Panel>
  );
}
