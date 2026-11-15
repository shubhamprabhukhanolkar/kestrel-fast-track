import { useEffect, useState } from "react";
import {
  SlidersHorizontal,
  Sparkles,
  Save,
  RotateCcw,
  History,
  ArrowRight,
  ShieldCheck,
  Copy,
} from "lucide-react";
import { api, send } from "../api/client";
import { Title, Panel, Badge, Busy, Guardrail } from "./shared";
const labels = {
  extractor_prompt: "Cited extractor",
  critique_prompt: "Critique & grounding",
  toner_prompt: "Toner & communication",
};
const tones = [
  "Strict CRO Regulatory Memo",
  "Concise Analyst Dossier",
  "Polite RM Document Chaser",
];
export default function PromptTonerStudio({ active, user, notify, health }) {
  const [data, setData] = useState(null),
    [agent, setAgent] = useState("toner_prompt"),
    [content, setContent] = useState(""),
    [tone, setTone] = useState(tones[1]),
    [preview, setPreview] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [previewVersion, setPreviewVersion] = useState(null);
  const canEdit = ["meena", "farhan"].includes(user.persona);
  async function load() {
    const result = await api("/prompts");
    setData(result);
    return result;
  }
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (data) setContent(data.active[agent].content);
  }, [agent, data]);
  useEffect(() => {
    setPreview("");
    setPreviewVersion(null);
  }, [active.id, tone]);
  async function save() {
    setBusy(true);
    setError("");
    try {
      const result = await send(`/prompts/${agent}`, { content }, "PUT");
      await load();
      notify(
        `Prompt v${result.version} saved. New runs and previews will use it.`,
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function reset() {
    setBusy(true);
    setError("");
    try {
      await send("/prompts/reset", {});
      await load();
      notify(
        "Defaults restored as new versions. Prior versions remain in history.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function generate() {
    setBusy(true);
    setError("");
    try {
      const result = await send("/toner/preview", { case_id: active.id, tone });
      setPreview(result.text);
      setPreviewVersion(result.prompt_version);
      notify("Toner preview generated and the agent action metered.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Title
        eyebrow="TWO-WAY DOORS · PROMPT GOVERNANCE"
        title="Calibrate the agents. Keep the guardrails."
        description="Version every prompt change. Preview the tone. Preserve the evidence and human authority."
        action={<Badge type="purple">Prompts stored in SQLite</Badge>}
      />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="two-panels studio-panels">
        <Panel
          title="Agent prompt editor"
          subtitle="Editable system instructions with version history"
          icon={SlidersHorizontal}
          action={
            <Badge type="purple">
              v{data?.active[agent]?.version || 1} active
            </Badge>
          }
        >
          <div className="panel-body">
            <div className="segmented">
              {Object.entries(labels).map(([key, label]) => (
                <button
                  key={key}
                  className={agent === key ? "active" : ""}
                  onClick={() => setAgent(key)}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="row spread editor-label">
              <span className="section-label">
                SYSTEM PROMPT <span className="mono">{agent}</span>
              </span>
              <span className="small-muted">{content.length} characters</span>
            </div>
            <div className="code-editor">
              <div className="editor-gutter">
                01
                <br />
                02
                <br />
                03
                <br />
                04
                <br />
                05
                <br />
                06
                <br />
                07
                <br />
                08
                <br />
                09
                <br />
                10
                <br />
                11
                <br />
                12
              </div>
              <textarea
                aria-label={`${labels[agent]} system prompt`}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                spellCheck="false"
                disabled={!canEdit}
              />
            </div>
            <div className="editor-status">
              <span className="live-dot" />
              {content === data?.active[agent]?.content
                ? "Saved version active"
                : "Unsaved edits — save before previewing"}
              <span>{data?.active[agent]?.actor}</span>
            </div>
            <div className="notice">
              <ShieldCheck size={18} />
              <p>
                Prompts can change. Deterministic citation checks, intake rules
                and named human sign-off remain enforced in backend code.
              </p>
            </div>
            <div className="actions">
              <button
                className="secondary"
                onClick={reset}
                disabled={!canEdit || busy}
              >
                <RotateCcw size={15} />
                Restore defaults
              </button>
              <button
                className="primary"
                onClick={save}
                disabled={
                  !canEdit ||
                  busy ||
                  content.trim().length < 20 ||
                  content === data?.active[agent]?.content
                }
              >
                <Save size={15} />
                Save new version
              </button>
            </div>
            {!canEdit && (
              <p className="helper">
                Meena and Farhan can edit system prompts. All operators can
                preview saved versions.
              </p>
            )}
            <details className="version-history">
              <summary>
                <History size={14} />
                Prompt version history ·{" "}
                {data?.history.filter((p) => p.agent_key === agent).length ||
                  0}{" "}
                versions
              </summary>
              {data?.history
                .filter((p) => p.agent_key === agent)
                .map((p) => (
                  <div className="version-item" key={p.id}>
                    <span className="row spread">
                      <strong>
                        Version {p.version} · {p.actor}
                      </strong>
                      <small>
                        {new Date(p.timestamp).toLocaleString("en-IN")}
                      </small>
                    </span>
                    <p>{p.content}</p>
                    <button
                      className="ghost small"
                      disabled={!canEdit}
                      onClick={() => setContent(p.content)}
                    >
                      Load into editor
                    </button>
                  </div>
                ))}
            </details>
          </div>
        </Panel>
        <Panel
          title="Toner recalibration studio"
          subtitle="Same grounded evidence. A tone for every audience."
          icon={Sparkles}
          action={<Badge type="green">Live backend preview</Badge>}
        >
          <div className="panel-body">
            <div className="section-label">COMMUNICATION PRESET</div>
            <div className="tone-options">
              {tones.map((t, i) => (
                <button
                  key={t}
                  className={tone === t ? "selected" : ""}
                  onClick={() => setTone(t)}
                >
                  <span className="tone-index">0{i + 1}</span>
                  <span>
                    <strong>{t}</strong>
                    <small>
                      {
                        [
                          "Risk exceptions, policy context and explicit uncertainty",
                          "Evidence, monthly variances and analyst next steps",
                          "A courteous request for missing documents and clarification",
                        ][i]
                      }
                    </small>
                  </span>
                  <span className="radio-dot" />
                </button>
              ))}
            </div>
            <button
              className="primary full"
              onClick={generate}
              disabled={
                busy || !data || content !== data?.active[agent]?.content
              }
            >
              {busy ? (
                <Busy text="Formatting evidence…" />
              ) : (
                <>
                  <Sparkles size={16} />
                  Generate tone preview
                  <ArrowRight size={16} />
                </>
              )}
            </button>
            <div className="preview-head">
              <span className="section-label">EVIDENCE DOSSIER PREVIEW</span>
              {previewVersion && <Badge>Prompt v{previewVersion}</Badge>}
            </div>
            <div className="dossier-paper">
              <div className="dossier-letterhead">
                <span>K E S T R E L</span>
                <small>FINANCE · EVIDENCE DOSSIER</small>
              </div>
              <div className="dossier-meta">
                {active.id} <span>{active.business}</span>
              </div>
              <pre>{preview || active.dossier}</pre>
              <div className="paper-footer">
                {preview
                  ? "Generated preview · human review required"
                  : "Seeded draft · generate a preview from saved prompts"}
              </div>
            </div>
            <p className="helper">
              {health?.demo_mode
                ? "Offline sandbox: deterministic tone templates. Switch to live execution to evaluate custom prompt semantics."
                : "Preview calls the live model using the saved system prompt and current case evidence. Each attempt is metered."}
            </p>
            <Guardrail />
          </div>
        </Panel>
      </div>
    </>
  );
}
