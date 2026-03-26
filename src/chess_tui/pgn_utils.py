"""PGN export helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import chess
import chess.pgn


@dataclass(frozen=True, slots=True)
class PgnMetadata:
    """Optional PGN headers for exported games."""

    event: str = 'chess-tui'
    site: str = 'local'
    white: str = 'Human'
    black: str = 'Engine'
    round: str = '1'


def build_pgn(
    moves: list[chess.Move],
    starting_board: chess.Board | None = None,
    metadata: PgnMetadata | None = None,
) -> str:
    """Build a PGN string from a mainline list of moves.

    Args:
        moves: Moves from the starting position.
        starting_board: Optional starting board; if non-standard, FEN will be included.
        metadata: Optional PGN header fields.

    Returns:
        PGN text for the game.
    """
    board = starting_board.copy(stack=False) if starting_board is not None else chess.Board()

    game = chess.pgn.Game()
    meta = metadata or PgnMetadata()

    game.headers['Event'] = meta.event
    game.headers['Site'] = meta.site
    game.headers['Date'] = datetime.now(timezone.utc).strftime('%Y.%m.%d')
    game.headers['Round'] = meta.round
    game.headers['White'] = meta.white
    game.headers['Black'] = meta.black

    if board.fen() != chess.Board().fen():
        game.setup(board)
        game.headers['SetUp'] = '1'
        game.headers['FEN'] = board.fen()

    node = game
    for mv in moves:
        node = node.add_variation(mv)
        board.push(mv)

    game.headers['Result'] = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else '*'
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)
