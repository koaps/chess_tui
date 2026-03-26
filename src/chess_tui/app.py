"""Textual application for chess-tui.

Design:
- Maintain a canonical move list (`self.moves`).
- The board shown is a reconstructed view from `self.ply_cursor`.
- Moves can only be added in Live mode (cursor at end).
"""

from __future__ import annotations

from pathlib import Path

import chess
from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Input

from .controllers import SimpleEngineController
from .moves import mover_color_from_board_after_push, san_for_legal_move
from .pgn_utils import PgnMetadata, build_pgn
from .replay import board_at_ply, last_move_for_ply
from .widgets import ChessBoardWidget, FooterStatus, MoveHistory


class ChessApp(App):
    """Main Textual app with PGN export, replay navigation, and footer status."""

    CSS = """
    #root { height: 100%; }

    #body {
        background: $background;
        height: 1fr;
        grid-size: 2;
        grid-columns: 1fr 32;
        grid-rows: 1fr;
        padding: 1;
    }

    #chess-board { width: 1fr; margin-right: 1; }

    #history {
        width: 32;
        border: round $accent;
        padding: 1;
        height: 1fr;
    }

    #board-container {
        border: round $accent;
        padding: 1;
        height: 1fr;
    }

    #board-center {
        height: 1fr;
        width: 1fr;
    }

    #board-image {
        height: 1fr;   /* critical: leaves room for the Input below */
        width: auto;
    }

    #cmd {
        height: 3;
        margin-top: 1;
        width: 1fr;
    }

    #footer {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text;
    }

    .selected { background: $accent 30%; }
    """

    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('escape', 'quit', 'Quit'),
        ('p', 'export_pgn', 'Export PGN'),
        ('up', 'replay_prev', 'Replay: prev ply'),
        ('down', 'replay_next', 'Replay: next ply'),
        ('shift+up', 'replay_prev_full', 'Replay: prev move'),
        ('shift+down', 'replay_next_full', 'Replay: next move'),
        ('home', 'replay_start', 'Replay: start'),
        ('end', 'replay_end', 'Replay: end'),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='root'):
            with Grid(id='body'):
                yield ChessBoardWidget(id='chess-board')
                yield MoveHistory(id='history')
            yield FooterStatus(id='footer')

    def on_mount(self) -> None:
        self.board_widget = self.query_one(ChessBoardWidget)
        self.history = self.query_one(MoveHistory)
        self.footer = self.query_one(FooterStatus)

        try:
            self.set_focus(self.board_widget.query_one(Input))
        except Exception:
            self.set_focus(self.board_widget)

        self.engine_side = chess.BLACK
        self.engine = SimpleEngineController(self.board_widget.board, self.engine_side)

        # Canonical game record
        self.starting_board = chess.Board()
        self.moves: list[chess.Move] = []

        # Cursor into the move list (0..len(moves))
        self.ply_cursor: int = 0

        self._sync_replay_view()

    @property
    def is_replaying(self) -> bool:
        """True when viewing an earlier ply (cursor not at end)."""
        return self.ply_cursor != len(self.moves)

    def _set_footer_mode(self) -> None:
        total = len(self.moves)
        if self.is_replaying:
            self.footer.set_mode(f'Replay: ply {self.ply_cursor}/{total} (Up/Down ply, Shift+Up/Down row, Home/End)')
        else:
            self.footer.set_mode(f'Live: ply {self.ply_cursor}/{total} (p: export PGN)')

    def _sync_replay_view(self) -> None:
        """Rebuild the view board from the canonical move list + cursor."""
        view_board = board_at_ply(self.starting_board, self.moves, self.ply_cursor)
        self.board_widget.board = view_board
        self.board_widget._last_move = last_move_for_ply(self.moves, self.ply_cursor)
        self.board_widget.refresh_image()
        self.history.set_cursor_ply(self.ply_cursor)
        self._set_footer_mode()

    def _apply_move_and_update_ui(self, move: chess.Move) -> None:
        """Apply a move in Live mode, append to canonical move list, and refresh UI."""
        if self.is_replaying:
            self.footer.set_message('Finish replay (Down/End) to return to current position before making moves.')
            return

        board = self.board_widget.board
        san = san_for_legal_move(board, move)  # must be computed pre-push
        board.push(move)

        self.moves.append(move)
        self.ply_cursor = len(self.moves)

        mover = mover_color_from_board_after_push(board)
        self.history.add_san_ply(mover, san)

        self.footer.clear_message()
        self._sync_replay_view()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        board = self.board_widget.board

        # Parse SAN, then UCI
        try:
            move = board.parse_san(cmd)
        except Exception:
            try:
                move = chess.Move.from_uci(cmd)
            except Exception:
                self.footer.set_message('Invalid move format (use SAN like Nf3 or UCI like e2e4).')
                return

        if move not in board.legal_moves:
            self.footer.set_message('Illegal move.')
            return

        self._apply_move_and_update_ui(move)
        event.input.value = ''

        if not self.is_replaying and self.engine.is_engine_to_move() and not board.is_game_over():
            self.run_engine_move()

    def run_engine_move(self) -> None:
        """Have the engine play one move (Live mode only)."""
        if self.is_replaying:
            return
        if not self.engine.is_engine_to_move():
            return

        move = self.engine.pick_move()
        if move is None:
            return
        self._apply_move_and_update_ui(move)

    # -----------------------
    # Replay actions (ply)
    # -----------------------
    def action_replay_prev(self) -> None:
        if self.ply_cursor > 0:
            self.ply_cursor -= 1
            self.footer.clear_message()
            self._sync_replay_view()

    def action_replay_next(self) -> None:
        if self.ply_cursor < len(self.moves):
            self.ply_cursor += 1
            self.footer.clear_message()
            self._sync_replay_view()

    # -----------------------
    # Replay actions (full move rows = 2 plies), with two-step snap when on odd ply
    # -----------------------
    @staticmethod
    def _row_start_ply(ply: int) -> int:
        """Return the start ply for the PGN row containing `ply` (even ply index)."""
        return ply - (ply % 2)

    def action_replay_prev_full(self) -> None:
        """Shift+Up: if odd ply, snap to row start; else go to previous row start."""
        if self.ply_cursor <= 0:
            return

        if self.ply_cursor % 2 == 1:
            self.ply_cursor = self._row_start_ply(self.ply_cursor)
            self.footer.clear_message()
            self._sync_replay_view()
            return

        self.ply_cursor = max(0, self.ply_cursor - 2)
        self.footer.clear_message()
        self._sync_replay_view()

    def action_replay_next_full(self) -> None:
        """Shift+Down: if odd ply, snap to row start (no advance); else advance one row."""
        if self.ply_cursor >= len(self.moves):
            return

        if self.ply_cursor % 2 == 1:
            self.ply_cursor = self._row_start_ply(self.ply_cursor)
            self.footer.clear_message()
            self._sync_replay_view()
            return

        self.ply_cursor = min(len(self.moves), self.ply_cursor + 2)
        self.footer.clear_message()
        self._sync_replay_view()

    def action_replay_start(self) -> None:
        self.ply_cursor = 0
        self.footer.clear_message()
        self._sync_replay_view()

    def action_replay_end(self) -> None:
        self.ply_cursor = len(self.moves)
        self.footer.clear_message()
        self._sync_replay_view()

    # -----------------------
    # PGN export
    # -----------------------
    def action_export_pgn(self) -> None:
        """Export the current mainline to ./game.pgn."""
        meta = PgnMetadata(white='Human', black='Engine')
        pgn_text = build_pgn(self.moves, starting_board=self.starting_board, metadata=meta)

        path = Path.cwd() / 'game.pgn'
        path.write_text(pgn_text, encoding='utf-8')
        self.footer.set_message(f'Exported PGN to {path}')


def main() -> None:
    """CLI entrypoint."""
    ChessApp().run()


if __name__ == '__main__':
    main()
