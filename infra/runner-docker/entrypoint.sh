#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${REPO_URL:-}" || -z "${ACCESS_TOKEN:-}" ]]; then
  echo "ERROR: Debes definir REPO_URL y ACCESS_TOKEN (GitHub PAT)."
  exit 1
fi

OWNER_REPO=$(echo "${REPO_URL}" | sed -E 's#https://github.com/([^/]+/[^/]+).*#\1#')
echo "Solicitando token de registro para el Self-Hosted Runner en ${OWNER_REPO}..."

REG_TOKEN=$(curl -sX POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "https://api.github.com/repos/${OWNER_REPO}/actions/runners/registration-token" | jq -r .token)

./config.sh \
  --url "${REPO_URL}" \
  --token "${REG_TOKEN}" \
  --name "${RUNNER_NAME:-azure-selfhosted-runner}" \
  --labels "${LABELS:-self-hosted,azure,linux}" \
  --work "${RUNNER_WORKDIR:-_work}" \
  --unattended \
  --replace

cleanup() {
  echo "Desregistrando runner de GitHub..."
  ./config.sh remove --unattended --token "${REG_TOKEN}" || true
}
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!
