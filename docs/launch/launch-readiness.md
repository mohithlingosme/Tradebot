# Launch Readiness Checklist

- [ ] **Security audit** – External partner report uploaded, critical findings remediated.
- [ ] **Critical bugs** – GitHub label `priority:critical` empty; blocker gate script returns zero.
- [ ] **Load testing** – `k6 run tests/load/candles.js` ≥3x peak traffic, P95 <150 ms.
- [ ] **Monitoring dashboards** – Grafana boards (`Finbot-API`, `Finbot-AI`, `Finbot-Cost`) reviewed and alerting configured.
- [ ] **Press kit** – Logos, founder bios, product screenshots zipped under `marketing/press-kit/finbot-press-kit.zip`.
- [ ] **Launch date confirmed** – Coordinated with partners, support, and marketing; freeze schedule communicated.

Meeting cadence: T-14, T-7, T-3, T-1 go/no-go reviews. Update this document after each meeting with notes and owners.
