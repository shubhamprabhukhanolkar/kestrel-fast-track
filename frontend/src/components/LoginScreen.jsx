import { useState } from "react";
import {
  ArrowRight,
  ShieldCheck,
  BriefcaseBusiness,
  ScanLine,
  PenLine,
  Activity,
  Hexagon,
  LockKeyhole,
} from "lucide-react";
import { send } from "../api/client";
import { Busy, Badge } from "./shared";
export const personas = [
  {
    key: "vikram",
    name: "Vikram Rao",
    role: "Relationship Manager",
    initials: "VR",
    icon: BriefcaseBusiness,
    description: "Bring complete borrower files into the fast-track lane.",
    access: "Intake, PDF uploads & RM chasers",
  },
  {
    key: "meena",
    name: "Meena Pillai",
    role: "Senior Credit Analyst",
    initials: "MP",
    icon: ScanLine,
    description: "Turn cited evidence into a verified spreading sheet.",
    access: "Extraction, reconciliation & verification",
  },
  {
    key: "arjun",
    name: "Arjun Iyer",
    role: "Credit Manager / CRO",
    initials: "AI",
    icon: PenLine,
    description: "Apply human judgement. Own the final credit decision.",
    access: "Evidence review & mandatory credit sign-off",
  },
  {
    key: "farhan",
    name: "Farhan Qureshi",
    role: "CIO / FinOps Admin",
    initials: "FQ",
    icon: Activity,
    description: "Keep the agent pipeline observable, resilient and efficient.",
    access: "Prompt governance, costs & provider failover",
  },
];
export default function LoginScreen({ onLogin, health }) {
  const [selected, setSelected] = useState("meena"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [password, setPassword] = useState("");
  const person = personas.find((p) => p.key === selected);
  async function enter() {
    setBusy(true);
    setError("");
    try {
      onLogin(await send("/auth/login", { persona: selected, password }));
      setPassword("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <section className="login-story">
        <div className="eyebrow">
          <span className="live-dot" /> SME FAST-TRACK WORKBENCH
        </div>
        <h1>
          More evidence.
          <br />
          Less waiting.
          <br />
          <em>Human judgement.</em>
        </h1>
        <p className="intro">
          A clearer path from borrower documents to a credit decision. Built for
          the simple cases that deserve a faster answer.
        </p>
        <div className="story-metrics">
          <div>
            <strong>&lt;₹25L</strong>
            <span>Focused first slice</span>
          </div>
          <div>
            <strong>12 months</strong>
            <span>Source-linked evidence</span>
          </div>
          <div>
            <strong>5 steps</strong>
            <span>One accountable workflow</span>
          </div>
        </div>
        <div className="story-flow">
          <span>
            <BriefcaseBusiness size={20} />
            Complete intake
          </span>
          <ArrowRight size={16} />
          <span>
            <ScanLine size={20} />
            Cited evidence
          </span>
          <ArrowRight size={16} />
          <span>
            <PenLine size={20} />
            Human decision
          </span>
        </div>
        <div className="login-note">
          <ShieldCheck size={20} />
          <span>
            No model approves credit. Every decision belongs to a named person.
          </span>
        </div>
      </section>
      <section className="login-card">
        <div className="row spread">
          <div className="icon-box large">
            <LockKeyhole size={23} />
          </div>
          <Badge type="purple">
            {health?.demo_mode ? "OFFLINE SANDBOX" : "LIVE WORKBENCH"}
          </Badge>
        </div>
        <h2>Select your operator persona</h2>
        <p>
          {health?.auth_mode === "password"
            ? "Select your operator account and sign in with its password."
            : "Enter the workbench with a role-specific set of actions."}
        </p>
        <div className="persona-list">
          {personas.map((p) => (
            <button
              key={p.key}
              className={`persona ${p.key === selected ? "selected" : ""}`}
              onClick={() => setSelected(p.key)}
            >
              <span className="avatar">{p.initials}</span>
              <span>
                <strong>{p.name}</strong>
                <small>{p.role}</small>
              </span>
              <p.icon size={19} />
              <span className="radio-dot" />
            </button>
          ))}
        </div>
        <div className="persona-context">
          <strong>{person.description}</strong>
          <span>{person.access}</span>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {health?.auth_mode === "password" && (
          <label className="login-password">
            Operator password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && password) enter();
              }}
              placeholder="Enter your operator password"
            />
          </label>
        )}
        {health?.auth_mode === "iap" && (
          <p className="helper">
            Sign in through your organization's Google IAP gateway. Your role is
            assigned from the verified identity.
          </p>
        )}
        <button
          className="primary full"
          disabled={
            busy ||
            !health ||
            health.auth_mode === "iap" ||
            (health.auth_mode === "password" && !password)
          }
          onClick={enter}
        >
          {busy ? (
            <Busy />
          ) : (
            <>
              Enter as {person.name}
              <ArrowRight size={17} />
            </>
          )}
        </button>
        <p className="login-disclosure">
          {health?.demo_mode
            ? "Offline sandbox: synthetic AI responses. Not a live provider demonstration."
            : "Live AI execution. Sample borrower documents are labelled; AI spend and latency come from actual provider attempts. Operator authentication is required."}
        </p>
      </section>
    </main>
  );
}
