# pi-run v0.2.4 Evidence Command Matrix

## Summary

- Case count: `12`
- PASS: `3`
- EXPECTED_FAIL: `6`
- BLOCKED_FRAMEWORK: `3`
- Unexpected FAIL: `0`
- Report supported positive cases: `PASS`
- Report supported positive missing formats: `none`
- Report supported negative cases: `EXPECTED_FAIL`
- Report supported negative missing formats: `none`
- Validate-evidence positive cases: `PASS`
- Validate-evidence negative cases: `EXPECTED_FAIL`

## Results

| Case | Category | Expected Exit | Actual Exit | Status |
|---|---|---:|---:|---:|
| `validate-evidence-valid` | `validate-evidence-positive` | 0 | 0 | `PASS` |
| `validate-evidence-missing-evidence` | `validate-evidence-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `validate-evidence-secret-leak` | `validate-evidence-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `report-valid-text` | `report-positive` | 0 | 0 | `PASS` |
| `report-valid-yaml` | `report-positive` | 0 | 0 | `PASS` |
| `report-valid-json` | `report-positive` | 0 | 2 | `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT` |
| `report-missing-evidence-text` | `report-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `report-missing-evidence-yaml` | `report-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `report-missing-evidence-json` | `report-negative` | 1 | 2 | `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT` |
| `report-secret-leak-text` | `report-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `report-secret-leak-yaml` | `report-negative` | 1 | 1 | `EXPECTED_FAIL` |
| `report-secret-leak-json` | `report-negative` | 1 | 2 | `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT` |
