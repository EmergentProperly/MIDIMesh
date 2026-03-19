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
import os
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.logger import Logger
from kivy.resources import resource_add_path

from misc.grid import Grid
from midimesh.main.control_panel.onscreen_minikeys import OnScreenKeyboards


normal_img = 'assets/back_normal.png'
down_img = 'assets/back_pressed.png'

LabelBase.register(
    name='dogicapixelbold',
    fn_regular='assets/dogicapixelbold.ttf',
)

try:
    assets_dir = os.path.join(base_dir, '../assets')
except NameError:
    assets_dir = os.path.join(os.path.abspath(os.getcwd()), 'assets')

resource_add_path(assets_dir)
print(f"INFO: Added Kivy resource path: {assets_dir}")


# MIDI Connectivity (TO DO: separate this into its own module and remove duplicate code across mini apps)
if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("BlowingUpShapes: Successfully imported AndroidMidi")
    except ImportError:
        print("BlowingUpShapes: Could not import AndroidMidi")

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import rtmidi
        print("BlowingUpShapes: Successfully imported WindowsMidi (aliased) and rtmidi")
    except ImportError:
        print("BlowingUpShapes: Could not import windows_midi or rtmidi")

else:
    try:
        import rtmidi
        print("BlowingUpShapes: Successfully imported rtmidi")
    except ImportError:
        print("BlowingUpShapes: rtmidi not found.")

kivy.require('2.1.0')

class ImageButton(ButtonBehavior, Image):
    def __init__(self, normal_img, down_img=None, **kwargs):
        super().__init__(**kwargs)
        self.normal_img = normal_img
        self.down_img = down_img or normal_img
        self.source = normal_img

    def on_press(self):
        self.source = self.down_img

    def on_release(self):
        self.source = self.normal_img

class FitLayout(FloatLayout):
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


NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
NOTE_NAMES = {v: k for k, v in NOTES.items()} # Reverse lookup for root key
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
    'MIXALODIAN': [0, 2, 4, 5, 7, 9, 10],
    'LOCRIAN': [0, 1, 3, 5, 6, 8, 10],
    'HARMONIC\nMINOR': [0, 2, 3, 5, 7, 8, 11],
    'HARMONIC\nMAJOR': [0, 2, 4, 5, 7, 8, 11],
    'MELODIC MINOR\n(Ascending)': [0, 2, 3, 5, 7, 9, 11],
    'WHOLE TONE': [0, 2, 4, 6, 8, 10],
    'DIMINISHED\n(Half-Whole)': [0, 1, 3, 4, 6, 7, 9, 10],
    'DIMINISHED\n(Whole-Half)': [0, 2, 3, 5, 6, 8, 9, 11],
    'AUGMENTED': [0, 3, 4, 7, 8, 11],
    'ENIGMATIC': [0, 1, 4, 6, 8, 10, 11],
}


def generate_scale_notes(key_name, scale_name, octaves=3, base_octave=3):
    base_note = NOTES[key_name]
    scale_intervals = SCALES[scale_name]
    notes = []
    for o in range(octaves):
        octave_offset = (base_octave + o) * 12
        for interval in scale_intervals:
            notes.append(base_note + interval + octave_offset)
    return notes

class GrowingBlob:
    def __init__(self, pos, growth_rate, visualizer, **kwargs):
        self.pos = Vector(pos)
        self.growth_rate = 15
        self.size = 2.0
        self.color = [random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), 0.8]
        self.age = 0.0
        self.max_age = random.uniform(8.0, 12.0)

        self.visualizer = visualizer


        self.is_waiting_to_explode = False

        self.shape_key = 'shape_2'
        self.frames = self.visualizer.shape_frames.get(self.shape_key, [])
        self.num_frames = len(self.frames)
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.04

    def _send_note_off(self, note, midi):
        try:
            midi.send_message([0x80, note, 0])
        except Exception as e:
            print(f"GrowingBlob MIDI Stop Error: {e}")

    def update(self, dt):
        should_cap = self.is_waiting_to_explode and self.age >= self.max_age

        if should_cap:
            max_cap_size = max(80.0, self.max_age * self.visualizer.growth_rate * 5) + 20
            if self.size < max_cap_size:
                 self.size += self.growth_rate * dt
        else:
            self.size += self.growth_rate * dt
            self.age += dt

        if self.num_frames > 1:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % self.num_frames

    def collide_point(self, x, y):
        touch_pos = Vector(x, y)
        distance = self.pos.distance(touch_pos)
        return distance < (self.size / 2)

    def draw(self, widget):
        with widget.canvas:
            current_frame = self.frames[self.frame_index] if self.frames else None
            if current_frame:
                Color(1, 1, 1, 1)
                Ellipse(
                    pos=(self.pos[0] - self.size / 2, self.pos[1] - self.size / 2),
                    size=(self.size, self.size),
                    source=current_frame
                )
            else:
                Color(*self.color)
                Ellipse(pos=(self.pos[0] - self.size / 2, self.pos[1] - self.size / 2),
                        size=(self.size, self.size))

    def explode(self, visualizer):
        self.is_waiting_to_explode = False

        num_blobs = random.randint(4, 5)

        octave = max(1, 6 - int(self.size / 60))
        new_blob_size = 60.0

        if new_blob_size < visualizer.min_diameter:
            print(f"GrowingBlob explosion aborted: New size {new_blob_size} < min_diameter {visualizer.min_diameter}")
            if self in visualizer.blobs:
                visualizer.blobs.remove(self)
            return

        parent_octave = max(1, octave - 1)
        parent_note = visualizer.get_notes_for_blobs(1, parent_octave)[0]

        if visualizer.midi:
            try:
                velocity = int(self.size) % 127 + 50
                visualizer.midi.send_message([0x90, parent_note, min(127, velocity)])

                Clock.schedule_once(
                    lambda dt, note=parent_note, midi=visualizer.midi: midi.send_message([0x80, note, 0]),
                    0.2
                )
            except Exception as e:
                print(f"GrowingBlob MIDI Send Error: {e}")

        notes = visualizer.get_notes_for_blobs(num_blobs, octave)

        for i in range(num_blobs):
            angle = random.uniform(0, 360)
            speed = random.uniform(100, 250)
            velocity = Vector(speed, 0).rotate(angle)

            separation = new_blob_size / 2.0 + 2.0
            start_pos = self.pos + velocity.normalize() * separation

            new_blob = BouncingBlob(
                pos=start_pos,
                velocity=velocity,
                note=notes[i],
                midi=visualizer.midi,
                visualizer=visualizer,
                collision_cooldown=0.5,
                size=new_blob_size,
                generation=1
            )
            visualizer.blobs.append(new_blob)

        if self in visualizer.blobs:
            visualizer.blobs.remove(self)

    def _send_note_off(self, note, midi):
        try:
            midi.send_message([0x80, note, 0])
        except Exception as e:
            print(f"GrowingBlob MIDI Stop Error: {e}")


class BouncingBlob:
    def __init__(self, pos, velocity, note, midi, visualizer, collision_cooldown=0.0, size=25.0, generation=1):
        self.pos = Vector(pos)
        self.velocity = velocity
        self.note = note
        self.midi = midi
        self.visualizer = visualizer
        self.size = size
        self.original_color = [random.uniform(0.5, 1.0) for _ in range(3)] + [1.0]
        self.color = self.original_color[:]
        self.playing = False
        self.collision_cooldown = collision_cooldown
        self.generation = generation
        self.shape_key = f'shape_{min(self.generation, 10)}'
        self.frames = visualizer.shape_frames.get(self.shape_key, [])
        self.num_frames = len(self.frames)
        self.frame_index = 0
        self.frame_timer = random.uniform(0.0, 0.1)
        self.frame_duration = 0.05
        self.is_flashing = False
        self.flash_frames = visualizer.shape_frames.get('flash', [])
        self.flash_index = 0
        self.flash_timer = 0.0
        self.flash_frame_duration = 0.03
        self.flash_duration = len(self.flash_frames) * self.flash_frame_duration

    def update(self, dt):
        self.pos += self.velocity * dt
        if self.collision_cooldown > 0:
            self.collision_cooldown -= dt

        if not self.is_flashing and self.num_frames > 1:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % self.num_frames

        if self.is_flashing and self.flash_frames:
            self.flash_timer += dt
            self.flash_index = int(self.flash_timer / self.flash_frame_duration)
            if self.flash_timer >= self.flash_duration:
                self.is_flashing = False
                self.flash_timer = 0.0
                self.flash_index = 0


    def draw(self, widget):
        with widget.canvas:
            current_frame = None
            if self.is_flashing and self.flash_frames:
                flash_idx = min(self.flash_index, len(self.flash_frames) - 1)
                current_frame = self.flash_frames[flash_idx]
            elif self.frames:
                current_frame = self.frames[self.frame_index]

            if current_frame:
                Color(1, 1, 1, 1)
                Ellipse(
                    pos=(self.pos[0] - self.size / 2, self.pos[1] - self.size / 2),
                    size=(self.size, self.size),
                    source=current_frame
                )
            else:
                Color(*self.color)
                Ellipse(pos=(self.pos[0] - self.size / 2, self.pos[1] - self.size / 2),
                        size=(self.size, self.size))

    def check_wall_wrap(self, bounds_size):
        w, h = bounds_size
        r = self.size / 2

        if self.pos.x + r < 0:
            self.pos.x = w + r
        elif self.pos.x - r > w:
            self.pos.x = -r

        # Check Y-axis
        if self.pos.y + r < 0:
            self.pos.y = h + r
        elif self.pos.y - r > h:
            self.pos.y = -r

    def check_blob_collision(self, other):
        if self.collision_cooldown > 0 or other.collision_cooldown > 0:
            return False

        dist = self.pos.distance(other.pos)
        min_dist = self.size / 2 + other.size / 2

        if dist < min_dist and dist > 0:
            self.velocity, other.velocity = other.velocity, self.velocity
            overlap = (min_dist - dist) / 2
            separation_vec = (self.pos - other.pos).normalize()
            self.pos += separation_vec * overlap
            other.pos -= separation_vec * overlap

            if random.random() < 0.5:
                self.handle_collision(play_note=True)
                other.handle_collision(play_note=False)
            else:
                self.handle_collision(play_note=False)
                other.handle_collision(play_note=True)

            return True
        return False

    def handle_collision(self, play_note=True):
        if play_note:
            self.play_note()

        self.is_flashing = True
        self.flash_timer = 0.0
        self.flash_index = 0
        self.collision_cooldown = 0.5

        new_size = self.size * 0.5
        if new_size >= self.visualizer.min_diameter:
            self.fracture(new_size)
            if self in self.visualizer.blobs:
                self.visualizer.blobs.remove(self)
                print(f"Removed fractured blob with note {self.note}")
        else:
            if self in self.visualizer.blobs:
                self.visualizer.blobs.remove(self)
                print(f"Removed dead blob (too small) with note {self.note}")

    def fracture(self, new_size):
        if not self.visualizer: return
        num_offspring = 2
        current_octave = self.note // 12
        new_octave = min(current_octave + 1, 8) # Cap at octave 8
        notes = self.visualizer.get_notes_for_blobs(num_offspring, new_octave)

        if not notes:
            print(f"Fracture: Could not get notes for octave {new_octave}")
            return

        new_generation = self.generation + 1

        for i in range(num_offspring):
            angle = random.uniform(0, 360)
            speed = self.velocity.length()
            speed = max(40, speed) * random.uniform(0.8, 1)
            velocity = Vector(speed, 0).rotate(angle)

            new_blob = BouncingBlob(
                pos=Vector(self.pos),
                velocity=velocity,
                note=notes[i],
                midi=self.midi,
                collision_cooldown=0.5,
                visualizer=self.visualizer,
                size=new_size,
                generation=new_generation
            )
            self.visualizer.blobs.append(new_blob)

    def play_note(self):
        if self.playing or not self.midi:
            return

        self.playing = True
        try:
            velocity = int(random.uniform(30, 100))
            self.midi.send_message([0x90, self.note, velocity])
            Clock.schedule_once(
                lambda dt, m=self.midi, n=self.note: m.send_message([0x80, n, 0]),
                0.15
            )
        except Exception as e:
            print(f"MIDI Send Error: {e}")
            self.playing = False


class MenuAppContainer(FitLayout):
    def __init__(self, menu_content_world, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_bg, pos=self._update_bg)
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )

        self.scatter.add_widget(menu_content_world)
        self.add_widget(self.scatter)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

class MenuWorld(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (1920, 1080)

        grid_bg = Grid()
        self.add_widget(grid_bg)

        panel_width = 1600
        panel_height = 900
        panel_x = (1920 - panel_width) / 2
        panel_y = (1080 - panel_height) / 2

        self.panel_bg = Image(
            source='assets/panel_01_OSD.png',
            size_hint=(None, None),
            size=(panel_width, panel_height),
            pos=(panel_x, panel_y),
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.panel_bg)
        self.layout = BoxLayout(
            orientation='vertical',
            padding=[200, 200, 140, 100],
            spacing=60,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.layout)

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        self.scale_names = list(SCALES.keys())
        self.num_scales = len(self.scale_names)
        self.menu_world = MenuWorld()
        layout = self.menu_world.layout

        scale_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=80,padding=[100, 0, 100, 0])

        self.scale_label = Label(
            text=f'{self.scale_names[0]}',
            color=(0.1, 0.1, 0.1, 1),
            line_height=1.5,
            font_size='34px',
            size_hint_x=0.3
        )

        self.scale_slider = Slider(
            min=0,
            max=self.num_scales - 1,
            value=self.scale_names.index('MAJOR'),
            step=1,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.7
        )

        self.scale_slider.bind(value=self.on_scale_slider_update)
        scale_layout.add_widget(self.scale_label)
        scale_layout.add_widget(self.scale_slider)
        layout.add_widget(scale_layout)
        diameter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=80,padding=[100, 0, 100, 0])

        self.diameter_label = Label(
            text='MIN SIZE: 10.0',
            color=(0.1, 0.1, 0.1, 1),
            font_size='34px',
            size_hint_x=0.3
        )

        self.diameter_slider = Slider(
            min=7,
            max=50,
            value=10.0,
            step=1.0,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.7
        )
        self.diameter_slider.bind(value=self.on_other_slider_update)
        diameter_layout.add_widget(self.diameter_label)
        diameter_layout.add_widget(self.diameter_slider)
        layout.add_widget(diameter_layout)

        growth_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=80,padding=[100, 0, 100, 0])

        self.growth_label = Label(
            text='SPAWN: 2.0',
            color=(0.1, 0.1, 0.1, 1),
            font_size='34px',
            size_hint_x=0.3
        )

        self.growth_slider = Slider(
            min=0.1,
            max=10.0,
            value=2.0,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.7
        )
        self.growth_slider.bind(value=self.on_other_slider_update)
        growth_layout.add_widget(self.growth_label)
        growth_layout.add_widget(self.growth_slider)
        layout.add_widget(growth_layout)

        layout.add_widget(BoxLayout())
        button_layout = BoxLayout(orientation='horizontal',
                                  size_hint_x=0.5,
                                  size_hint_y=None,
                                  height=220,
                                  spacing=52,
                                  padding=[40, 00, 250, 0]
                                  )

        start_button = Button(
            text='',
            font_size='28px',
            color=(0.0, 0.0, 0.0, 1),
            background_normal='assets/start_button.png',
            background_down='assets/start_button_pressed.png',
            border=(0, 0, 0, 0),
            size_hint_y=1
        )
        start_button.bind(on_release=self.start_visualizer)
        button_layout.add_widget(start_button)

        back_button = Button(
            text='',
            font_size='28px',
            color=(0.0, 0.0, 0.0, 1),
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            border=(0, 0, 0, 0),
            background_color=(1, 1, 1, 1),
            size_hint_y=1
        )
        back_button.bind(on_release=lambda x: App.get_running_app().switch_to_widget('goodies_menu'))
        button_layout.add_widget(back_button)

        layout.add_widget(button_layout)
        layout.add_widget(BoxLayout(size_hint_y=0.1))

        menu_container = MenuAppContainer(menu_content_world=self.menu_world)
        self.add_widget(menu_container)

    def on_other_slider_update(self, instance, value):
        if instance == self.diameter_slider:
            self.diameter_label.text = f'MIN SIZE: {value:.1f}'
        elif instance == self.growth_slider:
            self.growth_label.text = f'SPAWN: {value:.1f}'

    def on_scale_slider_update(self, instance, value):
        index = int(value)
        current_scale_name = self.scale_names[index]
        self.scale_label.text = current_scale_name

    def start_visualizer(self, instance):
        visualizer_screen = self.manager.get_screen('visualizer')
        scale_index = int(self.scale_slider.value)
        selected_scale = self.scale_names[scale_index]

        visualizer_screen.settings = {
            'scale': selected_scale,
            'min_diameter': self.diameter_slider.value,
            'growth_rate': self.growth_slider.value / 10.0
        }

        visualizer_screen.start()
        self.manager.current = 'visualizer'

    def get_settings(self):
        scale_index = int(self.scale_slider.value)
        selected_scale = self.scale_names[scale_index]

        return {
            'scale': selected_scale,
            'min_diameter': self.diameter_slider.value,
            'growth_rate': self.growth_slider.value / 10.0
        }

class AppContainer(FitLayout):
    def __init__(self, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )

        self.world = VisualizerWorld(main_midi_out=main_midi_out)
        self.scatter.add_widget(self.world)
        self.add_widget(self.scatter)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class HideUIButton(ButtonBehavior, Image):
    def __init__(self, visualizer_world, **kwargs):
        super().__init__(**kwargs)
        self.visualizer_world = visualizer_world
        self.source = 'assets/hide_UI_normal.png'
        self.size_hint = (None, None)
        self.size = (100, 100)

    def on_press(self):
        self.source = 'assets/hide_UI_pressed.png'

    def on_release(self):
        self.source = 'assets/hide_UI_normal.png'
        if self.visualizer_world:
            self.visualizer_world.toggle_ui_state()

class VisualizerWorld(FloatLayout):
    def __init__(self, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        print("VisualizerWorld __init__ starting...")
        # Set fixed virtual size
        self.size_hint = (None, None)
        self.size = (1920, 1080)
        self.settings = {}
        self.blobs = []
        self.scale_notes = []
        self.min_diameter = 10.0
        self.growth_rate = 0.2
        self.MAX_GROWING_BLOBS = 5
        self.MAX_BLOBS = 60
        self.SANE_BLOBS = 50
        self.spawn_timer = 0
        self.midi = None
        self.main_midi_out = main_midi_out
        self.game_loop = None
        self.info_label = None
        self.speed_multiplier = 1.0
        self.key = 'C'
        self.base_octave = 4
        self.scale_name = 'Pentatonic Major'
        self.shape_frames = {}
        self.CELL_SIZE = 100
        self.grid = {}
        self.rupture_cascade_timer = 0.0
        self.RUPTURE_INTERVAL = 1
        self.grid_bg = Grid(
            size_hint=(None, None),
            size=(1920, 1080),
            pos=(0, 0)
        )
        self.add_widget(self.grid_bg)
        self.control_panel = FloatLayout(
            size_hint=(None, None),
            width=1920,
            height=140,
            pos=(0,940),
        )

        with self.control_panel.canvas.before:
            Color(1, 1, 1, 1)
            self.control_panel_bg = Rectangle(
                pos=self.control_panel.pos,
                size=self.control_panel.size,
                source='assets/panel_02.png'
            )

        def update_control_panel_bg(instance, value):
            self.control_panel_bg.pos = instance.pos
            self.control_panel_bg.size = instance.size

        self.control_panel.bind(pos=update_control_panel_bg, size=update_control_panel_bg)

        self.ui_visible = True

        self.hide_ui_button = HideUIButton(visualizer_world=self)
        self.hide_ui_button.pos = (20, 20)

        self.hide_ui_label = Label(
            text="HIDE",
            font_size='24px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100),
            pos=(20, 20)
        )

        self.add_widget(self.hide_ui_button)
        self.add_widget(self.hide_ui_label)

        self.back_button = ImageButton(
            normal_img=normal_img,
            down_img=down_img,
            size_hint=(None, None),
            size=(145, 195),
            pos=(0,910)
        )

        self.back_button.bind(on_release=self.go_to_menu)
        self.control_panel.add_widget(self.back_button)

        self.speed_slider = Slider(
            min=0.1,
            max=3.0,
            value=1.0,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            padding=180,
            pos=(90,935)
        )
        self.speed_slider.bind(value=self.on_speed_update)
        self.control_panel.add_widget(self.speed_slider)
        self.add_widget(self.control_panel)
        self.keyboard = OnScreenKeyboards(midi_callback=self.on_key_press_release)
        self.keyboard.pos = (540, 20)
        self.add_widget(self.keyboard)

    def toggle_ui_state(self):
        self.ui_visible = not self.ui_visible

        target_opacity = 1 if self.ui_visible else 0
        is_disabled = not self.ui_visible

        self.control_panel.opacity = target_opacity
        self.control_panel.disabled = is_disabled

        self.keyboard.opacity = target_opacity
        self.keyboard.disabled = is_disabled

        self.hide_ui_label.text = "HIDE" if self.ui_visible else "UN-\nHIDE"

    def on_key_press_release(self, message_type, note, velocity):

        if message_type == 'note_on':
            root_note_value = note % 12
            self.key = NOTE_NAMES.get(root_note_value, 'C')
            self.base_octave = self.keyboard.current_octave

            self.update_scale_notes()

    def load_all_shape_frames(self):
        self.shape_frames = {}
        try:
            base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../assets/shapes')
        except NameError:
            base_path = os.path.join(os.path.abspath(os.getcwd()), '../assets/shapes')

        shape_dirs = [f'shape_{i}' for i in range(11)] + ['flash']

        def to_kivy_path(sys_path):
            return sys_path.replace(os.sep, '/')

        for shape_name in shape_dirs:
            dir_path = os.path.join(base_path, shape_name)

            if not os.path.isdir(dir_path):
                print(f"WARNING: Shape directory not found: {dir_path}")
                continue

            all_files = os.listdir(dir_path)

            system_paths = [os.path.join(dir_path, f) for f in all_files if f.endswith('.png')]

            sorted_system_paths = sorted(system_paths)

            frames = [to_kivy_path(p) for p in sorted_system_paths]

            if frames:
                self.shape_frames[shape_name] = frames
                print(f"Loaded {len(frames)} frames for {shape_name} from {dir_path}")
            else:
                print(f"INFO: No PNG frames found in {dir_path}")


    def on_speed_update(self, instance, value):
        self.speed_multiplier = value

    def populate_grid(self):
        self.grid = {}
        if self.width == 0 or self.height == 0: return
        self.num_cells_x = int(self.width / self.CELL_SIZE) + 1
        self.num_cells_y = int(self.height / self.CELL_SIZE) + 1

        for blob in self.blobs:
            if isinstance(blob, BouncingBlob):
                ix = int(blob.pos.x / self.CELL_SIZE)
                iy = int(blob.pos.y / self.CELL_SIZE)
                key = (ix % self.num_cells_x, iy % self.num_cells_y)

                if key not in self.grid:
                    self.grid[key] = []
                self.grid[key].append(blob)


    def grid_check_collisions(self, blob_a):
        ix = int(blob_a.pos.x / self.CELL_SIZE) % self.num_cells_x
        iy = int(blob_a.pos.y / self.CELL_SIZE) % self.num_cells_y

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx = (ix + dx + self.num_cells_x) % self.num_cells_x
                ny = (iy + dy + self.num_cells_y) % self.num_cells_y

                neighbor_key = (nx, ny)

                if neighbor_key in self.grid:
                    for blob_b in self.grid[neighbor_key]:
                        if blob_a is blob_b:
                            continue

                        if id(blob_a) >= id(blob_b):
                            continue

                        blob_a.check_blob_collision(blob_b)

    def cascading_rupture(self, dt):
        current_count = len(self.blobs)
        growing_count = sum(1 for b in self.blobs if isinstance(b, GrowingBlob))

        if current_count > self.SANE_BLOBS:
            self.rupture_cascade_timer = 0.0
            return
        if growing_count >= self.MAX_GROWING_BLOBS:
            # print("Cascade blocked: MAX_GROWING_BLOBS reached.")
            return

        self.rupture_cascade_timer += dt

        if self.rupture_cascade_timer > self.RUPTURE_INTERVAL:
            self.rupture_cascade_timer = 0.0
            waiting_blob = next(
                (b for b in self.blobs if isinstance(b, GrowingBlob) and b.is_waiting_to_explode),
                None
            )

            if waiting_blob:
                print(f"Cascading Rupture: Forcing standby blob to explode. Current total: {current_count}")
                waiting_blob.explode(self)
            else:
                pass


    def start(self):
        self.cleanup()

        self.load_all_shape_frames()


        self.scale_name = self.settings.get('scale', 'Pentatonic Major')
        self.min_diameter = self.settings.get('min_diameter', 10.0)
        self.growth_rate = self.settings.get('growth_rate', 0.2)
        self.base_octave = self.keyboard.current_octave
        self.key = NOTE_NAMES.get((self.base_octave + 1) * 12 % 12, 'C')
        self.update_scale_notes()
        if self.main_midi_out:
            self.midi = self.main_midi_out
            print("INFO: Using main app MIDI port.")
        elif not self.midi:
            if platform in ('android', 'win') and AndroidMidi:
                print(f"Initializing MIDI Out via wrapper ({platform})...")
                try:
                    self.midi = AndroidMidi()
                    if hasattr(self.midi, 'open_output'):
                        self.midi.open_output()
                    if platform == 'win' and hasattr(self.midi, 'get_host_devices'):
                        devs = self.midi.get_host_devices()
                        if devs:
                            print(f"Auto-connecting to: {devs[0][0]}")
                            self.midi.connect_to_device(devs[0][1])

                except Exception as e:
                    print(f"MIDI Out wrapper error: {e}")

            elif rtmidi:
                print("INFO: No main app MIDI port found, creating rtmidi fallback.")
                try:
                    self.midi = rtmidi.MidiOut()
                    ports = self.midi.get_ports()
                    if ports:
                        self.midi.open_port(0)
                    else:
                        self.midi.open_virtual_port("Blowing Shapes Out")
                except Exception as e:
                    print(f"rtmidi init error: {e}")

        self.info_label = Label(
            text='Tap the screen to begin',
            font_size='24sp',
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.info_label)
        self.game_loop = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def cleanup(self):
        if self.game_loop:
            self.game_loop.cancel()
            self.game_loop = None
        self.blobs = []
        self.canvas.after.clear()
        self.grid = {}
        if self.info_label and self.info_label.parent:
            self.remove_widget(self.info_label)
            self.info_label = None

    def go_to_menu(self, instance):
        current_widget = self.parent
        manager = None
        for _ in range(4):
            if current_widget:
                current_widget = current_widget.parent
            else:
                break

        if current_widget and isinstance(current_widget, ScreenManager):
            manager = current_widget
            manager.current = 'main_menu'
        else:
            print("ERROR: Could not find the ScreenManager to go back to the menu.")


    def on_pre_leave(self, *args):
        self.cleanup()

        if self.midi:
            try:
                self.midi.send_message([0xB0, 123, 0])
                print("Visualizer: Sent All Notes Off.")
            except Exception as e:
                print(f"Visualizer: Error sending All Notes Off: {e}")
            if self.midi is not self.main_midi_out:
                print("Visualizer: Closing fallback MIDI port.")
                self.midi.close()
                self.midi = None
            else:
                print("Visualizer: Not closing shared main app MIDI port.")

    def update_scale_notes(self):
        self.scale_notes = generate_scale_notes(
            self.key,
            self.scale_name,
            octaves=7,
            base_octave=1
        )
        print(f"Scale updated: Key={self.key}, Scale={self.scale_name}, Base Octave={self.base_octave}")

    def update(self, dt):
        self.grid_bg.canvas.clear()

        physics_dt = dt * self.speed_multiplier
        current_count = len(self.blobs)
        self.cascading_rupture(dt)
        has_waiting_blobs = any(b.is_waiting_to_explode for b in self.blobs if isinstance(b, GrowingBlob))

        self.populate_grid()

        for blob in self.blobs[:]:
            if blob not in self.blobs: continue

            if isinstance(blob, GrowingBlob):

                blob.update(dt)
                blob.draw(self.grid_bg)

                if blob.age > blob.max_age:

                    if current_count >= self.MAX_BLOBS:
                         blob.is_waiting_to_explode = True
                         continue

                    if blob.is_waiting_to_explode:
                        continue

                    else:
                         blob.explode(self)
                         continue



            elif isinstance(blob, BouncingBlob):
                blob.update(physics_dt)
                blob.draw(self.grid_bg)

                blob.check_wall_wrap((self.width, self.height))

                if blob in self.blobs:
                    self.grid_check_collisions(blob)

                if blob in self.blobs and blob.size < self.min_diameter:
                    self.blobs.remove(blob)

        self.spawn_timer += dt
        spawn_interval = 3.33 / self.growth_rate
        if self.spawn_timer > spawn_interval:
            self.spawn_timer = 0
            if not (self.info_label and self.info_label.parent):

                current_count = len(self.blobs)
                if current_count >= self.MAX_BLOBS:
                    print(f"Auto-spawn blocked: MAX_BLOBS ({self.MAX_BLOBS}) reached.")
                    return

                if has_waiting_blobs and current_count > self.SANE_BLOBS:
                    print(f"Auto-spawn blocked: Waiting blobs present and count {current_count} > SANE_BLOBS {self.SANE_BLOBS}.")
                    return

                self.spawn_growing_blob()

    def spawn_growing_blob(self):
        growing_count = sum(1 for b in self.blobs if isinstance(b, GrowingBlob))
        if growing_count >= self.MAX_GROWING_BLOBS:
            print(f"INFO: Growing Blob spawn suppressed. Max growing limit ({self.MAX_GROWING_BLOBS}) reached.")
            return

        KEYBOARD_X_START = 520
        KEYBOARD_X_END = 1396
        KEYBOARD_Y_MAX = 345
        BLOB_PADDING = max(50, self.min_diameter / 2)

        while True:
            x = random.uniform(100, self.width - 100)
            y = random.uniform(100, self.height - 100)

            is_in_keyboard_x = (x >= KEYBOARD_X_START - BLOB_PADDING) and (x <= KEYBOARD_X_END + BLOB_PADDING)
            is_in_keyboard_y = (y >= 0) and (y <= KEYBOARD_Y_MAX + BLOB_PADDING)

            if is_in_keyboard_x and is_in_keyboard_y:
                continue
            else:
                break
        new_blob = GrowingBlob(pos=(x, y), growth_rate=self.growth_rate, visualizer=self)
        self.blobs.append(new_blob)

    def get_notes_for_blobs(self, num_notes, octave):
        octave_notes = [n for n in self.scale_notes if (octave * 12) <= n < ((octave + 1) * 12)]

        if not octave_notes:
            if self.scale_notes:
                 base_octave_notes = [n for n in self.scale_notes if (self.base_octave * 12) <= n < ((self.base_octave + 1) * 12)]
                 if base_octave_notes:
                     octave_notes = base_octave_notes
                 else:
                     octave_notes = self.scale_notes

            if not octave_notes:
                return [60] * num_notes

        return [random.choice(octave_notes) for _ in range(num_notes)]

    def on_touch_down(self, touch):
        # 1. Always check the Hide Button first
        if self.hide_ui_button.collide_point(*touch.pos):
            return self.hide_ui_button.on_touch_down(touch)

        # 2. Check Control Panel and Keyboard ONLY if UI is visible
        if self.ui_visible:
            if self.control_panel.collide_point(*touch.pos) or self.keyboard.collide_point(*touch.pos):
                return super().on_touch_down(touch)

        # 3. Existing Game Logic (Info label handling)
        if self.info_label and self.info_label.parent:
            self.remove_widget(self.info_label)
            self.info_label = None
            if len(self.blobs) < self.MAX_BLOBS and sum(1 for b in self.blobs if isinstance(b, GrowingBlob)) < self.MAX_GROWING_BLOBS:
                 self.spawn_growing_blob()
            return True

        # 4. Existing Game Logic (Blob interaction)
        tapped_blob = None
        for blob in self.blobs:
            if blob in self.blobs and isinstance(blob, GrowingBlob) and blob.collide_point(*touch.pos):
                tapped_blob = blob
                break

        if tapped_blob:
            current_count = len(self.blobs)
            if current_count <= self.SANE_BLOBS:
                 tapped_blob.explode(self)
            elif current_count >= self.MAX_BLOBS:
                 tapped_blob.is_waiting_to_explode = True
                 print("Manual rupture blocked: MAX_BLOBS reached. Blob on standby.")
            elif tapped_blob.is_waiting_to_explode:
                 print(f"Manual rupture blocked: Blob waiting and count {current_count} > SANE_BLOBS {self.SANE_BLOBS}")
            else:
                 tapped_blob.explode(self)
        else:
            # Spawn logic
            growing_count = sum(1 for b in self.blobs if isinstance(b, GrowingBlob))
            if growing_count >= self.MAX_GROWING_BLOBS:
                # print(...)
                return True

            current_count = len(self.blobs)
            has_waiting_blobs = any(b.is_waiting_to_explode for b in self.blobs if isinstance(b, GrowingBlob))

            if current_count >= self.MAX_BLOBS:
                # print(...)
                return True

            if has_waiting_blobs and current_count > self.SANE_BLOBS:
                # print(...)
                return True

            new_blob = GrowingBlob(pos=touch.pos, growth_rate=self.growth_rate, visualizer=self)
            self.blobs.append(new_blob)

        return True

class VisualizerScreen(Screen):
    def __init__(self, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.settings = {}
        self.app_container = AppContainer(main_midi_out=main_midi_out)
        self.add_widget(self.app_container)
        self.world = self.app_container.world

    def start(self):
        self.world.settings = self.settings
        self.world.start()

    def on_pre_leave(self, *args):
        self.world.on_pre_leave()

class BlowingUpShapesRoot(ScreenManager):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.main_midi_out = main_midi_out
        self.add_widget(MainMenuScreen(name='main_menu'))
        self.add_widget(VisualizerScreen(name='visualizer', main_midi_out=self.main_midi_out))
        self.current = 'main_menu'

    def cleanup_app(self):
        viz_screen = self.get_screen('visualizer')
        viz_screen.on_pre_leave()
        self.current = 'main_menu'
