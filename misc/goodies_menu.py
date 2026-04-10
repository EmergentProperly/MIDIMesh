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
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle

from kivy.uix.togglebutton import ToggleButton
from misc.guided_popups import show_midi_configuration, settings_store, BigCheckBox

import os
import sys
import logging
import webbrowser
from kivy.utils import platform         
from kivy.uix.popup import Popup       
from kivy.uix.label import Label 

try:
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
except NameError:
    assets_dir = os.path.join(os.path.abspath(os.getcwd()), 'assets')

VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080


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


class _GoodiesMenuWorld(FloatLayout):

    def __init__(self, app_switcher, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.size_hint = (None, None)
        self.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        try:
            from misc.grid import Grid
            grid_bg = Grid(
                size_hint=(None, None),
                size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
                pos=(0, 0)
            )
            self.add_widget(grid_bg)
        except ImportError:
            pass

        panel_width = 1600
        panel_height = 900
        panel_x = (VIRTUAL_WIDTH - panel_width) / 2
        panel_y = (VIRTUAL_HEIGHT - panel_height) / 2

        self.panel_bg = Image(
            source='assets/panel_square_01.png',
            size_hint=(None, None),
            size=(panel_width, panel_height),
            pos=(panel_x, panel_y),
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.panel_bg)

        self.layout = GridLayout(
            cols=3,
            spacing=10,
            padding=[654, 230, 654, 200],
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            pos=(0, 0)
        )
        self.add_widget(self.layout)

        # 1. Blowing Shapes
        btn_blowing_shapes = Button(
            background_normal='assets/blowing_up_button.png',
            background_down='assets/blowing_up_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('blowing_up_shapes')
        )
        self.layout.add_widget(btn_blowing_shapes)

        # 2. Growing Trees
        btn_growing_trees = Button(
            background_normal='assets/growing_trees_button.png',
            background_down='assets/growing_trees_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('growing_trees')
        )
        self.layout.add_widget(btn_growing_trees)

        # 3. Growing Shapes
        btn_growing_shapes = Button(
            background_normal='assets/growing_shapes_button.png',
            background_down='assets/growing_shapes_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('growing_shapes')
        )
        self.layout.add_widget(btn_growing_shapes)

        # 4. Sequencer
        btn_sequencer = Button(
            background_normal='assets/sequencer_normal.png',
            background_down='assets/sequencer_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('128_step_sequencer')
        )
        self.layout.add_widget(btn_sequencer)

        # 5. Cavern Ace
        btn_cavern_ace = Button(
            background_normal='assets/cave_diver_button.png',
            background_down='assets/cave_diver_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('cavern_ace')
        )
        self.layout.add_widget(btn_cavern_ace)

        # 6. Shape Arcade (Midi Marauders)
        btn_shape_arcade = Button(
            background_normal='assets/shape_arcade_button.png',
            background_down='assets/shape_arcade_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('shape_arcade')
        )
        self.layout.add_widget(btn_shape_arcade)

        # 7. Tracker
        btn_tracker = Button(
            background_normal='assets/tracker_buttton.png',
            background_down='assets/tracker_buttton_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('tracker')
        )
        self.layout.add_widget(btn_tracker)

        # 8. Settings Menu
        btn_menu = Button(
            background_normal='assets/menu_normal.png',
            background_down='assets/menu_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('settings_menu') # Pointing to new target
        )
        self.layout.add_widget(btn_menu)

        # 9. Back to Main App
        btn_back = Button(
            background_normal='assets/main_app_button.png',
            background_down='assets/main_app_button_pressed.png',
            size_hint_y=None, width=200, height=200,
            border=(0,0,0,0,),
            on_release=lambda x: self.app_switcher('main_app')
        )
        self.layout.add_widget(btn_back)

    def placeholder(self, instance):
        logging.info("_GoodiesMenuWorld: Placeholder button pressed.")

class SettingsMenu(FitLayout):
    def __init__(self, app_switcher, midi_manager, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.midi_manager = midi_manager
        self.visualizer = visualizer
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )

        self.world = FloatLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        )

        panel_w, panel_h = 1920, 1080
        self.bg_panel = Image(
            source='assets/panel_01.png',
            size_hint=(None, None),
            size=(panel_w, panel_h),
            # Center math: (1920 - 1200) / 2, (1080 - 900) / 2
            pos=((VIRTUAL_WIDTH - panel_w) / 2, (VIRTUAL_HEIGHT - panel_h) / 2),
            allow_stretch=True,
            keep_ratio=False
        )
        self.world.add_widget(self.bg_panel)

        content_w, content_h = 800, 700
        content_layout = BoxLayout(
            orientation='vertical',
            spacing=30,
            size_hint=(None, None),
            size=(content_w, content_h),
            pos=(
                (VIRTUAL_WIDTH - content_w) / 2,
                ((VIRTUAL_HEIGHT - content_h) / 2) - 80
            )
        )

        title = Label(
            text="Miscellaneous",
            font_size='80px',
            bold=True,
            size_hint_y=None,
            height=100,
            color=(0.8, 0.8, 0.8, 1)
        )
        content_layout.add_widget(title)

        btn_midi = Button(
            text="DEVICE & MIDI SETUP",
            font_size='32px',
            background_normal='assets/flat_button_grey.png',
            background_down='assets/flat_button_grey_pressed.png',
            size_hint=(1, None), # Fill width of content_layout
            height=100
        )
        btn_midi.bind(on_release=self._open_midi_wizard)
        content_layout.add_widget(btn_midi)

        content_layout.add_widget(Widget(size_hint_y=None, height=20))

        chk_row = BoxLayout(
            orientation='horizontal',
            spacing=40,
            size_hint=(1, None),
            height=60
        )

        chk_label = Label(
            text="Show MIDI Wizard at startup",
            font_size='32px',
            color=(0.8, 0.8, 0.8, 1),
            halign='right',
            valign='middle',
            size_hint=(1, 1)
        )
        chk_label.bind(size=chk_label.setter('text_size'))

        is_skipped = False
        if settings_store.exists('skip_midi_setup'):
            is_skipped = settings_store.get('skip_midi_setup')['value']

        self.chk_startup = BigCheckBox()
        self.chk_startup.active = not is_skipped
        self.chk_startup.bind(active=self._on_checkbox_toggle)

        chk_row.add_widget(chk_label)
        chk_row.add_widget(self.chk_startup)
        content_layout.add_widget(chk_row)
        content_layout.add_widget(Widget(size_hint_y=1))

        btn_source = Button(
            text="SOURCE CODE",
            font_size='32px',
            background_normal='assets/flat_button_grey.png',
            background_down='assets/flat_button_grey_pressed.png',
            size_hint=(1, None),
            height=80
        )
        btn_source.bind(on_release=lambda x: webbrowser.open("https://github.com/EmergentProperly/MIDI_Mesh"))
        content_layout.add_widget(btn_source)

        btn_tuts = Button(
            text="TUTORIALS ETC (Coming soon...)",
            font_size='32px',
            background_normal='assets/flat_button_grey.png',
            background_down='assets/flat_button_grey_pressed.png',
            size_hint=(1, None),
            height=80
        )
        btn_tuts.bind(on_release=lambda x: webbrowser.open("https://www.youtube.com/@Emergent-Properly"))
        content_layout.add_widget(btn_tuts)

        btn_bug = Button(
            text="REPORT AN ISSUE",
            font_size='32px',
            background_normal='assets/flat_button_grey.png',
            background_down='assets/flat_button_grey_pressed.png',
            size_hint=(1, None),
            height=80
        )
        btn_bug.bind(on_release=lambda x: webbrowser.open("https://github.com/EmergentProperly/MIDI_Mesh"))
        content_layout.add_widget(btn_bug)

        btn_back = Button(
            text="BACK",
            font_size='32px',
            background_normal='assets/flat_button_red.png',
            background_down='assets/flat_button_red_pressed.png',
            size_hint=(None, None),
            size=(300, 100),
            pos_hint={'center_x': 0.5}
        )
        btn_back.bind(on_release=lambda x: self.app_switcher('goodies_menu'))
        content_layout.add_widget(btn_back)

        self.world.add_widget(content_layout)
        self.scatter.add_widget(self.world)
        self.add_widget(self.scatter)

    def _on_checkbox_toggle(self, instance, value):
        skip = not value
        settings_store.put('skip_midi_setup', value=skip)
        logging.info(f"Settings: 'Show Wizard' set to {value} (skip={skip})")

    def _open_midi_wizard(self, instance):

        current_platform = platform

        if current_platform in ("macosx", "linux"):
            popup_content = Label(
                text=(
                    "Running on: {}\n\n"
                    "Use a patchbay if you need to configure MIDI on this platform.\n\n"
                ).format(current_platform),
                halign="center",
                valign="middle",
                markup=True,
            )
            # Make the label wrap nicely inside the popup
            popup_content.bind(size=popup_content.setter('text_size'))

            popup = Popup(
                title="MIDI Setup Unavailable",
                content=popup_content,
                size_hint=(0.7, 0.4),   # 70 % width, 40 % height of the window
                auto_dismiss=True,
            )
            popup.open()

            logging.info(
                "MIDI wizard invoked on %s; showing popup instead of wizard.",
                current_platform,
            )
            return

        if not self.midi_manager:
            logging.warning(
                "Settings: Cannot open MIDI wizard, no MIDI manager found."
            )
            return

        show_midi_configuration(
            self.midi_manager,
            is_auto_launch=False,
            on_done_callback=lambda: self.app_switcher('settings_menu')
        )

class GoodiesMenu(FitLayout):
    def __init__(self, app_switcher, **kwargs):
        super().__init__(**kwargs)
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )
        menu_world = _GoodiesMenuWorld(app_switcher=app_switcher)
        self.scatter.add_widget(menu_world)
        self.add_widget(self.scatter)
