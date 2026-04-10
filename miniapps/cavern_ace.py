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

import random
import os
import math
import time
from kivy.vector import Vector
from kivy.app import App
from kivy.utils import platform
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Triangle, Rectangle, Mesh
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty, ObjectProperty
from kivy.resources import resource_add_path


try:
    import rtmidi
except ImportError:
    rtmidi = None

if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("CavernAce: Using AndroidMidi backend.")
    except ImportError:
        print("CavernAce: Could not import AndroidMidi.")
        AndroidMidi = None

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi

        import rtmidi
        print("CavernAce: Using WindowsMidi backend (aliased).")
    except ImportError:
        print("CavernAce: Could not import WindowsMidi or rtmidi.")
        AndroidMidi = None

else:
    print("CavernAce: Using rtmidi backend (if available).")
    AndroidMidi = None

class MidiWrapper:
    def __init__(self, external_midi_port=None):
        self.android_midi = None
        self.rt_midi_out = None
        self.external_midi = external_midi_port
        self.is_android = (platform in ('android', 'win'))

        if self.external_midi:
            print("MIDI: Using external/shared port.")

        elif self.is_android and AndroidMidi:
            try:
                print(f"MIDI: Initializing wrapper backend ({platform})...")
                self.android_midi = AndroidMidi()
                if hasattr(self.android_midi, 'open_output'):
                    self.android_midi.open_output()

                if platform == 'win' and hasattr(self.android_midi, 'get_host_devices'):
                    devs = self.android_midi.get_host_devices()
                    if devs:
                        print(f"MIDI: Auto-connecting to {devs[0][0]}")
                        self.android_midi.connect_to_device(devs[0][1])
            except Exception as e:
                print(f"MIDI Wrapper Error: {e}")

        else:
            try:
                if rtmidi:
                    self.rt_midi_out = rtmidi.MidiOut()
                    available_ports = self.rt_midi_out.get_ports()
                    if available_ports:
                        self.rt_midi_out.open_port(0)
                        print(f"MIDI: Opened output port 0: {available_ports[0]}")
                    else:
                        self.rt_midi_out.open_virtual_port("CavernAce Virtual")
                        print("MIDI: Opened virtual output port.")
                else:
                    print("MIDI WARNING: 'python-rtmidi' not installed. No sound.")
            except Exception as e:
                print(f"MIDI rtmidi Error: {e}")

    def send_note_on(self, note, velocity=100, channel=0):
        if not (0 <= note <= 127): return
        msg = [0x90 + channel, int(note), int(velocity)]

        if self.external_midi:
            self.external_midi.send_message(msg)
        elif self.is_android and self.android_midi:
            self.android_midi.send_message(msg)
        elif self.rt_midi_out:
            self.rt_midi_out.send_message(msg)

    def send_note_off(self, note, channel=0):
        if not (0 <= note <= 127): return
        msg = [0x80 + channel, int(note), 0]

        if self.external_midi:
            self.external_midi.send_message(msg)
        elif self.is_android and self.android_midi:
            self.android_midi.send_message(msg)
        elif self.rt_midi_out:
            self.rt_midi_out.send_message(msg)

    def close(self):
        if self.is_android and self.android_midi:
            self.android_midi.close()
        elif self.rt_midi_out:
            pass

SCALE_INTERVALS = {
    'MAJOR': [0, 2, 4, 5, 7, 9, 11],
    'MINOR': [0, 2, 3, 5, 7, 8, 10],
    'PENTA M.': [0, 2, 4, 7, 9],
    'PENTA m.': [0, 3, 5, 7, 10],
    'BLUES': [0, 3, 5, 6, 7, 10],
    'DORIAN': [0, 2, 3, 5, 7, 9, 10],
    'PHRYGIAN': [0, 1, 3, 5, 7, 8, 10],
    'PHRYGIAN\nDOM': [0, 1, 3, 5, 7, 8, 11],
    'LYDIAN': [0, 2, 4, 6, 7, 9, 11],
    'MIXOLYDIAN': [0, 2, 4, 5, 7, 9, 10],
    'LOCRIAN': [0, 1, 3, 5, 6, 8, 10],
    'HARMONIC Major': [0, 2, 3, 5, 7, 8, 11],
    'HARMONIC Minor': [0, 2, 4, 5, 7, 8, 11],
    'MELODIC Minor(^)': [0, 2, 3, 5, 7, 9, 11],
    'WHOLE TONE': [0, 2, 4, 6, 8, 10],
    'DIMINISHED\n(0.5-1)': [0, 1, 3, 4, 6, 7, 9, 10],
    'DIMINISHED\n(1-0.5)': [0, 2, 3, 5, 6, 8, 9, 11],
    'AUGMENTED': [0, 3, 4, 7, 8, 11],
    'ENIGMATIC': [0, 1, 4, 6, 8, 10, 11],
}

ROOT_NOTES = {
    "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
    "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
}

class MusicEngine:
    def __init__(self, external_midi_port=None):
        self.midi = MidiWrapper(external_midi_port)
        self.bpm = 120
        self.root_note = 60
        self.scale_name = "MAJOR"
        self.current_scale_notes = []
        self.arp2_len = 8
        self.arp2_type = "Down"
        self.chan_move = 0
        self.chan_fire = 1
        self.chan_impact = 2
        self.chan_alien = 3
        self.accumulated_time = 0.0
        self.seconds_per_beat = 0.5
        self.global_step_counter = 0
        self.arp2_index = 0
        self.active_notes = {}
        self.update_scale_notes()

    def update_settings(self, scale_idx, key_idx, bpm, a2_len, a2_type_idx,
                        c_move, c_fire, c_imp, c_alien):
        scale_names = list(SCALE_INTERVALS.keys())
        key_names = list(ROOT_NOTES.keys())
        arp_types = ["UP", "DOWN", "UP/DOWN", "RANDOM", "ALTERNATING"]
        self.scale_name = scale_names[scale_idx]
        self.root_note = ROOT_NOTES[key_names[key_idx]]
        self.bpm = bpm
        self.arp2_len = int(a2_len)
        self.arp2_type = arp_types[a2_type_idx]
        self.chan_move = int(c_move)
        self.chan_fire = int(c_fire)
        self.chan_impact = int(c_imp)
        self.chan_alien = int(c_alien)
        self.seconds_per_beat = (60.0 / self.bpm) / 4.0
        self.update_scale_notes()
        print(f"Music Engine Updated: {self.scale_name} in {key_names[key_idx]} @ {self.bpm} BPM")

    def update_scale_notes(self):
        intervals = SCALE_INTERVALS[self.scale_name]
        self.current_scale_notes = []
        base_root = self.root_note - 12
        for octave in range(4):
            for interval in intervals:
                note = base_root + (octave * 12) + interval
                if 0 <= note <= 127:
                    self.current_scale_notes.append(note)
        self.current_scale_notes.sort()

    def get_arp_note(self, length, index, pattern_type):
        center_idx = len(self.current_scale_notes) // 2
        offset = 0
        step = index % length
        if pattern_type == "UP": offset = step
        elif pattern_type == "DOWN": offset = length - 1 - step
        elif pattern_type == "UP/DOWN":
            eff_len = (length * 2) - 2
            phase = index % eff_len
            if phase < length: offset = phase
            else: offset = length - 1 - (phase - length + 1)
        elif pattern_type == "RANDOM": offset = random.randint(0, length - 1)
        elif pattern_type == "ALTERNATING": offset = step if (step % 2 == 0) else -step
        final_idx = center_idx + offset
        final_idx = max(0, min(len(self.current_scale_notes)-1, final_idx))
        return self.current_scale_notes[final_idx]

    def note_on(self, note, duration=0.1, velocity=100, channel=0):
        if note in self.active_notes:
            _, _, old_channel = self.active_notes[note]
            self.midi.send_note_off(note, old_channel)
        self.midi.send_note_on(note, velocity, channel)
        self.active_notes[note] = (time.time(), duration, channel)

    def update(self, dt, is_moving):
        now = time.time()
        to_remove = []
        for note, (start_t, dur, chan) in self.active_notes.items():
            if now - start_t >= dur:
                self.midi.send_note_off(note, chan)
                to_remove.append(note)
        for n in to_remove:
            del self.active_notes[n]

        self.accumulated_time += dt
        if self.accumulated_time >= self.seconds_per_beat:
            self.accumulated_time -= self.seconds_per_beat
            self.global_step_counter += 1


            if is_moving and (self.global_step_counter % 16 == 0):
                base_note = self.root_note

                if random.random() < 0.35:
                    current_note = base_note + 12
                else:
                    current_note = base_note

                self.note_on(current_note, duration=0.4, velocity=95, channel=self.chan_move)

    def trigger_fire_note(self):
        base_note = self.get_arp_note(self.arp2_len, self.arp2_index, self.arp2_type)
        self.arp2_index += 1
        self.note_on(base_note, duration=0.1, velocity=110, channel=self.chan_fire)

    def trigger_impact_note(self):
        if not self.current_scale_notes: return
        note = random.choice(self.current_scale_notes)
        high_note = note + 24
        while high_note > 108: high_note -= 12
        self.note_on(high_note, duration=0.05, velocity=80, channel=self.chan_impact)

    def trigger_alien_death(self):
        if not self.current_scale_notes: return
        note = random.choice(self.current_scale_notes)
        self.note_on(note, duration=0.2, velocity=100, channel=self.chan_alien)

    def trigger_player_death(self):
        note = self.root_note
        self.note_on(note+24, duration=0.2, velocity=50, channel=self.chan_move)


    def trigger_powerup_sound(self):
        if not self.current_scale_notes: return
        target_pitch = self.root_note + 24
        base_note = min(self.current_scale_notes, key=lambda x: abs(x - target_pitch))
        try:
            base_idx = self.current_scale_notes.index(base_note)
            harm_idx = min(base_idx + 4, len(self.current_scale_notes) - 1)
            harmony_note = self.current_scale_notes[harm_idx]
        except ValueError:
            harmony_note = base_note + 7
        self.note_on(base_note, duration=0.1, velocity=110, channel=self.chan_alien)
        self.note_on(harmony_note, duration=0.1, velocity=90, channel=self.chan_alien)


try:
    from grid import Grid
except ImportError:
    pass

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = os.path.abspath(os.getcwd())

assets_dir = os.path.join(base_dir, '../assets')
resource_add_path(assets_dir)

SPRITE_KEYS = [f'shapes/shape_{i}' for i in range(12)]

def load_sprite_frames():
    shape_frames = {}
    def to_kivy_path(rel_path, f):
        return f"{rel_path.replace(os.sep, '/')}/{f}"
    if not os.path.isdir(assets_dir):
        return {}
    for shape_name_rel in SPRITE_KEYS:
        dir_path_abs = os.path.join(assets_dir, shape_name_rel)
        if not os.path.isdir(dir_path_abs): continue
        all_files = os.listdir(dir_path_abs)
        png_files = sorted([f for f in all_files if f.endswith('.png')])
        frames = [to_kivy_path(shape_name_rel, f) for f in png_files]
        if frames: shape_frames[shape_name_rel] = frames
    flash_rel = 'shapes/flash'
    flash_dir_abs = os.path.join(assets_dir, flash_rel)
    if os.path.isdir(flash_dir_abs):
        specific_frames = ['frame_000.png', 'frame_002.png', 'frame_003.png', 'frame_005.png']
        flash_paths = []
        for f in specific_frames:
            if os.path.exists(os.path.join(flash_dir_abs, f)):
                flash_paths.append(to_kivy_path(flash_rel, f))
        if flash_paths: shape_frames[flash_rel] = flash_paths
    return shape_frames

VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080
BACKTRACK_BUFFER = VIRTUAL_WIDTH * 3

class FitLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_bg, pos=self._update_bg)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def do_layout(self, *largs):
        if not self.children: return
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
            if hasattr(content, 'scale'): content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

class TransitionCurtain(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.label = Label(
            text="",
            font_size='36px',
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.label)
        self.opacity = 0

    def fade_in(self, text, on_complete):
        self.label.text = text
        anim = Animation(opacity=1, duration=0.5)
        anim.bind(on_complete=lambda *args: on_complete())
        anim.start(self)

    def fade_out(self):
        anim = Animation(opacity=0, duration=0.5)
        anim.start(self)

class LabeledSlider(BoxLayout):
    title = StringProperty("Setting")
    value = NumericProperty(0)
    min_val = NumericProperty(0)
    max_val = NumericProperty(100)
    step = NumericProperty(1)
    display_map = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = 1.0
        self.size_hint_x = 1.0
        initial_text = str(int(self.value))
        if self.display_map and int(self.value) < len(self.display_map):
            initial_text = str(self.display_map[int(self.value)])
        self.lbl_value = Label(
            text=initial_text,
            halign='center',
            valign='center',
            font_size='30px',
            size_hint_y=0.11,
            color=(0.5, 1, 0.5, 1)
        )
        self.lbl_value.bind(size=self.lbl_value.setter('text_size'))
        self.add_widget(self.lbl_value)
        self.slider = Slider(
            min=self.min_val,
            max=self.max_val,
            value=self.value,
            step=self.step,
            orientation='vertical',
            border_vertical=(0, 0, 0, 0),
            background_width=40,
            background_vertical='assets/single_slider_bg_vertical.png',
            background_horizontal='',
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            size_hint_y=0.8,
            padding=60
        )
        self.slider.bind(value=self.on_slider_value)
        self.add_widget(self.slider)
        self.lbl_title = Label(
            text=self.title,
            halign='center',
            valign='top',
            font_size='36px',
            size_hint_y=0.14
        )
        self.lbl_title.bind(size=self.lbl_title.setter('text_size'))
        self.add_widget(self.lbl_title)

    def on_slider_value(self, instance, val):
        self.value = val
        if hasattr(self, 'lbl_value'):
            if self.display_map and int(val) < len(self.display_map):
                self.lbl_value.text = str(self.display_map[int(val)])
            else:
                self.lbl_value.text = str(int(val))

    def on_title(self, instance, val):
        if hasattr(self, 'lbl_title'):
            self.lbl_title.text = val

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_content = FloatLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            pos=(0, 0)
        )
        with self.menu_content.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(
                source='assets/scroller_menu_bg.png',
                pos=(0, 0),
                size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
            )
        self.add_widget(self.menu_content)
        main_layout = BoxLayout(
            orientation='horizontal',
            padding=30,
            spacing=30,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        col1 = BoxLayout(orientation='vertical', spacing=10, size_hint_x=2)
        col1.add_widget(Label(text="ARP", font_size='36px', size_hint_y=0.06, valign='top', color=(0.2, 0.8, 1, 1)))
        col1_sliders = BoxLayout(orientation='horizontal', spacing=10, padding=(40,-6,0,0), size_hint_x=0.9, size_hint_y=0.75)
        self.sld_arp2_len = LabeledSlider(title="Length", min_val=1, max_val=16, value=8)
        col1_sliders.add_widget(self.sld_arp2_len)
        arp_types = ["UP", "DOWN", "UP/DOWN", "RANDOM", "ALTERNATE"]
        self.sld_arp2_type = LabeledSlider(title="Type", min_val=0, max_val=4, value=1, display_map=arp_types)
        col1_sliders.add_widget(self.sld_arp2_type)
        col1.add_widget(col1_sliders)

        col2 = BoxLayout(orientation='vertical', spacing=10, size_hint_x=4)
        col2.add_widget(Label(text="MIDI ROUTING (CH)", font_size='36px', size_hint_y=0.07, valign='top', color=(1, 0.4, 0.4, 1)))
        col2_sliders = BoxLayout(orientation='horizontal', spacing=10, padding=(70,-15,0,0), size_hint_x=0.9, size_hint_y=0.75)
        self.sld_chan_move = LabeledSlider(title="Move", min_val=1, max_val=16, value=1)
        col2_sliders.add_widget(self.sld_chan_move)
        self.sld_chan_fire = LabeledSlider(title="Fire", min_val=1, max_val=16, value=2)
        col2_sliders.add_widget(self.sld_chan_fire)
        self.sld_chan_impact = LabeledSlider(title="Impact", min_val=1, max_val=16, value=3)
        col2_sliders.add_widget(self.sld_chan_impact)
        self.sld_chan_alien = LabeledSlider(title="Alien", min_val=1, max_val=16, value=4)
        col2_sliders.add_widget(self.sld_chan_alien)
        col2.add_widget(col2_sliders)

        col3 = BoxLayout(orientation='vertical', spacing=8, size_hint_x=2.8)
        col3.add_widget(Widget(size_hint_y=0.0025))
        col3.add_widget(Label(text="GLOBAL SETTINGS", font_size='36px', size_hint_y=0.08, valign='top', color=(1, 0.6, 0.2, 1)))
        col3_sliders = BoxLayout(orientation='horizontal', spacing=0, padding=(40,-5,0,0), size_hint_x=1, size_hint_y=0.75)
        scale_types = list(SCALE_INTERVALS.keys())
        self.sld_scale = LabeledSlider(title="Scale", min_val=0, max_val=len(scale_types)-1, value=0, display_map=scale_types)
        col3_sliders.add_widget(self.sld_scale)
        keys = list(ROOT_NOTES.keys())
        self.sld_key = LabeledSlider(title="Key", min_val=0, max_val=11, value=0, display_map=keys)
        col3_sliders.add_widget(self.sld_key)
        self.sld_tempo = LabeledSlider(title="BPM", min_val=60, max_val=200, value=120)
        col3_sliders.add_widget(self.sld_tempo)
        col3.add_widget(col3_sliders)
        button_row = BoxLayout(orientation='horizontal', spacing=70, size_hint_y=0.15)
        button_row.add_widget(Widget())
        btn_back = Button(
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            size_hint=(None, None),
            size=(200, 200),
            border=(0,0,0,0)
        )
        btn_back.bind(on_release=self.go_to_goodies)
        button_row.add_widget(btn_back)
        btn_start = Button(
            background_normal='assets/start_button.png',
            background_down='assets/start_button_pressed.png',
            size_hint=(None, None),
            size=(200, 200),
            border=(0,0,0,0)
        )
        btn_start.bind(on_release=self.start_game)
        button_row.add_widget(btn_start)
        button_row.add_widget(Widget())
        col3.add_widget(Widget(size_hint_y=0.04))
        col3.add_widget(button_row)
        main_layout.add_widget(col1)
        main_layout.add_widget(col2)
        main_layout.add_widget(col3)
        self.menu_content.add_widget(main_layout)

    def go_to_goodies(self, instance):
        self.manager.go_to_goodies()

    def start_game(self, instance):
        game_screen = self.manager.get_screen('game')
        if game_screen:
            game_instance = game_screen.game
            game_instance.music_engine.update_settings(
                scale_idx=int(self.sld_scale.value),
                key_idx=int(self.sld_key.value),
                bpm=int(self.sld_tempo.value),
                a2_len=int(self.sld_arp2_len.value),
                a2_type_idx=int(self.sld_arp2_type.value),
                c_move=int(self.sld_chan_move.value) - 1,
                c_fire=int(self.sld_chan_fire.value) - 1,
                c_imp=int(self.sld_chan_impact.value) - 1,
                c_alien=int(self.sld_chan_alien.value) - 1
            )
        self.manager.trigger_screen_switch('game', "ENTERING THE CAVE")


class Bullet(Image):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)

    def __init__(self, start_pos, vel_x=1200, vel_y=0, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (40, 20)
        self.pos = start_pos
        self.velocity_x = vel_x
        self.velocity_y = vel_y

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

class AlienBullet(Image):
    velocity_x = NumericProperty(-600)
    def __init__(self, start_pos, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (30, 15)
        self.pos = start_pos
        self.color = (1, 0.2, 0.2, 1)

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

class Fragment(Image):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    gravity = NumericProperty(-1500)

    def __init__(self, start_pos, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (25, 25)
        self.pos = start_pos
        speed = random.uniform(200, 600)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed

    def update(self, dt):
        if self.frames:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.source = self.frames[self.frame_index]
        self.velocity_y += self.gravity * dt
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

class LifePowerUp(Image):
    def __init__(self, start_pos, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (50, 50)
        self.pos = start_pos
        self.color = (0.2, 1.0, 0.2, 1)

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

class Player(Image):
    speed = NumericProperty(350)
    def __init__(self, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (80, 60)
        self.color = (1, 0.4, 0.4, 1)

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

class Alien(Image):
    def __init__(self, start_pos, sprite_frames=[], move_type='stationary', can_fire=False, **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.pos = start_pos
        self.move_type = move_type
        self.can_fire = can_fire
        self.fire_timer = random.uniform(0.5, 2.0)
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.1
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (70, 50)
        self.time_alive = 0.0
        self.color = (
            random.uniform(0.65, 1.0),
            random.uniform(0.65, 1.0),
            random.uniform(0.65, 1.0),
            1
        )

    def update(self, dt, game_ref):
        if self.frames:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.source = self.frames[self.frame_index]
        self.time_alive += dt
        if self.move_type == 'moving':
            self.x -= 150 * dt
            self.y += math.sin(self.time_alive * 3) * 1.5
        if self.can_fire:
            self.fire_timer -= dt
            if self.fire_timer <= 0:
                self.fire(game_ref)
                self.fire_timer = random.uniform(2.0, 4.0)

    def fire(self, game_ref):
        bx = self.x - 20
        by = self.center_y - 7
        bullet = AlienBullet(start_pos=(bx, by), sprite_frames=game_ref.get_frames('shapes/flash'))
        game_ref.add_widget_to_game(bullet)
        game_ref.alien_bullets.append(bullet)

class TerrainLayer:
    def __init__(self, canvas_group, screen_height,
                 speed_mult=1.0,
                 width_mult=1.0,
                 floor_color=(1,1,1),
                 roof_color=(1,1,1),
                 is_main=False):

        self.speed_mult = speed_mult
        self.width_mult = width_mult
        self.screen_height = screen_height
        self.is_main = is_main
        self.floor_points = []
        self.roof_points = []
        self.segment_width = 40
        self.min_gap = 140 * width_mult
        self.max_gap = 600 * width_mult
        self.volatility = 60
        self.roughness = 40
        self.last_generated_x = 0

        with canvas_group:
            Color(*floor_color, 1.0)
            self.floor_mesh = Mesh(mode='triangle_strip')
            if is_main: Color(1, 0, 0, 1)
            else: Color(*floor_color, 1.0)
            self.floor_line = Line(width=1.2 if is_main else 1.5)

            Color(*roof_color, 1.0)
            self.roof_mesh = Mesh(mode='triangle_strip')
            if is_main: Color(1, 0, 0, 1)
            else: Color(*roof_color, 1.0)
            self.roof_line = Line(width=1.2 if is_main else 1.5)

    def init_segment(self, width):
        self.floor_points = []
        self.roof_points = []
        self.last_generated_x = 0
        current_x = 0
        base_gap = (self.screen_height * 0.6) * self.width_mult
        if base_gap > self.screen_height - 100: base_gap = self.screen_height - 100
        mid = self.screen_height / 2.0
        last_floor_y = mid - (base_gap / 2.0)
        last_roof_y = mid + (base_gap / 2.0)

        while current_x < width + self.segment_width * 4:
            self.add_segment(current_x, last_floor_y, last_roof_y)
            current_x += self.segment_width
            if self.floor_points:
                last_floor_y = self.floor_points[-1]
                last_roof_y = self.roof_points[-1]
        self.last_generated_x = current_x
        self.update_visuals(0)

    def add_segment(self, x, last_floor_y, last_roof_y):
        prev_mid = (last_floor_y + last_roof_y) / 2.0
        prev_height = last_roof_y - last_floor_y
        center_bias = (self.screen_height / 2.0) - prev_mid
        move_delta = random.randint(-self.volatility, self.volatility) + (center_bias * 0.05)
        new_mid = prev_mid + move_delta
        thickness_delta = random.randint(-self.roughness, self.roughness)
        new_height = prev_height + thickness_delta

        if random.random() < 0.05:
             new_height = self.min_gap + random.randint(0, 50)
        new_height = max(self.min_gap, min(self.max_gap, new_height))
        new_floor_y = new_mid - (new_height / 2.0)
        new_roof_y = new_mid + (new_height / 2.0)
        new_floor_y += random.randint(-10, 10)
        new_roof_y += random.randint(-10, 10)

        if new_floor_y < 10:
            new_floor_y = 10
            new_roof_y = max(new_roof_y, new_floor_y + self.min_gap)
        if new_roof_y > self.screen_height - 10:
            new_roof_y = self.screen_height - 10
            new_floor_y = min(new_floor_y, new_roof_y - self.min_gap)
        self.floor_points.extend([x, new_floor_y])
        self.roof_points.extend([x, new_roof_y])

    def update_view(self, global_scroll_x, screen_width):
        if not self.floor_points: return
        layer_scroll = global_scroll_x * self.speed_mult
        buffer_right = screen_width + 200
        while self.last_generated_x < layer_scroll + buffer_right:
            last_floor_y = self.floor_points[-1]
            last_roof_y = self.roof_points[-1]
            self.add_segment(self.last_generated_x + self.segment_width, last_floor_y, last_roof_y)
            self.last_generated_x += self.segment_width
        cutoff = layer_scroll - BACKTRACK_BUFFER
        if len(self.floor_points) > 4 and self.floor_points[0] < cutoff and self.floor_points[2] < cutoff:
             self.floor_points = self.floor_points[2:]
             self.roof_points = self.roof_points[2:]
        self.update_visuals(layer_scroll)

    def update_visuals(self, layer_scroll):
        def get_screen_points(world_points):
            screen_pts = []
            for i in range(0, len(world_points), 2):
                wx = world_points[i]
                wy = world_points[i+1]
                sx = wx - layer_scroll
                if -200 < sx < VIRTUAL_WIDTH + 200:
                     screen_pts.extend([sx, wy])
            return screen_pts
        render_floor = get_screen_points(self.floor_points)
        render_roof = get_screen_points(self.roof_points)
        self.floor_line.points = render_floor
        self.roof_line.points = render_roof
        f_vertices, f_indices = [], []
        idx = 0
        for i in range(0, len(render_floor), 2):
            x = render_floor[i]
            y = render_floor[i+1]
            f_vertices.extend([x, 0, 0, 0, x, y, 0, 0])
            f_indices.extend([idx, idx+1])
            idx += 2
        self.floor_mesh.vertices = f_vertices
        self.floor_mesh.indices = f_indices
        r_vertices, r_indices = [], []
        idx = 0
        for i in range(0, len(render_roof), 2):
            x = render_roof[i]
            y = render_roof[i+1]
            r_vertices.extend([x, y, 0, 0, x, self.screen_height, 0, 0])
            r_indices.extend([idx, idx+1])
            idx += 2
        self.roof_mesh.vertices = r_vertices
        self.roof_mesh.indices = r_indices

class TerrainGenerator(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layers = []
        self.main_layer = None
        self.foreground_widget = Widget()
        c_0 = (0.08, 0.065, 0.3)
        c_1 = (0.2, 0.09, 0.4)
        c_2 = (0.30, 0.025, 0.20)
        c_3 = (0.3, 0.05, 0.125)
        c_4 = (0.052, 0.01, 0.05)
        layer_configs = [
            {'speed': 0.4, 'width': 0.5, 'col': c_0, 'main': False},
            {'speed': 0.5, 'width': 2.0, 'col': c_1, 'main': False},
            {'speed': 0.6, 'width': 1.5, 'col': c_2, 'main': False},
            {'speed': 1.0, 'width': 1.2, 'col': c_3, 'main': True},
            {'speed': 1.4, 'width': 4.8, 'col': c_4, 'main': False},
        ]
        for i, config in enumerate(layer_configs):
            if i == 4: target_canvas = self.foreground_widget.canvas
            else: target_canvas = self.canvas
            layer = TerrainLayer(
                target_canvas,
                VIRTUAL_HEIGHT,
                speed_mult=config['speed'],
                width_mult=config['width'],
                floor_color=config['col'],
                roof_color=config['col'],
                is_main=config['main']
            )
            self.layers.append(layer)
            if config['main']: self.main_layer = layer

    def on_size(self, *args):
        self.foreground_widget.size = self.size
        self.foreground_widget.pos = self.pos

    def on_pos(self, *args):
        self.foreground_widget.size = self.size
        self.foreground_widget.pos = self.pos

    def init_terrain(self, width, height):
        for layer in self.layers:
            layer.screen_height = height
            layer.init_segment(width)

    def update(self, global_scroll_x):
        for layer in self.layers:
            layer.update_view(global_scroll_x, self.width)

    def get_primary_floor_y(self, screen_x, current_scroll_x):
        world_x = screen_x + current_scroll_x
        return self._get_y_at(world_x, self.main_layer.floor_points)

    def get_primary_roof_y(self, screen_x, current_scroll_x):
        world_x = screen_x + current_scroll_x
        return self._get_y_at(world_x, self.main_layer.roof_points)

    def _get_y_at(self, world_x_target, points_list):
        if not points_list or len(points_list) < 4: return None
        for i in range(0, len(points_list) - 2, 2):
            x1 = points_list[i]
            y1 = points_list[i+1]
            x2 = points_list[i+2]
            y2 = points_list[i+3]
            if x1 <= world_x_target <= x2:
                ratio = (world_x_target - x1) / (x2 - x1)
                return y1 + (y2 - y1) * ratio
        return points_list[1]

class LifeIcon(Image):
    def __init__(self, sprite_frames=[], **kwargs):
        super().__init__(**kwargs)
        self.frames = sprite_frames
        if self.frames: self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)
        self.size = (60, 45)

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

class VirtualJoystick(Widget):
    def __init__(self, stick_radius=200, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (stick_radius * 2, stick_radius * 2)
        self.stick_radius = stick_radius
        self.active = False
        self.joy_val = Vector(0, 0)
        self.pos = (150, 150)

        with self.canvas:
            Color(1, 1, 1, 0.3)
            self.bg_line = Line(circle=(self.center_x, self.center_y, self.stick_radius), width=1.5)
            Color(1, 1, 1, 0.5)
            self.knob = Mesh(mode='triangle_fan')
            self.update_knob_visuals(self.center_x, self.center_y)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.bg_line.circle = (self.center_x, self.center_y, self.stick_radius)
        if not self.active:
            self.update_knob_visuals(self.center_x, self.center_y)

    def update_knob_visuals(self, x, y):
        r = 30
        vertices = [x, y, 0, 0]
        indices = [0]
        step = 20
        for i in range(0, 360 + step, step):
            rad = math.radians(i)
            vertices.extend([x + math.cos(rad) * r, y + math.sin(rad) * r, 0, 0])
            indices.append(len(indices))
        self.knob.vertices = vertices
        self.knob.indices = indices

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self.active = True
        self.update_stick(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.update_stick(touch)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.active = False
            self.joy_val = Vector(0, 0)
            self.update_knob_visuals(self.center_x, self.center_y)
            return True
        return False

    def update_stick(self, touch):
        v = Vector(touch.pos) - Vector(self.center)
        if v.length() > self.stick_radius:
            v = v.normalize() * self.stick_radius
        self.joy_val = v / self.stick_radius
        self.update_knob_visuals(self.center_x + v.x, self.center_y + v.y)

class VirtualFireButton(Widget):
    def __init__(self, callback, radius=200, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.radius = radius
        self.size_hint = (None, None)
        self.size = (radius * 2, radius * 2)
        self.pos = (1600, 150)

        with self.canvas:
            self.color = Color(1, 0.2, 0.2, 0.4)
            self.line = Line(circle=(self.center_x, self.center_y, self.radius), width=2.0)
            self.fill = Mesh(mode='triangle_fan')

        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.line.circle = (self.center_x, self.center_y, self.radius)

    def draw_fill(self):
        x, y = self.center_x, self.center_y
        r = self.radius
        vertices = [x, y, 0, 0]
        indices = [0]
        step = 20
        for i in range(0, 360 + step, step):
            rad = math.radians(i)
            vertices.extend([x + math.cos(rad) * r, y + math.sin(rad) * r, 0, 0])
            indices.append(len(indices))
        self.fill.vertices = vertices
        self.fill.indices = indices

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.color.a = 0.8
            self.draw_fill()
            self.callback()
            return True
        return False

    def on_touch_up(self, touch):
        if self.color.a == 0.8:
            self.color.a = 0.4
            self.fill.vertices = []
            return True
        return False

class CaveGame(Widget):
    bg_scroll_x = NumericProperty(0)
    touch_start_pos = ListProperty([0,0])
    scroll_x = NumericProperty(0)
    is_initialized = False
    autoplay = BooleanProperty(False)

    def __init__(self, music_engine, menu_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.menu_callback = menu_callback

        self.size_hint = (None, None)
        self.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        self.sprite_frames = load_sprite_frames()
        self.keys_pressed = set()
        self.bullets = []
        self.aliens = []
        self.alien_bullets = []
        self.fragments = []
        self.powerups = []
        self.is_player_dead = False
        self.is_game_over_showing = False
        self.game_over_overlay = None

        self.spawn_timer = 0
        self.time_to_next_spawn = 1.5
        self.is_dragging = False

        self.autoplay_shoot_timer = 0.0
        self.autoplay_move_state_timer = 0.0
        self.autoplay_is_moving_right = True
        self.autoplay_target_y = 0

        self.lives = 3
        self.is_invincible = False
        self.invincibility_timer = 0.0

        self.life_icons = []
        self.joystick = None
        self.fire_btn = None
        self.is_android = (platform == 'android')

        if self.is_android:
            self.joystick = VirtualJoystick(stick_radius=100)
            self.fire_btn = VirtualFireButton(callback=self.spawn_bullet, radius=90)

        try:
            from grid import Grid
            self.background_grid = Grid()
            self.background_grid.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
            self.add_widget(self.background_grid)
        except ImportError:
            self.background_grid = Widget()

        self.music_engine = music_engine
        self.terrain = TerrainGenerator()
        self.add_widget(self.terrain)
        self.entity_container = Widget()
        self.add_widget(self.entity_container)
        self.add_widget(self.terrain.foreground_widget)

        self.player = Player(sprite_frames=self.get_frames('shapes/shape_8'))
        self.player.pos = (200, 300)
        self.entity_container.add_widget(self.player)

        self.btn_back = Button(
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            size_hint=(None, None),
            size=(120, 120),
            pos=(20, 940),
            font_size=18,
        )
        self.btn_back.bind(on_release=self.go_to_menu)
        self.add_widget(self.btn_back)

        self.autoplay_btn = ToggleButton(
            background_normal='assets/auto_normal.png',
            background_down='assets/auto_down.png',
            size_hint=(None, None),
            size=(120, 120),
            pos=(160, 940),
            border=(0, 0, 0, 0)
        )
        self.autoplay_btn.bind(state=self.on_toggle_autoplay)
        self.add_widget(self.autoplay_btn)

        self.distance_label = Label(
            text="0m",
            font_size='36px',
            color=(0.5, 1, 1, 1),
            bold=True,
            size_hint=(None, None),
            size=(300, 100),
            pos=(1600,960),
            halign='right',
            valign='middle'
        )
        self.add_widget(self.distance_label)

        self.lives_layout = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint=(None, None),
            size=(250, 60),
            pos=(30, 30)
        )

        player_frames = self.get_frames('shapes/shape_8')
        for i in range(3):
            icon = LifeIcon(sprite_frames=player_frames)
            self.life_icons.append(icon)
            self.lives_layout.add_widget(icon)

        self.add_widget(self.lives_layout)

        if self.joystick:
            self.add_widget(self.joystick)
        if self.fire_btn:
            self.add_widget(self.fire_btn)

        self.update_event = None
        Clock.schedule_once(self.post_init, 0.1)

    def get_frames(self, key):
        return self.sprite_frames.get(key, [])

    def go_to_menu(self, instance):
        if self.menu_callback:
            self.menu_callback()
        else:
            print("WARNING: No menu callback defined for CaveGame.")

    def spawn_player_safely(self):
        start_x = 200
        floor_y = self.terrain.get_primary_floor_y(start_x, 0)
        roof_y = self.terrain.get_primary_roof_y(start_x, 0)

        if floor_y is None: floor_y = 100
        if roof_y is None: roof_y = self.height - 100

        center_y = (floor_y + roof_y) / 2.0
        self.player.pos = (start_x, center_y - (self.player.height / 2.0))

    def on_toggle_autoplay(self, instance, value):
        self.autoplay = (value == 'down')
        if self.autoplay:
            self.keys_pressed.clear()
            self.autoplay_move_state_timer = 0
            self.autoplay_is_moving_right = True
            if self.joystick: self.joystick.opacity = 0
            if self.fire_btn: self.fire_btn.opacity = 0
        else:
            if self.joystick: self.joystick.opacity = 1
            if self.fire_btn: self.fire_btn.opacity = 1

    def post_init(self, dt):
        self.update_grid_layout()
        self.terrain.size = self.size
        self.entity_container.size = self.size
        self.terrain.init_terrain(self.width, self.height)
        self.spawn_player_safely()
        self.is_initialized = True

    def update_grid_layout(self):
        if hasattr(self.background_grid, 'grid_size'):
            grid_sz = self.background_grid.grid_size
            self.background_grid.size = (self.width + grid_sz, self.height)
            scroll_speed_factor = 0.1
            offset_x = (self.scroll_x * scroll_speed_factor) % grid_sz
            self.background_grid.pos = (-offset_x, 0)

    def add_widget_to_game(self, widget):
        self.entity_container.add_widget(widget)

    def remove_widget_from_game(self, widget):
        if widget.parent == self.entity_container:
            self.entity_container.remove_widget(widget)

    def spawn_explosion(self, x, y, count=10):
        for _ in range(count):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            frag = Fragment(start_pos=(x + offset_x, y + offset_y), sprite_frames=self.get_frames('shapes/flash'))
            self.fragments.append(frag)
            self.add_widget_to_game(frag)

    def cleanup_state(self):
        if self.game_over_overlay:
            self.remove_widget(self.game_over_overlay)
            self.game_over_overlay = None
        self.is_game_over_showing = False
        for b in self.bullets: self.remove_widget_from_game(b)
        for a in self.aliens: self.remove_widget_from_game(a)
        for ab in self.alien_bullets: self.remove_widget_from_game(ab)
        for f in self.fragments: self.remove_widget_from_game(f)
        for p in self.powerups: self.remove_widget_from_game(p)
        self.bullets.clear()
        self.aliens.clear()
        self.alien_bullets.clear()
        self.fragments.clear()
        self.powerups.clear()
        self.keys_pressed.clear()
        self.player.opacity = 1
        self.player.color = (1, 0.4, 0.4, 1)

    def reset_game(self):
        self.cleanup_state()
        self.lives = 3
        for icon in self.life_icons:
            icon.opacity = 1
            icon.color = (1, 1, 1, 1)
        self.is_invincible = False
        self.invincibility_timer = 0.0
        self.player.color = (1, 0.4, 0.4, 1)
        self.is_player_dead = False
        self.player.opacity = 1
        self.scroll_x = 0
        self.distance_label.text = "0m"
        self.terrain.init_terrain(self.width, self.height)
        self.spawn_player_safely()

    def start_running(self):
        self.reset_game()
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def stop_running(self):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def show_game_over_screen(self):
        self.is_game_over_showing = True
        score_meters = int((self.scroll_x / VIRTUAL_WIDTH) * 100)
        self.game_over_overlay = FloatLayout(size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pos=(0, 0), size_hint=(None, None))
        with self.game_over_overlay.canvas.before:
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        label = Label(
            text=f"GAME OVER\nDistance: {score_meters}m",
            font_size='60sp',
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 1),
            color=(1, 1, 1, 1)
        )
        self.game_over_overlay.add_widget(label)
        self.add_widget(self.game_over_overlay)
        step_duration = self.music_engine.seconds_per_beat
        delay = 16 * step_duration
        Clock.schedule_once(self.finalize_reset, delay)

    def finalize_reset(self, dt):
        self.reset_game()

    def handle_player_hit(self):
        if self.is_invincible or self.is_player_dead:
            return
        self.lives -= 1
        if 0 <= self.lives < len(self.life_icons):
            self.life_icons[self.lives].opacity = 0.2
        print(f"Player Hit! Lives remaining: {self.lives}")
        if self.lives <= 0:
            self.is_player_dead = True
            self.player.opacity = 0
            self.spawn_explosion(self.player.center_x, self.player.center_y, count=20)
            self.music_engine.trigger_player_death()
        else:
            self.is_invincible = True
            self.invincibility_timer = 5.0

    def spawn_bullet(self, auto_vx=None, auto_vy=None):
        if self.is_player_dead: return
        self.music_engine.trigger_fire_note()
        base_speed = 1200
        vx = 0
        vy = 0
        if self.autoplay:
            vx = auto_vx if auto_vx is not None else base_speed
            vy = auto_vy if auto_vy is not None else 0
        else:
            up_pressed = 119 in self.keys_pressed or 273 in self.keys_pressed
            down_pressed = 115 in self.keys_pressed or 274 in self.keys_pressed
            left_pressed = 97 in self.keys_pressed or 276 in self.keys_pressed
            right_pressed = 100 in self.keys_pressed or 275 in self.keys_pressed

            if self.joystick and self.joystick.active:
                threshold = 0.3
                if self.joystick.joy_val.y > threshold: up_pressed = True
                if self.joystick.joy_val.y < -threshold: down_pressed = True
                if self.joystick.joy_val.x > threshold: right_pressed = True
                if self.joystick.joy_val.x < -threshold: left_pressed = True

            if up_pressed: vy = base_speed
            elif down_pressed: vy = -base_speed
            if left_pressed: vx = -base_speed
            elif right_pressed: vx = base_speed
            if vx == 0 and vy == 0: vx = base_speed

        bx = self.player.center_x - 20
        by = self.player.center_y
        new_bullet = Bullet(start_pos=(bx, by), vel_x=vx, vel_y=vy, sprite_frames=self.get_frames('shapes/flash'))
        self.add_widget_to_game(new_bullet)
        self.bullets.append(new_bullet)

    def attempt_spawn_alien(self):
        spawn_screen_x = self.width + 50
        floor_y = self.terrain.get_primary_floor_y(spawn_screen_x, self.scroll_x)
        roof_y = self.terrain.get_primary_roof_y(spawn_screen_x, self.scroll_x)
        if floor_y is None or roof_y is None: return
        gap = roof_y - floor_y
        padding = 60
        if gap < (padding * 2): return
        spawn_y = random.uniform(floor_y + padding, roof_y - padding)
        move_type = random.choice(['stationary', 'stationary', 'moving'])
        can_fire = random.choice([True, False])
        random_shape = random.choice(SPRITE_KEYS)
        alien = Alien(start_pos=(spawn_screen_x, spawn_y), sprite_frames=self.get_frames(random_shape), move_type=move_type, can_fire=can_fire)
        self.aliens.append(alien)
        self.add_widget_to_game(alien)

    def on_key_down(self, window, key, *args):
        if self.autoplay: return
        keycode = key[0] if isinstance(key, (list, tuple)) else key
        self.keys_pressed.add(keycode)
        if keycode == 32: self.spawn_bullet()

    def on_key_up(self, window, key, *args):
        if self.autoplay: return
        keycode = key[0] if isinstance(key, (list, tuple)) else key
        if keycode in self.keys_pressed: self.keys_pressed.remove(keycode)

    def on_touch_down(self, touch):
        if self.fire_btn and self.fire_btn.on_touch_down(touch):
            return True

        if self.joystick and self.joystick.on_touch_down(touch):
            return True

        if self.btn_back.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.autoplay_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.joystick and self.joystick.on_touch_move(touch):
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.fire_btn and self.fire_btn.on_touch_up(touch):
            return True
        if self.joystick and self.joystick.on_touch_up(touch):
            return True
        return super().on_touch_up(touch)

    def calculate_autoplay_moves(self, dt, step):
        dx, dy = 0, 0
        intended_vx = 1200
        intended_vy = 0
        self.autoplay_move_state_timer -= dt
        if self.autoplay_move_state_timer <= 0:
            if random.random() < 0.65:
                self.autoplay_is_moving_right = True
                self.autoplay_move_state_timer = random.uniform(0.3,0.8)
            else:
                self.autoplay_is_moving_right = False
                self.autoplay_move_state_timer = random.uniform(0.1, 0.5)
        if self.autoplay_is_moving_right:
            dx += step
            intended_vx = 1200
        current_x = self.player.center_x
        current_y = self.player.center_y
        floor_y = self.terrain.get_primary_floor_y(current_x, self.scroll_x)
        roof_y = self.terrain.get_primary_roof_y(current_x, self.scroll_x)
        if floor_y is None: floor_y = 100
        if roof_y is None: roof_y = self.height - 100
        target_y = (floor_y + roof_y) / 2.0
        for ab in self.alien_bullets:
            x_dist = ab.center_x - current_x
            if 0 < x_dist < 400:
                y_dist = ab.center_y - current_y
                if abs(y_dist) < 70:
                    if y_dist > 0: target_y = floor_y + 40
                    else: target_y = roof_y - 40
        y_diff = target_y - current_y
        speed_y = y_diff * 5.0
        max_speed = self.player.speed
        speed_y = max(-max_speed, min(max_speed, speed_y))
        if speed_y > 100: intended_vy = 1200
        elif speed_y < -100: intended_vy = -1200
        dy = speed_y * dt
        self.autoplay_shoot_timer -= dt
        if self.autoplay_shoot_timer <= 0:
            should_fire = False
            for alien in self.aliens:
                if alien.x > current_x and alien.x < current_x + 900:
                    if abs(alien.center_y - current_y) < 80:
                        should_fire = True
                        break

            if should_fire:
                self.spawn_bullet(auto_vx=intended_vx, auto_vy=intended_vy)
                self.autoplay_shoot_timer = random.uniform(0.05, 0.80)
        return dx, dy

    def update(self, dt):
        if not self.is_initialized: return
        current_distance = int((self.scroll_x / VIRTUAL_WIDTH) * 100)
        self.distance_label.text = f"{current_distance}m"
        for icon in self.life_icons:
            icon.update_animation(dt)
        for f in self.fragments[:]:
            f.update(dt)
            if f.top < 0 or f.x > self.width + 200 or f.x < -200:
                self.fragments.remove(f)
                self.remove_widget_from_game(f)
        for pu in self.powerups[:]:
            pu.update_animation(dt)
            if pu.right < -100:
                self.powerups.remove(pu)
                self.remove_widget_from_game(pu)
                continue
            if pu.collide_widget(self.player):
                if self.lives < 3:
                    if self.lives >= 0 and self.lives < len(self.life_icons):
                         self.life_icons[self.lives].opacity = 1
                    self.lives += 1
                    self.music_engine.trigger_powerup_sound()
                else:
                    self.music_engine.trigger_powerup_sound()
                self.powerups.remove(pu)
                self.remove_widget_from_game(pu)
        if self.is_player_dead:
            if len(self.fragments) > 0:
                return
            else:
                if not self.is_game_over_showing:
                    self.show_game_over_screen()
                return
        if self.is_invincible:
            self.invincibility_timer -= dt
            if int(self.invincibility_timer * 10) % 2 == 0:
                self.player.color = (1, 0.4, 0.4, 0.2)
            else:
                self.player.color = (1, 0.4, 0.4, 1.0)
            if self.invincibility_timer <= 0:
                self.is_invincible = False
                self.player.color = (1, 0.4, 0.4, 1.0)
        self.player.update_animation(dt)
        dx, dy = 0, 0
        step = self.player.speed * dt

        if self.autoplay:
            dx, dy = self.calculate_autoplay_moves(dt, step)
        else:
            up_pressed = 119 in self.keys_pressed or 273 in self.keys_pressed
            down_pressed = 115 in self.keys_pressed or 274 in self.keys_pressed
            left_pressed = 97 in self.keys_pressed or 276 in self.keys_pressed
            right_pressed = 100 in self.keys_pressed or 275 in self.keys_pressed

            if self.joystick and self.joystick.active:
                threshold = 0.3
                if self.joystick.joy_val.y > threshold: up_pressed = True
                if self.joystick.joy_val.y < -threshold: down_pressed = True
                if self.joystick.joy_val.x > threshold: right_pressed = True
                if self.joystick.joy_val.x < -threshold: left_pressed = True

            if up_pressed: dy += step
            if down_pressed: dy -= step
            if left_pressed: dx -= step
            if right_pressed: dx += step

        is_moving = (dx != 0 or dy != 0)
        self.music_engine.update(dt, is_moving)
        if dy != 0:
            self.player.y = max(0, min(self.height - self.player.height, self.player.y + dy))
        proposed_player_x = self.player.x + dx
        scroll_delta = 0
        right_threshold = self.width * 0.55
        left_threshold = self.width * 0.20
        if proposed_player_x > right_threshold:
            if dx > 0:
                scroll_delta = dx
                self.player.x = right_threshold
            else:
                self.player.x = proposed_player_x
        elif proposed_player_x < left_threshold:
            if self.scroll_x > 0:
                if dx < 0:
                    scroll_delta = dx
                    self.player.x = left_threshold
                else:
                    self.player.x = proposed_player_x
            else:
                self.player.x = max(0, proposed_player_x)
        else:
            self.player.x = proposed_player_x
        if self.player.right > self.width: self.player.right = self.width
        if scroll_delta != 0:
            self.scroll_x += scroll_delta
            if self.scroll_x < 0: self.scroll_x = 0
            for ent in self.aliens + self.bullets + self.alien_bullets + self.fragments + self.powerups:
                ent.x -= scroll_delta
        self.terrain.update(self.scroll_x)
        self.update_grid_layout()
        self.spawn_timer += dt
        if self.spawn_timer >= self.time_to_next_spawn:
            self.attempt_spawn_alien()
            self.spawn_timer = 0
            self.time_to_next_spawn = random.uniform(1.0, 2.5)
        for b in self.bullets[:]:
            b.x += b.velocity_x * dt
            b.y += b.velocity_y * dt
            b.update_animation(dt)
            if b.x > self.width + 100 or b.x < -100 or b.y > self.height + 100 or b.y < -100:
                self.remove_widget_from_game(b)
                self.bullets.remove(b)
                continue
            floor_y = self.terrain.get_primary_floor_y(b.center_x, self.scroll_x)
            roof_y = self.terrain.get_primary_roof_y(b.center_x, self.scroll_x)
            if floor_y is not None and roof_y is not None:
                if b.y < floor_y or b.top > roof_y:
                    self.music_engine.trigger_impact_note()
                    self.remove_widget_from_game(b)
                    self.bullets.remove(b)
        for alien in self.aliens[:]:
            alien.update(dt, self)
            if alien.right < -200 or alien.x > self.width + 200:
                self.remove_widget_from_game(alien)
                self.aliens.remove(alien)
                continue
            destroyed = False
            for b in self.bullets[:]:
                if alien.collide_widget(b):
                    self.spawn_explosion(alien.center_x, alien.center_y, count=8)
                    self.music_engine.trigger_alien_death()
                    if random.random() < 0.2:
                        pu = LifePowerUp(start_pos=(alien.x, alien.y), sprite_frames=self.get_frames('shapes/flash'))
                        self.powerups.append(pu)
                        self.add_widget_to_game(pu)
                    self.remove_widget_from_game(alien)
                    self.aliens.remove(alien)
                    self.remove_widget_from_game(b)
                    self.bullets.remove(b)
                    destroyed = True
                    break
            if destroyed: continue
            if alien.collide_widget(self.player):
                self.handle_player_hit()
        for ab in self.alien_bullets[:]:
            ab.x += ab.velocity_x * dt
            ab.update_animation(dt)
            if ab.right < -50:
                self.remove_widget_from_game(ab)
                self.alien_bullets.remove(ab)
                continue
            floor_y = self.terrain.get_primary_floor_y(ab.center_x, self.scroll_x)
            roof_y = self.terrain.get_primary_roof_y(ab.center_x, self.scroll_x)
            if floor_y is not None and roof_y is not None:
                if ab.y < floor_y or ab.top > roof_y:
                    self.remove_widget_from_game(ab)
                    self.alien_bullets.remove(ab)
                    continue
            if ab.collide_widget(self.player):
                self.handle_player_hit()
        check_x = self.player.center_x
        floor_y = self.terrain.get_primary_floor_y(check_x, self.scroll_x)
        roof_y = self.terrain.get_primary_roof_y(check_x, self.scroll_x)
        if floor_y is not None and roof_y is not None:
            if self.player.y < floor_y or self.player.top > roof_y:
                self.handle_player_hit()

class GameScreenContainer(Screen):
    def __init__(self, music_engine, **kwargs):
        super().__init__(**kwargs)
        self.fit_layout = FitLayout()
        self.add_widget(self.fit_layout)
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False
        )
        self.clipper = StencilView(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        )
        self.game = CaveGame(music_engine=music_engine, menu_callback=self.return_to_menu)
        self.clipper.add_widget(self.game)
        self.scatter.add_widget(self.clipper)
        self.fit_layout.add_widget(self.scatter)

    def on_enter(self, *args):
        Window.bind(on_key_down=self.game.on_key_down)
        Window.bind(on_key_up=self.game.on_key_up)
        self.game.start_running()

    def on_leave(self, *args):
        Window.unbind(on_key_down=self.game.on_key_down)
        Window.unbind(on_key_up=self.game.on_key_up)
        self.game.stop_running()
        self.game.cleanup_state()

    def return_to_menu(self):
        if self.manager:
            self.manager.trigger_screen_switch('menu', "EXITING THE CAVE")

class _CavernAceWorld(ScreenManager):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.transition = NoTransition()
        self.music_engine = MusicEngine(external_midi_port=main_midi_out)
        menu_screen = MainMenuScreen(name='menu')
        game_screen = GameScreenContainer(name='game', music_engine=self.music_engine)
        self.add_widget(menu_screen)
        self.add_widget(game_screen)

    def go_to_goodies(self):
        self.app_switcher('goodies_menu')

    def trigger_screen_switch(self, target_screen, text):
        curtain = None
        for child in self.parent.children:
            if isinstance(child, TransitionCurtain):
                curtain = child
                break
        if curtain:
             curtain.fade_in(text, lambda: self._do_switch(target_screen, curtain))
        else:
            self._do_switch(target_screen, None)

    def _do_switch(self, target_screen, curtain):
        if target_screen == 'game':
            game_screen = self.get_screen('game')
            game_screen.game.cleanup_state()
            game_screen.game.reset_game()
        if target_screen == 'menu':
            game_screen = self.get_screen('game')
            game_screen.game.stop_running()
            game_screen.game.cleanup_state()
        self.current = target_screen
        if curtain:
            curtain.fade_out()

class CavernAceRoot(FitLayout):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )
        self.world = _CavernAceWorld(app_switcher, main_midi_out)
        self.scatter.add_widget(self.world)
        self.curtain = TransitionCurtain()
        self.scatter.add_widget(self.curtain)
        self.add_widget(self.scatter)

    def cleanup_app(self):
        game_screen = self.world.get_screen('game')
        if game_screen and game_screen.game:
            game_screen.game.stop_running()
            if game_screen.game.music_engine:
                 game_screen.game.music_engine.midi.close()
