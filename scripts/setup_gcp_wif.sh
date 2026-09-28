#!/bin/bash
# One-time setup: lets the weekly-report.yml GitHub Actions workflow query BigQuery without any
# long-lived key. GitHub's OIDC token is exchanged for short-lived GCP credentials at request time
# (Workload Identity Federation), scoped to this exact repo only.
#
# Run this yourself, once, from a terminal already authenticated to the master-chariot-413216
# project (gcloud auth login). Not run automatically: it changes real GCP IAM.
#
# Safe to re-run: every step checks what already exists and skips it, so a run interrupted partway
# (or by the new-service-account propagation delay in step 3) can just be started again from the top.
set -euo pipefail

PROJECT_ID="master-chariot-413216"
REPO="Himanshu2405/P1-Weekly-Insights-Report-Agent"
POOL_ID="github-actions-pool"
PROVIDER_ID="github-actions-provider"
SA_NAME="p1-weekly-report-ci"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

echo "== 1. Enable the APIs Workload Identity Federation needs"
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com --project "$PROJECT_ID"

echo "== 2. Create the service account the workflow will impersonate (no key ever created for it)"
if gcloud iam service-accounts describe "$SA_EMAIL" --project "$PROJECT_ID" >/dev/null 2>&1; then
  echo "already exists, skipping"
else
  gcloud iam service-accounts create "$SA_NAME" \
    --project "$PROJECT_ID" \
    --display-name "P1 weekly report - GitHub Actions CI"
  echo "waiting for the new service account to finish propagating..."
  sleep 15
fi

echo "== 3. Grant it just what build_report.py needs: running BigQuery queries"
# A brand-new service account can take a few seconds to become visible to the IAM policy API,
# so retry a couple of times instead of failing on the first attempt.
for i in 1 2 3 4 5; do
  if gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member "serviceAccount:${SA_EMAIL}" \
      --role "roles/bigquery.jobUser" \
      --condition=None >/dev/null; then
    break
  fi
  echo "not visible yet, retrying in 10s ($i/5)..."
  sleep 10
done

echo "== 4. Create the Workload Identity Pool"
if gcloud iam workload-identity-pools describe "$POOL_ID" --project "$PROJECT_ID" --location "global" >/dev/null 2>&1; then
  echo "already exists, skipping"
else
  gcloud iam workload-identity-pools create "$POOL_ID" \
    --project "$PROJECT_ID" \
    --location "global" \
    --display-name "GitHub Actions pool"
fi

echo "== 5. Create the OIDC provider, restricted to this exact repo"
if gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --project "$PROJECT_ID" --location "global" --workload-identity-pool "$POOL_ID" >/dev/null 2>&1; then
  echo "already exists, skipping"
else
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --project "$PROJECT_ID" \
    --location "global" \
    --workload-identity-pool "$POOL_ID" \
    --display-name "GitHub Actions provider" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition "assertion.repository == '${REPO}'" \
    --issuer-uri "https://token.actions.githubusercontent.com"
fi

echo "== 6. Let ONLY this repo's workflow impersonate the service account"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project "$PROJECT_ID" \
  --role "roles/iam.workloadIdentityUser" \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}"

echo
echo "Done. Add these as GitHub repo VARIABLES (Settings > Secrets and variables > Actions > Variables),"
echo "not secrets - neither value is sensitive on its own:"
echo
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
echo "GCP_SERVICE_ACCOUNT=${SA_EMAIL}"
