import { useEffect, useRef, useState } from "react";
import {
  Table2,
  FileSearch,
  PenLine,
  Download,
  CheckCircle2,
  ArrowUpRight,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";
import { api, send, inr, monthLabel } from "../api/client";
import { Title, Panel, Badge, Steps, Guardrail, Busy, Empty } from "./shared";
const fields = [
  ["credits", "Bank credits"],
  ["debits", "Bank debits"],
  ["average_balance", "Average balance"],
  ["gstr1", "GSTR-1 turnover"],
  ["gstr3b", "GSTR-3B turnover"],
];
export default function SpreadingWorkspace({
  active,
  user,
  refresh,
  notify,
  navigate,
}) {
  const [month, setMonth] = useState("2025-11"),
    [selectedId, setSelectedId] = useState(null),
    [value, setValue] = useState(""),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [outcome, setOutcome] = useState("approve"),
    [signature, setSignature] = useState(""),
    [rationale, setRationale] = useState(""),
    [threshold, setThreshold] = useState(10),
    [preview, setPreview] = useState("");
  const sourceRef = useRef(null);
  const selected =
    active.cells.find((c) => c.id === selectedId) ||
    active.cells.find((c) => c.month === month && c.field === "credits");
  const doc = active.documents.find(
    (d) => d.name === selected?.citation?.source_doc,
  );
  const monthRows = active.cells.filter((c) => c.month === month);
  const citedRange = selected?.citation.line_ref.match(/^L(\d+)(?:-L?(\d+))?$/);
  const lineIsCited = (i) =>
    citedRange &&
    i + 1 >= Number(citedRange[1]) &&
    i + 1 <= Number(citedRange[2] || citedRange[1]);
  const reconciliation = active.reconciliation.find((r) => r.month === month);
  const locked = !!active.decision;
  useEffect(() => {
    setSelectedId(null);
    setReason("");
    setError("");
    setPreview("");
    setSignature("");
    setRationale("");
  }, [active.id]);
  useEffect(() => {
    setValue(selected?.value ?? "");
    setReason("");
    sourceRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selected?.id]);
  useEffect(() => {
    api("/prompts")
      .then((p) => setThreshold(p.policy.gst_variance_threshold_pct))
      .catch((e) => setError(e.message));
  }, [active.id]);
  async function verify() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await send(
        `/cases/${active.id}/verify`,
        { cell_id: selected.id, value: Number(value), reason },
        "PUT",
      );
      await refresh();
      notify("Cell verified. Analyst audit and correction rate updated.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function sign(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await send(`/cases/${active.id}/decision`, {
        outcome,
        signature,
        rationale,
      });
      await refresh();
      notify("Human credit decision recorded. The case is now locked.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function savePolicy() {
    setBusy(true);
    setError("");
    try {
      await send(
        "/policy",
        { gst_variance_threshold_pct: Number(threshold) },
        "PUT",
      );
      await refresh();
      notify("Policy version saved. Reconciliation recalculated.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function generateMemo() {
    setBusy(true);
    setError("");
    try {
      const result = await send("/toner/preview", {
        case_id: active.id,
        tone: "Concise Analyst Dossier",
      });
      setPreview(result.text);
      notify("Dossier preview refreshed from current verified evidence.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const ready =
    active.cells.length === 60 &&
    active.verified_count === 60 &&
    active.intake.passed;
  return (
    <>
      <Title
        eyebrow="STEPS 03–05 · VERIFY, JUDGE & SIGN"
        title="Evidence you can trace. Decisions you own."
        description={`${active.business}, ${active.city} · Review every source field before recording a human outcome.`}
        action={
          <a
            className="button secondary"
            href={`/api/v1/cases/${active.id}/dossier.pdf`}
          >
            <Download size={15} />
            Evidence dossier
          </a>
        }
      />
      <Steps active={locked ? 5 : ready ? 5 : 4} />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!active.cells.length ? (
        <Empty>
          Intake is incomplete.{" "}
          <button className="ghost" onClick={() => navigate("intake")}>
            Resolve intake gaps →
          </button>
        </Empty>
      ) : (
        <div className="two-panels verification-panels">
          <div className="panel-stack">
            <Panel
              title="Cited spreading sheet"
              subtitle="Steps 3 & 4 · Select a cell to inspect its exact source"
              icon={Table2}
              action={
                <Badge type="green">{active.verified_count}/60 verified</Badge>
              }
            >
              <div className="panel-body compact">
                <div className="row spread wrap">
                  <label className="inline-label">
                    REVIEW MONTH{" "}
                    <select
                      value={month}
                      onChange={(e) => {
                        setMonth(e.target.value);
                        setSelectedId(null);
                      }}
                    >
                      {active.reconciliation.map((r) => (
                        <option key={r.month} value={r.month}>
                          {monthLabel(r.month)}
                          {r.flagged ? " · exception" : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Badge type={reconciliation?.flagged ? "amber" : "green"}>
                    {reconciliation?.flagged
                      ? "Reconciliation exception"
                      : "Within tolerance"}
                  </Badge>
                </div>
              </div>
              <div className="table-scroll">
                <table className="spread-table">
                  <thead>
                    <tr>
                      <th>Field / month</th>
                      <th>Value</th>
                      <th>Source citation</th>
                      <th>Analyst</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fields.map(([key, label]) => {
                      const cell = monthRows.find((c) => c.field === key);
                      if (!cell) return null;
                      return (
                        <tr
                          key={key}
                          className={
                            selected?.id === cell.id ? "selected-row" : ""
                          }
                          onClick={() => setSelectedId(cell.id)}
                        >
                          <td>
                            <strong>{label}</strong>
                            <small>{monthLabel(month)}</small>
                          </td>
                          <td className="numeric">{inr(cell.value)}</td>
                          <td>
                            <button
                              className="citation"
                              onClick={() => setSelectedId(cell.id)}
                            >
                              <FileSearch size={12} />
                              p.{cell.citation.page_number},{" "}
                              {cell.citation.line_ref}
                              <ArrowUpRight size={11} />
                            </button>
                            <small>
                              {Math.round(cell.citation.confidence * 100)}%
                              extraction confidence
                            </small>
                          </td>
                          <td>
                            {cell.verified_by ? (
                              <Badge type="green">
                                <CheckCircle2 size={11} />
                                Verified
                              </Badge>
                            ) : (
                              <Badge>Pending</Badge>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="correction-strip">
                <span>
                  Analyst correction rate{" "}
                  <strong>{active.correction_rate_pct}%</strong>
                </span>
                <small>
                  Distinct changed cells ÷ {active.cells.length} extracted cells
                </small>
              </div>
              <div className="panel-body">
                <div className="section-label">
                  VERIFY SELECTED CELL <span>Meena Pillai</span>
                </div>
                <div className="verify-form">
                  <label>
                    Confirmed value (INR)
                    <input
                      aria-label="Confirmed value"
                      type="number"
                      min="0"
                      step="0.01"
                      value={value}
                      onChange={(e) => setValue(e.target.value)}
                      disabled={user.persona !== "meena" || locked}
                    />
                  </label>
                  <label>
                    Verification / correction rationale
                    <textarea
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Describe what you checked against the source…"
                      rows={2}
                      disabled={user.persona !== "meena" || locked}
                    />
                  </label>
                  <button
                    className="primary"
                    disabled={
                      busy ||
                      locked ||
                      user.persona !== "meena" ||
                      !selected ||
                      reason.trim().length < 5 ||
                      value === "" ||
                      !Number.isFinite(Number(value))
                    }
                    onClick={verify}
                  >
                    {busy ? (
                      <Busy />
                    ) : (
                      <>
                        <CheckCircle2 size={15} />
                        Confirm & log verification
                      </>
                    )}
                  </button>
                  {user.persona !== "meena" && (
                    <small className="helper">
                      Switch to Meena Pillai to verify or correct source
                      figures.
                    </small>
                  )}
                </div>
              </div>
            </Panel>
            <Panel
              title="12-month reconciliation"
              subtitle="Absolute bank–GST difference ÷ bank credits × 100"
              icon={Table2}
            >
              <div className="panel-body">
                <div className="heatmap">
                  {active.reconciliation.map((r) => (
                    <button
                      key={r.month}
                      onClick={() => {
                        setMonth(r.month);
                        setSelectedId(null);
                      }}
                      className={`${r.flagged ? "flagged" : ""} ${month === r.month ? "selected" : ""}`}
                    >
                      <small>{monthLabel(r.month)}</small>
                      <strong>
                        {r.gstr3b_variance_pct === null
                          ? "N/A"
                          : `${r.gstr3b_variance_pct.toFixed(1)}%`}
                      </strong>
                      <span>3B variance</span>
                    </button>
                  ))}
                </div>
                <div className="variance-detail">
                  <span>
                    GSTR-1{" "}
                    <strong>
                      {reconciliation?.gstr1_variance_pct?.toFixed(2) ?? "N/A"}%
                    </strong>
                  </span>
                  <span>
                    GSTR-3B{" "}
                    <strong>
                      {reconciliation?.gstr3b_variance_pct?.toFixed(2) ?? "N/A"}
                      %
                    </strong>
                  </span>
                  <span>
                    Threshold <strong>{reconciliation?.threshold_pct}%</strong>
                  </span>
                </div>
                <div className="policy-control">
                  <label>
                    Policy tolerance (%)
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={threshold}
                      onChange={(e) => setThreshold(e.target.value)}
                      disabled={!["arjun", "farhan"].includes(user.persona)}
                    />
                  </label>
                  <button
                    className="secondary"
                    onClick={savePolicy}
                    disabled={
                      busy ||
                      !["arjun", "farhan"].includes(user.persona) ||
                      threshold === ""
                    }
                  >
                    Save policy
                  </button>
                </div>
                <p className="helper">
                  Both GSTR-1 and GSTR-3B are checked. Either can flag a month.
                  Cash-share notes never automatically clear an exception.
                </p>
              </div>
            </Panel>
          </div>
          <div className="panel-stack">
            <Panel
              title="Source-to-cell traceability"
              subtitle="Exact PDF page & indexed source line"
              icon={FileSearch}
              action={
                selected && (
                  <Badge type="purple">
                    p.{selected.citation.page_number} ·{" "}
                    {selected.citation.line_ref}
                  </Badge>
                )
              }
            >
              <div className="panel-body">
                <div className="row spread source-filename">
                  <span>{doc?.name || "Select a source cell"}</span>
                  {doc && (
                    <a
                      target="_blank"
                      rel="noreferrer"
                      href={`/api/v1/cases/${active.id}/documents/${doc.id}/pdf#page=${selected.citation.page_number}`}
                      aria-label="Open original PDF"
                    >
                      <ExternalLink size={15} />
                    </a>
                  )}
                </div>
                <div
                  className="source-page"
                  key={`${selected?.id}-${active.id}`}
                >
                  <div className="pdf-brand">
                    PDF SOURCE{" "}
                    <span>
                      {doc?.is_sample
                        ? "SYNTHETIC SAMPLE DOCUMENT"
                        : "UPLOADED SOURCE DOCUMENT"}
                    </span>
                  </div>
                  <h3>
                    {monthLabel(month)} · Source page{" "}
                    {selected?.citation.page_number}
                  </h3>
                  <div className="pdf-rule" />
                  {doc?.pages?.[selected.citation.page_number - 1]?.map(
                    (line, i) => (
                      <div
                        ref={lineIsCited(i) ? sourceRef : null}
                        key={i}
                        className={`source-line ${lineIsCited(i) ? "highlighted" : ""}`}
                      >
                        <span>L{String(i + 1).padStart(2, "0")}</span>
                        <code>{line}</code>
                        {lineIsCited(i) && <CheckCircle2 size={14} />}
                      </div>
                    ),
                  )}
                  <p className="pdf-footnote">
                    Exact indexed text from this document page. Open the PDF
                    above to inspect the full rendered source.
                  </p>
                </div>
                <div className="source-status">
                  <ShieldIcon />
                  Citation grounded in stored source · Confidence is a model
                  estimate
                </div>
                {doc && (
                  <details className="pdf-details">
                    <summary>View original PDF in workspace</summary>
                    <iframe
                      title="Original source PDF"
                      src={`/api/v1/cases/${active.id}/documents/${doc.id}/pdf#page=${selected.citation.page_number}`}
                      key={`${doc.id}-${selected.citation.page_number}`}
                    />
                  </details>
                )}
              </div>
            </Panel>
            <Panel
              title="Human credit judgement & decision"
              subtitle="Step 5 · Named signature and mandatory rationale"
              icon={PenLine}
              action={
                <Badge type={locked ? "green" : "amber"}>
                  {locked ? "Signed & locked" : "Human decision pending"}
                </Badge>
              }
            >
              <div className="panel-body">
                <Guardrail />
                <div className="section-label">
                  ONE-PAGE EVIDENCE DOSSIER{" "}
                  <button
                    className="ghost small"
                    disabled={busy || !ready}
                    onClick={generateMemo}
                  >
                    Refresh preview
                  </button>
                </div>
                <div className="memo">
                  <pre>{preview || active.dossier}</pre>
                </div>
                <div className="rm-note">
                  <strong>RM cash-share notes · {active.cash_share}%</strong>
                  <p>{active.gap_notes}</p>
                </div>
                {locked ? (
                  <div className="signed-record">
                    <CheckCircle2 size={22} />
                    <div>
                      <strong>
                        {active.decision.outcome.replaceAll("_", " ")} ·{" "}
                        {active.decision.signature}
                      </strong>
                      <p>{active.decision.rationale}</p>
                      <small>
                        {new Date(active.decision.timestamp).toLocaleString(
                          "en-IN",
                        )}
                      </small>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={sign} className="decision-form">
                    <label>
                      Credit manager determination
                      <select
                        value={outcome}
                        onChange={(e) => setOutcome(e.target.value)}
                        disabled={user.persona !== "arjun"}
                      >
                        <option value="approve">
                          Approve — human decision
                        </option>
                        <option value="return_to_rm">Return to RM</option>
                        <option value="decline">Decline</option>
                      </select>
                    </label>
                    <label>
                      Mandatory underwriting rationale
                      <textarea
                        rows={3}
                        value={rationale}
                        onChange={(e) => setRationale(e.target.value)}
                        placeholder="Record your assessment, evidence reviewed, and reasons for accepting or declining exceptions…"
                        minLength={30}
                        required
                        disabled={user.persona !== "arjun"}
                      />
                    </label>
                    <label>
                      Named human signature
                      <input
                        value={signature}
                        onChange={(e) => setSignature(e.target.value)}
                        placeholder="Type Arjun Iyer"
                        required
                        disabled={user.persona !== "arjun"}
                      />
                    </label>
                    <button
                      className="primary full"
                      type="submit"
                      disabled={
                        busy ||
                        user.persona !== "arjun" ||
                        !ready ||
                        signature !== "Arjun Iyer" ||
                        rationale.trim().length < 30
                      }
                    >
                      <PenLine size={16} />
                      Sign & record audit outcome
                    </button>
                    {!ready && (
                      <p className="helper">
                        {60 - active.verified_count} source cells still require
                        Meena's verification.
                      </p>
                    )}
                    {user.persona !== "arjun" && (
                      <p className="helper">
                        Only Arjun Iyer can record the credit outcome. Switch
                        persona in the top bar.
                      </p>
                    )}
                  </form>
                )}
              </div>
            </Panel>
          </div>
        </div>
      )}
      <details className="audit-details">
        <summary>
          Case audit trail · {active.audit.length} recent events
        </summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {active.audit.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.timestamp).toLocaleString("en-IN")}</td>
                  <td>{e.actor}</td>
                  <td>{e.action}</td>
                  <td>
                    <code>{e.payload}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
function ShieldIcon() {
  return <CheckCircle2 size={13} />;
}
