# Multi-user Scoring & Leaderboard (Supabase) — Design

## Summary

NILEFRONT is currently a single-player, offline, single-`index.html` game with a
local-only score (`player.score`, +1/kill, +10/boss) that resets every run and is
never persisted. This adds accounts, a richer scoring formula, and a global
leaderboard backed by Supabase — with score submission validated server-side so
the leaderboard can't be forged by a player editing client JS or network requests.

This spec covers accounts + scoring + leaderboard only. A separate, unrelated
feature — a per-wave minimap so players can see where they are on the current
map — is out of scope here and will get its own spec.

## Scope decisions

- **Multi-user** means separate accounts playing solo, each submitting runs to a
  shared leaderboard — not real-time multiplayer. Players never see or interact
  with each other in the game world.
- **Auth**: Supabase Auth, email + password. Signup also collects a chosen
  username (leaderboard shows usernames, never emails).
- **Login is required before START** — the title screen shows sign-in/sign-up in
  place of (or ahead of) the START button. There is no guest/anonymous play path.
- **Score submission**: one row per completed run (death or win), submitted at
  game-over. The leaderboard shows each player's *best* run, not every run.
- **Leaderboard**: a single all-time top-10 list, shown on the title screen and
  again on the game-over screen with the player's own entry highlighted if
  present.
- **Security posture**: given this is a personal/portfolio project rather than a
  competitive leaderboard with real stakes, "secure" here specifically means
  *the leaderboard can't be forged by a client sending an arbitrary score* — not
  full anti-cheat (e.g. a player could still use aimbot-style automation to earn
  a legitimately-computed high score; that's accepted).

## Architecture

- **Client** (`index.html`): loads `supabase-js` via CDN, same no-build-step
  pattern as three.js today. Handles auth (sign-up/sign-in/session), tracks raw
  run stats during play, and calls one Edge Function at game-over. It never
  computes or submits a final score directly to the database.
- **Server**: one Supabase Edge Function, `submit-score`. Receives the
  authenticated user's raw run stats, re-derives the score using the
  authoritative formula (a server-side copy of the same logic used for the
  client's live HUD preview), and inserts the row using the service-role key —
  which never reaches the browser.
- **Database lockdown**: the `runs` table has **no `INSERT`/`UPDATE`/`DELETE`
  policy for `authenticated`/`anon` roles** — only the service-role client
  inside the Edge Function can write. `SELECT` is public on both `runs` and
  `profiles`, since the leaderboard is public. This means even a player who
  fully reverse-engineers the client JS cannot forge a leaderboard entry — the
  only write path is server-side recomputation from raw stats.

## Data model

```sql
profiles (
  id uuid primary key references auth.users(id),
  username text unique not null,
  created_at timestamptz default now()
)
-- row created automatically by a trigger on auth.users insert (signup),
-- pulling the username out of the signup form's user metadata

runs (
  id bigint generated always as identity primary key,
  user_id uuid not null references profiles(id),
  score int not null,
  wave_reached int not null,
  era_reached int not null,
  kills int not null,
  boss_kills int not null,
  shots_fired int not null,
  shots_hit int not null,
  max_streak int not null,
  duration_seconds numeric not null,
  created_at timestamptz default now()
)
```

RLS:
- `profiles`: `SELECT` open to all; no client-side `INSERT` (the signup trigger
  creates the row).
- `runs`: `SELECT` open to all; **no client-side write policy at all** — only
  service-role (used exclusively inside `submit-score`) can insert.

Leaderboard view:

```sql
create view leaderboard as
select distinct on (r.user_id)
  p.username, r.score, r.wave_reached, r.era_reached, r.created_at
from runs r
join profiles p on p.id = r.user_id
order by r.user_id, r.score desc;
```

The client queries `leaderboard`, ordered by `score desc`, limited to 10 — each
player's best run only, per the "leaderboard shows best run" decision above.

Kept intentionally minimal for a first version — no weapon/loadout breakdown,
no per-era history, no full run log. Can be extended later without breaking
this design.

## Score formula

Computed identically (same shape) by the client, for a live HUD preview during
play, and by the Edge Function, as the authoritative value that gets stored:

```
score = killPoints + waveBonus + accuracyBonus + speedBonus

killPoints    = sum of (points per kill × streak multiplier at time of kill)
                — base points: 1/enemy, 10/boss (unchanged from today)
                — streak multiplier: +10% per 5 consecutive kills within a
                  3s window of each other, capped at +100%

waveBonus     = 20 × waves cleared + 150 × bosses defeated

accuracyBonus = up to 200 points, scaled linearly by (shots_hit / shots_fired)

speedBonus    = up to 150 points if the run's duration beats a par time for
                the wave reached, scaling down to 0 at/after par
```

The specific constants (10%, 20, 150, 200, par times) are tunable during
implementation/playtesting — this spec fixes the formula's shape, not final
balance numbers. Some duplication between the client's live-preview copy and
the Edge Function's authoritative copy is accepted; the client's number is only
a preview, the server's is what's stored.

## Client flow

1. **Title screen**: if there's no active Supabase session, show sign-in /
   sign-up (email, password, and — sign-up only — a chosen username) in place
   of START. On success, START becomes available. Sessions persist via
   `supabase-js`'s `localStorage` handling, so returning players stay logged in.
2. **During play**: the game tracks the raw stats the formula needs — kills by
   type, boss kills, shots fired/hit, current/max streak, wave/era reached
   (wave/era already tracked today), and a run-start timestamp.
3. **On death or win** (game-over): tracking stops; the client calls
   `submit-score` with the raw stats and the user's auth token.
4. **Game-over screen**: shows the score returned by the Edge Function
   (authoritative — may differ slightly from the live HUD preview if the two
   formula copies drift) and the top-10 leaderboard, with the player's own
   entry highlighted if present.

## Error handling

- **Submission fails** (network down, function error): show the run's score
  locally with a "couldn't save to leaderboard" note; don't block starting
  another run. No retry queue.
- **Session expires mid-run**: same "couldn't save" message rather than a
  crash.
- **Leaderboard fetch fails** (title screen or game-over): show "leaderboard
  unavailable"; don't block login or play.

## Testing

The project has no existing automated test harness — it's a single static HTML
file. Verification is manual:
- Sign-up and sign-in flow, including duplicate-username handling.
- A full run end-to-end against a real Supabase project, confirming the score
  shown at game-over matches what lands in `runs`.
- Confirming a direct client-side `INSERT` into `runs` is rejected by RLS (the
  security property this design is built around).
- Leaderboard ordering and best-per-user dedup.

## Out of scope

- Real-time multiplayer (players never share a live game session).
- Per-wave minimap — separate spec.
- Full run history / stats page (only best-run-per-user is surfaced).
- Anti-cheat beyond preventing forged score submission (e.g. no detection of
  automation/macros that legitimately play the game).
