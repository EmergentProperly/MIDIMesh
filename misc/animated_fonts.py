'''
                      .,,
                    l;:;c::
                   ,:o. d.O
                    c:c;c:'
       .c:::c.        0.k
      'o,c'l.k        0.x
      .x'c,c.d,       0.x
        ;;;:cc:l;     0.d         ;;;;:
              :l:cc.  O.x        k'c,:'x.
                'lc:lcx 0.  .;::c,.o'c;o'
                   d:.:,:,cllc:::;c;;;c'
                   ,o::.d.x;.
                   lc'loc.O.
              .,'cl;o, ..lc:o,'.
            :cc:c.ll      'x :,::;
            0.l .d,c      ,;o. o.k
            :cc;c:o        c;c:c:'
              ','            ...

'''

# Copyright (C) 2026 Emergent Properly
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import ListProperty

# List of animated font files to cycle through
ANIM_FONTS = [
    'assets/Handwrite-01.ttf',
    'assets/Handwrite-02.ttf',
    'assets/Handwrite-03.ttf',
]


class AnimatedLabel(Label):
    """
    A Label that automatically cycles through a list of font files.

    Parameters
    ----------
    font_list : list, optional
        List of font file paths. Defaults to ANIM_FONTS.
    animation_interval : float, optional
        Time in seconds between font changes. Defaults to 0.125.
    """

    font_list = ListProperty([])

    def __init__(self, font_list=None, animation_interval=0.125, **kwargs):
        super().__init__(**kwargs)

        self._anim_font_idx = 0
        self._anim_event = None
        self.animation_interval = animation_interval

        # Set font list (use provided or default)
        self.font_list = font_list if font_list is not None else ANIM_FONTS

        # Start animation if fonts are available
        if self.font_list:
            self._start_animation()

    def _start_animation(self):
        """Start the font cycling animation."""
        if self.font_list and not self._anim_event:
            self._anim_event = Clock.schedule_interval(self._animate_step, self.animation_interval)
            # Apply first font immediately
            self._apply_font()

    def _stop_animation(self):
        """Stop the font cycling animation."""
        if self._anim_event:
            self._anim_event.cancel()
            self._anim_event = None

    def _animate_step(self, dt):
        """Cycle to next font in list."""
        self._anim_font_idx = (self._anim_font_idx + 1) % len(self.font_list)
        self._apply_font()

    def _apply_font(self):
        """Apply current font from the list."""
        if self.font_list:
            try:
                self.font_name = self.font_list[self._anim_font_idx]
            except Exception:
                pass

    def on_font_list(self, instance, value):
        """Handle changes to the font list."""
        self._anim_font_idx = 0
        if value:
            self._start_animation()
        else:
            self._stop_animation()
