import chess

from chess_tui.controllers import SimpleEngineController


def test_engine_returns_none_when_no_legal_moves() -> None:
    board = chess.Board('7k/5Q2/7K/8/8/8/8/8 b - - 0 1')  # black checkmated
    engine = SimpleEngineController(board, chess.BLACK)
    assert engine.pick_move() is None


def test_engine_move_is_legal() -> None:
    board = chess.Board()
    engine = SimpleEngineController(board, chess.WHITE)
    move = engine.pick_move()
    assert move in board.legal_moves
