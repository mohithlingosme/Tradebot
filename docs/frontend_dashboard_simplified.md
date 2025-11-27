# Frontend dashboard simplification

- Layout: sidebar nav (Home, Orders, Positions, Logs) with a clean content area; no Finbot AI/chat components are rendered in any route.
- Realtime: `useDashboardFeed` connects to `ws://<API_HOST>/api/ws/dashboard` (configurable via `VITE_WS_URL`), with retry/backoff and a 15s polling fallback when the socket is offline. Manual refresh buttons trigger the same snapshot fetch.
- Data sources: snapshots use `/portfolio` (P&L), `/positions`, `/orders/recent`, `/logs`, `/strategy/status`, and `/risk/status` under the API prefix. Websocket messages fan out P&L, orders, positions, logs, strategy, and risk updates.
- Pages:
  - Home: P&L, active position count, strategy state, risk badge, top 5 positions table with link to the Positions page, strategy/risk status block.
  - Orders: tabular feed with status filter, live indicator, and manual refresh.
  - Positions: active positions table with unrealized total, live indicator, and manual refresh.
  - Logs: log viewer with level filter, max-rows selector, live indicator, and manual refresh.
- Run: `cd frontend && npm install` (if needed) then `npm run dev` for Vite; `npm run tauri dev` for the Tauri shell.
