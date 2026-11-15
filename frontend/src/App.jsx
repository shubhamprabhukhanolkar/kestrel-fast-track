import { useEffect, useState } from "react";
import {
  Hexagon,
  Sun,
  Moon,
  LogOut,
  ShieldCheck,
  ChevronDown,
  ArrowUpRight,
  Activity,
} from "lucide-react";
import { api, send, inr } from "./api/client";
import LoginScreen from "./components/LoginScreen";
import IntakePipeline from "./components/IntakePipeline";
import SpreadingWorkspace from "./components/SpreadingWorkspace";
import PromptTonerStudio from "./components/PromptTonerStudio";
import FinOpsDashboard from "./components/FinOpsDashboard";
import { Badge } from "./components/shared";
const tabs = [
  ["intake", "Intake & Extraction"],
  ["verification", "Verification & Sign-Off"],
  ["studio", "Prompt & Toner Studio"],
  ["finops", "FinOps & API Health"],
];
export default function App() {
  const [theme, setTheme] = useState(
      localStorage.getItem("kestrel-theme") || "light",
    ),
    [user, setUser] = useState(null),
    [health, setHealth] = useState(null),
    [tab, setTab] = useState(location.hash.slice(1) || "intake"),
    [cases, setCases] = useState([]),
    [caseId, setCaseId] = useState("KF-2026-0892"),
    [active, setActive] = useState(null),
    [toast, setToast] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("kestrel-theme", theme);
  }, [theme]);
  useEffect(() => {
    api("/health")
      .then(setHealth)
      .catch((e) => setError(e.message));
    api("/auth/me")
      .then(setUser)
      .catch(() => {});
    const handler = () => setTab(location.hash.slice(1) || "intake");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(""), 5500);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  async function refresh() {
    try {
      const [list, detail] = await Promise.all([
        api("/cases"),
        api(`/cases/${caseId}`),
      ]);
      setCases(list);
      setActive(detail);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => {
    if (user) {
      setActive(null);
      refresh();
    }
  }, [user, caseId]);
  function navigate(next) {
    location.hash = next;
    setTab(next);
  }
  function login(person) {
    setUser(person);
    navigate(
      person.persona === "arjun"
        ? "verification"
        : person.persona === "farhan"
          ? "finops"
          : "intake",
    );
    if (person.persona === "arjun") setCaseId("KF-2026-0911");
  }
  async function logout() {
    try {
      await send("/auth/logout", {});
      setUser(null);
      setActive(null);
    } catch (e) {
      setError(e.message);
    }
  }
  const props = { active, user, refresh, notify: setToast, navigate, health };
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <a href="#intake" className="brand">
            <span className="brand-mark">
              <Hexagon size={23} />
              <span />
            </span>
            <strong>
              Kestrel<span> Finance</span>
            </strong>
          </a>
          <Badge type="purple">&lt;₹25L Fast-Track</Badge>
          {user && (
            <nav aria-label="Main navigation">
              {tabs.map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => navigate(key)}
                  className={tab === key ? "active" : ""}
                >
                  {label}
                </button>
              ))}
            </nav>
          )}
          <div className="topbar-actions">
            <button
              className="theme-switch"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            >
              <Sun size={15} className={theme === "light" ? "selected" : ""} />
              <Moon size={15} className={theme === "dark" ? "selected" : ""} />
            </button>
            {user ? (
              <>
                <button
                  className="user-menu"
                  title="Switch operator persona"
                  onClick={logout}
                >
                  <span className="avatar small">{user.initials}</span>
                  <span>
                    <strong>{user.name}</strong>
                    <small>{user.role}</small>
                  </span>
                  <LogOut size={15} />
                </button>
              </>
            ) : (
              <span className="muted text-sm">Enterprise access gateway</span>
            )}
          </div>
        </div>
      </header>
      <div className="microbar">
        <div>
          <ShieldCheck size={12} />
          <span>
            Backend-only AI · {health?.project || "Connecting to backend"} ·{" "}
            {health?.region || "asia-south1"}
          </span>
        </div>
        <div>
          <span className="live-dot" />
          {health?.demo_mode
            ? "Offline sandbox · simulated AI"
            : "Live AI · actual provider telemetry"}
          <span className="micro-divider">|</span>
          <span>NO MODEL APPROVES CREDIT</span>
        </div>
      </div>
      {error && (
        <div className="global-error" role="alert">
          {error}
          <button onClick={() => (user ? refresh() : location.reload())}>
            Retry
          </button>
        </div>
      )}
      {!user ? (
        <LoginScreen onLogin={login} health={health} />
      ) : (
        <main className="workspace">
          <div className="workspace-bar">
            <div className="breadcrumbs">
              Workbench <span>/</span>{" "}
              {tabs.find((t) => t[0] === tab)?.[1] || "Intake & Extraction"}
            </div>
            <span className="small-muted">
              <Activity size={13} /> {health?.model} · Backend proxy
            </span>
          </div>
          <div className="case-context">
            <div className="case-select">
              <label htmlFor="active-case">ACTIVE DOSSIER</label>
              <select
                id="active-case"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
              >
                {cases.length ? (
                  cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} · {c.business}
                    </option>
                  ))
                ) : (
                  <option>Loading cases…</option>
                )}
              </select>
            </div>
            <div>
              <small>REQUESTED FACILITY</small>
              <strong>
                {active ? inr(active.loan_amount) : "…"}{" "}
                <span>· Working capital</span>
              </strong>
            </div>
            <div>
              <small>COHORT</small>
              <strong>&lt;₹25L · Text-based PDF</strong>
            </div>
            <Badge type={active?.intake?.passed ? "green" : "amber"}>
              {active?.status?.replaceAll("_", " ") || "Loading dossier"}
            </Badge>
          </div>
          {active ? (
            tab === "verification" ? (
              <SpreadingWorkspace {...props} />
            ) : tab === "studio" ? (
              <PromptTonerStudio {...props} />
            ) : tab === "finops" ? (
              <FinOpsDashboard {...props} />
            ) : (
              <IntakePipeline {...props} />
            )
          ) : (
            <div className="loading-state">Loading evidence dossier…</div>
          )}
        </main>
      )}
      <footer>
        <span>© 2026 Kestrel Finance · SME First Slice</span>
        <span>
          {health?.demo_mode
            ? "Prototype · Synthetic evidence"
            : "Human-controlled underwriting"}
          <span className="footer-dot">•</span>Jan–Dec 2025 cohort
        </span>
        <span className="row">
          <span className="live-dot" />{" "}
          {health ? "Backend connected" : "Connecting"}
        </span>
      </footer>
      {toast && (
        <div className="toast" role="status">
          <ShieldCheck size={18} />
          {toast}
        </div>
      )}
    </>
  );
}
