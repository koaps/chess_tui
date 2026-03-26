import chess

from chess_tui.pgn_utils import build_pgn


def test_build_pgn_contains_moves() -> None:
    board = chess.Board()
    moves: list[chess.Move] = []

    for san in ['e4', 'e5', 'Nf3', 'Nc6']:
        mv = board.parse_san(san)
        moves.append(mv)
        board.push(mv)

    pgn = build_pgn(moves)

    assert '1. e4 e5 2. Nf3 Nc6' in pgn
    assert '[Event ' in pgn
    assert '[Result ' in pgn
