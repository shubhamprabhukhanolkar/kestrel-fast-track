# Kestrel Finance — live SME Fast-Track Workbench

The workbench defaults to **real backend model calls**, authenticated operators, cited PDF extraction, critique retries, versioned prompts and mandatory human credit sign-off. Sample borrower documents are labelled; sample data does not imply simulated inference. Provider errors never fall back to fabricated responses.

React 18/Vite/Tailwind/Lucide is served by FastAPI in one container. Python 3.12 is managed with uv. SQLite remains available locally; the cloud production profile adds PostgreSQL, private GCS PDFs and Cloud Tasks to address Cloud Run durability.

## GitHub and hosting

GitHub hosts this repository and its CI/CD workflow. **GitHub Pages cannot run the FastAPI backend.** The complete live application targets Google Cloud Run.

Pushes run automated tests and the frontend build. Cloud deployment is skipped until the repository variable `DEPLOY_ENABLED=true` is explicitly set and the required configuration below is supplied. No GCP keys, Gemini keys, Groq keys, local credentials, databases, uploaded PDFs or runtime reports belong in the repository.

## Run live locally

```powershell
uv sync --frozen
cd frontend
npm ci
npm run build
cd ..
# Add GEMINI_API_KEY privately to the ignored .env file before starting the backend.
```

Copy `.env.example` to `.env` for another checkout. Set `GEMINI_API_KEY` privately in that ignored file. `PRIMARY_PROVIDER=gemini_api` selects key-based inference; Vertex and Application Default Credentials are not required for primary AI calls. Google credentials remain necessary only for GCP resource access such as Secret Manager, GCS and deployment.

The local and cloud deployment profiles keep hosting/storage in `asia-south1`. As explicitly approved by the operator, Gemini Developer API inference is provider-managed and is not represented as Mumbai-only processing. The key is never sent to the browser or committed to GitHub.

Provision each operator's password in your own terminal. Passwords require at least 12 characters and are stored as salted scrypt hashes.

```powershell
uv run python -m backend.manage set-password --persona vikram
uv run python -m backend.manage set-password --persona meena
uv run python -m backend.manage set-password --persona arjun
uv run python -m backend.manage set-password --persona farhan
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

Open **http://127.0.0.1:8080**. Select your operator and enter its password. Five failed attempts lock that account for 15 minutes. Password reset revokes its sessions. Offline persona cookies cannot authorize live password sessions. Verified Google IAP identity is supported through `AUTH_MODE=iap`.

For UI development, run `npm run dev` in frontend while the backend runs on 8080. Fonts are bundled; the browser calls only same-origin `/api/v1/*`.

## Actual provider status and lab constraints

The primary provider is now **Gemini Developer API**, selected with `PRIMARY_PROVIDER=gemini_api`. The requested lightweight default is `GEMINI_MODEL_NAME=gemini-2.5-flash-lite`; a valid key and model access must be verified on the Developer API before calling the app operational. Configure `GEMINI_API_KEY` locally, or `GEMINI_SECRET_NAME` for a backend Secret Manager reference. `ALLOW_NONREGIONAL_INFERENCE=true` records the operator-approved change in inference boundary.

Vertex is retained only as an optional legacy provider. Earlier Vertex tests returned 404 for the 2.5 family and an organization-model-policy error for 3.5 Flash-Lite. Those Vertex-specific checks do not establish Gemini Developer API availability. Current readiness checks only the selected provider and model, and never silently substitute Vertex or offline templates.

On 15 November 2026, a complete live run using the locally configured Gemini `gemini-3.5-flash-lite` passed extraction, critique and dossier generation without injected failures or fallback: 60 cited fields, zero citation issues and one reconciliation exception month. A separate outage test injected primary 503 responses and completed all three agents using real Groq `openai/gpt-oss-120b` calls. Groq throttling recovered using bounded Retry-After waits. Both runs used labelled synthetic borrower PDFs; analyst verification and credit sign-off remained pending. This verifies live inference locally, not a deployed Cloud Run service. Transport schemas are simplified for Google compatibility while full Pydantic, completeness and citation constraints remain enforced in the backend.

Gemini cost defaults are illustrative paid-tier estimates based on the [listed Flash-Lite prices](https://ai.google.dev/gemini-api/docs/pricing) and an assumed INR 90/USD conversion, not a live exchange quote or your invoice. Set GEMINI_INPUT_INR/GEMINI_OUTPUT_INR to your contracted billing rates, especially when changing models or using a free tier.

For a cloud deployment, place the Gemini key in the approved backend secret `kestrel-gemini-api-key` and grant the runtime identity access. The workflow references the secret; no key value is stored in source or the frontend. API-key authentication changes the Google API service being used; hosting remains in Mumbai. See the [Google Gen AI SDK authentication documentation](https://googleapis.github.io/python-genai/).

For local fallback, add `GROQ_API_KEY` privately to the ignored `.env`. The default backup is `openai/gpt-oss-120b`, using JSON mode and low reasoning effort. Compact agent inputs retain all extracted fields and independent source evidence to fit provider limits. A Groq key was also stored with explicit approval at `projects/slabspro-slabsuser37/secrets/kestrel-groq-api-key`, replicated in asia-south1; cloud runtime access still requires Secret Accessor on that secret. Direct local keys do not require Secret Manager permissions.

Farhan's **Check live providers** independently calls the selected Gemini provider and Groq with a small diagnostic prompt and meters both attempts. `/api/v1/health` is process liveness; `/api/v1/ready` requires configured authentication and recent successful live provider checks. It does not claim readiness solely because environment variables exist.

For an explicitly billable verification using isolated synthetic PDFs:

```powershell
uv run python -m backend.verify_live --primary-pipeline
```

This creates a separate database/report under `artifacts/live-verification-*/` and verifies extraction, critique and dossier generation using normal live routing and synthetic PDFs. No outage is injected; configured Groq fallback can handle real primary errors, and the report identifies the provider used for every attempt. To test actual Groq failover under a labelled injected primary 503, use `--backup-pipeline` instead. Reports preserve genuine success or failure; neither path can approve credit.

## Workflow

1. **Vikram / Meena — intake:** check native PDF text layers, complete Jan–Dec 2025 bank/GSTR-1/GSTR-3B coverage and structured cash-share notes. Scans and incomplete files are blocked.
2. **Extraction:** the API persists a queued run before returning 202. A worker claims it; the UI shows actual node events. The LangGraph route is Orchestrator → Extractor → Critique → Toner, with one correction retry at most.
3. **Reconciliation:** both GSTR-1 and GSTR-3B use `abs(bank credits - GST turnover) / abs(bank credits) * 100`. Exactly 10% passes the default tolerance; higher values flag. Missing values and zero-bank/nonzero-GST remain unresolved. RM cash-share notes do not waive the rule.
4. **Meena — verification:** select a cell to highlight its exact source line/range and inspect the original PDF. Confirm/correct with a rationale. Every edit records old/new values, actor and citation. Correction rate counts distinct corrected fields.
5. **Arjun — judgement:** a completed live extraction/critique and all 60 analyst verifications are required in live mode. Enter a substantive rationale and named signature. The final record snapshots values, citations, policy and dossier; the case locks.

**NO MODEL APPROVES CREDIT.** No prompt edit, provider response or sample verification bypasses the human decision gate.

Each extracted figure must match a verbatim quote in its exact document/page/line range, the reporting month, a compatible field label and the numeric value. The critique LLM independently audits the output alongside deterministic checks. ISO, numeric and named-month dates and ordinary financial labels are supported; ambiguous layouts fail closed. This is a focused first slice, not a universal bank parser or OCR engine. PDF uploads are limited to 15 MB and 200 pages.

## Samples and agent studio

The seven synthetic borrowers include Shree Ganesh Surgicals (Pune, ₹18.5L), Deccan Precision Logistics (Chennai, ₹22L), Kaveri Agro Traders (Coimbatore, ₹14L), Malabar Packaging (Kochi, ₹12L), Sahyadri Engineering (Nashik, ₹32L), Coastal Food Distributors (Mangaluru, ₹48L) and Narmada Textiles (Surat, exactly ₹25L). The Pending cases tab shows counts and filters for facilities below ₹25L versus ₹25L and above. The latter stay outside fast-track for standard review. Shree Ganesh includes ₹14,20,000 November bank credits and ₹12,45,340 GST turnover, a 12.3% variance, reported 15% cash share and an October technical bounce. Deccan demonstrates missing returns and a scanned statement. In live mode even the clean sample requires a real pipeline and human verification before sign-off. New sample cases are added on startup without resetting existing cases, verification or decisions.

In Intake, generate the RM chaser, edit its text directly and supply instructions for the drafter agent to return a revised draft. Revisions include the selected case's actual intake gaps and are metered as model calls; nothing is sent to the RM. FinOps includes a Cost calculation tab showing the configured Gemini and Groq model rates, an interactive input/output token calculator, and explanations of retries, failover, provider checks and historical cost estimates.

The header's **Help** button opens a searchable operating guide before or after sign-in. It covers a complete demo walkthrough, operator roles, pending cases, document requirements, chaser revisions, verification, human sign-off, PDF exports, prompts, model costs and troubleshooting. Download the same content as `Kestrel-Operating-Guide.md` for offline use. Signed-in operators can jump directly from a guide topic to its workbench screen.

Meena/Farhan can edit and version system prompts; restoring defaults creates new versions. Saved prompt changes affect actual live previews. Final memo previews require all 60 human verifications; an RM document chaser remains available for incomplete files. Nothing is emailed.

Farhan can inject labelled primary 503/429 failures and inspect actual backup attempts. Turn the switches off after a presentation. Live FinOps excludes old synthetic telemetry, reports SDK tokens (including Vertex thinking), latency, model, provider, status and failover, and estimates INR cost from configurable rates. Connectivity-check costs are excluded from loan cost/application averages. Unknown failed-request usage is not proof of zero billing.

## Persistence and execution

Local mode uses SQLite WAL and a DB-backed queue with owner tokens, leases, heartbeat, attempt count and bounded infrastructure retries. Queued runs survive process restart. Expired leases recover; stale workers cannot commit over new owners. Permanent critique failures stop after the single extraction correction loop. Duplicate task delivery is safe.

Cloud mode uses Cloud SQL/PostgreSQL, private content-addressed GCS objects and authenticated Cloud Tasks. PDFs are uploaded before metadata commits. A persisted outbox is dispatched independently of the browser request, and task OIDC audience and service identity are verified. Database transactions serialize conflicting edits/sign-offs across instances. No cryptographically sealed external ledger or LMS integration is claimed.

## Cloud Run deployment

The multi-stage Dockerfile uses Node 20 to build React and Python 3.12/uv to run one non-root FastAPI process on $PORT. The frontend and API share that container.

The workflow preserves p1.yml's project `slabspro-slabsuser37`, region `asia-south1`, Artifact Registry `omnistream-repo`, JSON service-account authentication and Docker build/push stages. It sets **DEMO_MODE=false**, IAP authentication, secure cookies, private ingress, Cloud SQL, GCS, Cloud Tasks and secret references. Primary inference uses the backend Gemini API key; no Vertex model policy or Vertex IAM role is required for this mode.

Before enabling deployment:

- Supply GitHub secret `GCP_CREDENTIALS` or `GCP_SA_KEY` using the lab's existing identity.
- Set repository variables `RUNTIME_SERVICE_ACCOUNT`, `TASK_SERVICE_ACCOUNT`, `DOCUMENTS_BUCKET`, `CLOUD_SQL_CONNECTION`, `SERVICE_URL` (direct service URL/task audience), `IAP_AUDIENCE`, and `IAP_ROLE_MAP` (approved email-to-role JSON).
- Store a dedicated PostgreSQL connection URL in Secret Manager secret `kestrel-database-url` and the backup key in `kestrel-groq-api-key`. A Cloud SQL socket URL has the form `postgresql+psycopg://USER:URL_ENCODED_PASSWORD@/kestrel?host=/cloudsql/PROJECT:asia-south1:INSTANCE`. Store the Gemini Developer API key in `kestrel-gemini-api-key`.
- Configure the IAP load balancer, grant its service identity Cloud Run invocation and verify Cloud Tasks ingress. Direct unauthenticated invocation is disabled.
- Confirm the selected Gemini Developer API model/key and successful readiness checks. A successful image deployment alone is insufficient.
- Set `DEPLOY_ENABLED=true` when these prerequisites are ready.

`infra/main.tf` is an **unapplied, reviewable infrastructure option**: regional PostgreSQL 16 with backups/PITR/deletion protection, a private versioned Mumbai bucket, task queue and scoped service accounts. It extends the original SQLite-only plan to provide actual Cloud Run durability, and has cost/lab-permission implications. Review a Terraform plan before provisioning. Import the existing Groq secret if managing it in Terraform. Keep plaintext secrets out of Terraform variables/state. If the lab mandates SQLite, use persistent local disk rather than claiming Cloud Run ephemeral files are durable.

The production profile refuses simulated AI, unprotected demo personas, ephemeral SQLite, missing durable storage/tasks or cross-region settings. Infrastructure has not been provisioned merely by preparing these files.

## Verification

```powershell
uv run pytest -q
uv run python -m compileall -q backend
cd frontend
npm run build
npm run test:e2e
```

The local suite covers authentication/lockout, session isolation, real-provider routing without template fallback, live-only telemetry, provenance attacks, multi-line citations, durable queue recovery/fencing, prompt/policy versions, analyst edits and signed-case locks. Browser tests use an explicitly offline isolated profile to test the UI, not to claim live inference success.

CI provisions PostgreSQL 16 and runs DB-backed tests against both SQLite and PostgreSQL using isolated test schemas. Set `TEST_DATABASE_URL` to an expendable test database to run that matrix locally. The fixture creates/drops only its generated schemas. Terraform/Docker/cloud integration must be validated with their actual services; syntax checks are not deployment evidence.

For deliberate offline development, copy `.env.offline.example` to `.env`. That profile alone permits simulated responses, unprotected persona selection and optional sample cost rows.

## References

The original Stitch light/dark files and p1.yml remain in the project. The two referenced PDFs and presentation HTML were absent, so domain grounding uses the pasted brief; synthetic figures are not verbatim interview evidence.

[LangGraph](https://reference.langchain.com/python/langgraph/graph/state/StateGraph) · [Google Gen AI SDK](https://googleapis.github.io/python-genai/) · [Cloud Run/Cloud SQL](https://docs.cloud.google.com/sql/docs/postgres/connect-run) · [Authenticated Cloud Tasks](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks)
