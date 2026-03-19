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

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.graphics import Color, Ellipse, Line, InstructionGroup, Translate, Scale, PushMatrix, PopMatrix, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.image import Image
import math
from collections import deque
import random
from functools import partial
from kivy.config import Config
from kivy.core.text import LabelBase
from midimesh.main.control_panel.onscreen_minikeys import OnScreenKeyboards
from kivy.utils import platform
from kivy.logger import Logger

LabelBase.register(
    name='DSEG7Modern-Regular',
    fn_regular='assets/DSEG7Modern-Regular.ttf',
)

if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        Logger.info("MIDI: Successfully imported AndroidMidi backend.")
    except ImportError:
        Logger.error("MIDI: Could not import android_midi.py. MIDI will be disabled.")
        AndroidMidi = None

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import mido
        import mido.backends.rtmidi
        Logger.info("MIDI: Successfully imported WindowsMidi (aliased) and mido.")
    except ImportError:
        Logger.error("MIDI: Could not import windows_midi or mido.")
        AndroidMidi = None

else:
    try:
        import mido
        import mido.backends.rtmidi
        Logger.info("MIDI: Imported mido for Linux/Mac.")
    except ImportError:
        Logger.error("MIDI: mido not found.")
    AndroidMidi = None


NOTE_TO_HUE = {
    'C': 0.0, 'C#': 1/12.0, 'D': 2/12.0, 'D#': 3/12.0, 'E': 4/12.0, 'F': 5/12.0,
    'F#': 6/12.0, 'G': 7/12.0, 'G#': 8/12.0, 'A': 9/12.0, 'A#': 10/12.0, 'B': 11/12.0,
}

NOTE_TO_MIDI_OFFSET = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
}

SCALES = {
    'MAJOR': [0, 2, 4, 5, 7, 9, 11],
    'MINOR': [0, 2, 3, 5, 7, 8, 10],
    'PENTATONIC\nMAJOR': [0, 2, 4, 7, 9],
    'PENTATONIC\nMINOR': [0, 3, 5, 7, 10],
    'BLUES': [0, 3, 5, 6, 7, 10],
    'DORIAN': [0, 2, 3, 5, 7, 9, 10],
    'PHRYGIAN': [0, 1, 3, 5, 7, 8, 10],
    'PHRYGIAN\nDOMINANT': [0, 1, 3, 5, 7, 8, 11],
    'LYDIAN': [0, 2, 4, 6, 7, 9, 11],
    'MIXOLYDIAN': [0, 2, 4, 5, 7, 9, 10],
    'LOCRIAN': [0, 1, 3, 5, 6, 8, 10],
    'HARMONIC\nMINOR': [0, 2, 3, 5, 7, 8, 11],
    'HARMONIC\nMAJOR': [0, 2, 4, 5, 7, 8, 11],
    'MELODIC MINOR\n    (Ascending)': [0, 2, 3, 5, 7, 9, 11],
    'WHOLE TONE': [0, 2, 4, 6, 8, 10],
    'DIMINISHED\n(Half-Whole)': [0, 1, 3, 4, 6, 7, 9, 10],
    'DIMINISHED\n(Whole-Half)': [0, 2, 3, 5, 6, 8, 9, 11],
    'AUGMENTED': [0, 3, 4, 7, 8, 11],
    'ENIGMATIC': [0, 1, 4, 6, 8, 10, 11],
}

MIDI_OFFSET_TO_NOTE = {v: k for k, v in NOTE_TO_MIDI_OFFSET.items()}
ARPEGGIO_INDICES = [0, 2, 4, 6, 1, 3, 5]

kivy.require('2.0.0')

class FitLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(
                pos=self.pos,
                size=self.size,
            )
        self.bind(size=self._update_bg, pos=self._update_bg)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def do_layout(self, *largs):
        if not self.children:
            return

        content = self.children[0]
        content_width, content_height = content.size

        if not content_width or not content_height or not self.width or not self.height:
            return

        scale_x = self.width / content_width
        scale_y = self.height / content_height
        scale = min(scale_x, scale_y)
        scaled_width = content_width * scale
        scaled_height = content_height * scale
        new_pos_x = self.x + (self.width - scaled_width) / 2.0
        new_pos_y = self.y + (self.height - scaled_height) / 2.0
        epsilon = 1e-6


        if (abs(content.scale - scale) > epsilon or
            abs(content.pos[0] - new_pos_x) > epsilon or
            abs(content.pos[1] - new_pos_y) > epsilon):
            content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

KV_STRING = """
#:kivy 2.0.0

<SequencerStep@ToggleButton>:
    text: ''
    background_normal: 'assets/node_purple.png' if not self.is_active else ('assets/node_purple.png' if self.state != 'down' else 'assets/node.png')
    background_down: 'assets/node.png'
    background_color: (1, 1, 1, 1)

<SequencerStep>:
    text: ''
    background_normal: 'assets/node_purple.png'
    background_down: 'assets/node.png'
    background_color: (1, 1, 1, 1) # Use a white color tint
    border: (0, 0, 0, 0) # Remove border lines


<MenuLayout>:
    orientation: 'vertical'
    padding: '20px'
    spacing: '20px' # Reduced spacing

    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)  # Draw with no tint
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'assets/panel_shapes_01.png'

    Widget:
        size_hint_y: 1

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        spacing: '40px'
        height: self.minimum_height # Make height dynamic

        Label:
            text: 'MIDI CHANNEL PER LEVEL'
            font_size: '36px'
            size_hint: (None, None)
            pos_hint: {'center_x': 0.5}
            height: self.texture_size[1]

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {'center_x': 0.5}
            spacing: '20px'

            BoxLayout:
                orientation: 'horizontal'
                size_hint: (None, None) # Use fixed width/height
                width: '1870px'
                height: '100px'
                spacing: '52px'

                Label:
                    id: midi_ch_1
                    text: str(root.midi_channels[0])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_2
                    text: str(root.midi_channels[1])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_3
                    text: str(root.midi_channels[2])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_4
                    text: str(root.midi_channels[3])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_5
                    text: str(root.midi_channels[4])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_6
                    text: str(root.midi_channels[5])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_7
                    text: str(root.midi_channels[6])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_8
                    text: str(root.midi_channels[7])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_9
                    text: str(root.midi_channels[8])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1
                Label:
                    id: midi_ch_10
                    text: str(root.midi_channels[9])
                    font_name: 'DSEG7Modern-Regular'
                    font_size: '56px'
                    valign: 'center'
                    halign: 'right'
                    text_size: self.size
                    color: 1, 0, 0.2, 1

            BoxLayout:
                orientation: 'horizontal'
                size_hint: (None, None) # Use fixed width/height
                width: '1880px'
                height: '100px'
                spacing: '72px'
                padding: (15,20)
                pos_hint: {'center_x': 0.501}

                Button:
                    text: 'L1'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(0)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L2'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(1)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L3'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(2)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L4'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(3)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L5'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(4)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L6'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(5)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L7'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(6)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L8'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(7)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L9'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(8)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'
                Button:
                    text: 'L10'
                    color: 0, 0, 0, 1
                    font_size: '36px'
                    on_press: root.increment_midi_channel(9)
                    background_normal: 'assets/spinner_pressed.png'
                    background_down: 'assets/spinner_default.png'



    Widget:
        size_hint_y: None
        height: '20px' # MODIFIED: Was size_hint_y: 0.1

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '500px'
        spacing: '10px'
        padding: '10px'

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: scale_slider
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                min: 0
                max: len(root.scales_names) - 1
                value: 0
                step: 1
                on_value: scale_label.text = root.scales_names[int(self.value)]
            Label:
                text: 'Scale'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: scale_label
                text: root.scales_names[int(scale_slider.value)]
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: num_notes_slider
                min: 1
                max: 5
                value: 3
                step: 1
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: num_notes_label.text = str(int(self.value))
            Label:
                text: 'Bunch Size'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: num_notes_label
                text: str(int(num_notes_slider.value))
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: max_levels_slider
                min: 1
                max: 10
                value: 5
                step: 1
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: max_levels_label.text = str(int(self.value))
            Label:
                text: 'Bunch Levels'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: max_levels_label
                text: str(int(max_levels_slider.value))
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: length_slider
                min: 0.0
                max: 1000.0
                value: 50.0
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: length_label.text = str(int(self.value))
            Label:
                text: 'Stem Length'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: length_label
                text: str(int(length_slider.value))
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: angle_slider
                min: 0.0
                max: 360.0
                value: 45.0
                step: 1.0
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: angle_label.text = str(int(self.value))
            Label:
                text: 'Stem Angle'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: angle_label
                text: str(int(angle_slider.value))
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: pattern_length_slider
                min: 8
                max: 32
                value: 32
                step: 1
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: pattern_length_label.text = str(int(self.value))
            Label:
                text: 'Pattern Length'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: pattern_length_label
                text: str(int(pattern_length_slider.value))
                font_size: '30px'
                size_hint_y: None

        BoxLayout:
            orientation: 'vertical'
            spacing: '30px'
            Slider:
                id: propagation_mode_slider # New ID
                min: 0
                max: len(root.propagation_mode_names) - 1
                value: 0 # 'Cycle Levels'
                step: 1
                background_vertical: 'assets/single_slider_bg_vertical.png'
                border_vertical: (0, 0, 0, 0)
                background_width: 40
                orientation: 'vertical'
                value_track_color: (0, 0, 0, 0)
                cursor_image: 'assets/node_mini_app.png'
                cursor_size: (100, 100)
                on_value: propagation_mode_label.text = root.propagation_mode_names[int(self.value)]
            Label:
                text: 'Order'
                font_size: '36px'
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                id: propagation_mode_label
                text: root.propagation_mode_names[int(propagation_mode_slider.value)]
                font_size: '30px'
                size_hint_y: None


    BoxLayout:
        orientation: 'horizontal'
        spacing: '20px'
        size_hint_y: None
        height: '150px'
        Button:
            text: 'START'
            font_size: '36px'
            size_hint_y: None
            height: '100px'
            background_normal: 'assets/spinner_pressed_green.png'
            background_down: 'assets/spinner_default_green.png'
            on_press: root.app.start_game()

        Button:
            text: 'BACK'
            font_size: '36px'
            size_hint_y: None
            height: '100px'
            background_normal: 'assets/spinner_pressed.png'
            background_down: 'assets/spinner_default.png'
            on_press: root.go_to_goodies_menu()


<MenuScreen>:
    menu_layout: menu_layout_id # Link to ObjectProperty
    FitLayout:
        ScatterLayout:
            size_hint: (None, None)
            size: (1920, 1080) # Virtual 16:9 resolution
            do_rotation: False
            do_translation: False
            do_scale: False
            auto_bring_to_front: False


            MenuLayout:
                id: menu_layout_id # The actual menu content
                app: root.app

<GameScreen>:
    game_canvas: game_canvas_id
    playable_keyboard: playable_keyboard_id
    sequencer_grid: sequencer_grid_id
    tap_label: tap_label_id
    bottom_controls: bottom_controls_id



    FitLayout:
        ScatterLayout:
            size_hint: (None, None)
            size: (1920, 1080) # Virtual 16:9 resolution
            do_rotation: False
            do_translation: False
            do_scale: False
            auto_bring_to_front: False

            GameCanvas:
                id: game_canvas_id
                app: root.app
                game_screen: root # Pass a reference to the GameScreen 'root'

            Image:
                source: 'assets/panel_square_02.png'
                size_hint: (0.475, 1.0) # Fill left 47.5% of the screen
                pos_hint: {'x': 0, 'top': 1} # Align top-left
                allow_stretch: True
                keep_ratio: False # Stretch to fill the area

            GridLayout:
                id: sequencer_grid_id
                cols: 8
                rows: 4
                pos_hint: {'top': 1}
                size_hint: (0.475, 0.435)
                height: '480px'
                padding: '20px'
                spacing: '2px'


            Button:
                text: ''
                pos: ('1780', '940')
                size_hint: (None, None)
                size: ('120px', '120px')
                background_normal: 'assets/back_normal.png'
                background_down: 'assets/back_pressed.png'
                on_press:
                    game_canvas_id.stop_animation()
                    root.manager.current = 'menu' # WAS: app.root.current = 'menu'

            OnScreenKeyboards:
                id: playable_keyboard_id
                pos: (38, 38)


            Widget:
                size_hint_x: 1

            Label:
                id: tap_label_id
                text: ''
                font_size: '30px'
                size: (200,100)
                pos_hint: {'center_x': 0.75, 'center_y': 0.5}

            BoxLayout:
                id: bottom_controls_id
                orientation: 'vertical'
                size_hint: (0.475, 0.135)
                height: self.minimum_height
                pos: (20, 420)
                padding: (20,0)
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 0
                    Rectangle:
                        pos: self.pos
                        size: self.size

                BoxLayout:
                    id: game_controls
                    orientation: 'horizontal'
                    size_hint: (1, 1)
                    spacing: '30px'

                    Button:
                        text: 'STOP'
                        background_normal: 'assets/spinner_pressed.png'
                        background_down: 'assets/spinner_default.png'
                        font_size: '30px'
                        size_hint_x: 0.2
                        on_press: game_canvas_id.stop_animation() # Use ID


                    BoxLayout:
                        orientation: 'horizontal'
                        padding: (0,0)
                        spacing: '10px'
                        Slider:
                            id: game_tempo_slider
                            min: 60
                            max: 200
                            padding: '40px'
                            size_hint_x: 0.3
                            background_horizontal: 'assets/single_slider_bg.png'
                            border_horizontal: (0, 0, 0, 0)
                            background_width: 40
                            orientation: 'horizontal'
                            value_track_color: (0, 0, 0, 0)
                            cursor_image: 'assets/node_mini_app.png'
                            cursor_size: (100, 100)
                            value: root.game_canvas.tempo # Bind to game_canvas property
                            step: 1
                            on_value:
                                root.game_canvas.tempo = self.value # This triggers on_tempo
                                game_tempo_label.text = f"{int(self.value)}"
                        Label:
                            id: game_tempo_label
                            text: f"{int(game_tempo_slider.value)}"
                            size_hint_x: 0.1
                            font_name: 'DSEG7Modern-Regular'
                            font_size: '42px'
                            valign: 'center'
                            halign: 'right'
                            text_size: self.size
                            color: 1, 0, 0.2, 1
                            height: self.texture_size[1]
                            padding: (0, 0, 53, 30)





<RootManager>:
    MenuScreen:
        name: 'menu'
        app: root.app
    GameScreen:
        name: 'game'
        app: root.app
"""

class SequencerStep(ToggleButton):
    playhead_active = BooleanProperty(False)
    is_active = BooleanProperty(True)

    def on_is_active(self, instance, value):
        self.disabled = not value
        if not value:
            self.state = 'normal'

    def on_playhead_active(self, instance, value):
        self.canvas.after.clear()
        if value:
            with self.canvas.after:
                Color(0.8, 0.1, 0.1, 1)
                Line(rectangle=(self.x+1, self.y+1, self.width-2, self.height-2), width=2.0)

class MenuLayout(BoxLayout):
    midi_channels = ListProperty([1] * 10)
    app = ObjectProperty(None)
    scales_names = ListProperty(list(SCALES.keys()))
    propagation_mode_names = ListProperty(['Cycle Levels', 'Level by Level', 'Deep Dive', 'Random', 'Spiralling Out'])

    def increment_midi_channel(self, level_index):
        if 0 <= level_index < 10:
            current_channel = self.midi_channels[level_index]
            new_channel = (current_channel % 16) + 1
            self.midi_channels[level_index] = new_channel
            self.ids[f'midi_ch_{level_index + 1}'].text = str(new_channel)

    def go_to_goodies_menu(self):
        if self.app:
            self.app.go_to_goodies_menu()



class MenuScreen(Screen):
    menu_layout = ObjectProperty(None)
    app = ObjectProperty(None)

class GameCanvas(Widget):
    app = ObjectProperty(None)
    game_screen = ObjectProperty(None)

    tempo = NumericProperty(120.0)
    length_mult = NumericProperty(50.0)
    angle_deg = NumericProperty(45.0)
    notes = ListProperty([])
    propagation_mode = StringProperty('Cycle Levels')
    max_levels = NumericProperty(5)
    scale_factor = NumericProperty(0.7)
    scale_mode = StringProperty('Major')
    num_notes = NumericProperty(3)
    root_note_offset = NumericProperty(0)
    processor_function = ObjectProperty(None, allownone=True)
    base_step_time = NumericProperty(0.0)
    last_task_level = NumericProperty(1)
    midi_port = ObjectProperty(None, allownone=True)
    level_midi_channels = ListProperty([1] * 10)
    base_octave = NumericProperty(3)
    draw_queue = ObjectProperty(None)
    level_queues = ListProperty([])
    draw_timer = ObjectProperty(None, allownone=True)
    current_level_turn = NumericProperty(0)
    current_spiral_level = NumericProperty(0)
    global_step_counter = NumericProperty(0)
    _total_tasks_remaining = 0
    scale = NumericProperty(1.0)
    translate_x = NumericProperty(0.0)
    translate_y = NumericProperty(0.0)
    tap_move_threshold = NumericProperty(10)
    sequencer_step = NumericProperty(0)
    sequencer_steps = ListProperty([])
    pattern_length = NumericProperty(32)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touches = []
        self.line_group = InstructionGroup()
        self.circle_group = InstructionGroup()
        self.world_canvas = InstructionGroup()
        self.world_canvas.add(self.line_group)
        self.world_canvas.add(self.circle_group)
        self.transform_group = InstructionGroup()
        with self.canvas:
            PushMatrix()
            self.canvas.add(self.transform_group)
            self.canvas.add(self.world_canvas)
            PopMatrix()
        self.bind(scale=self._update_transform,
                  translate_x=self._update_transform,
                  translate_y=self._update_transform)
        self._update_transform()
        self.on_tempo(self, self.tempo)

    def on_tempo(self, instance, value):
        self.base_step_time = (60.0 / value) / 4.0

    def _update_transform(self, *args):
        self.transform_group.clear()
        self.transform_group.add(Translate(self.translate_x, self.translate_y))
        self.transform_group.add(Scale(self.scale, self.scale, self.scale))

    def zoom_at(self, factor, point):
        new_scale = self.scale * factor
        if not (0.1 <= new_scale <= 20.0):
             return

        lx, ly = point

        scale_factor = new_scale / self.scale

        self.translate_x = lx * (1.0 - scale_factor) + self.translate_x * scale_factor
        self.translate_y = ly * (1.0 - scale_factor) + self.translate_y * scale_factor
        self.scale = new_scale

    def get_midi_note(self, note_name, level):
        offset = NOTE_TO_MIDI_OFFSET.get(note_name, 0)
        note_number = (self.base_octave + (level - 1)) * 12 + offset
        return max(0, min(127, note_number))

    def change_octave(self, amount):
        new_octave = self.base_octave + amount
        if -4 <= new_octave <= 4:
            self.base_octave = new_octave
            print(f"Base octave set to: {self.base_octave}")
        else:
            print(f"Octave change rejected. Would be {new_octave}, but must be 0-8.")

    def play_midi_note(self, note_number, velocity, duration, level):
        if not self.midi_port:
            return

        channel_index = (level - 1) % 10
        channel = self.level_midi_channels[channel_index] - 1 # 0-15

        try:
            msg_on_bytes = [0x90 | channel, note_number, velocity]
            if platform in ('android', 'win') and hasattr(self.midi_port, 'send_message'):
                 self.midi_port.send_message(msg_on_bytes)
            else:
                if hasattr(self.midi_port, 'send'):
                    msg_on = mido.Message.from_bytes(msg_on_bytes)
                    self.midi_port.send(msg_on)
                elif hasattr(self.midi_port, 'send_message'): # rtmidi fallback
                    self.midi_port.send_message(msg_on_bytes)

            callback = partial(self._send_note_off, note_number=note_number, channel=channel)
            Clock.schedule_once(callback, duration)
        except Exception as e:
            print(f"Error sending MIDI message: {e}")

    def _send_note_off(self, dt, note_number, channel):
        if self.midi_port:
            try:
                msg_off_bytes = [0x80 | channel, note_number, 0]
                if platform in ('android', 'win') and hasattr(self.midi_port, 'send_message'):
                    self.midi_port.send_message(msg_off_bytes)
                else:
                    if hasattr(self.midi_port, 'send'):
                        msg_off = mido.Message.from_bytes(msg_off_bytes)
                        self.midi_port.send(msg_off)
                    elif hasattr(self.midi_port, 'send_message'):
                        self.midi_port.send_message(msg_off_bytes)

            except Exception as e:
                print(f"Error sending MIDI note_off: {e}")

    def stop_animation(self):
        print("Stopping animation...")
        if self.draw_timer:
            self.draw_timer.cancel()
            self.draw_timer = None

        Animation.stop_all(self, 'pos', 'size', 'r', 'g', 'b', 'a')

        if self.sequencer_steps:
            try:
                self.sequencer_steps[self.sequencer_step].playhead_active = False
            except IndexError:
                pass
        self.sequencer_step = 0

        if self.midi_port:
            print("Sending All Notes Off.")
            for channel in range(16):
                try:
                    msg_all_off_bytes = [0xB0 | channel, 123, 0]
                    if platform == 'android':
                        self.midi_port.send_message(msg_all_off_bytes)
                    else:
                        if hasattr(self.midi_port, 'send_message'):
                            self.midi_port.send_message(msg_all_off_bytes)
                        else:
                            msg_all_off = mido.Message.from_bytes(msg_all_off_bytes)
                            self.midi_port.send(msg_all_off)
                except Exception as e:
                    print(f"Error sending MIDI all notes off: {e}")

        if self.game_screen and self.game_screen.tap_label:
             self.game_screen.tap_label.text = 'Tap to restart'

    def on_touch_down(self, touch):
        if not self.game_screen:
            return super().on_touch_down(touch)

        if self.game_screen.playable_keyboard.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.game_screen.bottom_controls.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if not self.collide_point(*touch.pos):
            return False

        if touch.is_mouse_scrolling:
            widget_pos = self.to_widget(*touch.pos) # Use to_widget, NOT to_local
            if touch.button == 'scrollup':
                self.zoom_at(1.1, widget_pos)
            elif touch.button == 'scrolldown':
                self.zoom_at(0.9, widget_pos)
            return True

        touch.grab(self)
        self.touches.append(touch)
        touch.ud['group'] = 'gestures'
        touch.ud['start_pos'] = touch.pos
        touch.ud['has_moved'] = False

        if len(self.touches) == 2:
            other = self.touches[0]
            touch.ud['initial_dist'] = math.dist(touch.pos, other.pos)
            touch.ud['initial_scale'] = self.scale
            other.ud['initial_dist'] = touch.ud['initial_dist']
            other.ud['initial_scale'] = self.scale
            initial_screen_mid_x = (touch.x + other.x) / 2
            initial_screen_mid_y = (touch.y + other.y) / 2
            initial_lx, initial_ly = self.to_widget(initial_screen_mid_x, initial_screen_mid_y)
            initial_wx = (initial_lx - self.translate_x) / self.scale
            initial_wy = (initial_ly - self.translate_y) / self.scale
            touch.ud['initial_wx'] = initial_wx
            touch.ud['initial_wy'] = initial_wy
            other.ud['initial_wx'] = initial_wx
            other.ud['initial_wy'] = initial_wy
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or 'group' not in touch.ud:
            return super().on_touch_move(touch)

        if not touch.ud.get('has_moved', False):
            distance = math.dist(touch.ud['start_pos'], touch.pos)
            if distance > self.tap_move_threshold:
                touch.ud['has_moved'] = True

        if len(self.touches) == 1:
            self.translate_x += touch.dx
            self.translate_y += touch.dy
        elif len(self.touches) == 2:
            other = self.touches[0] if self.touches[1] is touch else self.touches[1]
            initial_dist = touch.ud.get('initial_dist', 1)
            initial_scale = touch.ud.get('initial_scale', 1)
            initial_wx = touch.ud.get('initial_wx', 0)
            initial_wy = touch.ud.get('initial_wy', 0)

            if initial_dist == 0: return True
            new_dist = math.dist(touch.pos, other.pos)
            new_scale = initial_scale * (new_dist / initial_dist)
            new_scale = max(0.1, min(20.0, new_scale))
            new_screen_mid_x = (touch.x + other.x) / 2
            new_screen_mid_y = (touch.y + other.y) / 2
            new_lx, new_ly = self.to_widget(new_screen_mid_x, new_screen_mid_y)
            self.scale = new_scale
            self.translate_x = new_lx - (initial_wx * self.scale)
            self.translate_y = new_ly - (initial_wy * self.scale)

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self or 'group' not in touch.ud:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        if len(self.touches) == 1 and not touch.ud.get('has_moved', False):
            if self.game_screen and self.game_screen.tap_label.text:
                self.game_screen.tap_label.text = ''
            self.start_fractal()
        if touch in self.touches:
            self.touches.remove(touch)
        return True

    def _generate_scale(self):
        scale_intervals = SCALES.get(self.scale_mode, SCALES['MAJOR'])

        note_intervals = []
        for i in range(self.num_notes):
            scale_degree_index = ARPEGGIO_INDICES[i]
            if scale_degree_index >= len(scale_intervals):
                scale_degree_index = scale_degree_index % len(scale_intervals)
            note_intervals.append(scale_intervals[scale_degree_index])

        note_offsets = [(self.root_note_offset + interval) % 12 for interval in note_intervals]
        self.notes = [MIDI_OFFSET_TO_NOTE[offset] for offset in note_offsets]

        print_scale_name = self.scale_mode.replace('\n', ' ')
        print(f"Generated scale ({print_scale_name}, Root: {MIDI_OFFSET_TO_NOTE[self.root_note_offset]}): {self.notes}")

    def set_root_note(self, root_offset):
        print(f"Setting root note offset to: {root_offset} ({MIDI_OFFSET_TO_NOTE[root_offset]})")
        self.root_note_offset = root_offset

        if self.game_screen and self.game_screen.tap_label.text:
            self.game_screen.tap_label.text = ''
        if self.draw_timer:
            self._generate_scale()
        else:
            self.start_fractal()

    def start_fractal(self):
        if self.draw_timer:
            self.draw_timer.cancel()
            self.draw_timer = None
        Animation.stop_all(self, 'pos', 'size', 'r', 'g', 'b', 'a')

        self.line_group.clear()
        self.circle_group.clear()
        self.scale = 1.0
        self.translate_x = 0.0
        self.translate_y = 0.0
        self._generate_scale()

        print(f"--- Starting Fractal (Mode: {self.propagation_mode}, Levels: {self.max_levels}) ---")
        if self.midi_port:

            if platform != 'android':
                if hasattr(self.midi_port, 'name'):
                    print(f"MIDI Port: {self.midi_port.name}")
                else:
                     print(f"MIDI Port: rtmidi Output")
            else:
                print(f"MIDI Port: AndroidMidi")
        else:
            print("MIDI Port: None")
        print(f"MIDI Channel Assignments: {list(self.level_midi_channels)}")

        self._total_tasks_remaining = 0
        self.current_level_turn = 0
        self.processor_function = None
        self.global_step_counter = 0

        center_x = self.width / 1.35
        center_y = self.height / 2
        radius_0 = 50
        parent_center = (center_x, center_y)
        duration = 0.3
        flash_group_0 = InstructionGroup()
        flash_color_0 = Color(1, 1, 1, 1.0)
        flash_radius_0 = radius_0 + 5
        circle0_flash = Ellipse(
            pos=(center_x - flash_radius_0, center_y - flash_radius_0),
            size=(flash_radius_0 * 2, flash_radius_0 * 2)
        )
        flash_group_0.add(flash_color_0)
        flash_group_0.add(circle0_flash)
        self.circle_group.add(flash_group_0)
        fill_color_0 = Color(0, 0, 0, 1)
        final_radius_0 = radius_0
        circle0_fill = Ellipse(
            pos=(center_x - final_radius_0, center_y - final_radius_0),
            size=(final_radius_0 * 2, final_radius_0 * 2)
        )
        self.circle_group.add(fill_color_0)
        self.circle_group.add(circle0_fill)

        border_width_0 = 2.0
        border_color_0 = Color(1, 1, 1, 1.0)
        circle0_border = Line(
            circle=(center_x, center_y, final_radius_0),
            width=border_width_0
        )
        self.circle_group.add(border_color_0)
        self.circle_group.add(circle0_border)


        anim_color0_flash = Animation(a=0.0, duration=duration)
        final_pos_0 = (center_x - final_radius_0, center_y - final_radius_0)
        final_size_0 = (final_radius_0 * 2, final_radius_0 * 2)
        anim_ellipse0_flash = Animation(pos=final_pos_0, size=final_size_0, duration=duration)

        anim_color0_flash.start(flash_color_0)
        anim_ellipse0_flash.start(circle0_flash)
        Clock.schedule_once(lambda dt: self.circle_group.remove(flash_group_0), duration + 0.01)

        self.last_task_level = 1

        print(f"Tempo: {self.tempo}bpm, Step Time (16th): {self.base_step_time:.3f}s")
        if self.propagation_mode == 'Level by Level':
            self.draw_queue = deque()
            self.processor_function = self.process_breadth_first
            for i in range(len(self.notes)):
                task = (1, parent_center, radius_0, i)
                self.draw_queue.append(task)
                self._total_tasks_remaining += 1
        elif self.propagation_mode == 'Deep Dive':
            self.draw_queue = deque()
            self.processor_function = self.process_depth_first
            for i in reversed(range(len(self.notes))):
                task = (1, parent_center, radius_0, i)
                self.draw_queue.append(task)
                self._total_tasks_remaining += 1
        elif self.propagation_mode in ['Cycle Levels', 'Random', 'Spiralling Out']:
            self.level_queues = [deque() for _ in range(self.max_levels)]
            if self.propagation_mode == 'Cycle Levels':
                self.processor_function = self.process_cycle_levels
            elif self.propagation_mode == 'Random':
                self.processor_function = self.process_random
            elif self.propagation_mode == 'Spiralling Out':
                self.processor_function = self.process_spiral
                self.current_spiral_level = 0
            for i in range(len(self.notes)):
                task = (1, parent_center, radius_0, i)
                self.level_queues[0].append(task)
                self._total_tasks_remaining += 1

        self.sequencer_step = 0
        if self.sequencer_steps:
            try:
                self.sequencer_steps[0].playhead_active = True
            except IndexError:
                 print("WARNING: Sequencer steps not populated by GameScreen.")
        else:
            print("WARNING: Sequencer steps not populated by GameScreen.")
        if self.processor_function:
            self.draw_timer = Clock.schedule_once(self._step, self.base_step_time)
        else:
            print(f"Error: Unknown propagation mode '{self.propagation_mode}'")

    def _step(self, dt):
        if self._check_completion():
            return
        if not self.sequencer_steps:
            return
        try:
            current_widget = self.sequencer_steps[self.sequencer_step]
        except IndexError:
            print("Error: Sequencer step index out of range. Stopping.")
            self.stop_animation()
            return

        is_on = (current_widget.state == 'down')
        if is_on and self.processor_function:
            if self._total_tasks_remaining > 0:
                self.processor_function()
            else:
                if self._check_completion():
                    return
        current_widget.playhead_active = False
        self.sequencer_step = (self.sequencer_step + 1) % self.pattern_length
        self.sequencer_steps[self.sequencer_step].playhead_active = True
        next_step_time = self.base_step_time
        self.draw_timer = Clock.schedule_once(self._step, max(0.01, next_step_time))

    def _check_completion(self):
        if self._total_tasks_remaining <= 0:
            if self.draw_timer:
                self.draw_timer.cancel()
                self.draw_timer = None
            print(f"--- Animation Complete ({self.propagation_mode}) ---")
            if self.sequencer_steps:
                try:
                    self.sequencer_steps[self.sequencer_step].playhead_active = False
                except IndexError:
                    pass

            self.stop_animation()
            if self.game_screen and self.game_screen.tap_label:
                self.game_screen.tap_label.text = 'Tap to restart'
            return True
        return False

    def _draw_and_queue_children(self, task, add_to_queue_func):
        level, parent_center, parent_radius, note_index = task
        self.last_task_level = level

        if self.propagation_mode == 'Spiralling Out':
            note = self.notes[self.global_step_counter % len(self.notes)]
            self.global_step_counter += 1
        else:
            note = self.notes[note_index]

        base_hue = NOTE_TO_HUE.get(note, 0.0)
        saturation = 0.5
        max_b, min_b = 1.0, 0.6
        value = max_b - (level - 1) * (max_b - min_b) / (self.max_levels - 1) if self.max_levels > 1 else max_b
        main_color = Color(base_hue, saturation, value, mode='hsv')

        parent_cx, parent_cy = parent_center
        num_notes = len(self.notes)
        scale_factor = self.scale_factor
        spoke_length = self.length_mult * (scale_factor ** (level - 1))
        child_radius = parent_radius * scale_factor
        line_width = max(1, 2.0 * (scale_factor ** (level - 1)))

        base_angle_rad = math.radians(note_index * (360.0 / num_notes))
        base_x = parent_cx + parent_radius * math.cos(base_angle_rad)
        base_y = parent_cy + parent_radius * math.sin(base_angle_rad)

        spoke_angle_rad = base_angle_rad + math.radians(self.angle_deg)
        end_x = base_x + spoke_length * math.cos(spoke_angle_rad)
        end_y = base_y + spoke_length * math.sin(spoke_angle_rad)
        child_center = (end_x, end_y)

        self.line_group.add(Color(main_color.r, main_color.g, main_color.b, 0.5))
        self.line_group.add(Line(points=[base_x, base_y, end_x, end_y], width=line_width))

        final_radius = child_radius
        final_color = main_color
        duration = 0.3

        flash_group = InstructionGroup()
        flash_color = Color(1, 1, 1, 1.0)
        flash_radius = final_radius + 5
        circle_flash = Ellipse(
            pos=(end_x - flash_radius, end_y - flash_radius),
            size=(flash_radius * 2, flash_radius * 2)
        )
        flash_group.add(flash_color)
        flash_group.add(circle_flash)
        self.circle_group.add(flash_group)

        circle_fill_color_inst = Color(0, 0, 0, 1)
        circle_fill_inst = Ellipse(
            pos=(end_x - final_radius, end_y - final_radius),
            size=(final_radius * 2, final_radius * 2)
        )
        self.circle_group.add(circle_fill_color_inst)
        self.circle_group.add(circle_fill_inst)

        border_width = max(1.0, 1.5 * (scale_factor ** (level - 1)))
        border_color_inst = Color(final_color.r, final_color.g, final_color.b, 1.0)
        border_line_inst = Line(
            circle=(end_x, end_y, final_radius),
            width=border_width
        )
        self.circle_group.add(border_color_inst)
        self.circle_group.add(border_line_inst)

        anim_color_flash = Animation(a=0.0, duration=duration)
        final_pos = (end_x - final_radius, end_y - final_radius)
        final_size = (final_radius * 2, final_radius * 2)
        anim_ellipse_flash = Animation(pos=final_pos, size=final_size, duration=duration)

        anim_color_flash.start(flash_color)
        anim_ellipse_flash.start(circle_flash)

        Clock.schedule_once(lambda dt: self.circle_group.remove(flash_group), duration + 0.01)

        anim_color_border = Animation(r=final_color.r, g=final_color.g, b=final_color.b, duration=duration)
        anim_color_border.start(border_color_inst)

        base_velocity_float = 0.8
        release_factor = 0.8
        level_velocity_scale = max(0.0, 1.0 - (level - 1) * 0.20)
        velocity = int(base_velocity_float * level_velocity_scale * 127)
        if velocity == 0 and base_velocity_float > 0:
            velocity = 1

        note_duration = self.base_step_time * release_factor
        note_number = self.get_midi_note(note, level)
        channel_index = (level - 1) % 10

        self.play_midi_note(note_number, velocity, note_duration, level)

        self._total_tasks_remaining -= 1

        if level < self.max_levels:
            child_level = level + 1
            new_tasks = []
            for i in range(len(self.notes)):
                new_task = (child_level, child_center, child_radius, i)
                new_tasks.append(new_task)
            add_to_queue_func(new_tasks)
            self._total_tasks_remaining += len(new_tasks)

    def process_breadth_first(self):
        if not self.draw_queue: return
        task = self.draw_queue.popleft()
        def add_children(tasks):
            for t in tasks: self.draw_queue.append(t)
        self._draw_and_queue_children(task, add_children)

    def process_depth_first(self):
        if not self.draw_queue: return
        task = self.draw_queue.pop()
        def add_children(tasks):
            for t in reversed(tasks): self.draw_queue.append(t)
        self._draw_and_queue_children(task, add_children)

    def process_cycle_levels(self):
        task = None
        search_start_level = self.current_level_turn
        while True:
            queue = self.level_queues[self.current_level_turn]
            if queue:
                task = queue.popleft()
                self.current_level_turn = (self.current_level_turn + 1) % self.max_levels
                break
            else:
                self.current_level_turn = (self.current_level_turn + 1) % self.max_levels
                if self.current_level_turn == search_start_level:
                    return
        if not task: return
        def add_children(tasks):
            child_queue_index = task[0]
            for t in tasks: self.level_queues[child_queue_index].append(t)
        self._draw_and_queue_children(task, add_children)

    def process_random(self):
        non_empty_queues = [q for q in self.level_queues if q]
        if not non_empty_queues: return
        chosen_queue = random.choice(non_empty_queues)
        task = chosen_queue.popleft()
        def add_children(tasks):
            child_queue_index = task[0]
            for t in tasks: self.level_queues[child_queue_index].append(t)
        self._draw_and_queue_children(task, add_children)

    def reorder_level_queue(self, level_index):
        queue = self.level_queues[level_index]
        if not queue: return
        num_notes = len(self.notes)
        if num_notes <= 1: return
        num_tasks = len(queue)
        num_parents = num_tasks // num_notes
        if num_parents * num_notes != num_tasks:
            print(f"Warning: Level {level_index+1} task count ({num_tasks}) not divisible by note count ({num_notes}). Using BFS order for this level.")
            return
        original_tasks = list(queue)
        queue.clear()
        for i in range(num_notes):
            for j in range(num_parents):
                task = original_tasks[j * num_notes + i]
                queue.append(task)

    def process_spiral(self):
        queue = self.level_queues[self.current_spiral_level]
        if not queue:
            next_level = self.current_spiral_level + 1
            if next_level >= self.max_levels or not self.level_queues[next_level]:
                return
            self.reorder_level_queue(next_level)
            self.current_spiral_level = next_level
            queue = self.level_queues[self.current_spiral_level]
            if not queue:
                return
        task = queue.popleft()
        def add_children(tasks):
            child_queue_index = task[0]
            if child_queue_index < self.max_levels:
                for t in tasks:
                    self.level_queues[child_queue_index].append(t)
        self._draw_and_queue_children(task, add_children)

class GameScreen(Screen):
    game_canvas = ObjectProperty(None)
    playable_keyboard = ObjectProperty(None)
    sequencer_grid = ObjectProperty(None)
    tap_label = ObjectProperty(None)
    bottom_controls = ObjectProperty(None)
    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._populate_sequencer)

    def on_enter(self, *args):
        super().on_enter(*args)
        self.tap_label.text = '1. Program the sequencer \n\n 2. Select a key to grow the shape\n\n(or just tap the screen to show the first grape)'

        if self.playable_keyboard.midi_callback is None:
            self.playable_keyboard.midi_callback = self.handle_keyboard_press
        self.playable_keyboard.change_octave = self.game_canvas.change_octave
        if not self.sequencer_grid.children:
            Clock.schedule_once(self._set_active_steps)
            return
        self._set_active_steps()

    def handle_keyboard_press(self, message_type, note_value, velocity):
        if message_type == 'note_on':
            root_offset = note_value % 12
            self.game_canvas.set_root_note(root_offset)

    def _set_active_steps(self, dt=None):
        game_canvas = self.game_canvas
        grid = self.sequencer_grid
        if not grid.children:
            print("ERROR: _set_active_steps called but grid still empty.")
            return
        steps = list(reversed(grid.children))
        pat_len = game_canvas.pattern_length
        print(f"GameScreen: Setting active sequencer steps to {pat_len}")
        for i, step in enumerate(steps):
            step.is_active = (i < pat_len)
        game_canvas.sequencer_steps = steps

    def _populate_sequencer(self, dt):
        grid = self.sequencer_grid
        if not grid.children:
            print("Populating sequencer grid...")
            for i in range(32):
                step = SequencerStep()
                grid.add_widget(step)
            print(f"Added {len(grid.children)} sequencer steps.")

class RootManager(ScreenManager):
    pass

class _GrowingShapesWorld(RootManager):

    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        self.app_switcher = app_switcher
        self.main_midi_out = main_midi_out
        self.midi_port = self.main_midi_out
        self.app = self

        Builder.load_string(KV_STRING)

        super().__init__(**kwargs)

    def cleanup_app(self):
        print("GrowingShapes: Cleaning up...")
        try:
            game_canvas = self.get_screen('game').game_canvas
            if game_canvas:
                game_canvas.stop_animation()
        except Exception as e:
            print(f"GrowingShapes: Error stopping game canvas: {e}")

        self.current = 'menu'

    def go_to_goodies_menu(self):
        self.cleanup_app()
        self.app_switcher('goodies_menu')

    def start_game(self):
        print("Gathering settings...")
        menu_layout = self.get_screen('menu').menu_layout
        length = menu_layout.ids.length_slider.value
        angle = menu_layout.ids.angle_slider.value
        max_levels = menu_layout.ids.max_levels_slider.value
        pattern_length = menu_layout.ids.pattern_length_slider.value
        midi_channels = list(menu_layout.midi_channels)

        propagation_slider_val = int(menu_layout.ids.propagation_mode_slider.value)
        mode = menu_layout.propagation_mode_names[propagation_slider_val]

        slider_index = int(menu_layout.ids.scale_slider.value)
        scale_mode = menu_layout.scales_names[slider_index]
        num_notes = menu_layout.ids.num_notes_slider.value

        game_canvas = self.get_screen('game').game_canvas
        game_canvas.length_mult = length
        game_canvas.angle_deg = angle
        game_canvas.max_levels = int(max_levels)
        game_canvas.pattern_length = int(pattern_length)
        game_canvas.propagation_mode = mode
        game_canvas.midi_port = self.main_midi_out
        game_canvas.level_midi_channels = midi_channels
        game_canvas.scale_mode = scale_mode
        game_canvas.num_notes = int(num_notes)
        game_canvas.root_note_offset = 0
        self.current = 'game'

class GrowingShapesRoot(FitLayout):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )

        self.shapes_world = _GrowingShapesWorld(
            app_switcher=app_switcher,
            main_midi_out=main_midi_out
        )

        self.scatter.add_widget(self.shapes_world)

        self.splash_image = Image(
            source='assets/g_shape_splash.png',
            size_hint=(None, None),
            size=(1920, 1080),
            allow_stretch=True,
            keep_ratio=False
        )
        self.scatter.add_widget(self.splash_image)
        Clock.schedule_once(self.remove_splash, 3)
        self.add_widget(self.scatter)

    def remove_splash(self, dt):

        if self.splash_image:
            if self.splash_image.parent:
                self.splash_image.parent.remove_widget(self.splash_image)
            self.splash_image = None
            print("Splash screen removed.")

    def cleanup_app(self):
        self.shapes_world.cleanup_app()
