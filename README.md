# chess-tui

A small Textual-based chess TUI using `python-chess`.

## Run

```bash
poetry install
poetry run chess-tui
```

## Keys
- Enter a move in SAN (`Nf3`, O`-O`) or UCI (`e2e4`)
- `Up/Down`: step through game by ply (half-move)
- `Shift+Up/Shift+Down`: step by full-move rows (with snap-to-row-start behavior when mid-row)
- `Home/End`: jump to start/end
- `p`: export PGN to `./game.pgn`
- `q` or `Esc`: quit
