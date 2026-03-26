import chess
import pytest

from chess_tui.replay import board_at_ply, last_move_for_ply


def test_board_at_ply_reconstructs_position() -> None:
    board = chess.Board()
    moves: list[chess.Move] = []
    for san in ['e4', 'e5', 'Nf3']:
        mv = board.parse_san(san)
        moves.append(mv)
        board.push(mv)

    b0 = board_at_ply(chess.Board(), moves, 0)
    assert b0.fen() == chess.Board().fen()

    b2 = board_at_ply(chess.Board(), moves, 2)
    assert b2.turn == chess.WHITE  # after e4 e5

    b3 = board_at_ply(chess.Board(), moves, 3)
    assert b3.turn == chess.BLACK  # after e4 e5 Nf3


def test_board_at_ply_out_of_range() -> None:
    board = chess.Board()
    mv = board.parse_san('e4')
    moves = [mv]

    with pytest.raises(ValueError):
        board_at_ply(chess.Board(), moves, -1)
    with pytest.raises(ValueError):
        board_at_ply(chess.Board(), moves, 2)


def test_last_move_for_ply() -> None:
    board = chess.Board()
    m1 = board.parse_san('e4')
    board.push(m1)
    m2 = board.parse_san('e5')
    moves = [m1, m2]

    assert last_move_for_ply(moves, 0) is None
    assert last_move_for_ply(moves, 1) == m1
    assert last_move_for_ply(moves, 2) == m2
