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

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.utils import platform
import colorsys
import random
import os
from kivy.resources import resource_add_path
import math

from misc.grid import Grid

class AlignedLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size


if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("ShapeArcade: Successfully imported AndroidMidi")
    except ImportError:
        print("ShapeArcade: Could not import AndroidMidi")
        AndroidMidi = None

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import rtmidi
        print("ShapeArcade: Successfully imported WindowsMidi (aliased) and rtmidi")
    except ImportError:
        print("ShapeArcade: Could not import windows_midi or rtmidi")
        AndroidMidi = None

else:
    try:
        import rtmidi
        print("ShapeArcade: Successfully imported rtmidi")
    except ImportError:
        print("ShapeArcade: rtmidi not found.")
        rtmidi = None

VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

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
    'MELODIC\nMINOR (Asc)': [0, 2, 3, 5, 7, 9, 11],
    'WHOLE TONE': [0, 2, 4, 6, 8, 10],
    'DIMINISHED\n(Half-Whole)': [0, 1, 3, 4, 6, 7, 9, 10],
    'DIMINISHED\n(Whole-Half)': [0, 2, 3, 5, 6, 8, 9, 11],
    'AUGMENTED': [0, 3, 4, 7, 8, 11],
    'ENIGMATIC': [0, 1, 4, 6, 8, 10, 11],
}
SCALE_NAMES = list(SCALES.keys())

BASE_OCTAVE = 4
BASE_MIDI_NOTE = 12 * (BASE_OCTAVE + 1)

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = os.path.abspath(os.getcwd())

assets_dir = os.path.join(base_dir, '../assets')
resource_add_path(assets_dir)

SPRITE_KEYS = [f'shapes/shape_{i}' for i in range(12)]

def load_sprite_frames():
    shape_frames = {}
    shape_dirs = SPRITE_KEYS + ['shapes/flash']
    abs_base_path = os.path.join(assets_dir, 'shapes')

    def to_kivy_path(rel_path, f):
        return f"{rel_path.replace(os.sep, '/')}/{f}"

    for shape_name_rel in shape_dirs:
        dir_path_abs = os.path.join(assets_dir, shape_name_rel)
        if not os.path.isdir(dir_path_abs):
            continue

        all_files = os.listdir(dir_path_abs)
        png_files = sorted([f for f in all_files if f.endswith('.png')])
        frames = [to_kivy_path(shape_name_rel, f) for f in png_files]

        if frames:
            shape_frames[shape_name_rel] = frames
        else:
            print(f"INFO: No PNG frames found in {dir_path_abs}")

    return shape_frames

class MidiController:
    def __init__(self, external_midi_out=None):
        self.is_android = (platform == 'android')
        self.midi_backend = external_midi_out
        self.is_external = external_midi_out is not None

        if not self.is_external:
            self._create_internal_backend()

    def _create_internal_backend(self):
        if platform in ('android', 'win') and AndroidMidi:
            try:
                print(f"ShapeArcade: Initializing wrapper backend ({platform})...")
                self.midi_backend = AndroidMidi()

                if platform == 'win' and hasattr(self.midi_backend, 'get_host_devices'):
                    devs = self.midi_backend.get_host_devices()
                    if devs:
                        print(f"ShapeArcade: Auto-connecting to {devs[0][0]}")
                        self.midi_backend.connect_to_device(devs[0][1])

            except Exception as e:
                print(f"ShapeArcade: Wrapper Init Error: {e}")
                self.midi_backend = None

        elif rtmidi:
            try:
                self.midi_backend = rtmidi.MidiOut()
                print("ShapeArcade: Created rtmidi backend.")
            except Exception as e:
                print(f"ShapeArcade: rtmidi Init Error: {e}")
                self.midi_backend = None
        else:
            print("ShapeArcade: No MIDI backend available.")
            self.midi_backend = None

    def open(self):
        if self.is_external:
            return

        if not self.midi_backend:
            self._create_internal_backend()

        if not self.midi_backend:
            return

        try:
            if self.is_android:
                self.midi_backend.open_output()
            else:
                ports = self.midi_backend.get_ports()
                if ports:
                    self.midi_backend.open_port(0)
                    print(f"INFO: rtmidi port opened: {ports[0]}")
        except Exception as e:
            print(f"ERROR: Could not open MIDI port: {e}")

    def send_message(self, msg_list):
        if not self.midi_backend:
            return
        try:
            if hasattr(self.midi_backend, 'send_message'):
                self.midi_backend.send_message(msg_list)
        except Exception as e:
            print(f"ERROR: Could not send MIDI message: {e}")

    def play_note(self, note, duration=0.15, velocity=100, channel=0):
        if note < 0 or note > 127:
            return

        channel = max(0, min(15, int(channel)))
        note_on_status = 0x90 + channel
        note_off_status = 0x80 + channel

        self.send_message([note_on_status, int(note), velocity])
        Clock.schedule_once(
            lambda dt: self.send_message([note_off_status, int(note), 0]),
            duration
        )

    def close(self):
        if self.is_external:
            return

        if not self.midi_backend:
            return

        try:
            if self.is_android:
                self.midi_backend.close()
            else:
                if hasattr(self, 'midi_backend') and self.midi_backend:
                    self.midi_backend.close_port()

            self.midi_backend = None

        except Exception as e:
            print(f"ERROR: Error closing MIDI: {e}")

class Player(Image):
    def __init__(self, frames, **kwargs):
        super().__init__(**kwargs)
        self.frames = frames
        if self.frames:
            self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]


class Projectile(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(1, 1, 0)
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_ellipse, size=self.update_ellipse)

    def update_ellipse(self, *args):
        self.ellipse.pos = self.pos
        self.ellipse.size = self.size

    def move(self):
        self.y += 9

class Fragment(Image):
    def __init__(self, **kwargs):
        self.frames = kwargs.pop('frames', [])
        self.velocity_x = kwargs.pop('velocity_x', 0)
        self.velocity_y = kwargs.pop('velocity_y', 0)
        self.angular_velocity = kwargs.pop('angular_velocity', 0)
        super().__init__(**kwargs)
        if self.frames:
            self.source = random.choice(self.frames)
        self.frame_index = 0
        self.frame_timer = random.uniform(0.0, 0.1)
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False
        self.angle = 0

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]

        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.velocity_y -= 980 * dt
        self.angle += self.angular_velocity * dt


class Alien(Image):
    midi_note = NumericProperty(60)
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    fire_timer = NumericProperty(0)

    def __init__(self, frames, **kwargs):
        super().__init__(**kwargs)
        self.frames = frames

        h = random.random()
        s = random.uniform(0.3, 0.6)
        v = random.uniform(0.9, 1.0)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.color = (r, g, b, 1)

        if self.frames:
            self.source = self.frames[0]
        self.frame_index = 0
        self.frame_timer = random.uniform(0.0, 0.1)
        self.frame_duration = 0.05
        self.allow_stretch = True
        self.keep_ratio = False

    def update_animation(self, dt):
        if not self.frames: return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]


class ArcadeGameScreen(Screen):
    player = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.projectiles = []
        self.aliens = []
        self.fragments = []
        self._game_event = None
        self._keys_down = set()
        self.player_speed = 0
        self.is_player_destroyed = False
        self.alien_direction = 1
        self.base_alien_speed_x = 0
        self.alien_speed_x = 0
        self.alien_speed_y = 0
        self.alien_step_down_amount = 0
        self.alien_max_move_time = 0.5
        self.alien_move_timer = 0.0
        self.total_aliens = 0
        self.autoplay_enabled = False
        self.autoplay_wander_direction = 1
        self.autoplay_move_timer = 0.0
        self.autoplay_fire_timer = 0.0
        self.current_autoplay_velocity = 0.0
        self.movement_smoothing = 10.0
        self.autoplay_button = None
        self.back_button = None
        self.grid = None
        self.lives = 3
        self.score = 0
        self.life_icons = []
        self.score_label = None
        self.game_over_overlay = None
        self.game_over_label = None

    def on_enter(self, *args, initial_autoplay=False):
        if not self.grid:
            self.grid = Grid(size_hint=(1, 1))
            self.add_widget(self.grid)

        self.lives = 3
        self.score = 0
        self.life_icons = []
        self.spawn_player()
        self.player_speed = self.width * 0.7
        self._keys_down = set()
        self._key_bindings = Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        self.alien_step_down_amount = self.height * 0.03
        self.base_alien_speed_x = self.width * 0.08
        self.alien_speed_x = self.base_alien_speed_x
        self.alien_speed_y = 0
        self.alien_move_timer = self.alien_max_move_time
        self.alien_fire_cooldown = 0.0
        self.autoplay_enabled = initial_autoplay
        self.autoplay_move_timer = random.uniform(1.0, 3.0)
        self.autoplay_wander_direction = random.choice([-1, 1])
        self.autoplay_fire_timer = 0.0
        self.current_autoplay_velocity = 0.0

        initial_bg_normal = 'assets/auto_down.png' if self.autoplay_enabled else 'assets/auto_normal.png'

        self.autoplay_button = Button(
            background_normal=initial_bg_normal,
            background_down='assets/auto_down.png',
            size_hint=(None, None),
            size=(120, 120),
            pos=(160, 940),
            border=(0, 0, 0, 0),
            on_release=self.toggle_autoplay_ui
        )
        self.add_widget(self.autoplay_button)
        self.back_button = Button(
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            size_hint=(None, None),
            size=(120, 120),
            border=(0, 0, 0, 0),
            pos=(20,940),
            on_release=self.go_to_menu
        )
        self.add_widget(self.back_button)

        icon_size = 60
        spacing = 70
        start_x = 20
        start_y = 20
        for i in range(self.lives):
            frames = self.manager.sprite_frames.get('shapes/shape_8', [])
            icon = Player(frames=frames, size_hint=(None, None), size=(icon_size, icon_size))
            icon.pos = (start_x + (i * spacing), start_y)
            self.add_widget(icon)
            self.life_icons.append(icon)

        self.score_label = Label(
            text=f"SCORE: {self.score}",
            font_name='assets/dogicapixelbold.ttf',
            font_size='32px',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(400, 100),
            halign='right',
            valign='top'
        )

        self.score_label.pos = (self.width - self.score_label.width - 20, self.height - self.score_label.height - 20)
        self.add_widget(self.score_label)
        self.spawn_aliens()
        self._game_event = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def spawn_player(self):
        if self.player and self.player.parent:
            self.remove_widget(self.player)
        player_w = self.width * 0.06
        player_h = player_w

        frames = self.manager.sprite_frames.get('shapes/shape_8', [])
        self.player = Player(frames=frames, size_hint=(None, None), size=(player_w, player_h))
        self.player.pos = (self.width / 2 - self.player.width / 2, self.height * 0.05)
        self.add_widget(self.player)
        self.is_player_destroyed = False

    def spawn_aliens(self):
        num_cols = 8
        num_rows = 4
        alien_w = self.width * 0.05
        alien_h = alien_w
        spacing = alien_w * 0.3
        scale = self.manager.scale_intervals
        num_notes = len(scale)
        note_counter = 0
        for row in range(num_rows):
            for col in range(num_cols):
                x = (spacing + alien_w) * col + spacing
                y = self.height - (spacing + alien_h) * (row + 1) - self.height * 0.1
                note_offset = scale[note_counter % num_notes]
                octave_shift = 12
                midi_note = self.manager.root_note_val + note_offset + octave_shift + 12
                alien_shape_key = random.choice(SPRITE_KEYS)

                frames = self.manager.sprite_frames.get(alien_shape_key, [])

                alien = Alien(
                    frames=frames,
                    size_hint=(None, None),
                    size=(alien_w, alien_h),
                    pos=(x, y),
                    midi_note=midi_note,
                    velocity_x=self.base_alien_speed_x * self.alien_direction
                )
                self.aliens.append(alien)
                self.add_widget(alien)
                note_counter += 1
        self.total_aliens = len(self.aliens)
        if self.total_aliens == 0: self.total_aliens = 1

    def stop_game(self):
        if self._game_event:
            self._game_event.cancel()
            self._game_event = None

        Window.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

        for p in self.projectiles: self.remove_widget(p)
        for f in self.fragments: self.remove_widget(f)
        for a in self.aliens: self.remove_widget(a)
        if self.player: self.remove_widget(self.player)

        # Cleanup UI
        if self.autoplay_button:
            self.remove_widget(self.autoplay_button)
            self.autoplay_button = None
        if self.back_button:
            self.remove_widget(self.back_button)
            self.back_button = None
        for icon in self.life_icons:
            self.remove_widget(icon)
        self.life_icons.clear()
        if self.score_label:
            self.remove_widget(self.score_label)
            self.score_label = None
        if self.game_over_overlay:
            self.remove_widget(self.game_over_overlay)
            self.game_over_overlay = None
        if self.game_over_label:
            self.remove_widget(self.game_over_label)
            self.game_over_label = None

        self.projectiles.clear()
        self.fragments.clear()
        self.aliens.clear()
        self.player = None
        self._keys_down.clear()

    def update(self, dt):
        def lerp(start, end, t): return start + (end - start) * t

        for icon in self.life_icons:
            icon.update_animation(dt)

        if not self.is_player_destroyed:
            if self.autoplay_enabled and self.player:
                current_count = len(self.aliens)
                start_count = self.total_aliens if self.total_aliens > 0 else 1
                targeting_intensity = 1.0 - (current_count / start_count)
                desired_velocity = 0.0
                dodge_threshold = self.player.width * 1.5
                is_dodging = False
                for f in self.fragments:
                    if f.top > self.player.top and abs(f.center_x - self.player.center_x) < dodge_threshold:
                        if f.center_x < self.player.center_x: desired_velocity = self.player_speed
                        else: desired_velocity = -self.player_speed
                        is_dodging = True
                        break
                if not is_dodging:
                    should_track = (random.random() < targeting_intensity) and (len(self.aliens) > 0)
                    if should_track:
                        closest_alien = min(self.aliens, key=lambda a: abs(a.center_x - self.player.center_x))
                        diff = closest_alien.center_x - self.player.center_x
                        desired_velocity = diff * 5.0
                        desired_velocity = max(min(desired_velocity, self.player_speed), -self.player_speed)
                    else:
                        self.autoplay_move_timer -= dt
                        if self.autoplay_move_timer <= 0:
                            self.autoplay_wander_direction *= -1
                            self.autoplay_move_timer = random.uniform(0.5, 1.5)
                        desired_velocity = self.player_speed * 0.8 * self.autoplay_wander_direction
                self.current_autoplay_velocity = lerp(self.current_autoplay_velocity, desired_velocity, dt * self.movement_smoothing)
                self.player.x += self.current_autoplay_velocity * dt
                if self.player.x < 0:
                    self.player.x = 0
                    self.current_autoplay_velocity *= -0.5
                    self.autoplay_wander_direction = 1
                elif self.player.right > self.width:
                    self.player.right = self.width
                    self.current_autoplay_velocity *= -0.5
                    self.autoplay_wander_direction = -1
                self.autoplay_fire_timer -= dt
                if self.autoplay_fire_timer <= 0:
                    fire_lane_width = self.player.width * 1.5
                    can_fire = any(abs(alien.center_x - self.player.center_x) < (fire_lane_width / 2) for alien in self.aliens)
                    if can_fire and not is_dodging:
                        self.fire_projectile()
                        base_rate = random.uniform(0.1, 0.9)
                        self.autoplay_fire_timer = base_rate * (1.0 - (targeting_intensity * 0.5))
            elif not self.autoplay_enabled and self.player:
                move_dist = self.player_speed * dt
                if 'left' in self._keys_down: self.player.x -= move_dist
                if 'right' in self._keys_down: self.player.x += move_dist
            if self.player:
                if self.player.x < 0: self.player.x = 0
                if self.player.right > self.width: self.player.right = self.width
                self.player.update_animation(dt)

        for p in self.projectiles[:]:
            p.move()
            hit = False
            for alien in self.aliens[:]:
                if p.collide_widget(alien):
                    self.projectiles.remove(p)
                    self.remove_widget(p)
                    self.aliens.remove(alien)
                    self.remove_widget(alien)
                    self.create_explosion(alien, is_player=False)
                    self.play_answer_note(alien.midi_note)
                    self.score += 50
                    if self.score_label:
                        self.score_label.text = f"SCORE: {self.score}"
                    hit = True
                    break
            if hit: continue
            if p.top > self.height:
                self.projectiles.remove(p)
                self.remove_widget(p)

        for f in self.fragments[:]:
            f.update_animation(dt)
            if self.player and not self.is_player_destroyed and f.collide_widget(self.player):
                print("Hit by fragment!")
                self.create_explosion(self.player, is_player=True)
                self.is_player_destroyed = True
                self.lives -= 1
                if self.life_icons:
                    removed_icon = self.life_icons.pop()
                    self.remove_widget(removed_icon)

                if self.lives <= 0:
                    self.show_game_over()

            if f.right < 0 or f.x > self.width or f.top < 0 or f.y > self.height:
                self.fragments.remove(f)
                self.remove_widget(f)

        hit_wall = False
        for alien in self.aliens[:]:
            alien.x += alien.velocity_x * dt
            alien.y += alien.velocity_y * dt
            alien.update_animation(dt)
            if (alien.right > self.width and alien.velocity_x > 0) or \
               (alien.x < 0 and alien.velocity_x < 0):
                hit_wall = True

        if hit_wall:
            self.alien_direction *= -1
            self.alien_speed_x *= -1
            self.alien_speed_y = -self.alien_step_down_amount / self.alien_max_move_time
            for alien in self.aliens:
                alien.velocity_x = self.alien_speed_x
                alien.velocity_y = self.alien_speed_y

        self.alien_move_timer -= dt
        if self.alien_move_timer <= 0:
            self.alien_move_timer = self.alien_max_move_time
            self.alien_speed_y = 0
            for alien in self.aliens: alien.velocity_y = 0

        player_zone_y = self.height * 0.05 + (self.width * 0.06)

        if not self.is_player_destroyed:
            for alien in self.aliens:
                if (self.player and alien.top < self.player.top) or (alien.y < player_zone_y):
                     print("Game Over! Aliens reached player zone.")
                     self.lives = 0 # Force 0 lives
                     self.show_game_over()
                     return

        if not self.aliens:
            print("You Win! Resetting...")
            self.reset_game()

        if self.is_player_destroyed and not self.fragments and self.lives > 0:
            self.spawn_player()

    def show_game_over(self):
        if self._game_event:
            self._game_event.cancel()
            self._game_event = None

        self.game_over_overlay = Widget(size_hint=(1, 1))
        with self.game_over_overlay.canvas:
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        self.game_over_label = Label(
            text="GAME OVER",
            font_name='assets/dogicapixelbold.ttf',
            font_size='100px',
            color=(1, 1, 1, 1),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            halign='center',
            valign='middle'
        )

        self.add_widget(self.game_over_overlay)
        self.add_widget(self.game_over_label)

        Clock.schedule_once(lambda dt: self.reset_game(), 1.0)

    def create_explosion(self, widget, is_player):
        frag_w = widget.width / 3.0
        frag_h = widget.height / 3.0
        fragment_frames = self.manager.sprite_frames.get('shapes/flash', [])

        if not fragment_frames: return
        if is_player and self.player:
            self.remove_widget(self.player)
            self.player = None
        for _ in range(4):
            angle_deg = random.uniform(0, 360)
            speed = self.width * random.uniform(0.05, 0.3)
            ang_vel = random.uniform(-300, 300)
            angle_rad = math.radians(angle_deg)
            fragment = Fragment(
                frames=fragment_frames,
                velocity_x=speed * math.cos(angle_rad),
                velocity_y=speed * math.sin(angle_rad),
                angular_velocity=ang_vel,
                size_hint=(None, None),
                size=(frag_w, frag_h),
                center=widget.center
            )
            self.fragments.append(fragment)
            self.add_widget(fragment)

    def play_call_note(self):
        random_interval = random.choice(self.manager.scale_intervals)
        base_note = self.manager.root_note_val - 12
        note = base_note + random_interval
        self.manager.midi.play_note(note, velocity=90, channel=self.manager.player_channel)

    def play_answer_note(self, note):
        self.manager.midi.play_note(note, duration=0.2, velocity=120, channel=self.manager.alien_channel)
        if self.total_aliens > 0:
            remaining_ratio = len(self.aliens) / self.total_aliens
            current_ratio = 1.0 - remaining_ratio
            speed_multiplier = 1.0 + current_ratio * 1.5
            self.alien_speed_x = self.base_alien_speed_x * speed_multiplier * self.alien_direction
            self.alien_max_move_time = 0.5 - (0.4 * current_ratio)
            self.alien_move_timer = self.alien_max_move_time
            for alien in self.aliens:
                alien.velocity_x = self.alien_speed_x

    def fire_projectile(self):
        if not self.player: return
        p_size = self.width * 0.01
        p = Projectile(
            size_hint=(None, None),
            size=(p_size, p_size * 2),
            pos=(self.player.center_x - p_size / 2, self.player.top)
        )
        self.projectiles.append(p)
        self.add_widget(p)
        self.play_call_note()

    def go_to_menu(self, instance):
        self.stop_game()
        self.manager.current = 'menu'

    def on_leave(self, *args):
        self.stop_game()

    def toggle_autoplay_ui(self, instance):
        self.autoplay_enabled = not self.autoplay_enabled
        if self.autoplay_enabled:
            instance.background_normal = 'assets/auto_down.png'
            instance.text = ''
            self.autoplay_move_timer = random.uniform(1.0, 3.0)
            self.autoplay_wander_direction = random.choice([-1, 1])
            self.autoplay_fire_timer = 0.0
            self._keys_down.clear()
        else:
            instance.background_normal = 'assets/auto_normal.png'
            instance.text = ''
            self.current_autoplay_velocity = 0
        print(f"Autoplay: {'ENABLED' if self.autoplay_enabled else 'DISABLED'}")

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True

        if self.autoplay_enabled:
            return False

        if self.player and touch.y < self.height * 0.8:
            self.fire_projectile()
            return True

        return False

    def on_touch_move(self, touch):
        if self.autoplay_enabled: return False
        local_touch = self.to_local(*touch.pos)
        if self.player:
            self.player.center_x = local_touch[0]
            if self.player.x < 0: self.player.x = 0
            if self.player.right > self.width: self.player.right = self.width
            return True
        return super().on_touch_move(touch)

    def _on_key_down(self, window, key, *args):
        if key == 112:
            if self.autoplay_button: self.toggle_autoplay_ui(self.autoplay_button)
            return True
        if self.autoplay_enabled: return True
        if key == 32: self.fire_projectile()
        elif key == 276 or key == 97: self._keys_down.add('left')
        elif key == 275 or key == 100: self._keys_down.add('right')
        return True

    def _on_key_up(self, window, key, *args):
        if key == 276 or key == 97: self._keys_down.discard('left')
        elif key == 275 or key == 100: self._keys_down.discard('right')
        return True

    def reset_game(self):
        was_autoplay_enabled = self.autoplay_enabled
        self.is_player_destroyed = False
        self.stop_game()
        self.alien_direction = 1
        self.on_enter(initial_autoplay=was_autoplay_enabled)

class ArcadeMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.grid = Grid(size_hint=(1, 1))
        self.add_widget(self.grid)

        self.bg_panel = Image(
            source='assets/panel_02_OSD.png',
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.bg_panel)

        main_layout = BoxLayout(
            orientation='vertical',
            padding=80,
            spacing=60,
            size_hint_y=0.7,
            pos=(0, 280)
        )

        row_key = BoxLayout(
            orientation='horizontal',
            spacing=0,
            padding=(50, 0, 0, 0)
        )

        row_key.add_widget(AlignedLabel(
            text="Key:",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.17,
            font_size='31px',
            halign='left',
            valign='middle',
            color=(0.1, 0.1, 0.1, 1)
        ))

        self.key_val_label = AlignedLabel(
            text=NOTES[0],
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.23,
            font_size='31px',
            halign='left',
            valign='middle',
            color=(0.1, 0.1, 0.1, 1)
        )
        row_key.add_widget(self.key_val_label)

        self.key_slider = Slider(
            min=0,
            max=len(NOTES) - 1,
            value=0,
            step=1,
            size_hint_x=0.6,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            padding=60
        )
        self.key_slider.bind(value=self.on_key_change)
        row_key.add_widget(self.key_slider)
        main_layout.add_widget(row_key)

        row_scale = BoxLayout(
            orientation='horizontal',
            spacing=0,
            padding=(50, 0, 0, 0)
        )

        default_scale = 'MAJOR'
        default_scale_idx = SCALE_NAMES.index(default_scale) if default_scale in SCALE_NAMES else 0

        row_scale.add_widget(AlignedLabel(
            text="Scale:",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.17,
            font_size='31px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        ))

        self.scale_val_label = AlignedLabel(
            text=SCALE_NAMES[default_scale_idx],
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.23,
            line_height=1.2,
            font_size='31px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        )
        row_scale.add_widget(self.scale_val_label)

        self.scale_slider = Slider(
            min=0,
            max=len(SCALE_NAMES) - 1,
            value=default_scale_idx,
            step=1,
            size_hint_x=0.6,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            padding=60
        )
        self.scale_slider.bind(value=self.on_scale_change)
        row_scale.add_widget(self.scale_slider)
        main_layout.add_widget(row_scale)

        row_p_chan = BoxLayout(
            orientation='horizontal',
            spacing=0,
            padding=(50, 0, 0, 0))

        row_p_chan.add_widget(AlignedLabel(
            text="Player CH:",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.17,
            font_size='31px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        ))

        self.player_chan_val_label = AlignedLabel(
            text="1",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.23,
            font_size='31px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        )
        row_p_chan.add_widget(self.player_chan_val_label)

        self.player_chan_slider = Slider(
            min=1,
            max=16,
            value=1,
            step=1,
            size_hint_x=0.6,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            padding=60
        )
        self.player_chan_slider.bind(value=self.on_player_chan_change)
        row_p_chan.add_widget(self.player_chan_slider)
        main_layout.add_widget(row_p_chan)

        row_a_chan = BoxLayout(
            orientation='horizontal',
            spacing=0,
            padding=(50, 0, 0, 0)
        )

        row_a_chan.add_widget(AlignedLabel(
            text="Alien CH:",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.17,
            font_size='31px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        ))

        self.alien_chan_val_label = AlignedLabel(
            text="2",
            font_name='assets/dogicapixelbold.ttf',
            size_hint_x=0.23,
            font_size='32px',
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1)
        )
        row_a_chan.add_widget(self.alien_chan_val_label)

        self.alien_chan_slider = Slider(
            min=1,
            max=16,
            value=2,
            step=1,
            size_hint_x=0.6,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            padding=60
        )
        self.alien_chan_slider.bind(value=self.on_alien_chan_change)
        row_a_chan.add_widget(self.alien_chan_slider)
        main_layout.add_widget(row_a_chan)

        main_layout.add_widget(Widget())

        self.add_widget(main_layout)

        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=300,
            size_hint=(None, None),
            height=200,
            width=440,
            pos=(990, 140)
        )

        back_button = Button(
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            size_hint=(None, None),
            size=(200, 200),
            border=(0, 0, 0, 0)
        )
        back_button.bind(on_release=self.on_back_pressed)
        button_layout.add_widget(back_button)

        start_button = Button(
            background_normal='assets/start_button.png',
            background_down='assets/start_button_pressed.png',
            size_hint=(None, None),
            size=(200, 200),
            border=(0, 0, 0, 0),
            on_press=self.start_game
        )
        button_layout.add_widget(start_button)

        self.add_widget(button_layout)

    def on_key_change(self, instance, value):
        idx = int(value)
        self.key_val_label.text = NOTES[idx]

    def on_scale_change(self, instance, value):
        idx = int(value)
        self.scale_val_label.text = SCALE_NAMES[idx]

    def on_player_chan_change(self, instance, value):
        val = int(value)
        self.player_chan_val_label.text = str(val)

    def on_alien_chan_change(self, instance, value):
        val = int(value)
        self.alien_chan_val_label.text = str(val)

    def on_back_pressed(self, instance):
        # Use the app_switcher from the manager
        print("Back button pressed - Returning to Goodies Menu")
        if self.manager.app_switcher:
            self.manager.app_switcher('goodies_menu')

    def start_game(self, instance):
        key_idx = int(self.key_slider.value)
        scale_idx = int(self.scale_slider.value)

        selected_key = NOTES[key_idx]
        selected_scale_name = SCALE_NAMES[scale_idx]

        self.manager.root_note_val = BASE_MIDI_NOTE + key_idx
        self.manager.scale_intervals = SCALES[selected_scale_name]
        self.manager.player_channel = int(self.player_chan_slider.value) - 1
        self.manager.alien_channel = int(self.alien_chan_slider.value) - 1

        print(f"Start: Key={selected_key}, Scale={selected_scale_name}")
        print(f"MIDI: Player Ch={self.manager.player_channel + 1}, Alien Ch={self.manager.alien_channel + 1}")

        self.manager.midi.open()
        self.manager.current = 'game'

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
        if not content_width or not content_height or not self.width or not self.height: return
        scale_x = self.width / content_width
        scale_y = self.height / content_height
        scale = min(scale_x, scale_y)
        scaled_width = content_width * scale
        scaled_height = content_height * scale
        new_pos_x = self.x + (self.width - scaled_width) / 2.0
        new_pos_y = self.y + (self.height - scaled_height) / 2.0
        epsilon = 1e-6
        if (hasattr(content, 'scale') and abs(content.scale - scale) > epsilon) or \
           (abs(content.pos[0] - new_pos_x) > epsilon) or \
           (abs(content.pos[1] - new_pos_y) > epsilon):
            if hasattr(content, 'scale'): content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

class _ShapeArcadeWorld(ScreenManager):
    def __init__(self, app_switcher, midi_controller, sprite_frames, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.midi = midi_controller
        self.sprite_frames = sprite_frames
        self.root_note_val = 60
        self.scale_intervals = SCALES['MAJOR']
        self.player_channel = 0
        self.alien_channel = 1
        self.add_widget(ArcadeMenuScreen(name='menu'))
        self.add_widget(ArcadeGameScreen(name='game'))
        self.current = 'menu'

class ShapeArcadeRoot(FitLayout):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)

        self.sprite_frames = load_sprite_frames()
        self.midi = MidiController(external_midi_out=main_midi_out)

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )

        self.world = _ShapeArcadeWorld(
            app_switcher=app_switcher,
            midi_controller=self.midi,
            sprite_frames=self.sprite_frames
        )

        self.scatter.add_widget(self.world)
        self.add_widget(self.scatter)

    def cleanup_app(self):
        print("Cleaning up Shape Arcade...")
        if self.world.has_screen('game'):
            game_screen = self.world.get_screen('game')
            game_screen.stop_game()

        self.midi.close()
