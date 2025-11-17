# UAT Plan

| ID | Scenario | Owner | Expected Outcome | Status |
| --- | --- | --- | --- | --- |
| UAT-001 | User registers and upgrades to Pro | Product | Razorpay payment succeeds and dashboard unlocks | Pending |
| UAT-002 | AI assistant declines unsafe prompt | AI Lead | User receives “needs clarification” response | Pending |
| UAT-003 | Load dashboard under 2k rpm | SRE | Latency <150 ms and no errors | Pending |

### Execution Guidelines
1. Spin up staging environment (`staging.finbot.in`).
2. Use sandbox Razorpay keys.
3. Capture screenshots/log evidence.
4. Update status in this table with links.
