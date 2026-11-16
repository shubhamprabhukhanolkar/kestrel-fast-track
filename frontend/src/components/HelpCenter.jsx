import { useEffect, useRef, useState } from "react";
import { BookOpen, Download, Search, X, ArrowRight } from "lucide-react";

const topics = [
  {
    id: "start",
    title: "Start here: demo walkthrough",
    subtitle:
      "A complete route through the prototype, from pending case to human decision.",
    steps: [
      "Sign in as Meena Pillai for document intake, extraction and verification. Use the password supplied by the demo owner. Use the operator button in the top bar to sign out and switch to the authorizer.",
      "Open Intake & Extraction → Pending cases. Compare the four facilities below ₹25 lakh with the three at or above ₹25 lakh. Open Narmada Textiles to show that exactly ₹25 lakh is outside fast-track.",
      "Open Deccan Precision Logistics to demonstrate incomplete intake: the bank statement is scanned and October/November GSTR-3B returns are missing. Draft an RM chaser, edit it and ask the agent to revise its wording.",
      "Open Shree Ganesh Surgicals and choose Run cited extraction. Follow the extraction and critique events. When completed, choose Open verification workspace.",
      "As Meena, check each of the 60 figures against the highlighted PDF source. Review the November variance, enter a source-check reason and confirm each field. Generating a dossier does not verify its figures.",
      "Switch to Arjun Iyer and select the same case in Active dossier. After all prerequisites pass, review the evidence, choose an outcome, enter a rationale and sign with Arjun Iyer. Use a different sample case if you want to keep this case unsigned for another walkthrough.",
      "Switch to Arjun Iyer to show provider connectivity, recorded attempts, failover controls and the Cost calculation tab. Turn simulated outage switches off when finished.",
    ],
    notes: [
      "Live mode uses real model calls and may consume provider quota. Offline sandbox mode uses simulated responses. The strip under the header identifies the current mode.",
      "Borrower examples are synthetic. No model approves credit; a named human decision is required.",
    ],
    target: "intake",
  },
  {
    id: "roles",
    title: "Operator roles & navigation",
    subtitle:
      "Choose the persona that owns the action you want to demonstrate.",
    steps: [
      "Meena Pillai — Senior Credit Analyst: replace PDFs, check intake, run extraction, verify figures, enter supplied CIBIL scores, prepare chasers and submit drafts for authorization.",
      "Arjun Iyer — Credit Manager / CRO: review evidence, adjust the reconciliation tolerance and record the final human outcome, signature and rationale.",
      "Arjun also manages provider checks, Finance controls and email authorization. He must confirm his password before an email approval can be recorded. Approved for sending records authorization only; no email service is connected.",
      "Active dossier selects the borrower across all screens. Requested facility and Cohort show its amount and routing. Use the sun/moon control for light or dark mode. Audio on/off in the header controls short action, success and error sounds across every screen; the preference is remembered. Help is available before and after sign-in.",
    ],
    notes: [
      "A disabled action can mean the selected persona lacks permission, evidence is incomplete, extraction is running or the case is signed. The backend enforces role permissions.",
      "Switching personas signs out the current session. Copy any unsaved draft or prompt edits before leaving that screen.",
    ],
  },
  {
    id: "cases",
    title: "Pending cases & the ₹25 lakh cutoff",
    subtitle:
      "Use the queue to demonstrate eligible requests, document gaps and standard review.",
    steps: [
      "Choose Pending cases to see the case count, borrower, facility, route and pending stage. Filter All pending, Below ₹25 lakh or ₹25 lakh & above; choose Open case to inspect a borrower.",
      "Below ₹25 lakh: Shree Ganesh Surgicals ₹18.5L, Deccan Precision Logistics ₹22L, Kaveri Agro Traders ₹14L and Malabar Packaging ₹12L. Below the cutoff does not automatically mean intake is complete.",
      "Standard-review examples: Sahyadri Engineering ₹32L, Coastal Food Distributors ₹48L and Narmada Textiles exactly ₹25L. Their fast-track extraction is blocked even if documents are complete. Standard review is a routing demonstration, not another automated approval pipeline.",
      "Pending counts exclude cases with a recorded human decision. A case can remain pending while awaiting documents, extraction, verification or sign-off. Select another case to continue the demo after signing one.",
    ],
    notes: [
      "The facility rule is strictly 0 < amount < ₹25,00,000. Extraction operates on the selected case, one case at a time; selecting a queue filter does not start a batch run.",
    ],
    target: "intake",
  },
  {
    id: "documents",
    title: "Documents & intake requirements",
    subtitle:
      "What to supply, how to replace a PDF and why intake can be blocked.",
    steps: [
      "The prototype reviews January–December 2025. Supply a bank statement, GSTR-1 returns and GSTR-3B returns covering all twelve months for the selected borrower.",
      "Use native text PDFs with a readable text layer on every page. Image-only scans are rejected. Monthly periods must be detectable; YYYY-MM, for example 2025-11, is a supported clear format. Do not rename another file type to .pdf.",
      "Sign in as Meena, open Current case, choose the document type and click Replace PDF. Upload a PDF no larger than 15 MB. This replaces that document type for the selected case; inspect the filename and coverage after upload.",
      "Click a document to open the stored PDF. Read the checklist for missing months, text-layer problems and structured cash-share/gap notes, then choose Re-check intake as Meena or Meena.",
      "The facility must be below ₹25 lakh, cash share must be between 0% and 100%, and gap notes must contain an explanation. Missing evidence stays blocked until supplied. Cash-share notes do not waive GST reconciliation exceptions.",
    ],
    notes: [
      "Sample PDFs are already supplied for the demo cases. Deccan intentionally has a scanned bank statement and missing October/November GSTR-3B returns.",
      "A replacement changes the evidence under review. Review the resulting case state and repeat extraction/verification when required. Signed cases are locked against evidence edits.",
    ],
    target: "intake",
  },
  {
    id: "chaser",
    title: "Edit & instruct the RM chaser",
    subtitle:
      "Create an unsent request for missing documents or clarification.",
    steps: [
      "Select the borrower in Intake & Extraction and choose Draft RM chaser. The agent receives that case's intake checks and evidence gaps.",
      "Edit the text directly in Editable RM chaser draft. For example, add a greeting, shorten a paragraph or clarify the requested document.",
      "In Instructions for the drafter agent, describe the desired change. Example: ‘Use three short bullet points. Request the outstanding October and November GSTR-3B and the native bank PDF. Ask for a reply by Friday.’",
      "Choose Revise draft with instructions. The agent receives both your edited draft and the instructions, then returns a complete revised draft. You can also enter instructions before generating the first draft.",
      "Review the result for correct dates, document requests and tone. Copy the final text for your own communication channel. Submit the draft for authorizer review. Arjun can approve the submitted version after password confirmation; no email service is connected and no message is delivered.",
      "Enter Recipient email and Email subject, then choose Submit current draft for authorization. Switch to Arjun, select the same borrower and open Intake & Extraction. Review the submitted version, enter the credit authorizer password and choose Confirm password & approve email. Approved for sending records authorization only; it does not transmit an email.",
    ],
    notes: [
      "Each generated or revised draft is a separate model call and appears in Finance telemetry. Direct typing does not call a model.",
      "Unsubmitted edits are held in the current screen. Submit the current draft for authorization to save a shared version before switching personas. Copy other unsaved edits before leaving. Keep instructions within 2,000 characters and draft text within 12,000.",
    ],
    target: "intake",
  },
  {
    id: "verify",
    title: "Extraction, citations & reconciliation",
    subtitle:
      "Follow the fixed workflow and verify every amount against its original source.",
    steps: [
      "When intake passes, Meena can choose Run cited extraction. The fixed route is Orchestrator → Extractor → Critique → Evidence dossier. The execution log shows the actual progress and any failure.",
      "The extractor returns 60 fields: 12 months × bank credits, bank debits, average balance, GSTR-1 and GSTR-3B. Critique checks source grounding. One correction retry is allowed; another grounding failure blocks the dossier.",
      "In Verification & Sign-Off, select a spreadsheet cell. Inspect the source document, page, indexed line, exact quote and confidence. Open the original PDF when needed. Confidence is not a substitute for checking the source. The CIBIL panel shows an example or manually supplied score; Meena can enter 300?900 or leave it blank and record the source. No live bureau retrieval or score-based automatic decision occurs.",
      "As Meena, confirm or correct the amount, enter a source-check reason of at least five characters and choose Confirm & log verification. Repeat until all 60 fields are verified. Corrections and the original citation remain in the audit trail.",
      "For each GST figure, variance = abs(bank credits − GST turnover) / abs(bank credits) × 100. Both GSTR-1 and GSTR-3B are checked. Above the current tolerance flags a month; exactly the tolerance passes. Missing values and zero-bank/nonzero-GST remain unresolved.",
      "The initial tolerance is 10%; the screen shows the active value. Shree Ganesh demonstrates a November variance of 12.3%. Arjun can change the tolerance using Save policy; assess the effect before a human decision.",
    ],
    notes: [
      "A completed model run leaves analyst verification and human judgement pending. Provider outages and quota errors can delay a run; follow its log before attempting another run.",
    ],
    target: "verification",
  },
  {
    id: "signoff",
    title: "Human sign-off & dossier export",
    subtitle:
      "Finish the workflow with an explicit, attributable credit decision.",
    steps: [
      "Complete intake, a successful live extraction/critique run in live mode, all 60 analyst verifications and the evidence dossier before signing.",
      "Sign in as Arjun Iyer and select the same borrower. Review the verified figures, reconciliation exceptions and evidence dossier. Kaveri still needs a real run and analyst verification in live mode; its sample label is not approval.",
      "Choose Approve, Return to RM or Decline. Enter a meaningful underwriting rationale of at least 30 characters and type the exact signature Arjun Iyer. Address unresolved exceptions in your reasoning.",
      "Record the human decision. The signed evidence snapshot, outcome, rationale and audit information are retained, and the case is locked. A return-to-RM decision also locks this prototype's case; automatic reopening is not implemented.",
      "Use the dossier PDF export in the verification workspace. Before a decision it is an evidence snapshot with human outcome pending; after signing it includes the recorded human outcome, signature and rationale.",
    ],
    notes: [
      "Signing is a case-changing action, not a preview. Models prepare evidence and communication drafts; only the human credit manager records the decision.",
    ],
    target: "verification",
  },
  {
    id: "prompts",
    title: "Prompt & Toner Studio",
    subtitle:
      "Adjust agent behaviour and compare communication styles without changing source facts.",
    steps: [
      "Choose an agent: Cited extractor, Critique & grounding, or Toner & communication. Meena and Arjun can edit the system prompt.",
      "Edit the prompt and choose Save new version. The new version applies to subsequent runs and previews. Existing prompt history remains available; unsaved text is not active.",
      "Choose Strict CRO Regulatory Memo, Concise Analyst Dossier or Polite RM Document Chaser, then Generate tone preview. Final dossier previews require all 60 fields verified; the RM chaser is available earlier.",
      "Restore defaults creates new prompt versions rather than deleting history. Change only one instruction at a time during a demo so you can explain its effect.",
    ],
    notes: [
      "Tone changes presentation, not borrower evidence, policy thresholds or human credit authority. Generation and regeneration use model calls.",
    ],
    target: "studio",
  },
  {
    id: "finance",
    title: "Finance, costs & provider failover",
    subtitle:
      "Explain token charges and demonstrate resilience with recorded provider attempts.",
    steps: [
      "Spend & API health shows estimated spend, per-application averages, latency, agent tokens and the provider attempt log. Use Sync metrics to refresh immediately; the dashboard also refreshes automatically.",
      "Open Cost calculation. Enter input and output tokens to compare Gemini and Groq using the backend's configured model rates. Cost (₹) = (input tokens × input rate + output tokens × output rate) / 1,000,000. These are estimates, not invoices or live market prices.",
      "Each extraction, critique, draft revision and retry is separately metered. During failover, recorded primary usage and backup usage are added. Unknown failed-request usage is not proof of zero billing. Hosting and storage charges are outside the model calculator.",
      "As Arjun, choose Check live providers for small real Gemini and Groq diagnostic calls. Readiness checks recent successful observations; no recent check does not by itself prove a provider is broken.",
      "For a resilience demo, enable Simulate Gemini service outage or Simulate token quota exhaustion, then choose Run failover test action. Inspect the failed primary and backup entries in the log. In live mode the backup response is a real Groq call.",
      "Switch both simulations off after the demo. Keep real error messages and provider attempts visible when troubleshooting; never treat an unsuccessful request as a successful draft.",
    ],
    notes: [
      "Provider checks contribute to total spend but are excluded from per-application cost averages. Historical calls keep their recorded cost; the calculator uses current rates.",
      "Hosting and document storage target Mumbai. Gemini Developer API inference is provider-managed; it is not claimed to be restricted to Mumbai.",
    ],
    target: "finops",
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting & prototype limits",
    subtitle:
      "Resolve common blockers without mistaking a partial step for a completed workflow.",
    steps: [
      "Cannot sign in: check the persona and the password supplied by the demo owner. Five failed attempts lock that account for 15 minutes. Do not repeatedly guess credentials.",
      "Extraction button disabled: check the selected role, facility amount, intake gaps, an already-running job and whether the case has a human decision. Refresh the case and inspect the actual checklist.",
      "Upload rejected: use a native PDF under 15 MB, pick the correct document type and confirm complete January–December 2025 coverage. Image-only scans do not pass intake.",
      "Verification or sign-off blocked: inspect the verified count, source-check reason, unresolved prerequisites, exact human signature and rationale length. A generated narrative is not equivalent to verified evidence.",
      "Agent action fails: inspect the execution or provider attempt log. Arjun can check provider connectivity and confirm outage simulations are off. A failed revision does not send anything to the RM; keep a copy of your draft before retrying.",
      "Changes seem missing: the current hosted prototype uses local SQLite and file storage inside Cloud Run. An instance replacement can reset its workspace; instances do not share those files. Keep your own copies of uploaded documents and exported results.",
      "Need the guide offline: choose Download operating guide in this window. It contains these instructions in a Markdown file, without passwords, API keys or borrower uploads.",
    ],
    notes: [
      "Email approval records authorization only; delivery is not connected. The prototype does not run multi-case extraction batches, automatically approve credit or reopen signed cases.",
    ],
  },
];

export default function HelpCenter({ onClose, user, navigate }) {
  const dialog = useRef(null);
  const searchInput = useRef(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState("start");
  useEffect(() => {
    const element = dialog.current;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    element.showModal();
    searchInput.current.focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
      element.close();
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, []);
  const search = query.trim().toLowerCase();
  const matches = topics.filter((topic) =>
    [topic.title, topic.subtitle, ...topic.steps, ...topic.notes]
      .join(" ")
      .toLowerCase()
      .includes(search),
  );
  const current = matches.find((topic) => topic.id === selected) || matches[0];
  function download() {
    const text =
      "# Kestrel Workbench — Operating Guide\n\n" +
      topics
        .map(
          (topic) =>
            `## ${topic.title}\n\n${topic.subtitle}\n\n${topic.steps.map((step, index) => `${index + 1}. ${step}`).join("\n\n")}\n\n${topic.notes.map((note) => `Note: ${note}`).join("\n\n")}`,
        )
        .join("\n\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/markdown;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "Kestrel-Operating-Guide.md";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <dialog
      ref={dialog}
      className="help-dialog"
      aria-labelledby="help-title"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          onClose();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialog.current) onClose();
      }}
    >
      <div className="help-shell">
        <header className="help-header">
          <div>
            <span className="section-label">KESTREL WORKBENCH GUIDE</span>
            <h2 id="help-title">
              <BookOpen size={23} /> Help & Tutorial
            </h2>
            <p>Step-by-step instructions for your demo and daily operation.</p>
          </div>
          <button
            className="secondary"
            onClick={onClose}
            aria-label="Close help"
          >
            <X size={18} />
          </button>
        </header>
        <div className="help-tools">
          <label className="help-search">
            <Search size={17} />
            <input
              ref={searchInput}
              type="search"
              aria-label="Search operating guide"
              placeholder="Search documents, chaser, sign-off, costs…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <button className="secondary" onClick={download}>
            <Download size={15} /> Download operating guide
          </button>
        </div>
        <div className="help-layout">
          <nav className="help-topics" aria-label="Help topics">
            {matches.map((topic) => (
              <button
                key={topic.id}
                aria-current={current?.id === topic.id ? "page" : undefined}
                className={current?.id === topic.id ? "selected" : ""}
                onClick={() => setSelected(topic.id)}
              >
                {topic.title}
              </button>
            ))}
          </nav>
          <article className="help-content" key={current?.id}>
            {current ? (
              <>
                <span className="section-label">
                  {user
                    ? `SIGNED IN AS ${user.name.toUpperCase()}`
                    : "AVAILABLE BEFORE SIGN-IN"}
                </span>
                <h3>{current.title}</h3>
                <p className="help-subtitle">{current.subtitle}</p>
                <ol>
                  {current.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
                {current.notes.map((note) => (
                  <p className="help-note" key={note}>
                    {note}
                  </p>
                ))}
                {user && current.target && (
                  <button
                    className="primary"
                    onClick={() => {
                      navigate(current.target);
                      onClose();
                    }}
                  >
                    Open{" "}
                    {current.target === "intake"
                      ? "Intake & Extraction"
                      : current.target === "verification"
                        ? "Verification & Sign-Off"
                        : current.target === "studio"
                          ? "Prompt & Toner Studio"
                          : "FinOps & API Health"}
                    <ArrowRight size={15} />
                  </button>
                )}
              </>
            ) : (
              <div role="status">
                <h3>No matching topics</h3>
                <p>Try “PDF”, “chaser”, “cost” or “signature”.</p>
                <button className="secondary" onClick={() => setQuery("")}>
                  Clear search
                </button>
              </div>
            )}
          </article>
        </div>
      </div>
    </dialog>
  );
}
