"""Move parsing/formatting helpers.

Key point: `python-chess` requires SAN to be computed *before* pushing the move,
because `board.san(move)` expects `move` to be legal in the current position.
"""

from __future__ import annotations

import chess


def mover_color_from_board_after_push(board: chess.Board) -> chess.Color:
    """Return the mover's color, given a board after a move was pushed.

    `python-chess` flips `board.turn` after pushing, so the mover is `not board.turn`.
    """
    return not board.turn


def san_for_legal_move(board: chess.Board, move: chess.Move) -> str:
    """Return SAN for a legal move in the current position.

    Args:
        board: Current board state (before pushing).
        move: A legal move in that position.

    Returns:
        SAN notation; falls back to UCI if SAN computation fails.
    """
    try:
        return board.san(move)
    except Exception:
        return move.uci()


def format_pgn_row(fullmove_number: int, white_san: str | None, black_san: str | None) -> str:
    """Format one PGN-style row.

    Examples:
        1. e4 e5
        2. Nf3
        3. ... c5   (edge case if viewing from a non-standard position)

    Args:
        fullmove_number: Move number, starting at 1.
        white_san: White's SAN for that move number.
        black_san: Black's SAN for that move number.

    Returns:
        A display string.
    """
    if white_san and black_san:
        return f'{fullmove_number}. {white_san} {black_san}'
    if white_san:
        return f'{fullmove_number}. {white_san}'
    if black_san:
        return f'{fullmove_number}. ... {black_san}'
    return f'{fullmove_number}.'
