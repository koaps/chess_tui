"""Textual widgets used by chess-tui."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import chess
import chess.svg
from cairosvg import svg2png
from PIL import Image
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Input, Static
from textual_image.widget import Image as ImageWidget

from .moves import format_pgn_row


def board_image(board: chess.Board, last_move: Optional[chess.Move] = None, size: int = 512) -> Image.Image:
    """Render a board to a Pillow image."""
    svg = chess.svg.board(board=board, borders=True, lastmove=last_move, size=size)
    png = svg2png(
        bytestring=svg.encode('utf-8'),
        background_color='#202020',  # pick a dark neutral; adjust if desired
        output_height=size,
        output_width=size,
    )
    img = Image.open(io.BytesIO(png)).convert('RGBA')
    return img


@dataclass(slots=True)
class _MoveRow:
    """Internal model for one fullmove row (SAN only)."""

    number: int
    white: str | None = None
    black: str | None = None


class MoveHistory(VerticalScroll):
    """Scrollable PGN-style move history with replay highlighting."""

    def on_mount(self) -> None:
        # Using a nested container avoids ListView/ListItem requirements and reliably accumulates rows.
        self._rows: list[_MoveRow] = []
        self._row_widgets: list[Static] = []
        self._content = Vertical()
        self.mount(self._content)
        self._selected_row_index: int | None = None

    def add_san_ply(self, mover: chess.Color, san: str) -> None:
        """Add a SAN ply; pairs white/black into a single PGN row."""
        if mover == chess.WHITE:
            row = _MoveRow(number=len(self._rows) + 1, white=san, black=None)
            self._rows.append(row)
            widget = Static(Text(self._format_row(row)))
            self._row_widgets.append(widget)
            self._content.mount(widget)
        else:
            if not self._rows:
                # Edge case if starting from a position where black moves first.
                row = _MoveRow(number=1, white=None, black=san)
                self._rows.append(row)
                widget = Static(Text(self._format_row(row)))
                self._row_widgets.append(widget)
                self._content.mount(widget)
            else:
                row = self._rows[-1]
                row.black = san
                self._row_widgets[-1].update(self._format_row(row))

        self.scroll_end(animate=False)

    def set_cursor_ply(self, ply_index: int) -> None:
        """Highlight the row containing the given ply index."""
        if ply_index <= 0:
            self._set_selected_row(None)
            return

        row_index = (ply_index - 1) // 2
        if row_index < 0 or row_index >= len(self._row_widgets):
            self._set_selected_row(None)
            return

        self._set_selected_row(row_index)

    def _set_selected_row(self, row_index: int | None) -> None:
        if self._selected_row_index is not None and 0 <= self._selected_row_index < len(self._row_widgets):
            self._row_widgets[self._selected_row_index].remove_class('selected')

        self._selected_row_index = row_index

        if row_index is not None and 0 <= row_index < len(self._row_widgets):
            self._row_widgets[row_index].add_class('selected')
            self.scroll_to_widget(self._row_widgets[row_index], animate=False)

    @staticmethod
    def _format_row(row: _MoveRow) -> str:
        return format_pgn_row(row.number, row.white, row.black)


class FooterStatus(Static):
    """A simple footer/status bar.

    - `set_mode()` shows persistent state (Live/Replay, ply counts).
    - `set_message()` shows transient errors/info (illegal move, invalid input, export path).

    This widget overrides `render()` to always return a Rich `Text` renderable to satisfy
    Textual's rendering pipeline (avoids passing raw strings through the Visual system).
    """

    mode_text = reactive('')
    message_text = reactive('')

    def set_mode(self, text: str) -> None:
        """Set persistent mode/status text (left side)."""
        self.mode_text = text
        self.refresh()

    def set_message(self, text: str) -> None:
        """Set transient message text (right side)."""
        self.message_text = text
        self.refresh()

    def clear_message(self) -> None:
        """Clear transient message text."""
        self.message_text = ''
        self.refresh()

    def render(self) -> Text:
        """Render the footer as a Rich Text object."""
        left = self.mode_text.strip()
        right = self.message_text.strip()

        if left and right:
            return Text(f'{left}    |    {right}')
        return Text(left or right or '')


class ChessBoardWidget(Static):
    """Widget that renders the chess board and provides an input box for moves."""

    board = reactive(chess.Board())

    def compose(self) -> ComposeResult:
        with Vertical(id='board-container'):
            with Center(id='board-center'):
                yield ImageWidget(id='board-image')
            yield Input(placeholder='Type move (e2e4 or Nf3) and press Enter', id='cmd')

    def on_mount(self) -> None:
        self.refresh_image()
        try:
            self.app.set_focus(self.query_one(Input))
        except Exception:
            pass

    def refresh_image(self) -> None:
        """Re-render the board image and highlight the last move if present."""
        last_move = getattr(self, '_last_move', None)
        img = board_image(self.board, last_move)
        self.query_one(ImageWidget).image = img
