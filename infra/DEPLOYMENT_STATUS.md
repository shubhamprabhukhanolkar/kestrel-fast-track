# Kestrel Finance — Deployment Status

**Last Updated:** 15 November 2026

## Live Cloud Run Deployment

The unified application has been successfully containerized, built in `asia-south1`, and deployed to Google Cloud Run.

- **Service Name:** `kestrel-fast-track`
- **Region:** `asia-south1` (Mumbai)
- **Service URL:** [https://kestrel-fast-track-424664263792.asia-south1.run.app](https://kestrel-fast-track-424664263792.asia-south1.run.app)
- **Health Check:** [https://kestrel-fast-track-424664263792.asia-south1.run.app/api/v1/health](https://kestrel-fast-track-424664263792.asia-south1.run.app/api/v1/health)
- **Container Registry:** `asia-south1-docker.pkg.dev/slabspro-slabsuser37/omnistream-repo/kestrel-fast-track:latest`

## Operator Authentication & Personas

The workbench runs with live AI execution and operator authentication. Default operator credentials are automatically provisioned on start:

- **Default Password:** `KestrelOperator2026!`
- **Personas:**
  - `meena`: Meena Pillai (Senior Credit Analyst)
  - `arjun`: Arjun Iyer (Credit Manager / CRO)
  - `vikram`: Vikram Rao (Relationship Manager)
  - `farhan`: Farhan Qureshi (CIO / FinOps Admin)

## Repository & GitHub Actions

- **GitHub Repository:** `https://github.com/shubhamprabhukhanolkar/kestrel-fast-track.git`
- **Active Branch:** `main`
- **CI/CD Workflow:** `.github/workflows/deploy.yml`
  - Automated tests and linting (`test-and-build`) run automatically on all pushes to `main` and `master`.
  - Manual triggers available via `workflow_dispatch`.
