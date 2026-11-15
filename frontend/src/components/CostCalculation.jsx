import { useEffect, useState } from "react";
import { api, inr, number } from "../api/client";
import { Panel, Badge } from "./shared";

export default function CostCalculation() {
  const [pricing, setPricing] = useState(null);
  const [error, setError] = useState("");
  const [input, setInput] = useState(10000);
  const [output, setOutput] = useState(1000);
  useEffect(() => {
    api("/finops/pricing")
      .then(setPricing)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <Panel
      title="How model costs are calculated"
      subtitle="Compare the configured Gemini and Groq estimates for the same token usage"
    >
      <div className="panel-body">
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <div className="cost-formula">
          Cost (₹) = (input tokens × input rate + output tokens × output rate) ÷
          1,000,000
        </div>
        <p className="helper">
          Rates below come directly from this backend's configuration. Each
          model has a separate input and output rate, in INR per million tokens.
        </p>
        <div className="cost-inputs">
          <label>
            Input tokens
            <input
              type="number"
              min="0"
              max="10000000"
              step="1"
              value={input}
              onChange={(e) =>
                setInput(
                  Math.min(
                    10000000,
                    Math.max(0, Math.floor(Number(e.target.value) || 0)),
                  ),
                )
              }
            />
          </label>
          <label>
            Output tokens
            <input
              type="number"
              min="0"
              max="10000000"
              step="1"
              value={output}
              onChange={(e) =>
                setOutput(
                  Math.min(
                    10000000,
                    Math.max(0, Math.floor(Number(e.target.value) || 0)),
                  ),
                )
              }
            />
          </label>
        </div>
        <div className="two-panels">
          {pricing?.models.map((m) => {
            const inputCost = (input * m.input_rate) / 1000000;
            const outputCost = (output * m.output_rate) / 1000000;
            return (
              <div className="cost-model-card" key={m.provider}>
                <Badge type={m.provider === "Groq" ? "green" : "purple"}>
                  {m.provider}
                </Badge>
                <h3>{m.model}</h3>
                <p>
                  Input: <strong>{inr(m.input_rate, 2)}</strong> / million
                  tokens
                </p>
                <p>
                  Output: <strong>{inr(m.output_rate, 2)}</strong> / million
                  tokens
                </p>
                <hr />
                <p>
                  {number(input)} × {m.input_rate} ÷ 1,000,000 ={" "}
                  {inr(inputCost, 6)}
                </p>
                <p>
                  {number(output)} × {m.output_rate} ÷ 1,000,000 ={" "}
                  {inr(outputCost, 6)}
                </p>
                <strong className="cost-total">
                  {inr(inputCost + outputCost, 6)}
                </strong>
                <small>Estimated cost for one attempt</small>
              </div>
            );
          })}
        </div>
        <h3>Reading your Finance dashboard</h3>
        <ul className="cost-notes">
          {pricing?.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
