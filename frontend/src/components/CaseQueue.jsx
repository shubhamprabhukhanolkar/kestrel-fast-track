import { useState } from "react";
import { inr } from "../api/client";
import { Panel, Badge } from "./shared";

export default function CaseQueue({ cases, activeId, onOpen }) {
  const [filter, setFilter] = useState("all");
  const pending = cases.filter((c) => c.is_pending);
  const eligible = pending.filter((c) => c.loan_amount < 2500000);
  const standard = pending.filter((c) => c.loan_amount >= 2500000);
  const visible =
    filter === "below" ? eligible : filter === "standard" ? standard : pending;
  return (
    <Panel
      title="Pending case queue"
      subtitle="Sample borrowers for walking through intake, eligibility and credit review"
    >
      <div className="panel-body">
        <div
          className="feature-tabs"
          role="group"
          aria-label="Case queue filters"
        >
          {[
            ["all", `All pending (${pending.length})`],
            ["below", `Below ₹25 lakh (${eligible.length})`],
            ["standard", `₹25 lakh & above (${standard.length})`],
          ].map(([key, label]) => (
            <button
              key={key}
              className={filter === key ? "primary" : "secondary"}
              aria-pressed={filter === key}
              onClick={() => setFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="helper">
          Fast-track applies strictly below ₹25 lakh. Larger requests stay in
          the queue for standard credit review. Select a case to demonstrate its
          workflow; extraction runs one case at a time.
        </p>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Case / borrower</th>
              <th>Requested facility</th>
              <th>Route</th>
              <th>Pending stage</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => (
              <tr key={c.id}>
                <td>
                  <strong>{c.business}</strong>
                  <small>
                    {c.id} · {c.city} · Sample case
                  </small>
                </td>
                <td className="numeric">{inr(c.loan_amount)}</td>
                <td>
                  <Badge type={c.loan_amount < 2500000 ? "green" : "amber"}>
                    {c.loan_amount < 2500000 ? "Fast-track" : "Standard review"}
                  </Badge>
                </td>
                <td>{c.status.replaceAll("_", " ")}</td>
                <td>
                  <button
                    className="secondary"
                    onClick={() => onOpen(c.id)}
                    aria-label={`Open ${c.business}`}
                  >
                    {c.id === activeId ? "View current case" : "Open case"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!visible.length && (
          <p className="panel-body">No pending cases in this category.</p>
        )}
      </div>
    </Panel>
  );
}
