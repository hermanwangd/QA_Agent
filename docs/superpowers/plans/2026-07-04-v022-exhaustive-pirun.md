# v0.2.2 Exhaustive PI-run Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute every release-asset-visible v0.2.2 suite, evidence/report gate, and release artifact verification path that can run from the published assets without checking out source.

**Architecture:** Use the v0.2.2 jar and usage-kit as the source of executable truth. Build a small local runner that inventories suite manifests, executes validate/dry-run/run sequentially with `-Xmx512m`, records outputs, then runs evidence/report checks over generated `result.json` files.

**Tech Stack:** Java release jar, Python 3 standard library plus PyYAML for manifest parsing, shell/OpenSSL for release signature checks.

---

### Task 1: Inventory Executable Scope

**Files:**
- Read: `usage-kit-v0.2.2/usage-kit/samples/**/suite_manifest*.yaml`
- Read: `usage-kit-v0.2.2/usage-kit/docs/09-operations/provider_support_matrix.md`
- Create: `reports/pi-run-v0.2.2-exhaustive-matrix.json`

- [ ] **Step 1: Enumerate suite manifests**

Run:

```sh
python3 tools/run_v022_exhaustive_matrix.py --inventory-only
```

Expected:

```text
inventory_count: 28
```

- [ ] **Step 2: Classify external runtime availability**

Run:

```sh
command -v docker || true
command -v colima || true
command -v podman || true
command -v nerdctl || true
```

Expected on this machine:

```text
no container runtime path printed
```

### Task 2: Execute All Usage-kit Suites

**Files:**
- Create: `reports/pi-run-v0.2.2-exhaustive-matrix.json`
- Create: `reports/pi-run-v0.2.2-exhaustive-matrix.md`

- [ ] **Step 1: Run full suite matrix**

Run:

```sh
python3 tools/run_v022_exhaustive_matrix.py --run-all
```

Expected:

```text
matrix_written: reports/pi-run-v0.2.2-exhaustive-matrix.json
markdown_written: reports/pi-run-v0.2.2-exhaustive-matrix.md
```

- [ ] **Step 2: Review failures**

Run:

```sh
python3 tools/run_v022_exhaustive_matrix.py --summarize reports/pi-run-v0.2.2-exhaustive-matrix.json
```

Expected: every failure is classified as either an expected negative suite, a known blocker, or an environment/tooling limitation.

### Task 3: Verify Release Artifacts

**Files:**
- Read: `release-assets-v0.2.2/*`
- Update: `reports/pi-run-v0.2.2-exhaustive-report.md`

- [ ] **Step 1: Verify checksums**

Run:

```sh
cd release-assets-v0.2.2
awk '{name=$2; sub(/^target\//, "", name); printf "%s  %s\n", $1, name}' checksums.sha256 | shasum -a 256 -c -
```

Expected: all four checksum entries print `OK`.

- [ ] **Step 2: Verify detached signatures with embedded cert public keys**

Run:

```sh
cd release-assets-v0.2.2
for asset in spec-driven-auto-regression-0.2.2.jar spec-driven-auto-regression-0.2.2-usage-kit.zip bom.json bom.xml checksums.sha256; do
  printf '%s: ' "$asset"
  openssl dgst -sha256 \
    -verify <(base64 -D < "$asset.pem" | openssl x509 -pubkey -noout) \
    -signature <(base64 -D < "$asset.sig") \
    "$asset"
done
```

Expected: every asset prints `Verified OK`.

### Task 4: Run Custom Dummy REST PI-run

**Files:**
- Read: `dummy_app/app.py`
- Read: `pi_run_demo/dummy_rest/suite_manifest.yaml`
- Update: `reports/pi-run-v0.2.2-exhaustive-report.md`

- [ ] **Step 1: Run dummy app unit tests**

Run:

```sh
python3 -m unittest tests/test_dummy_app.py
```

Expected: `Ran 4 tests` and `OK`.

- [ ] **Step 2: Validate, dry-run, full-run, evidence-check, and report-check dummy REST suite**

Run the v0.2.2 jar against `pi_run_demo/dummy_rest/suite_manifest.yaml` using profile `local_dummy`; start `dummy_app.app` on `127.0.0.1:18080` only for the full run.

Expected:

```text
validate: exit 0
pi-run --dry-run: exit 0
pi-run: exit 0
validate-evidence: exit 0
report --format yaml: exit 1 with VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM
```

### Task 5: Write Exhaustive Report

**Files:**
- Create: `reports/pi-run-v0.2.2-exhaustive-report.md`

- [ ] **Step 1: Write coverage report**

The report must include:

- suite manifest execution matrix;
- provider/operation/verify coverage;
- release checksum/signature verification;
- Testcontainers/Docker feasibility result;
- custom dummy REST blocker;
- clear distinction between executable coverage and contract-only or environment-limited coverage.

- [ ] **Step 2: Final verification**

Run:

```sh
rg -n "Overall Verdict|Suite Matrix Summary|Not Fully Covered|Testcontainers" reports/pi-run-v0.2.2-exhaustive-report.md
pgrep -fl 'dummy_app|spec-driven-auto-regression|java'
git status --short --branch
```

Expected:

- report sections are present;
- no lingering `dummy_app` or Java process is present;
- git status only shows expected local report/script artifacts.
