import chess

from chess_tui.moves import format_pgn_row, mover_color_from_board_after_push, san_for_legal_move


def test_san_for_legal_move_is_computed_before_push() -> None:
    board = chess.Board()
    move = board.parse_san('e4')
    assert san_for_legal_move(board, move) == 'e4'
    board.push(move)
    assert mover_color_from_board_after_push(board) == chess.WHITE


def test_format_pgn_row() -> None:
    assert format_pgn_row(1, 'e4', 'e5') == '1. e4 e5'
    assert format_pgn_row(2, 'Nf3', None) == '2. Nf3'
    assert format_pgn_row(3, None, 'c5') == '3. ... c5'
