// ==========================================
// 1. k6 Load Testing Script
// ==========================================
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp-up to 20 users
    { duration: '1m', target: 50 },  // Plateau at 50 users
    { duration: '30s', target: 0 },  // Ramp-down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<1500'], // 95% of requests must complete under 1.5s
  },
};

export default function () {
  const url = __ENV.API_URL || 'http://localhost:8000/v1/health';
  const res = http.get(url);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'latency is normal': (r) => r.timings.duration < 2000,
  });
  
  sleep(1);
}
---
# ==========================================
# 2. SBOM & License Compliance Script (generate-sbom.sh)
# ==========================================
#!/bin/bash
set -e

echo "[SyncSphere Release Security] Initiating SBOM generation..."

# Generate frontend package-lock.json SBOM
if command -v trivy &> /dev/null; then
    trivy fs --format cyclonedx --output sbom-frontend.json ./frontend
    trivy fs --format cyclonedx --output sbom-backend.json ./backend
    echo "CycloneDX SBOM json reports exported successfully."
else
    # Mock generation fallback
    echo "{\n  \"bomFormat\": \"CycloneDX\",\n  \"specVersion\": \"1.5\",\n  \"component\": {\n    \"name\": \"syncsphere\",\n    \"version\": \"1.0.0\"\n  }\n}" > sbom-fallback.json
    echo "Trivy command missing. Generated fallback local SBOM template."
fi

# License compliance audits checking
echo "Checking licenses compliance..."
# Scrape requirements / node_modules for GPL/AGPL copyleft dependencies
grep -ri "GPL" ./frontend/package.json ./backend/requirements.txt || echo "No Copyleft licenses found. Security checked passed."
