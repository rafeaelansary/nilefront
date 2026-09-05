# Geometry audit

Headless checks for `index.html`. No browser, no build step.

    pip install py-mini-racer
    python3 tools/audit/audit.py

Executes the game's whole inline `<script>` body inside py_mini_racer against a
stubbed THREE.js + DOM (`three_stub.js`), then reads back real world-space
bounding boxes. The stub is faithful enough that all six overworlds, both
dungeons and all four arenas build without error.

## Checks

- **ground contact** — every actor model's lowest vertex sits on its arena's
  floor at the scale it actually spawns at. Catches bosses walking with their
  feet underground and creatures hovering above it.
- **connectivity** — every mesh in a model touches at least one other mesh in
  that model. Catches the recurring "chained segments render as a row of
  floating shards" bug (Hydra necks, Hydra tail, Saif blade, crossbow lath).
- **coplanarity** — no two meshes in a model share a near-coplanar face across
  an overlap. Catches z-fighting.

Several builders use `Math.random()`, so the audit runs each model a few times
and reports the worst case.

Exit code is 0 only when every check passes.

## Adding a model

Add a row to `ACTORS` in `audit.py`: the builder's name, a JS arrow expression
that calls it, the scale it spawns at (see `spawnBossFight()` / `spawnWave()`),
its arena's floor top, and a label.

## When the stub is missing something

A `THREE.Foo is not a constructor` or `x.bar is not a function` error on load
means the stub lacks something the game now uses. Add it to `three_stub.js` —
geometries only need to report a local half-extent box in `_half`, which is all
the bounding-box maths reads.
