import { useEffect, useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  ArrowRight,
  Play,
  Upload,
  ShieldCheck,
  Workflow,
  ScanLine,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { api, send } from "../api/client";
import { Title, Panel, Badge, Steps, Busy } from "./shared";
export default function IntakePipeline({
  active,
  user,
  refresh,
  notify,
  navigate,
}) {
  const [run, setRun] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [chaser, setChaser] = useState(""),
    [kind, setKind] = useState("bank");
  const canRun = ["vikram", "meena"].includes(user.persona);
  useEffect(() => {
    let stopped = false,
      lastStatus = null;
    async function poll() {
      try {
        const result = await api(`/cases/${active.id}/runs/latest`);
        if (!stopped) {
          setRun(result);
          if (
            result?.status === "completed" &&
            ["running", "queued"].includes(lastStatus)
          )
            refresh();
          lastStatus = result?.status;
        }
      } catch (e) {
        if (!stopped) setError(e.message);
      }
    }
    setRun(null);
    setError("");
    setChaser("");
    poll();
    const timer = setInterval(poll, 1500);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [active.id]);
  async function start() {
    setBusy(true);
    setError("");
    try {
      await send(`/cases/${active.id}/pipeline`, {});
      setRun({ status: "running", events: [] });
      notify("Extraction started. Live node events appear below.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function check() {
    setBusy(true);
    setError("");
    try {
      const result = await send(`/cases/${active.id}/intake-check`, {});
      await refresh();
      notify(
        result.passed
          ? "Intake passed. All deterministic checks cleared."
          : "Intake blocked. Review the missing evidence below.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function generateChaser() {
    setBusy(true);
    setError("");
    try {
      setChaser(
        (
          await send("/toner/preview", {
            case_id: active.id,
            tone: "Polite RM Document Chaser",
          })
        ).text,
      );
      notify("RM chaser generated; nothing has been sent.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("kind", kind);
      form.append("file", file);
      const result = await api(`/cases/${active.id}/documents`, {
        method: "POST",
        body: form,
      });
      await refresh();
      notify(
        result.native_text
          ? "PDF stored. Review updated coverage checks."
          : "PDF stored but scanned pages failed the text-only intake gate.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }
  const running = ["running", "queued"].includes(run?.status);
  const nodes = [
    {
      key: "Orchestrator",
      label: "Deterministic orchestrator",
      detail: "Check intake · pin prompt versions · select fixed route",
      type: "RULE",
    },
    {
      key: "Extractor",
      label: "Cited extractor agent",
      detail: "Read bank & GST sources · extract 60 source-linked cells",
      type: "GEN AI",
    },
    {
      key: "Critique",
      label: "Critique & grounding agent",
      detail: "Check exact citations · reconcile figures · retry once",
      type: "QA GUARDRAIL",
    },
    {
      key: "Toner",
      label: "Evidence dossier agent",
      detail: "Format grounded findings · preserve exceptions",
      type: "GEN AI",
    },
  ];
  return (
    <>
      <Title
        eyebrow="STEPS 01–02 · INTAKE & EXTRACTION"
        title="Good decisions start with complete evidence."
        description="Check the file once. Extract with citations. Keep the analyst in control."
        action={
          <Badge type={active.intake.passed ? "green" : "amber"}>
            {active.intake.passed ? (
              <CheckCircle2 size={13} />
            ) : (
              <AlertTriangle size={13} />
            )}{" "}
            {active.intake.passed
              ? "Ready for fast-track"
              : "Action needed from RM"}
          </Badge>
        }
      />
      <Steps
        active={run?.status === "completed" ? 3 : active.intake.passed ? 2 : 1}
      />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="two-panels">
        <Panel
          title="Intake & completeness"
          subtitle="Step 1 · Deterministic rules · A1 / A2"
          icon={ShieldCheck}
          action={
            <Badge type="purple">
              {active.intake.checks.filter((c) => c.passed).length}/
              {active.intake.checks.length} passed
            </Badge>
          }
        >
          <div className="panel-body">
            <div className="section-label">
              SUBMISSION CHECKLIST <span>JAN–DEC 2025</span>
            </div>
            <div className="checklist">
              {active.intake.checks.map((c) => (
                <div
                  className={`check-item ${c.passed ? "" : "failed"}`}
                  key={c.label}
                >
                  {c.passed ? (
                    <CheckCircle2 size={19} />
                  ) : (
                    <AlertTriangle size={19} />
                  )}
                  <div>
                    <strong>{c.label}</strong>
                    <p>{c.detail}</p>
                  </div>
                  <Badge type={c.passed ? "green" : "amber"}>
                    {c.passed ? "Pass" : "Gap"}
                  </Badge>
                </div>
              ))}
            </div>
            <div className="section-label">
              BORROWER DOCUMENTS{" "}
              <span>{active.documents.length} files in workspace</span>
            </div>
            <div className="document-list">
              {active.documents.map((d) => (
                <a
                  target="_blank"
                  rel="noreferrer"
                  href={`/api/v1/cases/${active.id}/documents/${d.id}/pdf`}
                  className="document-item"
                  key={d.id}
                >
                  <span className="file-icon">
                    <FileText size={19} />
                    <small>PDF</small>
                  </span>
                  <span>
                    <strong>{d.name}</strong>
                    <small>
                      {d.months.length}/12 months ·{" "}
                      {d.native_text ? "Native text layer" : "Image-only scan"}
                    </small>
                  </span>
                  <Badge
                    type={
                      d.native_text && d.months.length === 12
                        ? "green"
                        : "amber"
                    }
                  >
                    {d.native_text ? "Text PDF" : "Scan"}
                  </Badge>
                  <ArrowRight size={15} />
                </a>
              ))}
            </div>
            {user.persona === "vikram" && !active.decision && (
              <div className="upload-row">
                <select
                  aria-label="Document type"
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                >
                  <option value="bank">Bank statement</option>
                  <option value="gstr1">GSTR-1 returns</option>
                  <option value="gstr3b">GSTR-3B returns</option>
                </select>
                <label className={`button secondary ${busy ? "disabled" : ""}`}>
                  <Upload size={15} />
                  Replace PDF
                  <input
                    type="file"
                    accept="application/pdf"
                    disabled={busy || running}
                    onChange={upload}
                    hidden
                  />
                </label>
                <small>Max 15 MB · YYYY-MM periods</small>
              </div>
            )}
            <div className={`notice ${active.intake.passed ? "success" : ""}`}>
              <ShieldCheck size={18} />
              <p>
                {active.intake.passed
                  ? "All required evidence is present. The file can enter cited extraction."
                  : "The pipeline is blocked until native PDFs and all monthly returns are supplied."}
              </p>
            </div>
            <div className="actions">
              <button
                className="secondary"
                onClick={check}
                disabled={busy || !canRun}
              >
                <RefreshCw size={15} />
                Re-check intake
              </button>
              <button
                className="ghost"
                onClick={generateChaser}
                disabled={busy}
              >
                Draft RM chaser
                <ArrowRight size={15} />
              </button>
            </div>
            {chaser && (
              <div className="memo preview">
                <div className="section-label">
                  RM DOCUMENT CHASER · DRAFT ONLY
                </div>
                <pre>{chaser}</pre>
              </div>
            )}
          </div>
        </Panel>
        <Panel
          title="Cited extraction pipeline"
          subtitle="Step 2 · Fixed LangGraph route with critique loop"
          icon={Workflow}
          action={
            <Badge
              type={
                running ? "purple" : run?.status === "failed" ? "red" : "green"
              }
            >
              {running
                ? "Running"
                : run?.status === "completed"
                  ? "Completed"
                  : "Backend ready"}
            </Badge>
          }
        >
          <div className="panel-body">
            <div className="pipeline-callout">
              <span className="icon-box large">
                <ScanLine size={24} />
              </span>
              <div>
                <strong>Every figure has an evidence trail.</strong>
                <p>12 months × 5 fields, grounded in bank and GST PDFs.</p>
              </div>
            </div>
            <div className="agent-nodes">
              {nodes.map((node, i) => {
                const seen =
                  run?.events?.filter((e) => e.node === node.key) || [];
                return (
                  <div
                    className={`agent-node ${seen.length ? "visited" : ""}`}
                    key={node.key}
                  >
                    <span className="node-index">
                      {seen.length ? (
                        <CheckCircle2 size={18} />
                      ) : (
                        String(i + 1).padStart(2, "0")
                      )}
                    </span>
                    <div>
                      <div className="row spread">
                        <strong>{node.label}</strong>
                        <span className="node-type">{node.type}</span>
                      </div>
                      <p>{node.detail}</p>
                      {seen.length > 0 && (
                        <small className="node-event">
                          {seen.at(-1).message}
                        </small>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="retry-note">
              <RefreshCw size={15} />
              <span>
                Ungrounded citation? Critique sends it back once. A second
                failure blocks the dossier.
              </span>
            </div>
            <div className="pipeline-footer">
              <div className="row spread">
                <span className="small-muted">Execution log</span>
                <span className="small-muted">
                  {run?.events?.length || 0} events
                </span>
              </div>
              <div className="execution-log">
                {run?.events?.length ? (
                  run.events.map((e, i) => (
                    <div key={i}>
                      <time>
                        {new Date(e.timestamp).toLocaleTimeString("en-IN", {
                          hour12: false,
                        })}
                      </time>
                      <span>
                        <b>{e.node}</b> · {e.message}
                      </span>
                    </div>
                  ))
                ) : (
                  <p>
                    Ready. Start extraction to see actual backend node events.
                  </p>
                )}
              </div>
              {run?.error && <p className="error">{run.error}</p>}
              <button
                className="primary full"
                onClick={start}
                disabled={
                  busy ||
                  running ||
                  !active.intake.passed ||
                  !canRun ||
                  !!active.decision
                }
              >
                {running ? (
                  <Busy text="Agent pipeline running…" />
                ) : (
                  <>
                    <Play size={16} />
                    Run cited extraction
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
              {!canRun && (
                <p className="helper">
                  Vikram or Meena can run intake and extraction. Switch persona
                  in the top bar.
                </p>
              )}
              {run?.status === "completed" && (
                <button
                  className="ghost full"
                  onClick={() => {
                    refresh();
                    navigate("verification");
                  }}
                >
                  Open verification workspace
                  <ChevronRight size={16} />
                </button>
              )}
            </div>
          </div>
        </Panel>
      </div>
      <div className="bottom-note">
        <ShieldCheck size={14} />
        B1 cited extraction · A1 deterministic completeness · B2 backend
        document reading{" "}
        <span>Human verification is mandatory before credit sign-off.</span>
      </div>
    </>
  );
}
