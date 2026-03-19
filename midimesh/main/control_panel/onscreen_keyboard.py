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



Copyright © 2026 Emergent Properly
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

'''

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.core.image import Image as CoreImage
from kivy.uix.slider import Slider

class OctaveButton(Widget):
    direction = NumericProperty(0)

    def __init__(self, direction, octave_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.octave_callback = octave_callback

        self.is_pressed = False

        self.normal_image = 'assets/flat_button_red.png'
        self.pressed_image = 'assets/flat_button_red_pressed.png'
        self.current_image = self.normal_image

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.draw_button()

    def draw_button(self):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(source=self.current_image, pos=self.pos, size=self.size)

    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.disabled:
            return False

        if self.collide_point(*touch.pos):
            self.is_pressed = True

            self.current_image = self.pressed_image
            self.draw_button()

            return True
        return False

    def on_touch_up(self, touch):
        if self.disabled:
            return False

        if self.is_pressed:
            self.is_pressed = False

            self.current_image = self.normal_image
            self.draw_button()

            if self.octave_callback:
                self.octave_callback(self.direction)

            return True

        return False

class OnScreenKey(Widget):
    note_value = NumericProperty(-1)

    def __init__(self, note_value, is_black=False, midi_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.note_value = note_value
        self.is_pressed = False
        self.is_black = is_black
        self.midi_callback = midi_callback

        if self.is_black:
            self.normal_image = 'assets/black-key.png'
            self.pressed_image = 'assets/black-key-pressed.png'
        else:
            self.normal_image = 'assets/white-key.png'
            self.pressed_image = 'assets/white-key-pressed.png'

        self.current_image = self.normal_image

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.draw_key()

    def draw_key(self):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(source=self.current_image, pos=self.pos, size=self.size)


    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


    def on_touch_down(self, touch):
        if self.disabled:
            return False

        if self.collide_point(*touch.pos):
            self.is_pressed = True
            self.current_image = self.pressed_image
            self.draw_key()

            if self.midi_callback:
                parent = self.parent
                velocity = getattr(parent, 'velocity_slider', None)
                vel_value = velocity.value if velocity else 64
                self.midi_callback('note_on', self.note_value, int(vel_value))
            return True
        return False

    def on_touch_up(self, touch):
        if self.disabled:
            return False

        if self.is_pressed:
            self.is_pressed = False
            self.current_image = self.normal_image
            self.draw_key()

            if self.midi_callback:
                self.midi_callback('note_off', self.note_value, 0)
            return True
        return False


class OnScreenKeyboard(Widget):
    current_octave = NumericProperty(4)
    bg_source = StringProperty('assets/onscreen_bg.png')
    def __init__(self, midi_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.midi_callback = midi_callback
        self.size_hint = (None, None)
        self.size = (840, 335)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            self.border = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=1.5
            )

        self.bind(pos=self.update_graphics,
                  size=self.update_graphics,
                  bg_source=self._load_bg_texture)

        self._load_bg_texture()
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.create_keyboard()

    def _load_bg_texture(self, *args):
        try:
            img = CoreImage(self.bg_source)
            self.bg_rect.texture = img.texture
        except Exception as exc:
            print(f"[OnScreenKeyboard] Could not load background image "
                  f"'{self.bg_source}': {exc}")
            self.bg_rect.texture = None


    def _create_velocity_slider(self):
        slider = Slider(
            orientation='vertical',
            background_vertical='',
            background_horizontal='',
            background_width=0,
            cursor_image='assets/node_mini_app_02.png',
            cursor_size=(80, 90),
            size_hint=(1, 1),
            size=(90, 335),
            pos=(self.x + 7, self.y - 7),
            value_track_color=(0, 0, 0, 0),
            border_vertical=(0, 0, 0, 0),
            min=0,
            max=127,
            value=64,
            padding=48,
        )
        self.velocity_slider = slider
        return slider

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.disabled:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.disabled:
            return False
        return super().on_touch_up(touch)

    def create_keyboard(self):
        self.clear_widgets()

        padding = 20
        white_key_size = (92, 300)
        black_key_size = (60, 200)

        note_defs = [
            (0, False, True), (2, False, True), (4, False, False),   # C, D, E
            (5, False, True), (7, False, True), (9, False, True), (11, False, False)  # F, G, A, B
        ]

        white_keys = []

        slider = self._create_velocity_slider()
        self.add_widget(slider)

        current_x = self.x + padding - 15 + white_key_size[0]
        for note_offset, _, _ in note_defs:
            note_val = (self.current_octave + 1) * 12 + note_offset
            key = OnScreenKey(
                note_value=note_val,
                is_black=False,
                midi_callback=self.send_midi,
                size=white_key_size,
                pos=(current_x + 2, self.y + padding - 2)
            )
            white_keys.append(key)
            current_x += white_key_size[0]

        oct_up = OctaveButton(
            direction=1,
            octave_callback=self.change_octave,
            size=(90, 150),
            pos=(self.x + self.width - 95,
                 self.y + self.height - 162)
        )

        self.add_widget(oct_up)

        oct_down = OctaveButton(
            direction=-1,
            octave_callback=self.change_octave,
            size=(90, 156),
            pos=(self.x + self.width - 95,
                 self.y + 16)
        )
        self.add_widget(oct_down)

        for key in white_keys:
            self.add_widget(key)

        black_keys = []
        white_note_keys = [k for k in white_keys if isinstance(k, OnScreenKey)]

        for i, key in enumerate(white_note_keys):
            note_offset, _, has_sharp = note_defs[i]
            if has_sharp:
                note_val = (self.current_octave + 1) * 12 + note_offset + 1
                black_key = OnScreenKey(
                    note_value=note_val,
                    is_black=True,
                    midi_callback=self.send_midi,
                    size=black_key_size,
                    pos=(key.right - black_key_size[0] / 2,
                         self.y + padding + (white_key_size[1] - black_key_size[1]))
                )
                black_keys.append(black_key)

        for key in black_keys:
            self.add_widget(key)

    def send_midi(self, message_type, note, velocity):
        if self.midi_callback:
            self.midi_callback(message_type, note, velocity)

    def change_octave(self, direction):
        self.current_octave = max(0, min(8, self.current_octave + direction))
        self.create_keyboard()

    def update_graphics(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)

        if hasattr(self, 'velocity_slider'):
            self.velocity_slider.pos = (
                self.x,
                self.y + (self.height - self.velocity_slider.height) / 2
            )

        self.create_keyboard()
