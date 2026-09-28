# Store covers

The three covers CrazyGames asks for, made from the game itself — its own models, maps and renderer —
posed and lit for the purpose rather than screenshotted:

| file | size | CrazyGames slot |
|---|---|---|
| `cover_1920x1080.png` | 1920×1080 | Landscape (16:9) |
| `cover_800x1200.png`  | 800×1200  | Portrait (2:3) |
| `cover_800x800.png`   | 800×800   | Square (1:1) |

The scene: a cast from each road the game walks — mummy and jackal (Egypt), minotaur (Greece), jaguar
knight (Aztec Mexico), berserkr (Viking Sweden), Song guard (China) — in front of the Colossus (Boss I),
on open desert north of the Giza pyramids at dusk. The only text is the name, as CrazyGames requires
(no "Play", no logos, no borders), in the title screen's own lettering.

## Regenerating

    python3 tools/portal/covers/src/make_covers.py

Needs macOS with Google Chrome (rendered headless on the real GPU), Pillow, and Georgia Bold. Each cover's
camera and cast is in `src/landscape.js`, `src/portrait.js`, `src/square.js`; the dusk lighting is
`src/look.js`. Re-run after any change to the models or the Egypt map, so the covers keep matching the game.
