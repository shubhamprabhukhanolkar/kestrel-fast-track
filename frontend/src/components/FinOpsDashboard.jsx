import { useEffect, useState } from "react";
import {
  Wallet,
  Coins,
  Clock3,
  Zap,
  RefreshCw,
  Activity,
  Network,
  ShieldCheck,
  ArrowRight,
  Play,
  AlertTriangle,
} from "lucide-react";
import { api, send, inr, number } from "../api/client";
import { Title, Panel, Badge, Busy } from "./shared";
export default function FinOpsDashboard({ active, user, notify, health }) {
  const apiKeyPrimary = health?.primary_provider === "gemini_api";
  const [data, setData] = useState(null),
    [config, setConfig] = useState({
      simulate_503: false,
      simulate_429: false,
    }),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [checks, setChecks] = useState(null),
    [providerResults, setProviderResults] = useState([]);
  async function load() {
    const [summary, flags] = await Promise.all([
      api("/finops/summary"),
      api("/admin/failover-config"),
    ]);
    setData(summary);
    setConfig(flags);
  }
  useEffect(() => {
    let alive = true;
    async function tick() {
      try {
        const [summary, flags] = await Promise.all([
          api("/finops/summary"),
          api("/admin/failover-config"),
        ]);
        if (alive) {
          setData(summary);
          setConfig(flags);
        }
      } catch (e) {
        if (alive) setError(e.message);
      }
    }
    tick();
    const timer = setInterval(tick, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);
  async function toggle(key) {
    setBusy(true);
    setError("");
    try {
      const flags = await send("/admin/failover-config", {
        ...config,
        [key]: !config[key],
      });
      setConfig(flags);
      notify(
        "Failover simulation saved. The next agent action will use this setting.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function probe() {
    setBusy(true);
    setError("");
    try {
      await send("/toner/preview", {
        case_id: active.id,
        tone: "Polite RM Document Chaser",
      });
      await load();
      notify(
        "Backend agent action completed. Review provider attempts in the live log.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function checkLiveProviders() {
    setBusy(true);
    setError("");
    try {
      const result = await send("/admin/provider-check", {});
      setProviderResults(result.providers);
      setChecks(await api("/admin/readiness"));
      await load();
      notify(
        "Provider checks completed. These are actual calls; failed checks remain visible.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const chaos = config.simulate_503 || config.simulate_429;
  const totalTokens = (data?.input_tokens || 0) + (data?.output_tokens || 0);
  return (
    <>
      <Title
        eyebrow="FINOPS · OBSERVABILITY & RESILIENCE"
        title="Every agent action, accounted for."
        description="Follow token usage, estimated spend and actual provider attempts through the backend proxy."
        action={
          <button
            className="secondary"
            onClick={() => load().catch((e) => setError(e.message))}
          >
            <RefreshCw size={15} />
            Sync metrics
          </button>
        }
      />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!data?.demo_mode && user.persona === "farhan" && (
        <Panel
          title="Live environment readiness"
          subtitle="Configuration and actual model connectivity are checked separately"
          icon={ShieldCheck}
          action={
            <button
              className="secondary"
              disabled={busy}
              onClick={checkLiveProviders}
            >
              Check live providers
            </button>
          }
        >
          <div className="panel-body">
            <p className="helper">
              {apiKeyPrimary
                ? "This checks the backend Gemini API key and configured Groq backup with a small diagnostic prompt. Hosting remains in asia-south1; Gemini inference is provider-managed."
                : "This checks regional Vertex and the configured Groq backup with a small diagnostic prompt."}{" "}
              No borrower documents are sent.
            </p>
            <div className="readiness-checks">
              {checks?.checks.map((c) => (
                <div key={c.key}>
                  <Badge type={c.passed ? "green" : "amber"}>
                    {c.passed ? "Ready" : "Required"}
                  </Badge>
                  <span>{c.detail}</span>
                </div>
              ))}
              {providerResults.map((p) => (
                <div key={p.provider}>
                  <Badge type={p.connected ? "green" : "red"}>
                    {p.connected ? "Connected" : "Failed"}
                  </Badge>
                  <span>
                    {p.provider}{" "}
                    {p.connected
                      ? `${p.latency_ms} ms`
                      : `${p.error} · ${p.location || "backup"}`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      )}
      <div className="kpi-grid">
        {[
          {
            label: "Total pilot spend",
            value: inr(data?.total_spend_inr, 2),
            note: `Across ${data?.application_count || 0} applications`,
            icon: Wallet,
            color: "purple",
          },
          {
            label: "Avg cost / application",
            value: inr(data?.avg_cost_per_application_inr, 2),
            note: "Total action cost ÷ unique applications",
            icon: Coins,
            color: "green",
          },
          {
            label: "Average action latency",
            value: `${Math.round(data?.avg_latency_ms || 0)} ms`,
            note: `${data?.attempts || 0} recorded provider attempts`,
            icon: Clock3,
            color: "cyan",
          },
          {
            label: "Groq failover actions",
            value: String(data?.failover_calls || 0).padStart(2, "0"),
            note: "Backup attempts after primary failure",
            icon: Zap,
            color: "amber",
          },
        ].map((k) => (
          <div className="kpi" key={k.label}>
            <div className="row spread">
              <span className="section-label">{k.label}</span>
              <span className={`metric-icon ${k.color}`}>
                <k.icon size={18} />
              </span>
            </div>
            <strong>{k.value}</strong>
            <p>{k.note}</p>
            <div className="kpi-footer">
              <span className={`tiny-dot ${k.color}`} />
              {data?.demo_mode
                ? "Demo / synthetic metrics included"
                : "Estimated provider cost"}
            </div>
          </div>
        ))}
      </div>
      <div className="two-panels finops-panels">
        <Panel
          title="Agent action cost & tokens"
          subtitle="Estimated micro-billing across the underwriting pipeline"
          icon={Wallet}
          action={<Badge type="purple">{number(totalTokens)} tokens</Badge>}
        >
          <div className="panel-body">
            <div className="section-label">
              TOKEN DISTRIBUTION <span>Input + output</span>
            </div>
            <div className="token-bar">
              {data?.agents.map((a, i) => (
                <span
                  key={a.agent_name}
                  title={`${a.agent_name}: ${a.input_tokens + a.output_tokens} tokens`}
                  style={{
                    width: `${((a.input_tokens + a.output_tokens) / Math.max(1, totalTokens)) * 100}%`,
                    background: ["#4F46E5", "#A78BFA", "#10B981", "#06B6D4"][i],
                  }}
                />
              ))}
            </div>
            <div className="token-legend">
              {data?.agents.map((a, i) => (
                <span key={a.agent_name}>
                  <i
                    style={{
                      background: ["#4F46E5", "#A78BFA", "#10B981", "#06B6D4"][
                        i
                      ],
                    }}
                  />
                  {a.agent_name}{" "}
                  {Math.round(
                    ((a.input_tokens + a.output_tokens) /
                      Math.max(1, totalTokens)) *
                      100,
                  )}
                  %
                </span>
              ))}
            </div>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Tokens in / out</th>
                  <th>Avg latency</th>
                  <th>Total cost</th>
                </tr>
              </thead>
              <tbody>
                {data?.agents.map((a) => (
                  <tr key={a.agent_name}>
                    <td>
                      <strong>{a.agent_name}</strong>
                      <small>{a.calls} provider attempts</small>
                    </td>
                    <td className="numeric">
                      {number(a.input_tokens)}
                      <small>{number(a.output_tokens)} output</small>
                    </td>
                    <td>{Math.round(a.avg_latency_ms)} ms</td>
                    <td className="numeric">{inr(a.cost_inr, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="panel-body">
            <div className="section-label">PROVIDER SPLIT</div>
            {data?.providers.map((p) => (
              <div className="provider-split" key={p.provider}>
                <span>
                  <i
                    className={`tiny-dot ${p.provider !== "groq_backup" ? "purple" : "green"}`}
                  />
                  {p.provider === "gemini_api"
                    ? "Gemini API"
                    : p.provider === "vertex_gemini"
                      ? "Vertex Gemini"
                      : "Groq backup"}
                </span>
                <div>
                  <span
                    style={{
                      width: `${(p.calls / Math.max(1, data.attempts)) * 100}%`,
                    }}
                  />
                </div>
                <strong>{p.calls} calls</strong>
              </div>
            ))}
            <div className="cost-disclosure">
              <AlertTriangle size={16} />
              <p>{data?.cost_basis}</p>
            </div>
            <div className="mode-breakdown">
              {data?.modes.map((m) => (
                <span key={m.mode}>
                  {m.mode.replaceAll("_", " ")}{" "}
                  <strong>{inr(m.cost_inr, 2)}</strong>
                </span>
              ))}
            </div>
          </div>
        </Panel>
        <Panel
          title="API redundancy controller"
          subtitle={`${apiKeyPrimary ? "Gemini Developer API" : "Vertex AI"} → automatic Groq backup`}
          icon={Network}
          action={
            <Badge type={chaos ? "amber" : "green"}>
              {chaos ? "Chaos simulation active" : "Normal routing"}
            </Badge>
          }
        >
          <div className="panel-body">
            <div className="provider-card">
              <div className="provider-logo">G</div>
              <div>
                <div className="row spread">
                  <strong>
                    {apiKeyPrimary
                      ? "Gemini Developer API"
                      : "Google Vertex AI"}
                  </strong>
                  <Badge type={chaos ? "amber" : "green"}>
                    {chaos ? "Simulated failure" : "Primary"}
                  </Badge>
                </div>
                <code>{health?.model || "Loading model…"}</code>
                <small>
                  {apiKeyPrimary
                    ? "Backend API key · no frontend credentials"
                    : "Backend SDK · regional identity"}
                </small>
              </div>
            </div>
            <div className="failover-path">
              <span />
              <ArrowRight size={15} />
              <small>429 · 500 / 503 · timeout</small>
              <span />
            </div>
            <div className="provider-card backup">
              <div className="provider-logo">g</div>
              <div>
                <div className="row spread">
                  <strong>Groq backup</strong>
                  <Badge type={chaos ? "green" : ""}>
                    {chaos ? "Next action routed here" : "Standby"}
                  </Badge>
                </div>
                <code>llama-3.3-70b-versatile</code>
                <small>Backend secret only · no frontend API keys</small>
              </div>
            </div>
            <div className="chaos-controller">
              <div className="section-label">
                INTERACTIVE CHAOS SWITCHES{" "}
                <Badge type="amber">Admin only</Badge>
              </div>
              <p>
                Apply a failure to the primary provider, then run a real backend
                agent action to inspect the routing.
              </p>
              {[
                [
                  "simulate_503",
                  "Simulate Gemini service outage",
                  "503 · Service unavailable",
                ],
                [
                  "simulate_429",
                  "Simulate token quota exhaustion",
                  "429 · Resource exhausted",
                ],
              ].map(([key, label, detail]) => (
                <div className="toggle-row" key={key}>
                  <div>
                    <strong>{label}</strong>
                    <small>{detail}</small>
                  </div>
                  <button
                    role="switch"
                    aria-checked={config[key]}
                    aria-label={label}
                    className={`toggle ${config[key] ? "on" : ""}`}
                    disabled={busy || user.persona !== "farhan"}
                    onClick={() => toggle(key)}
                  >
                    <span />
                  </button>
                </div>
              ))}
              <button className="primary full" onClick={probe} disabled={busy}>
                {busy ? (
                  <Busy text="Running backend agent…" />
                ) : (
                  <>
                    <Play size={15} />
                    Run failover test action
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
              {user.persona !== "farhan" && (
                <p className="helper">
                  Switch to Farhan Qureshi to change outage settings.
                </p>
              )}
            </div>
            <div className="notice success">
              <ShieldCheck size={18} />
              <p>
                {data?.demo_mode
                  ? "Demo mode simulates provider responses and records each routing attempt. No live network call or live billing occurs."
                  : "Live mode calls the configured providers. Primary errors and backup attempts are recorded separately."}
              </p>
            </div>
          </div>
        </Panel>
      </div>
      <Panel
        title="Live provider attempt log"
        subtitle="Auto-refresh every 3 seconds · most recent 100 attempts"
        icon={Activity}
        action={
          <Badge type="green">
            <span className="live-dot" />
            Backend telemetry
          </Badge>
        }
        className="telemetry-panel"
      >
        <div className="table-scroll">
          <table className="telemetry-table">
            <thead>
              <tr>
                <th>Time / case</th>
                <th>Agent</th>
                <th>Provider / model</th>
                <th>Tokens in / out</th>
                <th>Latency</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.logs.map((log) => (
                <tr key={log.id}>
                  <td>
                    {new Date(log.timestamp).toLocaleTimeString("en-IN")}
                    <small>{log.case_id}</small>
                  </td>
                  <td>
                    <strong>{log.agent_name}</strong>
                    <small>{log.mode}</small>
                  </td>
                  <td>
                    {log.provider}
                    <small>{log.model_name}</small>
                  </td>
                  <td className="numeric">
                    {number(log.input_tokens)} / {number(log.output_tokens)}
                  </td>
                  <td>{Math.round(log.latency_ms)} ms</td>
                  <td className="numeric">{inr(log.cost_inr, 4)}</td>
                  <td>
                    <Badge type={log.status === "success" ? "green" : "amber"}>
                      {log.status}
                    </Badge>
                    {!!log.failover_triggered && (
                      <small className="failover-label">
                        <Zap size={11} />
                        Failover triggered
                      </small>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
