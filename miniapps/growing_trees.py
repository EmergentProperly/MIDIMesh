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
from kivy.config import Config

WIDTH = 1920
HEIGHT = 1080
Config.set('graphics', 'width', str(WIDTH))
Config.set('graphics', 'height', str(HEIGHT))
Config.set('graphics', 'resizable', 0)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics import Color, Rectangle
from kivy.utils import platform, get_color_from_hex
from kivy.graphics import Color, Line, Ellipse, InstructionGroup
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton


from kivy.config import Config
from kivy.core.text import LabelBase
from midimesh.main.control_panel.onscreen_minikeys import OnScreenKeyboards

import math
import random

LabelBase.register(
    name='Handwrite',
    fn_regular='assets/Handwrite-01.ttf',
)

ANIM_FONTS = [
    'assets/Handwrite-01.ttf',
    'assets/Handwrite-02.ttf',
    'assets/Handwrite-03.ttf'
]

VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080

if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("GrowingTrees: Successfully imported AndroidMidi")
    except ImportError:
        print("GrowingTrees: Could not import AndroidMidi")

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import rtmidi
        print("GrowingTrees: Successfully imported WindowsMidi (aliased) and rtmidi")
    except ImportError:
        print("GrowingTrees: Could not import windows_midi or rtmidi")

else:
    try:
        import rtmidi
        print("GrowingTrees: Successfully imported rtmidi")
    except ImportError:
        print("GrowingTrees: rtmidi not found.")
        rtmidi = None

# TO DO: Make scales its own module and remove duplication across mini apps.
SCALES = {
    'MAJOR': [0, 2, 4, 5, 7, 9, 11],
    'MINOR': [0, 2, 3, 5, 7, 8, 10],
    'PENTATONIC MAJOR': [0, 2, 4, 7, 9],
    'PENTATONIC MINOR': [0, 3, 5, 7, 10],
    'BLUES': [0, 3, 5, 6, 7, 10],
    'DORIAN': [0, 2, 3, 5, 7, 9, 10],
    'PHRYGIAN': [0, 1, 3, 5, 7, 8, 10],
    'PHRYGIAN DOMINANT': [0, 1, 3, 5, 7, 8, 11],
    'LYDIAN': [0, 2, 4, 6, 7, 9, 11],
    'MIXOLYDIAN': [0, 2, 4, 5, 7, 9, 10],
    'LOCRIAN': [0, 1, 3, 5, 6, 8, 10],
    'HARMONIC MINOR': [0, 2, 3, 5, 7, 8, 11],
    'HARMONIC MAJOR': [0, 2, 4, 5, 7, 8, 11],
    'MELODIC MINOR (Ascending)': [0, 2, 3, 5, 7, 9, 11],
    'WHOLE TONE': [0, 2, 4, 6, 8, 10],
    'DIMINISHED (Half-Whole)': [0, 1, 3, 4, 6, 7, 9, 10],
    'DIMINISHED (Whole-Half)': [0, 2, 3, 5, 6, 8, 9, 11],
    'AUGMENTED': [0, 3, 4, 7, 8, 11],
    'ENIGMATIC': [0, 1, 4, 6, 8, 10, 11],
}

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

            if hasattr(content, 'scale'):
                content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

class FractalNode:
    def __init__(self, x, y, angle, note_degree, terminus_x=None, terminus_y=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.note_degree = note_degree
        self.terminus_x = terminus_x
        self.terminus_y = terminus_y
        self.children = []

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.anim_event = None
        self.anim_font_idx = 0
        self.animated_widgets = []


        root_container = RelativeLayout()

        background = Image(
            source='assets/growing_trees_menu_bg.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root_container.add_widget(background)

        layout = BoxLayout(orientation='vertical', padding=(100,300,200,40), spacing=30)

        title = Label(
            text='',
            size_hint_y=None,
            height=160,
            font_size='60px',
            bold=True
        )
        layout.add_widget(title)
        self.animated_widgets.append(title)

        self.scale_names = list(SCALES.keys())
        self.num_scales = len(self.scale_names)
        initial_scale_name = 'MAJOR'
        try:
            initial_scale_index = self.scale_names.index(initial_scale_name)
        except ValueError:
            initial_scale_index = 0

        scale_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)

        self.scale_label = Label(
            text=f'{initial_scale_name}',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5
        )
        self.animated_widgets.append(self.scale_label)

        self.scale_slider = Slider(
            min=0,
            max=self.num_scales - 1,
            value=initial_scale_index,
            step=1,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.5
            )

        self.scale_slider.bind(value=self.on_scale_slider_update)

        scale_layout.add_widget(self.scale_label)
        scale_layout.add_widget(self.scale_slider)
        layout.add_widget(scale_layout)

        branches_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)

        self.branches_label = Label(
            text='Number of Branches: 2',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5
            )
        self.animated_widgets.append(self.branches_label)

        self.branches_slider = Slider(
            min=1,
            max=3,
            step=1,
            value=2,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.5
        )

        self.branches_slider.bind(value=self.update_branches_label)
        branches_layout.add_widget(self.branches_label)
        branches_layout.add_widget(self.branches_slider)
        layout.add_widget(branches_layout)

        length_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)

        self.length_label = Label(
            text='Branch Length: 75',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5
            )
        self.animated_widgets.append(self.length_label)

        self.length_slider = Slider(
            min=25,
            max=100,
            step=1,
            value=75,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.5
            )

        self.length_slider.bind(value=self.update_length_label)
        length_layout.add_widget(self.length_label)
        length_layout.add_widget(self.length_slider)
        layout.add_widget(length_layout)

        iter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)

        self.iter_label = Label(
            text='Iterations: 3',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5
            )
        self.animated_widgets.append(self.iter_label)

        self.iter_slider = Slider(
            min=1,
            max=8,
            step=1,
            value=3,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.5
            )

        self.iter_slider.bind(value=self.update_iter_label)
        iter_layout.add_widget(self.iter_label)
        iter_layout.add_widget(self.iter_slider)
        layout.add_widget(iter_layout)


        angle_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)

        self.angle_label = Label(
            text='Branch Angle: 30',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5
            )
        self.animated_widgets.append(self.angle_label)

        self.angle_slider = Slider(
            min=0,
            max=180,
            step=1,
            value=30,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(110, 110),
            padding=80,
            size_hint_x=0.5
            )

        self.angle_slider.disabled_image = 'assets/single_slider_bg.png'
        self.angle_slider.cursor_disabled_image = 'assets/node_mini_app_disabled.png'

        self.angle_slider.bind(value=self.update_angle_label)
        angle_layout.add_widget(self.angle_label)
        angle_layout.add_widget(self.angle_slider)

        layout.add_widget(angle_layout)

        random_layout = BoxLayout(orientation='horizontal', size_hint_y=None, size_hint_x=1, height=150, spacing=40)

        random_label = Label(
            text='Randomise Angle:\n(set angle first)',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='50px',
            size_hint_x=0.5,
            valign='middle',
            halign='center'
        )
        self.animated_widgets.append(random_label)

        self.random_toggle = ToggleButton(
            size_hint=(None, None),
            size=(100, 100),
            background_normal='assets/checkbox_unchecked.png',
            background_down='assets/checkbox_checked.png',
            text='',
            group=None,
        )

        toggle_container = BoxLayout(
            size_hint_x=0.5,
            padding=(0, 25, 100, 25)
        )

        def _on_random_toggle(instance, *args):
            is_active = instance.state == 'down'
            try:
                self.toggle_angle_slider(instance, is_active)
            except TypeError:
                self.toggle_angle_slider(is_active)

        random_label.bind(size=random_label.setter('text_size'))
        random_layout.add_widget(random_label)
        self.random_toggle.bind(state=lambda inst, st: _on_random_toggle(inst))
        toggle_container.add_widget(self.random_toggle)
        random_layout.add_widget(toggle_container)
        layout.add_widget(random_layout)

        layout.add_widget(BoxLayout(size_hint_y=1.0))

        button_box = BoxLayout(orientation='horizontal',
                               size_hint_y=None,
                               padding=(300,0,300,0),
                               height=150, spacing=300
                               )


        self.start_button = Button(
            background_normal='assets/messy_button_01.png',
            background_down='assets/messy_button_01.png',
            text='START',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='70px',
            size_hint_x=0.5
        )
        self.start_button.bind(on_press=self.start_generation)
        button_box.add_widget(self.start_button)
        self.animated_widgets.append(self.start_button)

        self.back_button = Button(
            background_normal='assets/messy_button_01.png',
            background_down='assets/messy_button_01.png',
            text='BACK',
            font_name='Handwrite',
            color=(0.1, 0.1, 0.1, 1),
            font_size='70px',
            size_hint_x=0.5
        )
        self.back_button.bind(on_press=self.go_to_goodies_menu)
        button_box.add_widget(self.back_button)
        self.animated_widgets.append(self.back_button)

        layout.add_widget(button_box)

        root_container.add_widget(layout)

        self.add_widget(root_container)

    def on_enter(self, *args):
        if not self.anim_event:
            self.anim_event = Clock.schedule_interval(self._animate_fonts, 0.125)

    def on_leave(self, *args):
        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None

    def _animate_fonts(self, dt):
        self.anim_font_idx = (self.anim_font_idx + 1) % len(ANIM_FONTS)
        new_font = ANIM_FONTS[self.anim_font_idx]
        for widget in self.animated_widgets:
            try:
                widget.font_name = new_font
            except Exception:
                pass

    def update_branches_label(self, i, value): self.branches_label.text = f"Number of Branches: {int(value)}"
    def update_length_label(self, i, value): self.length_label.text = f"Branch Length: {int(value)}"
    def update_angle_label(self, i, value):
        if self.random_toggle.state != 'down':
            self.angle_label.text = f"Branch Angle: {int(value)}"
    def update_iter_label(self, i, value): self.iter_label.text = f"Iterations: {int(value)}"

    def toggle_angle_slider(self, instance, active):
        self.angle_slider.disabled = active
        self.angle_label.disabled = active
        if active:
            self.angle_label.text = "Branch Angle: Random"
        else:
            self.angle_label.text = f"Branch Angle: {int(self.angle_slider.value)}"

    def on_scale_slider_update(self, instance, value):
        index = int(value)
        current_scale_name = self.scale_names[index]
        self.scale_label.text = f"{current_scale_name}"



    def start_generation(self, instance):
        scale_index = int(self.scale_slider.value)
        selected_scale = self.scale_names[scale_index]
        settings = {
            'scale': selected_scale,
            'branches': int(self.branches_slider.value),
            'length_percent': int(self.length_slider.value) / 100.0,
            'angle': int(self.angle_slider.value),
            'random_angle': self.random_toggle.state == 'down',
            'iterations': int(self.iter_slider.value)
        }

        root_widget = self.manager
        root_widget.fractal_settings = settings
        root_widget.current = 'fractal'

    def go_to_goodies_menu(self, instance):
        root_widget = self.manager
        root_widget.go_to_goodies_menu()

class FractalCanvasWidget(RelativeLayout):

    def get_current_scale(self):
        if self.parent:
            return self.parent.scale
        return 1.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_expired')

        self.fractal_tree = None
        self.settings = {}
        self.root_note = 60
        self.note_duration = 0.25

        self.packet_anim = None
        self.animation_path = []
        self.animation_path_index = 0
        self.pixels_per_second = 500
        self.BASE_PACKET_SIZE = 10.0

        with self.canvas.before:
            self.fractal_group = InstructionGroup()
            self.fractal_color = Color(1, 1, 1, 0.8)
            self.fractal_group.add(self.fractal_color)
            self.canvas.before.add(self.fractal_group)

        with self.canvas.after:
            self.packet_color = Color(0, 1, 0, 0)
            self.packet = Ellipse(pos=(0, 0), size=(self.BASE_PACKET_SIZE, self.BASE_PACKET_SIZE))

    def generate(self, settings):
        self.settings = settings
        self.fractal_group.clear()
        self.fractal_group.add(self.fractal_color)

        with self.canvas.after:
            self.packet_color = Color(0, 1, 0, 0)
            self.packet = Ellipse(pos=(0, 0), size=(self.BASE_PACKET_SIZE, self.BASE_PACKET_SIZE))

        start_x = self.width / 2
        start_y = self.height * 0.35
        start_length = self.height * 0.125

        self.fractal_tree = self._generate_recursive(
            start_x, start_y, 90, start_length,
            self.settings['iterations'], 0
        )

    def _generate_recursive(self, x, y, angle, length, iteration, parent_note_degree):
        rad = math.radians(angle)
        end_x = x + math.cos(rad) * length
        end_y = y + math.sin(rad) * length

        line = Line(points=[x, y, end_x, end_y], width=1.0)
        self.fractal_group.add(line)

        node = FractalNode(x, y, angle, parent_note_degree, terminus_x=end_x, terminus_y=end_y)

        if iteration > 0:
            num_branches = self.settings['branches']
            total_angle_span = self.settings['angle']

            if num_branches > 1:
                angle_step = total_angle_span / (num_branches - 1)
                start_branch_angle = angle - total_angle_span / 2
            else:
                angle_step = 0
                start_branch_angle = angle

            new_length = length * self.settings['length_percent']

            for i in range(num_branches):
                branch_angle = start_branch_angle + (i * angle_step)

                if self.settings['random_angle']:
                    fuzz = (angle_step / 2) if angle_step > 0 else self.settings['angle'] / 2
                    branch_angle += random.uniform(-fuzz, fuzz)

                child_note_degree = parent_note_degree + random.randint(1, 4)

                child_node = self._generate_recursive(
                    end_x, end_y, branch_angle, new_length,
                    iteration - 1, child_note_degree
                )
                node.children.append(child_node)

        return node


    def find_random_leaf(self, node):
        if not node:
            return None
        if not node.children:
            return node
        return self.find_random_leaf(random.choice(node.children))

    def find_path_to_leaf(self, start_node, target_leaf):
        if not start_node:
            return None

        path = [start_node]
        if start_node == target_leaf:
            return path

        if not start_node.children:
            return None

        for child in start_node.children:
            child_path = self.find_path_to_leaf(child, target_leaf)
            if child_path:
                return path + child_path

        return None


    def start_animation(self, root_note, pixels_per_second):
        if not self.fractal_tree:
            return

        if self.packet_anim:
            self.packet_anim.cancel(self.packet)
            Animation.cancel_all(self.packet_color)
            Animation.cancel_all(self.packet)

        self.reset_packet()

        self.root_note = root_note
        self.pixels_per_second = pixels_per_second

        leaf_node = self.find_random_leaf(self.fractal_tree)
        if not leaf_node:
            return

        self.animation_path = self.find_path_to_leaf(self.fractal_tree, leaf_node)
        if not self.animation_path:
            return

        final_node = self.animation_path[-1]
        terminus_point = {'x': final_node.terminus_x, 'y': final_node.terminus_y, 'is_terminus': True}

        self.animation_path.append(terminus_point)

        self.animation_path_index = 0

        self.play_node(self.fractal_tree)

        self.animate_next_segment()

    def animate_next_segment(self):
        if self.animation_path_index >= len(self.animation_path) - 1:
            self.flash_and_expire()
            return

        current_item = self.animation_path[self.animation_path_index]
        next_item = self.animation_path[self.animation_path_index + 1]

        is_final_segment = not isinstance(next_item, FractalNode)

        def get_coords(item):
            if isinstance(item, FractalNode):
                return (item.x, item.y)
            else:
                return (item['x'], item['y'])

        current_pos = get_coords(current_item)
        target_pos_raw = get_coords(next_item)

        scale = self.get_current_scale()
        scaled_size = self.BASE_PACKET_SIZE / scale
        scaled_radius = scaled_size / 2

        self.packet.size = (scaled_size, scaled_size)
        self.packet.pos = (current_pos[0] - scaled_radius, current_pos[1] - scaled_radius)
        self.packet_color.a = 1

        dist = math.sqrt((target_pos_raw[0] - current_pos[0])**2 + (target_pos_raw[1] - current_pos[1])**2)
        duration = max(0.05, dist / self.pixels_per_second)

        if is_final_segment:
            BASE_FLASH_SIZE = 30.0
            scaled_flash_size = BASE_FLASH_SIZE / scale
            flash_radius = scaled_flash_size / 2
            target_pos_flash = (target_pos_raw[0] - flash_radius, target_pos_raw[1] - flash_radius)
            move_and_flash_anim = Animation(pos=target_pos_flash,
                                            size=(scaled_flash_size, scaled_flash_size),
                                            duration=duration)
            move_and_flash_anim.bind(on_complete=self.on_animation_expired)
            expire_anim = Animation(a=0, duration=duration)
            move_and_flash_anim.start(self.packet)
            expire_anim.start(self.packet_color)

        else:
            target_pos = (target_pos_raw[0] - scaled_radius, target_pos_raw[1] - scaled_radius)

            self.packet_anim = Animation(pos=target_pos, duration=duration)
            self.packet_anim.bind(on_complete=self.packet_arrived_at_segment_end)
            self.packet_anim.start(self.packet)

    def packet_arrived_at_segment_end(self, animation, widget):
        self.animation_path_index += 1

        arrived_at_item = self.animation_path[self.animation_path_index]

        if isinstance(arrived_at_item, FractalNode):
             self.play_node(arrived_at_item)
             self.animate_next_segment()
        else:
             self.flash_and_expire()
             return

    def flash_and_expire(self):
        BASE_FLASH_SIZE = 30.0
        scale = self.get_current_scale()

        scaled_size = self.BASE_PACKET_SIZE / scale
        scaled_flash_size = BASE_FLASH_SIZE / scale

        center_x = self.packet.pos[0] + scaled_size / 2
        center_y = self.packet.pos[1] + scaled_size / 2

        flash_radius = scaled_flash_size / 2
        target_pos = (center_x - flash_radius, center_y - flash_radius)

        flash_anim = Animation(size=(scaled_flash_size, scaled_flash_size), pos=target_pos, duration=0.01)
        expire_anim = Animation(a=0, duration=0.001)

        flash_anim.bind(on_complete=lambda *args: expire_anim.start(self.packet_color))
        expire_anim.bind(on_complete=self.on_animation_expired)

        flash_anim.start(self.packet)

    def reset_packet(self, *args):
        scale = self.get_current_scale()
        scaled_size = self.BASE_PACKET_SIZE / scale

        self.packet.size = (scaled_size, scaled_size)
        self.packet_color.a = 0
        self.animation_path = []
        self.animation_path_index = 0

    def on_animation_expired(self, *args):
        self.reset_packet()
        self.dispatch('on_expired')

    def on_expired(self, *args):
        pass

    def play_node(self, node):
        root_widget = self.parent.parent.parent
        if not root_widget.midi_out:
            return

        scale_intervals = SCALES[self.settings['scale']]
        note_degree = node.note_degree
        num_notes_in_scale = len(scale_intervals)

        scale_degree_interval = scale_intervals[note_degree % num_notes_in_scale]

        octave_offset = note_degree // num_notes_in_scale

        final_note = self.root_note + scale_degree_interval + (octave_offset * 12)

        if 0 <= final_note <= 127:
            root_widget.send_midi_note(final_note, self.note_duration)

class FractalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = 'intro'
        self.intro_label = None
        self.canvas_widget = None
        self.keyboard_widget = None
        self.speed_slider = None
        self.loop_toggle = None
        self.cued_note = None
        self.anim_event = None
        self.anim_font_idx = 0

    def on_enter(self, *args):
        self.state = 'intro'
        self.cued_note = None
        self.clear_widgets()

        self.intro_label = Label(
            text='Tap screen to begin',
            font_name='Handwrite',
            font_size='50px',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.intro_label)

        self.anim_event = Clock.schedule_interval(self._animate_intro_font, 0.125)

        root_widget = self.manager
        if root_widget and not root_widget.midi_out:
            root_widget.init_midi()

    def _animate_intro_font(self, dt):
        if self.intro_label:
            self.anim_font_idx = (self.anim_font_idx + 1) % len(ANIM_FONTS)
            self.intro_label.font_name = ANIM_FONTS[self.anim_font_idx]

    def on_touch_down(self, touch):
        if self.state == 'intro':
            self.state = 'active'
            if self.anim_event:
                self.anim_event.cancel()
                self.anim_event = None
            if self.intro_label:
                self.remove_widget(self.intro_label)
                self.intro_label = None
            self.build_fractal_ui()

        return super().on_touch_down(touch)

    def on_leave(self, *args):
        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None

    def build_fractal_ui(self):
        global VIRTUAL_HEIGHT, VIRTUAL_WIDTH

        CONTROL_HEIGHT = 140

        scatter_container = Scatter(
            size_hint=(1, 1),
            pos=(0, 0),
            do_rotation=False,
            auto_bring_to_front=False,
            scale=1.0
        )

        original_on_touch_down = scatter_container.on_touch_down

        def new_on_touch_down(touch):
            if touch.y >= VIRTUAL_HEIGHT - CONTROL_HEIGHT:
                return False
            if self.keyboard_widget and self.keyboard_widget.collide_point(*touch.pos):
                return False
            return original_on_touch_down(touch)

        scatter_container.on_touch_down = new_on_touch_down

        self.canvas_widget = FractalCanvasWidget(size_hint=(None, None))
        self.canvas_widget.bind(on_expired=self.check_for_loop)
        self.canvas_widget.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        scatter_container.bind(size=self.trigger_fractal_generation)
        scatter_container.add_widget(self.canvas_widget)

        self.add_widget(scatter_container)

        control_layout = RelativeLayout(
            size_hint=(1, None),
            height=CONTROL_HEIGHT,
            pos_hint={'top': 1}
        )

        control_bg = Image(
            source='assets/panel_02.png',
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=False
        )
        control_layout.add_widget(control_bg)

        back_button = Button(
            text='',
            color=(0.0, 0.0, 0.0, 1),
            background_normal='assets/back_normal.png',
            background_down='assets/back_pressed.png',
            border=(0, 0, 0, 0),
            background_color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(120, 120),
            pos=(20,8)
        )

        back_button.bind(on_press=self.go_to_menu)
        control_layout.add_widget(back_button)

        self.loop_toggle = ToggleButton(
            text='',
            state='down',
            background_normal='assets/loop.png',
            background_down='assets/loop_pressed.png',
            size_hint=(None, None),
            size=(120, 120),
            pos=(150,8)
        )
        control_layout.add_widget(self.loop_toggle)

        self.speed_slider = Slider(
            min=50,
            max=2000,
            value=200,
            step=10,
            size_hint=(0.8, None),
            height=120,
            background_horizontal='assets/single_slider_bg.png',
            border_horizontal=(0, 0, 0, 0),
            background_width=40,
            value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png',
            cursor_size=(100, 100),
            pos=(320,8)
            )
        control_layout.add_widget(self.speed_slider)

        self.add_widget(control_layout)
        self.keyboard_widget = OnScreenKeyboards(
            midi_callback=self.midi_callback,
            size_hint=(None, None)
        )
        self.keyboard_widget.pos = (540, 20)
        self.add_widget(self.keyboard_widget)

    def generate_fractal(self, dt):
        root_widget = self.manager
        if self.canvas_widget and root_widget.fractal_settings:
            self.canvas_widget.generate(root_widget.fractal_settings)

    def trigger_fractal_generation(self, instance, value):
        self.generate_fractal(0)
        instance.unbind(size=self.trigger_fractal_generation)


    def generate_fractal(self, dt):
        root_widget = self.manager
        if self.canvas_widget and root_widget.fractal_settings:
            self.canvas_widget.generate(root_widget.fractal_settings)

    def trigger_fractal_generation(self, instance, value):
        self.canvas_widget.size = value
        self.generate_fractal(0)
        instance.unbind(size=self.trigger_fractal_generation)

    def start_packet_animation(self, root_note):
        if not (self.canvas_widget and self.speed_slider and self.loop_toggle):
            return

        is_looping = self.loop_toggle.state == 'down'
        is_running = bool(self.canvas_widget.animation_path)

        if is_looping and is_running:
            self.cued_note = root_note
        else:
            self.cued_note = None
            pixels_per_second = self.speed_slider.value
            self.canvas_widget.start_animation(root_note, pixels_per_second)

    def check_for_loop(self, instance):
        if self.loop_toggle and self.loop_toggle.state == 'down':

            if self.cued_note is not None:
                root_note = self.cued_note
                self.cued_note = None
            else:
                root_note = self.canvas_widget.root_note

            self.start_packet_animation(root_note)

    def go_to_menu(self, instance):
        if self.canvas_widget:
            if self.canvas_widget.packet_anim:
                self.canvas_widget.packet_anim.cancel(self.canvas_widget.packet)
            Animation.cancel_all(self.canvas_widget.packet)
            Animation.cancel_all(self.canvas_widget.packet_color)

        self.cued_note = None

        root_widget = self.manager
        root_widget.current = 'main_menu'


    def midi_callback(self, message_type, note, velocity):
        if message_type == 'note_on':
            self.start_packet_animation(note)

class _GrowingTreesWorld(ScreenManager):
    def __init__(self, app_switcher, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.midi_out = None
        self.main_midi_out = main_midi_out
        self.fractal_settings = {}

        self.size_hint = (None, None)
        self.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        self.add_widget(MainMenuScreen(name='main_menu'))
        self.add_widget(FractalScreen(name='fractal'))
        self.current = 'main_menu'

    def init_midi(self):
        if self.midi_out:
            return

        if self.main_midi_out:
            self.midi_out = self.main_midi_out
            print("GrowingTrees: Using main app MIDI port.")
            return

        if platform in ('android', 'win') and 'AndroidMidi' in globals():
            print(f"GrowingTrees: Initializing MIDI Out via wrapper ({platform})...")
            try:
                self.midi_out = AndroidMidi()
                if hasattr(self.midi_out, 'open_output'):
                    self.midi_out.open_output()

                if platform == 'win' and hasattr(self.midi_out, 'get_host_devices'):
                    devs = self.midi_out.get_host_devices()
                    if devs:
                        print(f"GrowingTrees: Auto-connecting to: {devs[0][0]}")
                        self.midi_out.connect_to_device(devs[0][1])
            except Exception as e:
                print(f"GrowingTrees: MIDI Wrapper Error: {e}")
                self.midi_out = None

        elif rtmidi:
            try:
                self.midi_out = rtmidi.MidiOut()
                self.midi_out.open_virtual_port("GrowingTrees Output")
                print("GrowingTrees: Created virtual output port.")
            except Exception as e:
                print(f"GrowingTrees: rtmidi Init Error: {e}")
                self.midi_out = None
        else:
            print("GrowingTrees: No MIDI backend available.")
            self.midi_out = None

    def send_midi_note(self, note, duration):
        if self.midi_out:
            try:
                note_on_msg = [0x90, int(note), 100]
                note_off_msg = [0x80, int(note), 0]

                self.midi_out.send_message(note_on_msg)

                Clock.schedule_once(
                    lambda dt: self.midi_out.send_message(note_off_msg),
                    duration
                )
            except Exception as e:
                pass

    def cleanup_app(self):
        fractal_screen = self.get_screen('fractal')
        if fractal_screen.canvas_widget:
            if fractal_screen.canvas_widget.packet_anim:
                fractal_screen.canvas_widget.packet_anim.cancel(fractal_screen.canvas_widget.packet)
            Animation.cancel_all(fractal_screen.canvas_widget.packet)
            Animation.cancel_all(fractal_screen.canvas_widget.packet_color)
            fractal_screen.canvas_widget.reset_packet()

        if self.midi_out:
            if self.midi_out is not self.main_midi_out:
                print("GrowingTrees: Closing fallback MIDI port.")
                if platform == 'android':
                    self.midi_out.close()
                else:
                    self.midi_out.close_port()
            else:
                print("GrowingTrees: Not closing shared main app MIDI port.")

        if self.midi_out is not self.main_midi_out:
                self.midi_out = None

        self.current = 'main_menu'

    def go_to_goodies_menu(self):
        self.cleanup_app()
        self.app_switcher('goodies_menu')

class GrowingTreesRoot(FitLayout):

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

        self.trees_world = _GrowingTreesWorld(
            app_switcher=app_switcher,
            main_midi_out=main_midi_out
        )

        self.scatter.add_widget(self.trees_world)
        self.add_widget(self.scatter)

    def cleanup_app(self):
        self.trees_world.cleanup_app()
