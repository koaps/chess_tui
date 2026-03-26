"""Controllers for chess-tui."""

from __future__ import annotations

import random

import chess


class SimpleEngineController:
    """A tiny controller implementing a naive engine.

    Strategy:
    - Prefer capture moves
    - Otherwise choose a random legal move
    """

    def __init__(self, board: chess.Board, engine_side: chess.Color = chess.BLACK) -> None:
        """Create the controller.

        Args:
            board: Shared board instance (used by the app).
            engine_side: Color controlled by the engine.
        """
        self.board = board
        self.engine_side = engine_side

    def is_engine_to_move(self) -> bool:
        """Return True when it's the engine's turn."""
        return self.board.turn == self.engine_side

    def pick_move(self) -> chess.Move | None:
        """Pick a legal move.

        Returns:
            A capture if available; else a random legal move; or None if no legal moves.
        """
        legal = list(self.board.legal_moves)
        if not legal:
            return None

        captures = [m for m in legal if self.board.is_capture(m)]
        return random.choice(captures) if captures else random.choice(legal)
