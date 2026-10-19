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




import os
import logging
import sys
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

import random
import threading
import time
import math
import json
import uuid
from kivy.utils import platform
from kivy.logger import Logger

if platform == 'android':
    from android.storage import app_storage_path
    kivy_home_dir = os.path.join(app_storage_path(), '.kivy')
    if not os.path.exists(kivy_home_dir):
        os.makedirs(kivy_home_dir)
    os.environ['KIVY_HOME'] = kivy_home_dir

# Kivy Imports
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as WidgetImage
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
import shutil
from kivy.graphics import Line, Color, Rectangle
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics.transformation import Matrix
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

# Project Imports
from midimesh.main import session_manager  # Adjust path if needed
from midimesh.main.control_panel.controlpanel import ControlPanel
from midimesh.main.control_panel.onscreen_keyboard import OnScreenKeyboard
from midimesh.main.control_panel.node_panel import MiscControls, MidiChannelSelector, CircleMidiChannelSelector
import midimesh.main.main_canvas.midi_manager as midi_manager
from midimesh.main.main_canvas import connection_manager
from midimesh.main.main_canvas import packet_manager
from misc.grid import Grid
from misc.goodies_menu import GoodiesMenu, SettingsMenu
from misc.animated_fonts import AnimatedLabel
from miniapps.blowing_up_shapes import BlowingUpShapesRoot
from miniapps.growing_trees import GrowingTreesRoot
from miniapps.growth_ui import GrowingShapesRoot
from miniapps.step_sequencer import SequencerRoot
from miniapps.cavern_ace import CavernAceRoot
from miniapps.shape_arcade import ShapeArcadeRoot
from miniapps.tracker import TrackerRoot
import misc.guided_popups
from misc.help import HelpWorld

# Import the extracted visualizer
from visualizer import MidiVisualizer, FrameAnimator, HideUIButton, PanicButton, KillPacketsButton, PlayPauseButton, ResetButton, SelfStrumPopup

ICON_PATH = 'assets/icon.png'



class FitLayout(FloatLayout):
    def do_layout(self, *args):
        if not self.children:
            return

        content = self.children[0]
        win_w, win_h = self.size
        content_w, content_h = content.size

        if win_w == 0 or win_h == 0 or content_w == 0 or content_h == 0:
            return

        new_scale = min(win_w / content_w, win_h / content_h)
        new_pos = (
            (win_w - content_w * new_scale) / 2,
            (win_h - content_h * new_scale) / 2
        )

        epsilon = 1e-6
        if (abs(content.scale - new_scale) > epsilon or
            abs(content.pos[0] - new_pos[0]) > epsilon or
            abs(content.pos[1] - new_pos[1]) > epsilon):
            content.scale = new_scale
            content.pos = new_pos

class AppContainer(FitLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080), # Set size directly here
            do_rotation=False, do_translation=False,
            do_scale=False, auto_bring_to_front=False,
        )
        self.root_layout = RootLayout(size=(1920, 1080), size_hint=(None, None))
        self.scatter.add_widget(self.root_layout)
        self.add_widget(self.scatter)

class HelpContainer(FitLayout):
    def __init__(self, app_switcher, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080),
            do_rotation=False, do_translation=False,
            do_scale=False, auto_bring_to_front=False,
        )

        self.help_world = HelpWorld(app_switcher=app_switcher)
        self.scatter.add_widget(self.help_world)
        self.add_widget(self.scatter)

class WorldScatterLayout(ScatterLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale_min = 1.0
        self.scale_max = 8.0
        self.scale = 1.0
        self.do_rotation = False
        self.auto_bring_to_front = False

    def bound_positions(self):

        sw = self.width * self.scale
        sh = self.height * self.scale

        self.x = max(self.width - sw, min(self.x, 0))
        self.y = max(self.height - sh, min(self.y, 0))

    def on_transform_with_touch(self, touch):
        super().on_transform_with_touch(touch)
        self.bound_positions()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False


        if touch.is_mouse_scrolling:
            if touch.button == 'scrollup':
                factor = 1.1
            elif touch.button == 'scrolldown':
                factor = 1 / 1.1
            else:
                return False

            local_pos = self.to_local(*touch.pos)
            new_scale = self.scale * factor
            new_scale = max(self.scale_min, min(new_scale, self.scale_max))

            if abs(new_scale - self.scale) < 1e-6:
                return True

            self.scale = new_scale

            new_parent_pos = self.to_parent(*local_pos)

            dx = touch.x - new_parent_pos[0]
            dy = touch.y - new_parent_pos[1]

            self.pos = (self.x + dx, self.y + dy)
            return True

        return super().on_touch_down(touch)

class RootLayout(FloatLayout):
    ui_visible = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.world_container = WorldScatterLayout(size=(1920, 1080), size_hint=(None, None))
        self.ui_container = FloatLayout(size=(1920, 1080), size_hint=(None, None))
        self.add_widget(self.world_container)
        self.add_widget(self.ui_container)
        self.visualizer = MidiVisualizer()
        self.grid = Grid()
        self.grid.size = self.world_container.size
        self.visualizer.size = self.world_container.size
        self.world_container.add_widget(self.grid)
        self.visualizer.grid = self.grid
        self.world_container.add_widget(self.visualizer)

        add_glass_overlay = True

        if platform == 'android':
            try:
                from jnius import autoclass
                Version = autoclass('android.os.Build$VERSION')
                if Version.SDK_INT < 29:
                    add_glass_overlay = False
            except Exception:
                pass

        if add_glass_overlay:
            self.glass_overlay = Image(
                source='assets/glass_overlay.png',
                size=(1920, 1080),
                size_hint=(None, None),
                allow_stretch=True,
                keep_ratio=False
            )
            self.world_container.add_widget(self.glass_overlay)

        self.control_panel = ControlPanel(self.visualizer)
        self.ui_container.add_widget(self.control_panel)

        self.misccontrols = MiscControls(self.visualizer)
        self.ui_container.add_widget(self.misccontrols)

        self.visualizer.control_panel_ref = self.control_panel
        self.visualizer.misc_controls_ref = self.misccontrols
        self.visualizer.root_layout_ref = self

        self.control_panel.bind(
            packet_speed=self.visualizer.update_packet_speed,
            packet_life=self.visualizer.update_packet_life,
            node_speed_multiplier=self.visualizer.update_node_speed,
            max_connection_distance=self.visualizer.update_max_distance,
            max_connections_per_node=self.visualizer.update_max_connections
        )

        self.keyboard = OnScreenKeyboard(midi_callback=self.visualizer.handle_onscreen_midi)
        self.ui_container.add_widget(self.keyboard)
        self.bind(size=self._update_keyboard_pos, pos=self._update_keyboard_pos)

        self.global_selector = MidiChannelSelector()
        self.misccontrols.add_widget(self.global_selector)

        self.circle_selector = CircleMidiChannelSelector()
        self.misccontrols.add_widget(self.circle_selector)

        self.play_trigger_button = Button(
            background_normal='assets/null.png', background_down='assets/play-trigger.png',
            size_hint=(None, None), size=(67, 67)
        )
        self.play_trigger_button.bind(on_press=self.toggle_play_trigger)
        self.ui_container.add_widget(self.play_trigger_button)

        self.save_button = Button(
            text="SAVE",
            font_size='24px',
            bold=True,
            color=(1, 1, 1, 0.6),
            background_normal="assets/brain-1.png",
            background_down="assets/brain-1_pressed.png",
            size_hint=(None, None),
            size=(100, 100)
            )

        self.load_button = Button(
            background_normal="assets/brain-2.png",
            background_down="assets/brain-2-pressed.png",
            size_hint=(None, None),
            size=(100, 100)
            )


        self.load_label = Label(
            text="LOAD",
            font_size='24px',
            bold=True,
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )

        self.kill_packets_button = KillPacketsButton(visualizer=self.visualizer)

        self.kill_packets_label = Label(
            text="KILL\nPKTS",
            font_size='24px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )


        self.hide_ui_button = HideUIButton(root_layout=self)
        self.hide_ui_label = Label(
            text="HIDE",
            font_size='24px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )
        self.ui_container.add_widget(self.hide_ui_button)
        self.ui_container.add_widget(self.hide_ui_label)

        self.panic_button = PanicButton(visualizer=self.visualizer)
        self.panic_label = Label(
            text="NOTE\nOFF",
            font_size='24px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )
        self.ui_container.add_widget(self.panic_button)
        self.ui_container.add_widget(self.panic_label)

        self.play_pause_button = PlayPauseButton(visualizer=self.visualizer)

        self.play_pause_label = Label(
            text="PLAY",
            font_size='24px',
            bold=True,
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )
        self.play_pause_button.label_widget = self.play_pause_label

        self.bind(size=self._update_all_positions, pos=self._update_all_positions)
        self._update_all_positions()

        self.visualizer.on_quarter_note_callback = self.play_pause_button.pulse

        self.save_button.bind(on_release=lambda x: self.visualizer.save_session())
        self._load_long_press_active = False
        self._load_popup = None
        self._long_press_event = None
        self.load_button.bind(on_press=self._on_load_press, on_release=self._on_load_release)

        self.ui_container.add_widget(self.load_button)
        self.ui_container.add_widget(self.load_label)
        self.ui_container.add_widget(self.save_button)

        self.help_button = Button(
            background_normal='assets/help.png',
            background_down='assets/help_pressed.png',
            text="HELP",
            font_size='24px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(100, 100)
        )
        self.help_button.bind(on_release=lambda x: App.get_running_app().switch_to_widget('help_menu'))
        self.ui_container.add_widget(self.help_button)

        self.ui_container.add_widget(self.kill_packets_button)
        self.ui_container.add_widget(self.kill_packets_label)
        self.ui_container.add_widget(self.play_pause_button)
        self.ui_container.add_widget(self.play_pause_label)

        self.bind(size=self._update_button_pos, pos=self._update_button_pos)
        self._update_button_pos()

        self.reset_button = ResetButton()
        self.reset_button.visualizer = self.visualizer
        self.reset_button.pos = (1780, 940)
        self.bind(size=self._update_reset_btn_pos, pos=self._update_reset_btn_pos)
        self.ui_container.add_widget(self.reset_button)

    def toggle_ui_state(self):
        self.ui_visible = not self.ui_visible

        new_opacity = 1 if self.ui_visible else 0
        new_disabled = not self.ui_visible

        if self.control_panel:
            self.control_panel.opacity = new_opacity
            self.control_panel.disabled = new_disabled

        if self.misccontrols:
            self.misccontrols.opacity = new_opacity
            self.misccontrols.disabled = new_disabled

        if self.keyboard:
            self.keyboard.opacity = new_opacity
            self.keyboard.disabled = new_disabled

        self.visualizer.use_boundaries = self.ui_visible
        self.hide_ui_label.text = "HIDE" if self.ui_visible else "UN-\nHIDE"

    def _on_load_press(self, instance):
        self._load_long_press_active = False
        self._long_press_event = Clock.schedule_once(self._do_load_long_press, 0.5)

    def _do_load_long_press(self, dt):
        self._long_press_event = None
        self._load_long_press_active = True

    def _on_load_release(self, instance):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None

            if self._load_popup and self._load_popup.parent:
                self._load_popup.dismiss()
            self._load_popup = session_manager.LoadPopup(visualizer=self.visualizer)
            self._load_popup.open()

        elif self._load_long_press_active:
            self._load_long_press_active = False
            next_file = session_manager.get_next_session_filename(self.visualizer)

            if next_file:
                if self.visualizer.is_playing:
                    self.visualizer.queue_session_load(next_file)
                else:
                    session_manager.load_session_from_file(self.visualizer, next_file)

    def on_touch_down(self, touch):
        if not self.reset_button.collide_point(*touch.pos):
            self.reset_button.set_state(ResetButton.STATE_DISARMED)
        return super().on_touch_down(touch)

    def _update_reset_btn_pos(self, *args):
        if hasattr(self, "reset_button"): self.reset_button.pos = (1800, 960)

    def _update_button_pos(self, *args):
        if hasattr(self, 'save_button'): self.save_button.pos = (20, 860)
        if hasattr(self, 'load_button'):
            self.load_button.pos = (20, 760)
            if hasattr(self, 'load_label'):
                self.load_label.pos = (self.load_button.x, self.load_button.y + 5)

        if hasattr(self, 'help_button'):
            self.help_button.pos = (20, 600)

        if hasattr(self, 'kill_packets_button'):
            self.kill_packets_button.pos = (1790, 820)
            if hasattr(self, 'kill_packets_label'):
                self.kill_packets_label.pos = (self.kill_packets_button.x, self.kill_packets_button.y)

        if hasattr(self, 'hide_ui_button'):
            self.hide_ui_button.pos = (1790, 710)
            if hasattr(self, 'hide_ui_label'):
                self.hide_ui_label.pos = (self.hide_ui_button.x, self.hide_ui_button.y)

        if hasattr(self, 'panic_button'):
            self.panic_button.pos = (1790, 600)
            if hasattr(self, 'panic_label'):
                self.panic_label.pos = (self.panic_button.x, self.panic_button.y)

        if hasattr(self, 'play_pause_button'):
            self.play_pause_button.pos = (20, 960)
            if hasattr(self, 'play_pause_label'):
                self.play_pause_label.pos = self.play_pause_button.pos

    def _update_all_positions(self, *args):
        self.control_panel.do_layout()
        self._update_keyboard_pos()
        if hasattr(self, 'play_trigger_button'): self.play_trigger_button.pos = (1615, 431)

    def _update_keyboard_pos(self, *args):
        if hasattr(self, 'keyboard'): self.keyboard.pos = (540, 20)

    def toggle_play_trigger(self, instance):
        circle = self.visualizer.last_selected_circle
        if not circle: return
        circle['play_trigger'] = not circle.get('play_trigger', False)
        self.sync_play_trigger_button(circle)

    def sync_play_trigger_button(self, circle):
        if circle and hasattr(self, 'play_trigger_button'):
            is_trigger = circle.get('play_trigger', False) if circle else False
            self.play_trigger_button.background_normal = 'assets/play-trigger.png' if is_trigger else 'assets/null.png'





class SplashWidget(Widget):
    def __init__(self, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (1920, 1080)
        self.on_complete = on_complete

        self.textures = []
        self._anim_event = None

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            splash_dir = os.path.join(script_dir, 'assets/splash_frames')
            frame_files = sorted([f for f in os.listdir(splash_dir) if f.lower().endswith('.png')])
            if not frame_files:
                raise FileNotFoundError(f"No PNG frames found in '{splash_dir}'")

            for frame_file in frame_files:
                path = os.path.join(splash_dir, frame_file)
                self.textures.append(CoreImage(path).texture)

            self.frame_iterator = iter(self.textures)
            with self.canvas:
                Color(1, 1, 1, 1)
                self.rect = Rectangle(texture=self.textures[0], pos=(0, 0), size=self.size)

            self.bind(size=self._update_rect)

        except Exception as e:
            raise e

    def _update_rect(self, instance, value):
        self.rect.size = instance.size

    def start_animation(self, fps=30):
        if self.textures and not self._anim_event:
            interval = 1.0 / fps
            self._anim_event = Clock.schedule_interval(self._animate_frame, interval)

    def stop_animation(self):
        if self._anim_event:
            self._anim_event.cancel()
            self._anim_event = None

    def _animate_frame(self, dt):
        try:
            self.rect.texture = next(self.frame_iterator)
        except StopIteration:
            self.stop_animation()
            if self.on_complete:
                self.on_complete()

class MidiMesh(App):

    main_app_widget = ObjectProperty(None)
    goodies_menu_widget = ObjectProperty(None)
    blowing_up_shapes_widget = ObjectProperty(None)
    growing_trees_widget = ObjectProperty(None)
    growing_shapes_widget = ObjectProperty(None)
    help_menu_widget = ObjectProperty(None, allownone=True)

    main_update_loop = ObjectProperty(None)
    current_widget_name = StringProperty('main_app')


    guided_tour_overlay = ObjectProperty(None, allownone=True)

    def build(self):
        Window.minimum_width = 1120
        Window.minimum_height = 630
        Window.fullscreen = False

        root = FloatLayout()
        self.app_container = None

        self.icon = ICON_PATH
        self.title = 'MIDI Mesh'

        try:
            splash_container = FitLayout()

            def transition_to_main_app():
                if splash_container.parent:
                    root.remove_widget(splash_container)

                if platform == 'android': hide_system_ui()

                self.app_container = AppContainer()
                self.main_update_loop = Clock.schedule_interval(self.app_container.root_layout.visualizer.update, 1.0 / 60.0)

                self.main_app_widget = self.app_container
                self.current_widget_name = 'main_app'

                self.midi_visualizer = MidiVisualizer()

                self.root.add_widget(self.main_app_widget)

                Clock.schedule_once(lambda dt: misc.guided_popups.show_midi_configuration(
                    self.main_app_widget.root_layout.visualizer.midi_out,
                    is_auto_launch=True
                ), 0.5)

            splash_scatter = ScatterLayout(
                size_hint=(None, None),
                size=(1920, 1080),
                do_rotation=False, do_translation=False,
                do_scale=False, auto_bring_to_front=False,
            )

            splash_content = SplashWidget(on_complete=transition_to_main_app)

            splash_scatter.add_widget(splash_content)
            splash_container.add_widget(splash_scatter)

            root.add_widget(splash_container)
            splash_content.start_animation(fps=24)

        except Exception as e:
            print(f"INFO: Splash screen failed to load ({e}). Loading app directly.")
            transition_to_main_app()

        return root

    def switch_to_widget(self, target_name):
        if self.current_widget_name == target_name:
            return

        logging.info(f"Switching from '{self.current_widget_name}' to '{target_name}'")

        if self.current_widget_name == 'main_app':
            if self.main_app_widget:
                self.main_update_loop.cancel()
                self.main_app_widget.root_layout.visualizer.cleanup_soft()
                self.root.remove_widget(self.main_app_widget)

        elif self.current_widget_name == 'goodies_menu':
            if self.goodies_menu_widget:
                self.root.remove_widget(self.goodies_menu_widget)

        elif self.current_widget_name == 'blowing_up_shapes':
            if self.blowing_up_shapes_widget:
                self.blowing_up_shapes_widget.cleanup_app()
                self.root.remove_widget(self.blowing_up_shapes_widget)

        elif self.current_widget_name == 'growing_trees':
            if self.growing_trees_widget:
                self.growing_trees_widget.cleanup_app()
                self.root.remove_widget(self.growing_trees_widget)

        elif self.current_widget_name == 'growing_shapes':
            if self.growing_shapes_widget:
                self.growing_shapes_widget.cleanup_app()
                self.root.remove_widget(self.growing_shapes_widget)

        elif self.current_widget_name == '128_step_sequencer':
             if hasattr(self, 'sequencer_widget') and self.sequencer_widget:
                 self.sequencer_widget.cleanup_app()
                 self.root.remove_widget(self.sequencer_widget)

        elif self.current_widget_name == 'cavern_ace':
             if hasattr(self, 'cavern_ace_widget') and self.cavern_ace_widget:
                 self.cavern_ace_widget.cleanup_app()
                 self.root.remove_widget(self.cavern_ace_widget)

        elif self.current_widget_name == 'shape_arcade':
             if hasattr(self, 'shape_arcade_widget') and self.shape_arcade_widget:
                 self.shape_arcade_widget.cleanup_app()
                 self.root.remove_widget(self.shape_arcade_widget)

        elif self.current_widget_name == 'tracker':
            if hasattr(self, 'tracker_widget') and self.tracker_widget:
                self.tracker_widget.cleanup_app()
                self.root.remove_widget(self.tracker_widget)
                self.tracker_widget = None

        if self.current_widget_name == 'help_menu':
            if self.help_menu_widget:
                self.help_menu_widget.help_world.cleanup()
                self.root.remove_widget(self.help_menu_widget)
                self.help_menu_widget = None

        if self.current_widget_name == 'settings_menu':
            if hasattr(self, 'settings_menu_widget') and self.settings_menu_widget:
                self.root.remove_widget(self.settings_menu_widget)
                self.settings_menu_widget = None

        if target_name == 'main_app':
            if self.main_app_widget:
                self.root.add_widget(self.main_app_widget)
                self.main_update_loop = Clock.schedule_interval(self.main_app_widget.root_layout.visualizer.update, 1.0 / 60.0)
                self.main_app_widget.root_layout.visualizer.setup_midi()
                self.current_widget_name = 'main_app'
                self.main_app_widget.root_layout.reset_button.set_state('disarmed')

        elif target_name == 'goodies_menu':
            if not self.goodies_menu_widget:
                self.goodies_menu_widget = GoodiesMenu(app_switcher=self.switch_to_widget)
            self.root.add_widget(self.goodies_menu_widget)
            self.current_widget_name = 'goodies_menu'

        elif target_name == 'blowing_up_shapes':
            if not self.blowing_up_shapes_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.blowing_up_shapes_widget = BlowingUpShapesRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.blowing_up_shapes_widget)
            self.blowing_up_shapes_widget.current = 'main_menu'
            self.current_widget_name = 'blowing_up_shapes'

        elif target_name == 'growing_trees':
            if not self.growing_trees_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.growing_trees_widget = GrowingTreesRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.growing_trees_widget)
            self.growing_trees_widget.current = 'main_menu'
            self.current_widget_name = 'growing_trees'

        elif target_name == 'growing_shapes':
            if not self.growing_shapes_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.growing_shapes_widget = GrowingShapesRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.growing_shapes_widget)
            self.growing_shapes_widget.shapes_world.current = 'menu'
            self.current_widget_name = 'growing_shapes'

        elif target_name == '128_step_sequencer':
            if not hasattr(self, 'sequencer_widget') or not self.sequencer_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.sequencer_widget = SequencerRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.sequencer_widget)
            self.current_widget_name = '128_step_sequencer'

        elif target_name == 'cavern_ace':
            if not hasattr(self, 'cavern_ace_widget') or not self.cavern_ace_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.cavern_ace_widget = CavernAceRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.cavern_ace_widget)
            self.cavern_ace_widget.world.current = 'menu'
            self.current_widget_name = 'cavern_ace'

        elif target_name == 'shape_arcade':
            if not hasattr(self, 'shape_arcade_widget') or not self.shape_arcade_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.shape_arcade_widget = ShapeArcadeRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.shape_arcade_widget)
            self.current_widget_name = 'shape_arcade'

        elif target_name == 'tracker':
            if not hasattr(self, 'tracker_widget') or not self.tracker_widget:
                main_midi_port = None
                if self.main_app_widget:
                    main_midi_port = self.main_app_widget.root_layout.visualizer.midi_out
                self.tracker_widget = TrackerRoot(
                    app_switcher=self.switch_to_widget,
                    main_midi_out=main_midi_port
                )
            self.root.add_widget(self.tracker_widget)
            self.current_widget_name = 'tracker'

        elif target_name == 'help_menu':
            if not self.help_menu_widget:
                self.help_menu_widget = HelpContainer(app_switcher=self.switch_to_widget)

            self.root.add_widget(self.help_menu_widget)
            self.current_widget_name = 'help_menu'

        elif target_name == 'settings_menu':
            midi_mgr = None
            if self.main_app_widget and hasattr(self.main_app_widget.root_layout, 'visualizer'):
                midi_mgr = self.main_app_widget.root_layout.visualizer.midi_out
            visualizer_ref = self.main_app_widget.root_layout.visualizer if self.main_app_widget else None
            self.settings_menu_widget = SettingsMenu(
                app_switcher=self.switch_to_widget,
                midi_manager=midi_mgr,
                visualizer=visualizer_ref
            )
            self.root.add_widget(self.settings_menu_widget)
            self.current_widget_name = 'settings_menu'

    if platform == 'android':
        from jnius import autoclass
        from android.runnable import run_on_ui_thread
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        @run_on_ui_thread
        def _set_screen_on(self, keep_on):
            window = self.PythonActivity.mActivity.getWindow()
            if keep_on: window.addFlags(self.LayoutParams.FLAG_KEEP_SCREEN_ON)
            else: window.clearFlags(self.LayoutParams.FLAG_KEEP_SCREEN_ON)
        def on_start(self): self._set_screen_on(True)
        def on_pause(self): self._set_screen_on(False); return True
        def on_resume(self): self._set_screen_on(True)
        def on_stop(self):
            if hasattr(self, 'app_container') and self.app_container:
                self.app_container.root_layout.visualizer.cleanup()
            if platform == 'android' and hasattr(self, '_set_screen_on'):
                self._set_screen_on(False)
    else:
        def on_start(self): pass
        def on_pause(self): return True
        def on_resume(self): pass
        def on_stop(self):
            if hasattr(self, 'app_container') and self.app_container:
                self.app_container.root_layout.visualizer.cleanup_full()
            if platform == 'android' and hasattr(self, '_set_screen_on'):
                self._set_screen_on(False)

if __name__ == '__main__':
    app = MidiMesh()
    try:
        app.run()
    except KeyboardInterrupt:
        app.on_stop()

