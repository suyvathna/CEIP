# Frontend update — what changed

## How to apply
From your repo root, with a clean working tree:

```
git apply ceip-frontend-updates.patch
# or, if that fails on whitespace/line-ending diffs:
git apply --3way ceip-frontend-updates.patch
```

Then:

```
cd frontend
npm install       # picks up the newly-used deps that were already in package.json (MUI, TanStack Query, recharts, react-hook-form, notistack)
cp .env.example .env   # only if you don't already have one
npm run dev
```

You'll also need a `backend/.env` — see `backend/.env.example` (new in this
patch) for the required keys. Without it the backend can't start
(`Settings()` reads required fields from that file).

## New features (the four you asked to prioritize)

- **Dashboard** — `/projects/:id/dashboard`. Stat cards, a bar chart of events
  by type and a pie chart of severity, recent events list. Backed by
  `GET /dashboard/{project_id}`.
- **Timeline** — `/projects/:id/timeline`. Filterable by date range, event
  type, severity; small analytics chart; events grouped by day. Backed by
  `GET /timeline/{project_id}` and the timeline-analytics endpoint.
- **Project Report** — `/projects/:id/report`. Summary panel plus PDF/Excel/
  JSON export buttons hitting the three export endpoints directly.
- **Intelligence search** — a search box in the top bar (`/search?q=...`).
  Results are grouped by type (Event / Daily Diary / Evidence). Since search
  results only carry an id (not a project id), two small resolver routes
  (`/events/:id`, `/diaries/:id`) fetch the record and redirect into the
  correct project-scoped URL. Evidence results link straight to the
  download endpoint.

## Tech stack change

`package.json` already listed MUI, TanStack Query, react-hook-form, yup, and
recharts as dependencies, but nothing used them — everything was plain CSS +
`useState`/`useEffect` + `fetch`. Per your call, the four new pages and the
navigation shell (`Layout`, `ProjectNav`, `ProjectListPage`, `ProjectCard`,
`ProjectDetailPage`, `EventList`) now use that stack. The rest of the CRUD
pages (login/register, new/edit project, new/edit event, event detail, new
diary, new evidence, deadlines dashboard) were left as they were — same
plain CSS, same fetch calls — just wrapped in a `.legacy-page` class so the
old element-level CSS (`button`, `input`, `form`, `h1`...) can't leak onto
the new MUI components, and so it still renders correctly inside the new
`Layout`'s `<Container>`.

## Small fixes found along the way

- `client.js` had no fallback for `VITE_API_BASE_URL` — with no `.env` set
  up, every API call failed silently. It now falls back to
  `http://localhost:8000`, and a `frontend/.env.example` is included.
- `EventDetailPage`'s evidence download link read `VITE_API_BASE_URL`
  directly instead of using the same `BASE_URL` constant as the rest of the
  app (would've broken once a fallback was added elsewhere) — fixed to use
  the shared constant.
- Added the API helpers the backend already exposed but the frontend never
  called: `filterEvents`, `searchEvents`, `searchEventsByDate`,
  `deleteEvidence`, `getEvidence`, `updateDailyDiary`, `deleteDailyDiary`,
  `getDailyReport`. Not all are wired into UI yet (out of the agreed scope)
  but they're there for the next round.

## Known pre-existing issues (not touched)

Ran `npm run lint` before and after — these two failures exist on `main`
already, unrelated to this work:
- `AuthContext.jsx` — fast-refresh lint rule (file exports both a component
  and helper functions).
- `EventDetailPage.jsx` — `setLoading(true)` called synchronously inside a
  `useEffect` (a real but pre-existing issue, not something I introduced).

## Verification performed

Spun up a local Postgres + the FastAPI backend, ran the Alembic migrations,
registered a user, and seeded a realistic project (8 events across every
type/severity, 2 diary entries, one notice marked "given on time"). Then
loaded every new/changed page in a headless browser and confirmed: no
console/page errors, correct data rendering, and that both search-result
redirect routes (`/events/:id`, `/diaries/:id`) land on the right
project-scoped URL. Also confirmed the legacy CRUD pages (e.g. "New
Project") still render pixel-identical to before inside the new shell.

One real bug this caught: this project's pinned MUI version's `<Stack>`
component doesn't accept `justifyContent`/`alignItems`/`flexWrap`/`gap` as
direct props (only `direction`/`spacing`/`divider`/`sx`) — passing them
silently leaked as invalid DOM attributes with a console warning on every
affected page. Fixed by moving those onto `sx={{ ... }}` everywhere.
