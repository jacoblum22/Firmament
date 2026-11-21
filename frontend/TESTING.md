# Frontend testing

## Commands

| Command | Purpose |
| -------- | -------- |
| `npm test` | Run Vitest once (CI-friendly) |
| `npm run test:watch` | Watch mode while developing |
| `npm run test:coverage` | Statement coverage (see `vite.config.ts` → `test.coverage`) |

Run these from the `frontend/` directory, or from the repo root with `npm run test:frontend`.

**CI:** GitHub Actions runs backend (`pytest`) and frontend (`vitest`) jobs on every push and pull request to `main` (see `.github/workflows/ci.yml`).

## Local API URL (Vite env)

`vite` loads `.env.development` **after** `.env.local`, so a `VITE_API_BASE_URL` line in `.env.development` overrides `.env.local`. This repo keeps the API base URL out of `.env.development` so `.env.local` (for example `http://127.0.0.1:8001`) wins. Restart the dev server after changing env files.

## Layout

- **Co-located tests**: `Component.tsx` → `Component.test.tsx` next to it (or adjacent folder). Keeps behavior and tests discoverable in review.
- **`src/test/`**: Shared setup (`setup.ts`), smoke check (`smoke.test.ts`), and **reusable mocks** under `src/test/mocks/` (for example Framer Motion stubs so UI tests stay fast and deterministic).

## Conventions

1. Prefer React Testing Library queries that mirror accessibility (`getByRole`, `getByLabelText`) over brittle CSS selectors.
2. Mock heavy animation libraries via `src/test/mocks/framerMotion.tsx` instead of duplicating stubs in every file.
3. Service tests (`apiService.test.ts`) mock network boundaries (`NetworkUtils` / `fetch`) rather than hitting a real API.

Overall coverage is weighted toward utilities, services, and isolated components; the main `App` shell and long orchestration hooks are thinner—documenting that honestly is stronger than inflating numbers.
