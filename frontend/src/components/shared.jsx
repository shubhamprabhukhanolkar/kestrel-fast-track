import {
  Check,
  AlertTriangle,
  ChevronRight,
  ShieldCheck,
  Loader2,
} from "lucide-react";
export function Badge({ children, type = "" }) {
  return <span className={`badge ${type}`}>{children}</span>;
}
export function Panel({
  title,
  subtitle,
  icon: Icon,
  action,
  children,
  className = "",
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div className="row">
          <span className="icon-box">{Icon && <Icon size={18} />}</span>
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Title({ eyebrow, title, description, action }) {
  return (
    <div className="page-title">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function Guardrail() {
  return (
    <div className="guardrail">
      <ShieldCheck size={22} />
      <div>
        <strong>NO MODEL APPROVES CREDIT</strong>
        <p>
          A named human credit manager must assess the evidence, sign and record
          a rationale.
        </p>
      </div>
    </div>
  );
}
export function Steps({ active = 1 }) {
  return (
    <div className="steps">
      {[
        "Intake check",
        "Cited extraction",
        "Reconciliation",
        "Analyst verification",
        "Human decision",
      ].map((s, i) => (
        <div className={active > i ? "done" : ""} key={s}>
          <span>{active > i + 1 ? <Check size={13} /> : i + 1}</span>
          <small>{s}</small>
          {i < 4 && <ChevronRight size={14} />}
        </div>
      ))}
    </div>
  );
}
export function Busy({ text = "Working…" }) {
  return (
    <span className="row">
      <Loader2 size={15} className="spin" />
      {text}
    </span>
  );
}
export function Empty({ children }) {
  return (
    <div className="notice">
      <AlertTriangle size={18} />
      {children}
    </div>
  );
}
