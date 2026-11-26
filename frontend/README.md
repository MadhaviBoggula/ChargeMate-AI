# ChargeMate AI — Frontend

React 19 + TypeScript SPA for EV drivers and charging-station owners.
Built with Vite, React Router, Tailwind CSS v4, and Lucide icons.

## Requirements

- Node.js 20+
- The FastAPI backend running at `http://127.0.0.1:8000`

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

The app runs at `http://localhost:5173`. `VITE_API_BASE_URL` must point at the
backend origin without a trailing slash.

## Commands

```bash
npm run dev        # Vite dev server
npm run build      # typecheck + production build to dist/
npm run preview    # serve the production build
npm run typecheck  # tsc --noEmit
npm run test       # Vitest
```

## Demo accounts

The backend seed creates these accounts:

| Role | Email | Password |
|---|---|---|
| Driver | `driver@chargemate.test` | `DriverPass123!` |
| Owner | `owner@chargemate.test` | `OwnerPass123!` |

## What is implemented

**Driver**

- Register, sign in, sign out, and session expiry handling.
- Station discovery with URL-backed text/connector/type/availability/price/power filters.
- Station detail with chargers and recorded availability.
- 30-minute slot booking: slot search, proposal, explicit confirmation, and cancellation.
- My bookings with Upcoming / Past / Cancelled / All tabs.
- AI assistant with conversation history, tool/RAG details, and confirmation cards.
- Profile with account, favourite stations, vehicles, and charging preferences.

**Owner**

- Dashboard with date-range analytics and revenue-by-station bars.
- Station creation and editing, soft deactivate, charger management.
- Charger status/price changes behind a confirmation dialog.
- Charging-session filters and totals.
- AI assistant scoped to the owner's network.
- Profile and account details.

All feature flags in `src/lib/flags.ts` are enabled because the matching backend
contracts are implemented. The UI never sends `owner_id`, `driver_id`, or `role`;
the backend derives them from the JWT.

## Notes

- Chat is synchronous, not streamed. A tool-backed answer can take several
  seconds; the first RAG answer after a backend restart may take longer.
- Availability is derived from stored charger and booking data, not live
  hardware status.
- Prices are INR per kWh. Times are rendered in the station timezone where the
  API supplies one, otherwise in the browser's timezone.
- The access token is kept in `sessionStorage` and cleared on logout or any 401.
- Production hosting needs SPA fallback to `index.html` and the deployed origin
  added to the backend CORS list.
