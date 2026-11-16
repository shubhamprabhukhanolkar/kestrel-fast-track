const topics = [
  {
    id: "start",
    title: "Getting started with your case",
    subtitle:
      "Find your case, complete your work and pass it to the next responsible person.",
    steps: [
      "Sign in with your assigned account and password. Meena's account supports analyst work; Arjun's account supports authorization and final credit decisions. Contact your administrator if you need access.",
      "Open Intake & Extraction → Pending cases. Find your borrower and choose Open case. Confirm the borrower name and requested facility in Active dossier before making changes.",
      "Read the intake checklist. Request missing documents or clarifications with an RM chaser. Requests at ₹25 lakh or above need standard credit review rather than fast-track extraction.",
      "If you are the analyst and intake passes, choose Run cited extraction. Follow the execution log and choose Open verification workspace when the run completes.",
      "Verify all 60 fields against their PDF sources and review reconciliation exceptions. Enter a source-check reason for each confirmation or correction. Generating a dossier does not verify its figures.",
      "Once the analyst has completed verification, the credit authorizer reviews the same case in Verification & Sign-Off and records the outcome, rationale and signature. Signing locks the case.",
      "Use FinOps & API Health to review model usage and estimated costs. Audio on/off controls action sounds across screens. Reopen Help whenever you need instructions.",
    ],
    notes: [
      "Check the status strip for the current operating mode. Live generation and revision use real model calls and provider quota.",
      "Example records are supplied for reference. Always review the selected record and evidence; no model approves credit.",
    ],
    target: "intake",
  },
  {
    id: "roles",
    title: "Operator roles & navigation",
    subtitle: "Understand your permissions and find the tools for your work.",
    steps: [
      "Meena Pillai — Senior Credit Analyst: upload PDFs, check intake, run extraction, verify figures, enter supplied CIBIL information, edit prompts and prepare drafts for authorization.",
      "Arjun Iyer — Credit Authorizer: review evidence, record the final credit decision, manage policy and provider controls, and approve submitted email drafts after password confirmation.",
      "Active dossier selects your borrower across screens. Requested facility shows the amount, Cohort shows its route, and the status badge shows the current stage. Check these before editing or signing.",
      "Use the sun/moon control for light or dark mode. Audio on/off enables or mutes short action, success and error sounds; your preference is remembered.",
      "Use the account button to sign out when you finish. The next responsible person should sign in with their own account and select the same case to continue the work.",
    ],
    notes: [
      "Disabled controls can mean your account lacks permission, evidence is incomplete, a job is running or the case is signed.",
      "Submit drafts or copy unsaved edits before signing out, changing cases or leaving a screen. Unsaved prompt and draft edits are not retained.",
    ],
  },
  {
    id: "cases",
    title: "Pending cases & the ₹25 lakh cutoff",
    subtitle: "Find outstanding work and identify the correct review route.",
    steps: [
      "Choose Pending cases to see the case count, borrower, requested facility, route and pending stage. Use the filters to narrow the list, then choose Open case.",
      "Below ₹25 lakh shows requests within the fast-track amount limit. Open the case and check its documents; the amount alone does not make intake complete.",
      "₹25 lakh & above shows requests requiring standard credit review. Exactly ₹25 lakh is outside fast-track. These cases cannot run fast-track extraction even if their documents are complete; arrange review through your standard process.",
      "Pending counts exclude cases with a recorded human decision. Read the stage to identify whether documents, extraction, verification or sign-off are still needed. Signed cases remain accessible through Active dossier for review and export.",
    ],
    notes: [
      "Fast-track requires 0 < facility amount < ₹25,00,000. Extraction runs one selected case at a time; choosing a queue filter does not start a batch run.",
    ],
    target: "intake",
  },
  {
    id: "documents",
    title: "Documents & intake requirements",
    subtitle:
      "Supply the required evidence and resolve checklist gaps before extraction.",
    steps: [
      "The current review window is January–December 2025. Supply bank statements, GSTR-1 returns and GSTR-3B returns covering all twelve months for the selected borrower.",
      "Use native text PDFs with a readable text layer on every page. Image-only scans are rejected. Monthly periods must be detectable; YYYY-MM, such as 2025-11, is a clear supported format. Renaming another file type to .pdf does not make it valid.",
      "From the analyst account, open Current case, select the document type and choose Replace PDF. Upload a PDF no larger than 15 MB. This replaces that document type for the selected case; check the filename and coverage after upload.",
      "Click a document to open the stored PDF. Read the checklist for missing months, text-layer problems and cash-share/gap notes, then choose Re-check intake.",
      "The facility must be below ₹25 lakh, cash share must be between 0% and 100%, and the gap notes must contain an explanation. Missing evidence stays blocked until supplied. Cash-share notes do not waive reconciliation exceptions.",
    ],
    notes: [
      "Inspect the files already listed under Borrower documents before requesting replacements. The checklist identifies the missing evidence.",
      "Replacing a PDF changes the evidence under review. Check the resulting case state and repeat extraction and verification when required. Signed cases are locked against evidence edits.",
    ],
    target: "intake",
  },
  {
    id: "chaser",
    title: "Edit & instruct the RM chaser",
    subtitle: "Prepare a document request and submit it for authorizer review.",
    steps: [
      "Select the borrower in Intake & Extraction and choose Draft RM chaser. The agent uses that case's intake checks and evidence gaps.",
      "Edit the text directly in Editable RM chaser draft. Check the borrower, missing documents, dates and tone.",
      "Enter your changes in Instructions for the drafter agent. For example: ‘Use three short bullet points. Request the missing October and November GSTR-3B and native bank PDF. Ask for a reply by Friday.’",
      "Choose Revise draft with instructions. The agent receives your edited text and instructions and returns a complete revised draft. You may also enter instructions before generating the first draft.",
      "Enter Recipient email and Email subject, then choose Submit current draft for authorization. This saves a shared version for the authorizer to review. Submit again if you need approval for a revised version.",
      "If you are the credit authorizer, select the same borrower and open Intake & Extraction. Review the submitted recipient, subject and body, enter your password and choose Confirm password & approve email. Approval applies to that submitted version, not to other unsaved edits.",
    ],
    notes: [
      "Each generated or revised draft is a separate model call. Direct typing does not call a model. Instructions allow up to 2,000 characters and draft text up to 12,000.",
      "Unsubmitted edits are held on the current screen. Submit the draft or copy your text before changing screens or signing out.",
      "Approved for sending records authorization only. Email delivery is not connected, so no message is transmitted. Use your approved communication channel if you need to deliver it.",
      "A newer submitted version must be reviewed again. Five failed password confirmations lock further email-approval attempts for 15 minutes.",
    ],
    target: "intake",
  },
  {
    id: "verify",
    title: "Extraction, citations & reconciliation",
    subtitle:
      "Verify every amount against its source and assess reconciliation exceptions.",
    steps: [
      "When intake passes, the analyst can choose Run cited extraction. The route is Orchestrator → Extractor → Critique → Evidence dossier. Read the execution log for progress or failure details.",
      "The extractor returns 60 fields: 12 months × bank credits, bank debits, average balance, GSTR-1 and GSTR-3B. Critique checks source grounding. One correction retry is allowed; another grounding failure blocks the dossier.",
      "In Verification & Sign-Off, select a spreadsheet cell. Inspect its document, page, indexed line, exact quote and confidence. Open the original PDF when needed; confidence does not replace checking the source.",
      "From the analyst account, confirm or correct the amount, enter a source-check reason of at least five characters and choose Confirm & log verification. Continue until all 60 fields are verified. Corrections and original citations remain in the audit trail.",
      "For each GST figure, variance = abs(bank credits − GST turnover) / abs(bank credits) × 100. Both GSTR-1 and GSTR-3B are checked. Above the active tolerance flags a month; exactly the tolerance passes. Missing values and zero-bank/nonzero-GST remain unresolved.",
      "Read the active tolerance on the screen; its initial value is 10%. Review flagged months and their evidence. The authorizer can adjust it using Save policy and should assess the impact before recording a decision.",
    ],
    notes: [
      "A completed model run leaves analyst verification and human judgement pending. If a run is delayed or fails, read its log before starting another.",
    ],
    target: "verification",
  },
  {
    id: "cibil",
    title: "View or update CIBIL information",
    subtitle:
      "Record the supplied score and its source without changing the credit decision automatically.",
    steps: [
      "Find the compact CIBIL score box at the bottom of Intake or Verification. The box displays the saved score and whether it is an example value or manually supplied information.",
      "From the analyst account, open Edit score & source. Enter a supplied score from 300 to 900, or leave the score blank when none is available.",
      "Enter a source or analyst note of at least five characters, such as the supplied report's date and what you reviewed. Choose Save CIBIL information. Check the updated score, source and last-updated details.",
      "As authorizer, review the recorded information alongside the case evidence. Signed cases cannot be edited. A missing score is shown as not provided rather than being replaced with an invented value.",
    ],
    notes: [
      "Example scores are not live bureau results. Manual entries record supplied information; the app does not retrieve a live CIBIL report.",
      "The score does not automatically approve or decline a case. The authorizer remains responsible for the credit decision.",
    ],
    target: "verification",
  },
  {
    id: "signoff",
    title: "Human sign-off & dossier export",
    subtitle:
      "Record an attributable credit decision after reviewing the verified evidence.",
    steps: [
      "Before signing, confirm intake has passed, all 60 fields are analyst-verified and the evidence dossier exists. In live mode, a completed live extraction and critique run is also required.",
      "Using the authorizer account, select the borrower and review the verified figures, reconciliation exceptions, CIBIL information and evidence dossier.",
      "Choose Approve, Return to RM or Decline. Enter an underwriting rationale of at least 30 characters and the exact signature Arjun Iyer. Address unresolved exceptions in your rationale.",
      "Record the decision only when your review is complete. The evidence snapshot, outcome, rationale and audit information are retained and the case is locked. Return to RM also locks the case; there is no automatic reopening action.",
      "Use the dossier PDF export in the verification workspace. Before a decision, the export is an evidence snapshot with the human outcome pending. After signing, it includes the recorded outcome, signature and rationale.",
    ],
    notes: [
      "Signing changes and locks the case; it is not a preview. Models prepare evidence and communication drafts. Only the credit authorizer records the decision.",
    ],
    target: "verification",
  },
  {
    id: "prompts",
    title: "Prompt & Toner Studio",
    subtitle:
      "Adjust agent instructions and communication style while preserving source facts.",
    steps: [
      "Choose an agent: Cited extractor, Critique & grounding or Toner & communication. Analyst and authorizer accounts can edit the prompt.",
      "Edit the instructions and choose Save new version. The saved version applies to subsequent runs and previews. Unsaved edits are not active; previous versions remain in history.",
      "Choose Strict CRO Regulatory Memo, Concise Analyst Dossier or Polite RM Document Chaser and select Generate tone preview. Final dossier previews require all 60 fields verified; the RM chaser is available earlier.",
      "Restore defaults creates new versions without deleting history. Before saving changes, check that instructions preserve source grounding, uncertainty and human decision authority, and review the effect on subsequent results.",
    ],
    notes: [
      "Tone changes presentation, not borrower evidence or policy thresholds. Generating and regenerating previews uses model calls.",
    ],
    target: "studio",
  },
  {
    id: "finance",
    title: "Finance, costs & provider failover",
    subtitle:
      "Understand estimated usage charges and investigate provider errors.",
    steps: [
      "Spend & API health shows estimated spend, application averages, latency, agent tokens and the provider attempt log. Use Sync metrics to refresh immediately; the dashboard also refreshes automatically.",
      "Open Cost calculation and enter input and output tokens to compare the configured Gemini and Groq rates. Cost (₹) = (input tokens × input rate + output tokens × output rate) / 1,000,000. These are estimates, not invoices or live price quotes.",
      "Each extraction, critique, revision and retry is separately metered. Failover adds recorded primary and backup usage. Unknown failed-request usage is not proof of zero billing. Hosting and storage charges are excluded from this calculator.",
      "From the authorizer account, choose Check live providers to run small Gemini and Groq connectivity checks. Readiness uses recent successful observations; an absent recent check alone does not prove a provider is broken.",
      "If you are authorized to diagnose failover, enable the relevant outage control and choose Run failover test action. Inspect the primary and backup log entries. In live mode, backup calls use Groq and may incur usage charges.",
      "Keep outage controls off during ordinary work. After a diagnostic test, turn them off and confirm normal routing. Inspect failed attempts before retrying; a failed request has not produced a successful draft.",
    ],
    notes: [
      "Provider checks contribute to total spend but are excluded from per-application averages. Historical attempts keep their recorded cost; the calculator uses current rates.",
      "Hosting and document storage target Mumbai. Gemini Developer API inference is provider-managed and is not claimed to be restricted to Mumbai.",
    ],
    target: "finops",
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting & saved work",
    subtitle:
      "Resolve blocked actions and understand how your work is retained.",
    steps: [
      "Cannot sign in: check your assigned account and password, or contact your administrator. Five failed attempts lock the account for 15 minutes; wait before trying again.",
      "Extraction is disabled: check your account permissions, facility amount, intake gaps, an active job and whether the case already has a human decision. Refresh the case and read the checklist.",
      "Upload is rejected: use a native PDF no larger than 15 MB, select the correct document type and check January–December 2025 coverage. Image-only scans do not pass intake.",
      "Verification or sign-off is blocked: check the verified count, source-check reason, intake prerequisites, exact signature and rationale length. A generated narrative is not equivalent to verified evidence.",
      "Email approval fails: confirm your authorizer password and review the newest submitted version. Older versions cannot be approved after a new submission. Five failed password confirmations lock further attempts for 15 minutes.",
      "An agent request fails: read the execution or provider attempt log. The authorizer can check connectivity and confirm outage controls are off. Keep a copy of your draft before retrying.",
      "Saved changes seem missing: first check the selected case. The current hosted workspace can reset when the service restarts or replaces an instance. Keep your own copies of uploaded documents and exported results.",
      "Need instructions offline: choose Download operating guide. The Markdown file contains these instructions without passwords, API keys or uploaded borrower documents.",
    ],
    notes: [
      "Email approval records authorization only; delivery is not connected. Extraction runs one case at a time, credit decisions require the authorizer and signed cases cannot be reopened here.",
    ],
  },
];

export default topics;
