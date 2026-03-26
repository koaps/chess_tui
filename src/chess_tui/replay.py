"""Replay helpers for stepping through a move list."""

from __future__ import annotations

import chess


def board_at_ply(starting_board: chess.Board, moves: list[chess.Move], ply_index: int) -> chess.Board:
    """Reconstruct a board at a given ply index.

    Args:
        starting_board: Initial board state.
        moves: Mainline moves from that initial state.
        ply_index: Number of plies to apply (0..len(moves)).

    Returns:
        A fresh board with the first `ply_index` moves applied.

    Raises:
        ValueError: If ply_index is out of range.
    """
    if ply_index < 0 or ply_index > len(moves):
        raise ValueError('ply_index out of range')

    b = starting_board.copy(stack=False)
    for mv in moves[:ply_index]:
        b.push(mv)
    return b


def last_move_for_ply(moves: list[chess.Move], ply_index: int) -> chess.Move | None:
    """Return the move that led to the position at ply_index (or None for ply 0)."""
    if ply_index <= 0 or ply_index > len(moves):
        return None
    return moves[ply_index - 1]
