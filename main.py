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


from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch') #<-- Comment this out if you want to use pseudo-multitouch on a desktop (kivy red dots)

import os
import logging
import sys
from kivy.utils import platform
from kivy.logger import Logger
if platform == 'android':
    from android.storage import app_storage_path
    kivy_home_dir = os.path.join(app_storage_path(), '.kivy')
    if not os.path.exists(kivy_home_dir):
        os.makedirs(kivy_home_dir)
    os.environ['KIVY_HOME'] = kivy_home_dir


import random
import threading
import time
import math
import json
import uuid
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as WidgetImage

from itertools import cycle
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
from kivy.core.window import Window

# UI and logic
from midimesh.main import session_manager
from midimesh.main.control_panel.controlpanel import ControlPanel
from midimesh.main.control_panel.onscreen_keyboard import OnScreenKeyboard
from midimesh.main.control_panel.node_panel import MiscControls, MidiChannelSelector, CircleMidiChannelSelector
import midimesh.main.main_canvas.midi_manager as midi_manager
from midimesh.main.main_canvas import connection_manager
from midimesh.main.main_canvas import packet_manager
from misc.grid import Grid

#Mini apps and menus.
from misc.goodies_menu import GoodiesMenu, SettingsMenu
from miniapps.blowing_up_shapes import BlowingUpShapesRoot
from miniapps.growing_trees import GrowingTreesRoot
from miniapps.growth_ui import GrowingShapesRoot
from miniapps.step_sequencer import SequencerRoot
from miniapps.cavern_ace import CavernAceRoot
from miniapps.shape_arcade import ShapeArcadeRoot
from miniapps.tracker import TrackerRoot
import misc.guided_popups
from misc.help import HelpWorld


if platform == 'android':
    from jnius import autoclass
    from android.runnable import run_on_ui_thread

    @run_on_ui_thread
    def hide_system_ui():
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        View = autoclass('android.view.View')
        decorView = activity.getWindow().getDecorView()
        decorView.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )

script_dir = os.path.dirname(os.path.abspath(__file__))

base_path = os.path.join(script_dir, 'assets/shapes')

OVERLOADED_SHAPES_DIR   = os.path.join(script_dir,'assets/executing')
OVERLOADED_PACKETS_DIR  = os.path.join(script_dir, 'assets/executing')

_PRELOADED_TEXTURES = {}

ICON_PATH = 'assets/icon.png'

def _preload_folder(folder_path):

    png_files = sorted(
        f for f in os.listdir(folder_path) if f.lower().endswith('.png')
    )
    if not png_files:
        raise FileNotFoundError(f'No PNG frames found in {folder_path}')
    textures = [
        CoreImage(os.path.join(folder_path, fn)).texture for fn in png_files
    ]
    _PRELOADED_TEXTURES[folder_path] = textures

_preload_folder(OVERLOADED_SHAPES_DIR)
_preload_folder(OVERLOADED_PACKETS_DIR)

COLLISION_BOUNDARIES = [
    {"x_start": 0,    "x_end": 500,   "min_y": 500},
    {"x_start": 520,  "x_end": 1396,  "min_y": 345},
    {"x_start": 1428, "x_end": 1920,  "min_y": 500},
]


class FrameAnimator:

    def __init__(self, widget, folder_path, fps=30):
        self.widget = widget
        self.folder = folder_path
        self.fps = fps
        try:
            self.textures = _PRELOADED_TEXTURES[self.folder]
        except KeyError as exc:
            raise RuntimeError(f'Folder "{self.folder}" was not pre‑loaded.') from exc
        self._rect = None; self._clock_event = None; self._frame_iter = None

    def _next_frame(self, dt):
        try:
            self._rect.texture = next(self._frame_iter)
        except StopIteration:
            self._frame_iter = cycle(self.textures)

    def start(self, center_offset=(0, 0)):
        w, h = self.widget.width, self.widget.height
        tex_w, tex_h = self.textures[0].width, self.textures[0].height
        x, y = (w - tex_w) / 2 + center_offset[0], (h - tex_h) / 2 + center_offset[1]
        with self.widget.canvas.after:
            Color(1, 1, 1, 1)
            self._rect = Rectangle(texture=self.textures[0], pos=(x, y), size=(tex_w, tex_h))
        self._frame_iter = cycle(self.textures)
        interval = 1.0 / float(self.fps)
        self._clock_event = Clock.schedule_interval(self._next_frame, interval)

    def stop(self):
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None
        if self._rect:
            try:
                self.widget.canvas.after.remove(self._rect)
            except Exception as e:
                logging.warning(f"FrameAnimator: Failed to remove rect: {e}")
            self._rect = None


class HideUIButton(ButtonBehavior, Image):
    def __init__(self, root_layout, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = root_layout
        self.source = 'assets/hide_UI_normal.png'
        self.size_hint = (None, None)
        self.size = (100, 100)

    def on_press(self):
        self.source = 'assets/hide_UI_pressed.png'

    def on_release(self):
        self.source = 'assets/hide_UI_normal.png'
        if self.root_layout:
            self.root_layout.toggle_ui_state()

class PanicButton(ButtonBehavior, Image):
    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.source = 'assets/red-packet.png'
        self.size_hint = (None, None)
        self.size = (100, 100)
        self.color = (1, 1, 1, 1)

    def on_press(self):
        self.source = 'assets/red-packet-active.png'
        self.visualizer.send_panic()

    def on_release(self):
        self.source = 'assets/red-packet.png'

class KillPacketsButton(ButtonBehavior, Image):
    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.source = 'assets/red-packet.png'
        self.size_hint = (None, None)
        self.size = (100, 100)

    def on_press(self):
        self.source = 'assets/red-packet-active.png'
        self.visualizer.kill_all_packets()

    def on_release(self):
        self.source = 'assets/red-packet.png'

class PlayPauseButton(ButtonBehavior, Image):
    midi_clock_armed = BooleanProperty(False)
    label_widget = ObjectProperty(None)

    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.play_state = 'pause'
        self.size_hint = (None, None)
        self.size = (100, 100)

        self._long_press_event = None

        self.armed_play_src = 'assets/play-button-clock.png'
        self.armed_pause_src = 'assets/stop-button-clock.png'
        self.disarmed_play_src = 'assets/pause.png'
        self.disarmed_pause_src = 'assets/play.png'

        self.source = self.disarmed_pause_src

    def on_press(self):
        self._long_press_event = Clock.schedule_once(self._do_long_press, 0.5)

    def on_release(self):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            self._do_short_press()

    def _do_long_press(self, dt):
        self._long_press_event = None
        self.midi_clock_armed = not self.midi_clock_armed
        self._update_source_image()

    def _do_short_press(self):
        if self.play_state == 'pause':
            self.play_state = 'play'
            self.visualizer.is_playing = True
            if self.midi_clock_armed:
                self.visualizer.send_midi_transport(0xFA) # MIDI Start
            self.visualizer.trigger_all_play_nodes()
        else:
            self.play_state = 'pause'
            self.visualizer.is_playing = False
            if self.midi_clock_armed:
                self.visualizer.send_midi_transport(0xFC) # MIDI Stop
            self.visualizer.kill_all_packets()

        self._update_source_image()

    def _update_source_image(self):
        if self.midi_clock_armed:
            self.source = self.armed_play_src if self.play_state == 'pause' else self.armed_pause_src
        else:
            self.source = self.disarmed_pause_src if self.play_state == 'pause' else self.disarmed_play_src

        if self.label_widget:
            self.label_widget.text = "PLAY" if self.play_state == 'pause' else "STOP"

    def pulse(self):
        if not self.midi_clock_armed:
            return

        original_source = self.source
        self.source = 'assets/clock-pulse.png'
        Clock.schedule_once(lambda dt: self._set_source_if_unchanged(original_source), 0.1)

    def _set_source_if_unchanged(self, source_to_restore):
        if self.source == 'assets/clock-pulse.png':
            self.source = source_to_restore

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


#The core logic for the main app (TO DO: move the UI stuff to its own module so only the core logic remains)
class MidiVisualizer(Widget):
    use_boundaries = BooleanProperty(True)
    _midi_initialized = False
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.control_panel_ref = None
        self.misc_controls_ref = None
        self.root_layout_ref = None
        self.current_save_index = 0
        self.circle_id_to_circle = {}
        self.all_connections = []
        self.connection_data = []
        self.circles = []
        self.last_selected_circle = None
        self.circle_animations = {}
        self.flash_animation = []
        self.animation_fps = 30.0
        self.load_animations()
        self.midi_in, self.midi_out, self.android_midi = None, None, None
        self.active_notes = {}
        self.packets = []
        self.packet_life = 10
        self.packet_speed = 200.0
        self.node_speed_multiplier = 1.0
        self.max_connections_per_node = 8
        self.max_connection_distance = 10.0
        self.setup_midi()
        self._long_press_event = None
        self._dragged_circle, self._drag_offset, self._candidate_circle, self._touch_start_pos = None, (0, 0), None, (0, 0)
        self._drag_threshold = 5
        self._line_colour_map = {}
        self.max_packets = 150
        self.max_circles = 150
        self._shape_warning_img, self._hard_reset_running = None, False
        self.onscreen_notes = {}
        self._current_dup, self._dup_parent = None, None
        self.show_duplicate = self._show_duplicate
        self.last_tempo_change_time = time.time()
        self.committed_ticks = 0
        self.current_tick_duration = 50.0 / max(self.packet_speed, 1.0)
        self.connection_color = Color(0.4, 0.1, 0.0, 1.0)
        self.is_playing = False
        self._just_triggered = False
        self._time_since_last_midi_clock = 0.0
        self.active_packet_count = 0
        self._time_since_last_quarter_note = 0.0
        self.quarter_notes_per_trigger = 0.5
        self.on_quarter_note_callback = None
        self.pending_session_file = None
        self.active_touches = {}
        self._ctrl_pressed = False
        self._last_ctrl_clicked_circle = None
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

    def send_panic(self):
        if not self.midi_out:
            return

        print("Sending MIDI Panic...")
        for channel in range(16):
            status = 0xB0 | channel
            self.midi_out.send_message([status, 123, 0])
            self.midi_out.send_message([status, 120, 0])
            self.midi_out.send_message([status, 64, 0])

        self.active_notes.clear()

    def queue_session_load(self, filename):
        self.pending_session_file = filename
        print(f"Session queued for next bar: {filename}")

    def save_session(self):
        session_manager.save_session(self)

    def load_session(self):
        session_manager.load_next_session(self)

    def load_session_from_file(self, filename):
        session_manager.load_session_from_file(self, filename)

    def check_collision(self, circle_x, circle_y, size):
        if not self.use_boundaries:
            return None

        cx, cy, radius = circle_x + size / 2, circle_y + size / 2, size / 2
        for boundary in COLLISION_BOUNDARIES:
            rx, ry = boundary["x_start"], 0
            rw, rh = boundary["x_end"] - boundary["x_start"], boundary["min_y"]
            closest_x = max(rx, min(cx, rx + rw))
            closest_y = max(ry, min(cy, ry + rh))
            dist_x, dist_y = cx - closest_x, cy - closest_y
            if (dist_x * dist_x) + (dist_y * dist_y) < (radius * radius):
                return boundary
        return None

    def _get_control_panel(self):
        if self.control_panel_ref:
            return self.control_panel_ref
        return None

    def _extract_line_color(self, line):
        if line in getattr(self, "_line_colour_map", {}):
            return self._line_colour_map[line]
        canvas_group = self.canvas.before
        try:
            idx = canvas_group.children.index(line)
        except ValueError:
            return (0.7, 0.0, 0.2, 0.5)
        for instr in reversed(canvas_group.children[:idx]):
            if isinstance(instr, Color):
                return (instr.r, instr.g, instr.b, instr.a)
        return (0.7, 0.0, 0.2, 0.5)

    def _show_duplicate(self, circle):
        if not self._dup_parent:
            if self.misc_controls_ref:
                self._dup_parent = self.misc_controls_ref
        if not self._dup_parent: return

        if self._current_dup:
            if hasattr(self._current_dup, '_anim_event'):
                self._current_dup._anim_event.cancel()
            self._dup_parent.remove_widget(self._current_dup)
            self._current_dup = None

        dup = WidgetImage(
            texture=circle['animation_frames'][0] if circle.get('animation_frames') else None,
            size=(circle['size'] + 40, circle['size'] + 40), size_hint=(None, None)
        )

        h, s, v = self._get_color_for_channel(circle.get('midi_channel', 1))
        r, g, b = self.hsv_to_rgb(h, s, v)
        dup.color = (r, g, b, 1)

        dup.pos = (self._dup_parent.x + 45, self._dup_parent.top - dup.height - 56)
        dup.source_circle = circle
        dup.bind(on_touch_down=self._on_duplicate_touch_down,
                 on_touch_up=self._on_duplicate_touch_up)

        self._dup_parent.add_widget(dup, index=len(self._dup_parent.children))

        self._current_dup = dup

        def _animate_dup(dt):
            one_shot_anim_key = circle.get('play_animation_once')
            if one_shot_anim_key:
                frames = circle.get(one_shot_anim_key)
            else:
                frames = circle.get('animation_frames')

            if not frames: return
            idx = getattr(dup, '_frame_idx', 0) + self.animation_fps * dt
            idx %= len(frames)
            dup.texture = frames[int(idx)]
            dup._frame_idx = idx

        dup._anim_event = Clock.schedule_interval(_animate_dup, 1 / self.animation_fps)

    def hsv_to_rgb(self, h, s, v):
        if s == 0.0: return v, v, v
        i, f = int(h * 6.0), (h * 6.0) - int(h * 6.0)
        p, q, t = v * (1.0 - s), v * (1.0 - s * f), v * (1.0 - s * (1.0 - f))
        i %= 6
        if i == 0: return v, t, p
        elif i == 1: return q, v, p
        elif i == 2: return p, v, t
        elif i == 3: return p, q, v
        elif i == 4: return t, p, v
        else: return v, p, q

    # NOTE: "circle" is a remnant of a very early iteration. Non-urgent-TO-DO: change all instances of "circle" to "shape".

    def update_circle_color(self, circle):
        if not circle: return

        h, s, v = self._get_color_for_channel(circle.get('midi_channel', 1))
        if 'color_instruction' in circle:
            circle['color_instruction'].h = h
            circle['color_instruction'].s = s
            circle['color_instruction'].v = v

        if self._current_dup and getattr(self._current_dup, 'source_circle', None) is circle:
            r, g, b = self.hsv_to_rgb(h, s, v)
            self._current_dup.color = (r, g, b, 1)

    def _update_selection_rect(self, circle):
        if hasattr(self, '_sel_color_instr') and self._sel_color_instr in self.canvas.after.children:
            self.canvas.after.remove(self._sel_color_instr)
        if hasattr(self, '_sel_line_instr') and self._sel_line_instr in self.canvas.after.children:
            self.canvas.after.remove(self._sel_line_instr)

        if not circle:
            return

        gap = 4 # (shape padding)
        with self.canvas.after:
            self._sel_color_instr = Color(1, 0, 0.3, 0.8) # Red
            self._sel_line_instr = Line(
                rectangle=(
                    circle['pos'][0] - gap,
                    circle['pos'][1] - gap,
                    circle['size'] + gap*2,
                    circle['size'] + gap*2
                ),
                width=1.5
            )

    def update_connections(self):
        if self.connection_color not in self.canvas.before.children:
            self.canvas.before.insert(0, self.connection_color)
        elif self.canvas.before.children.index(self.connection_color) != 0:
            self.canvas.before.remove(self.connection_color)
            self.canvas.before.insert(0, self.connection_color)

        connection_manager.update_connections(self)

    def calculate_connection_probability(self, distance, max_distance=800):
        probability = 1.0 - (distance / max_distance)
        return min(probability, 0.8)

    def get_circle_center(self, circle):
        x, y, size = circle['pos'][0], circle['pos'][1], circle['size']
        return x + size/2, y + size/2

    def get_connected_circles(self, circle):
        connected = []
        for c1, c2, _ in self.connection_data:
            if c1 is circle: connected.append(c2)
            elif c2 is circle: connected.append(c1)
        return connected

    def trigger_packet_routing(self, start_circle, play_note=True):
        if play_note:
            self.play_circle_note(start_circle)
        self.flash_circle(start_circle)
        connected_circles = self.get_connected_circles(start_circle)
        if not connected_circles: return
        target_circle = random.choice(connected_circles)
        if self.create_packet(start_circle, target_circle, time.time()) is not None:
            # Notify the overlay
            app = App.get_running_app()
            if hasattr(app, 'guided_tour_overlay') and app.guided_tour_overlay:
                app.guided_tour_overlay.on_packet_created()


    def trigger_all_play_nodes(self):
        for circle in self.circles:
            if circle.get('play_trigger', False):
                self.trigger_packet_routing(circle)

    def load_animations(self):
        for i in range(12):
            path = os.path.join(base_path, f'shape_{i}')
            if os.path.isdir(path):
                frames = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.png')])
                self.circle_animations[i] = [CoreImage(f).texture for f in frames]
        flash_path = os.path.join(base_path, 'flash')
        if os.path.isdir(flash_path):
            frames = sorted([os.path.join(flash_path, f) for f in os.listdir(flash_path) if f.endswith('.png')])
            self.flash_animation = [CoreImage(f).texture for f in frames]
        else:
            print(f"Warning: Directory not found at {flash_path}")



    def update_packet_speed(self, instance, value):
        self.packet_speed = value
        for packet in self.packets: packet['speed'] = value

    def update_packet_life(self, instance, value):
        self.packet_life = value

    def update_node_speed(self, instance, value):
        self.node_speed_multiplier = value

    def update_max_distance(self, instance, value):
        self.max_connection_distance = value

    def update_max_connections(self, instance, value):
        self.max_connections_per_node = value

    def _close_existing_ports(self):
        if getattr(self, "midi_in", None):
            try:
                self.midi_in.close_port()
            except Exception as e:
                Logger.warning(f"Failed to close MIDI IN port: {e}")
            finally:
                self.midi_in = None

        if getattr(self, "midi_out", None):
            try:
                self.midi_out.close_port()
            except Exception as e:
                Logger.warning(f"Failed to close MIDI OUT port: {e}")
            finally:
                self.midi_out = None

        self.__class__._midi_initialized = False


    def setup_midi(self):

        if self.__class__._midi_initialized:
            Logger.debug("MIDI already initialised – skipping creation.")
            return

        self._close_existing_ports()

        if platform == 'android':
            try:
                try:
                    from android_midi import AndroidMidi
                except ImportError:
                    from midimesh.main.android_midi import AndroidMidi

                self.android_midi = AndroidMidi()
                self.android_midi.open_output()
                self.midi_out = self.android_midi
                midi_manager.midi_out = self.midi_out
            except Exception as e:
                Logger.error(f"FATAL: Error setting up Android MIDI: {e}")

        elif platform == 'win':
            try:
                try:
                    from windows_midi import WindowsMidi
                except ImportError:
                    from midimesh.main.windows_midi import WindowsMidi

                self.windows_midi = WindowsMidi()
                self.midi_out = self.windows_midi
                midi_manager.midi_out = self.midi_out

                devices = self.windows_midi.get_host_devices()
                for name, dev_info in devices:
                    self.windows_midi.connect_to_device(dev_info)
            except Exception as e:
                Logger.error(f"FATAL: Error setting up Windows MIDI: {e}")

        else:
            try:
                import rtmidi

                self.midi_in = rtmidi.MidiIn()
                self.midi_in.open_virtual_port("MIDI Mesh - MIDI IN")
                self.midi_in.set_callback(self.midi_callback)
                self.midi_out = rtmidi.MidiOut()
                self.midi_out.open_virtual_port("MIDI Mesh - MIDI OUT")
                midi_manager.midi_out = self.midi_out
            except Exception as e:
                Logger.error(f"Error creating virtual rtmidi ports: {e}")

        if not hasattr(self, "_key_events_bound"):
            Window.bind(on_key_down=self._on_key_down)
            Window.bind(on_key_up=self._on_key_up)
            self._key_events_bound = True

        self.__class__._midi_initialized = True
        Logger.info("MIDI subsystem successfully initialised (1 IN, 1 OUT).")


    def reset_midi(self):
        Logger.info("Resetting MIDI subsystem...")
        self._close_existing_ports()
        self.setup_midi()

    def midi_callback(self, event, data=None):
        message, delta_time = event
        if len(message) < 3: return
        status, note, velocity = message[0], message[1], message[2]
        msg_type = status & 0xF0
        if msg_type == 0x90 and velocity > 0:
            self.active_notes[note] = time.time()
            Clock.schedule_once(lambda dt: self.create_circle(note, velocity), 0)
        elif msg_type == 0x80 or (msg_type == 0x90 and velocity == 0):
            if note in self.active_notes:
                duration = time.time() - self.active_notes.pop(note)

    def handle_onscreen_midi(self, message_type, note, velocity):
        if message_type == 'note_on' and velocity > 0:
            self.onscreen_notes[note] = time.time()
            self.send_midi_note(note, velocity)
            Clock.schedule_once(lambda dt: self.create_circle(note, velocity), 0)
        elif message_type == 'note_off' or (message_type == 'note_on' and velocity == 0):
            if note in self.onscreen_notes:
                duration = time.time() - self.onscreen_notes.pop(note)
                self.send_midi_note(note, 0, note_off=True)
                Clock.schedule_once(lambda dt: self.store_note_duration(note, duration), 0)

    def store_note_duration(self, note, duration):
        for circle in reversed(self.circles):
            if circle['note'] == note:
                circle['duration'] = duration
                break

    def send_midi_note(self, note, velocity, note_off=False, channel=None):
        if not self.midi_out: return
        try:
            ch = (channel - 1) if channel else (midi_manager.MIDI_CHANNEL - 1)
            message = [0x80 | ch, note, 0] if note_off else [0x90 | ch, note, velocity]
            self.midi_out.send_message(message)
            if not note_off: self.active_notes[note] = time.time()
            elif note in self.active_notes: del self.active_notes[note]
        except Exception as e: print(f"Error sending MIDI: {e}")

    def send_midi_transport(self, command):
        if not self.midi_out:
            return
        try:
            message = [command]
            self.midi_out.send_message(message)
        except Exception as e:
            print(f"Error sending MIDI transport command {command}: {e}")


    def _get_color_for_channel(self, channel):
        hue = (((channel - 1) % 16) / 16.0 + 0.55) % 1.0
        return (hue, 0.5, 1)

    def create_circle(self, note, velocity, circle_id=None, midi_channel=None):
        tile_index = note % 12
        animation_frames = self.circle_animations.get(tile_index, self.circle_animations.get(0))
        if not animation_frames: return
        size = 60
        speed_x = random.uniform(-2, 2) * (velocity / 127.0 * 2)
        speed_y = random.uniform(-2, 2) * (velocity / 127.0 * 2)

        x = (self.width / 2) - (size / 2)
        y = (self.height / 1.5) - (size / 2)

        is_grid_locked = False
        connection_mode = 0
        packet_state_a = False
        packet_state_b = False

        if self.last_selected_circle:
            is_grid_locked = self.last_selected_circle.get('grid_locked', False)
            connection_mode = self.last_selected_circle.get('connection_mode', 0)
            packet_state_a = self.last_selected_circle.get('packet_state_a', False)
            packet_state_b = self.last_selected_circle.get('packet_state_b', False)

        final_midi_channel = midi_channel if midi_channel is not None else midi_manager.MIDI_CHANNEL
        circle = {
            'pos': (x, y), 'size': size, 'note': note, 'velocity': velocity,
            'speed': (speed_x, speed_y), 'connections': [],
            'connection_mode': connection_mode,
            'duration': 0, 'flashing': False, 'flash_timer': 0.0, 'is_flashing_anim': False,
            'animation_frames': animation_frames, 'flash_frames': self.flash_animation,
            'current_frame_index': 0.0, 'midi_channel': final_midi_channel,
            'movement_enabled': not is_grid_locked,
            'packet_state_a': packet_state_a,
            'packet_state_b': packet_state_b,
            'grid_locked': is_grid_locked,
            'play_trigger': False, 'id': circle_id or str(uuid.uuid4())
        }

        if is_grid_locked:
            self._snap_circle_to_grid(circle)

        h, s, v = self._get_color_for_channel(circle['midi_channel'])
        with self.canvas.after:
            circle['color_instruction'] = Color(h, s, v, mode='hsv')
            circle['rect'] = Rectangle(texture=animation_frames[0], pos=circle['pos'], size=(size, size))

        self.circles.append(circle)
        self.show_duplicate(circle)
        circle['_dup_ref'] = self._current_dup
        self._select_circle(circle)

        app = App.get_running_app()
        if hasattr(app, 'guided_tour_overlay') and app.guided_tour_overlay:
            app.guided_tour_overlay.on_shape_created()


        if not self._hard_reset_running and len(self.circles) >= self.max_circles:
            self._trigger_shape_reset()
        return circle

    def flash_circle(self, circle):
        if circle['flash_frames']:
            circle['play_animation_once'] = 'flash_frames'
            circle['current_frame_index'] = 0

    def set_last_circle_connection_mode(self, mode):
        if not self.last_selected_circle: return
        self.last_selected_circle['connection_mode'] = mode
        if mode == 0:
            self._unlock_connections(self.last_selected_circle)
            for c1, c2, line, in self.connection_data[:]:
                if (c1 is self.last_selected_circle or c2 is self.last_selected_circle) and getattr(line, 'blocked', False):
                    self.canvas.before.remove(line)
                    self.connection_data.remove((c1, c2, line))
                    self.all_connections.remove(line)

    def _unlock_connections(self, circle):
        for c1, c2, line, in self.connection_data[:]:
            if c1 is circle or c2 is circle:
                if hasattr(line, 'locked'): del line.locked
                if hasattr(line, 'blocked'): del line.blocked

    def _select_circle(self, circle):
        self.last_selected_circle = circle
        self._update_selection_rect(circle)
        if circle:
            self.grid.visible = circle.get('grid_locked', False)
        else:
            if self._current_dup and self._dup_parent:
                if self._current_dup in self._dup_parent.children:
                    self._dup_parent.remove_widget(self._current_dup)
                self._current_dup = None

        root_layout = self.root_layout_ref
        if self.misc_controls_ref:
            misc = self.misc_controls_ref
            misc.sync_movement_button(circle)

            if root_layout:
                if hasattr(root_layout, 'circle_selector'):
                    cs = root_layout.circle_selector
                    if circle:
                        channel_num = circle.get('midi_channel', 1)
                        cs.channel_image.source = f"assets/shape_{channel_num}.png"
                        cs.current_channel = channel_num
                    else:
                        channel_num = midi_manager.MIDI_CHANNEL
                        cs.channel_image.source = f"assets/shape_{channel_num}.png"
                        cs.current_channel = channel_num

                if hasattr(root_layout, 'global_selector'):
                    gs = root_layout.global_selector
                    gs.channel_image.source = f"assets/shape_{midi_manager.MIDI_CHANNEL}.png"
                    gs.current_channel = midi_manager.MIDI_CHANNEL

            misc.sync_connection_mode_button(circle)
            misc.sync_packet_buttons(circle)

        if root_layout:
            root_layout.sync_play_trigger_button(circle)

    def _remove_circle(self, circle):
        if circle is self.last_selected_circle:
            self._update_selection_rect(None)
        if 'rect' in circle:
            if circle.get('color_instruction') in self.canvas.after.children:
                self.canvas.after.remove(circle['color_instruction'])
            if circle.get('rect') in self.canvas.after.children:
                self.canvas.after.remove(circle['rect'])

        if '_dup_ref' in circle and circle['_dup_ref'] in self._dup_parent.children:
            self._dup_parent.remove_widget(circle['_dup_ref'])
            self._current_dup = None
        for c1, c2, line, in self.connection_data[:]:
            if c1 is circle or c2 is circle:
                if color in self.canvas.before.children: self.canvas.before.remove(color)
                if line in self.canvas.before.children: self.canvas.before.remove(line)
                self.connection_data.remove((c1, c2, line, color))
                if line in self.all_connections: self.all_connections.remove(line)
        if circle in self.circles: self.circles.remove(circle)
        self.circle_id_to_circle.pop(circle.get('id'), None)

    def play_circle_note(self, circle):
        if not circle: return
        self.send_midi_note(circle['note'], circle['velocity'], channel=circle.get('midi_channel'))
        if circle['duration'] > 0:
            Clock.schedule_once(
                lambda dt, n=circle['note'], ch=circle.get('midi_channel'):
                self.send_midi_note(n, 0, True, ch),
                circle['duration']
            )

    def create_packet(self, start_circle, target_circle, creation_time):
        if start_circle is target_circle: return None
        x1, y1 = self.get_circle_center(start_circle)
        x2, y2 = self.get_circle_center(target_circle)
        euclidean_distance = math.hypot(x2 - x1, y2 - y1) or 1e-3
        grid_size = self.grid.grid_size
        start_grid_x = int(round(x1 / grid_size))
        start_grid_y = int(round(y1 / grid_size))
        target_grid_x = int(round(x2 / grid_size))
        target_grid_y = int(round(y2 / grid_size))
        journey_duration_in_ticks = max(abs(target_grid_x - start_grid_x), abs(target_grid_y - start_grid_y))
        start_tick = self.master_tick
        arrival_tick = start_tick + journey_duration_in_ticks
        packet = {
            'start_circle': start_circle, 'target_circle': target_circle, 'creation_time': creation_time,
            'start_tick': start_tick, 'journey_duration_in_ticks': journey_duration_in_ticks,
            'arrival_tick': arrival_tick, 'progress': 0.0, 'speed': self.packet_speed,
            'total_distance': euclidean_distance, 'graphic': None
        }


        sc_a = start_circle.get('packet_state_a', False)
        sc_b = start_circle.get('packet_state_b', False)
        if sc_a and sc_b:
            tc_a = target_circle.get('packet_state_a', False)
            tc_b = target_circle.get('packet_state_b', False)
            if tc_a and not tc_b:
                packet['respawn_origin_circle'] = start_circle

        if not hasattr(self, "packet_texture"): self.packet_texture = CoreImage("assets/packet.png").texture
        with self.canvas:
            packet['color_instruction'] = Color(1, 1, 1, 1)
            packet['graphic'] = Rectangle(texture=self.packet_texture, pos=(x1 - 10, y1 - 10), size=(20, 20))
        self.packets.append(packet)
        self.active_packet_count += 1
        return packet

    def update_packets(self, dt):
        packet_manager.update_packets(self, dt)

    def kill_all_packets(self):
        self.send_midi_transport(0xFC)
        for packet in self.packets:
            if not packet.get('is_fading'):
                packet['is_fading'] = True
                packet['fade_duration'] = 0.01
                packet['fade_timer'] = 0.0
                self.active_packet_count -= 1

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        if 'ctrl' in modifiers:
            self._ctrl_pressed = True

    def _on_key_up(self, window, key, scancode):
        if key in (305, 306):
            self._ctrl_pressed = False
            self._last_ctrl_clicked_circle = None

    def create_manual_connection(self, c1, c2):
        if not c1 or not c2 or c1 is c2:
            return

        pair_key = tuple(sorted((id(c1), id(c2))))
        connection_exists = any(
            tuple(sorted((id(c_a), id(c_b)))) == pair_key
            for c_a, c_b, _ in self.connection_data
        )

        if not connection_exists:
            x1, y1 = self.get_circle_center(c1)
            x2, y2 = self.get_circle_center(c2)
            connection_line = Line(points=[x1, y1, x2, y2], width=1.5)

            self.canvas.before.add(connection_line)
            self.connection_data.append((c1, c2, connection_line))
            self.all_connections.append(connection_line)

    def on_touch_down(self, touch, *args):

        if self.collide_point(touch.x, touch.y):
            for c1, c2, line in self.connection_data:
                if self.is_point_on_line_segment(touch.x, touch.y, *line.points):
                    is_inside_circle = any(
                        (touch.x - (c['pos'][0] + c['size'] / 2)) ** 2 +
                        (touch.y - (c['pos'][1] + c['size'] / 2)) ** 2
                        <= (c['size'] / 2) ** 2
                        for c in self.circles
                    )

                    if touch.is_double_tap and not is_inside_circle:
                        # Remove the line graphic
                        if line in self.canvas.before.children:
                            self.canvas.before.remove(line)
                        try:
                            self.connection_data.remove((c1, c2, line))
                        except ValueError:
                            pass

                        if hasattr(self, "_line_colour_map"):
                            self._line_colour_map.pop(line, None)

                        return True

            for circle in reversed(self.circles):
                cx, cy, r = (
                    circle['pos'][0] + circle['size'] / 2,
                    circle['pos'][1] + circle['size'] / 2,
                    circle['size'] / 2,
                )
                if (touch.x - cx) ** 2 + (touch.y - cy) ** 2 <= r ** 2:

                    # Ctrl‑click manual connection
                    if self._ctrl_pressed and (not hasattr(touch, 'button') or touch.button == 'left'):
                        if self._last_ctrl_clicked_circle and self._last_ctrl_clicked_circle is not circle:
                            self.create_manual_connection(self._last_ctrl_clicked_circle, circle)
                        self._last_ctrl_clicked_circle = circle
                        return True

                    self.active_touches[touch.id] = circle
                    other_touched_circles = [
                        c for tid, c in self.active_touches.items() if tid != touch.id
                    ]

                    if other_touched_circles:
                        for other_circle in other_touched_circles:
                            if other_circle is not circle:
                                self.create_manual_connection(circle, other_circle)
                        self._candidate_circle = None
                        self._dragged_circle = None
                        return True

                    self._candidate_circle = circle
                    self._touch_start_pos = (touch.x, touch.y)
                    self._drag_offset = (touch.x - cx, touch.y - cy)
                    self._select_circle(circle)
                    self.show_duplicate(circle)
                    return True

        touch.ud['mv_bg_tap'] = True
        return super().on_touch_down(touch, *args)

    def is_point_on_line_segment(self, px, py, x1, y1, x2, y2, threshold=10):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0: return (px - x1)**2 + (py - y1)**2 <= threshold**2
        proj = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx**2 + dy**2)))
        closest_x, closest_y = x1 + proj * dx, y1 + proj * dy
        return (px - closest_x)**2 + (py - closest_y)**2 <= threshold**2

    def on_touch_move(self, touch, *args):
        if self._dragged_circle:
            circle = self._dragged_circle
            new_cx, new_cy = touch.x - self._drag_offset[0], touch.y - self._drag_offset[1]
            if circle.get('grid_locked', False):
                grid_size = self.grid.grid_size
                new_cx, new_cy = round(new_cx / grid_size) * grid_size, round(new_cy / grid_size) * grid_size
            r = circle['size'] / 2
            nx = max(0, min(new_cx - r, self.width - circle['size']))
            ny = max(0, min(new_cy - r, self.height - circle['size']))
            circle['pos'] = (nx, ny)
            if 'rect' in circle: circle['rect'].pos = (nx, ny)
            return True
        if self._candidate_circle and math.hypot(touch.x - self._touch_start_pos[0], touch.y - self._touch_start_pos[1]) >= self._drag_threshold:
            self._dragged_circle, self._candidate_circle = self._candidate_circle, None
            return True
        return super().on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        self.active_touches.pop(touch.id, None)

        if self._dragged_circle:
            if self._dragged_circle.get('grid_locked', False): self._snap_circle_to_grid(self._dragged_circle)
            self._dragged_circle = None
            return True
        self._candidate_circle = None

        if touch.ud.get('mv_bg_tap'):
            dx = touch.x - touch.opos[0]
            dy = touch.y - touch.opos[1]

            if math.hypot(dx, dy) < 10:
                self._select_circle(None)

        return super().on_touch_up(touch, *args)

    def _on_duplicate_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._long_press_event = Clock.schedule_once(lambda dt: self._handle_duplicate_long_press(instance), 0.5)

            src = getattr(instance, 'source_circle', None)
            if src:
                self.play_circle_note(src)
                self.flash_circle(src)

            touch.grab(instance)
            return True
        return False

    def _on_duplicate_touch_up(self, instance, touch):
        if touch.grab_current is instance:
            if self._long_press_event:
                self._long_press_event.cancel()
                self._long_press_event = None
                src = getattr(instance, 'source_circle', None)
                if src:
                    self._select_circle(src)
                    self.trigger_packet_routing(src, play_note=False)
            touch.ungrab(instance)
            return True
        return False

    def _handle_duplicate_long_press(self, instance):
        self._long_press_event = None
        circle = instance.source_circle
        if not circle: return
        is_locked = not circle.get('grid_locked', False)
        circle['grid_locked'] = is_locked
        self.grid.visible = is_locked
        circle['movement_enabled'] = not is_locked
        if is_locked: self._snap_circle_to_grid(circle)

        app = App.get_running_app()
        if hasattr(app, 'guided_tour_overlay') and app.guided_tour_overlay:
            app.guided_tour_overlay.on_shape_locked()


        root = getattr(self, 'parent', None)
        if root and hasattr(root, 'misccontrols'):
            root.misccontrols.sync_movement_button(circle)

    def _snap_circle_to_grid(self, circle):
        grid_size, size = self.grid.grid_size, circle['size']
        center_x, center_y = circle['pos'][0] + size/2, circle['pos'][1] + size/2
        snapped_cx, snapped_cy = round(center_x / grid_size) * grid_size, round(center_y / grid_size) * grid_size
        new_x = max(0, min(snapped_cx - size/2, self.width - size))
        new_y = max(0, min(snapped_cy - size/2, self.height - size))
        circle['pos'] = (new_x, new_y)

    def update_tempo(self, new_packet_speed):
        elapsed_time = time.time() - self.last_tempo_change_time
        if self.current_tick_duration > 0:
            self.committed_ticks += int(elapsed_time / self.current_tick_duration)
        self.last_tempo_change_time = time.time()
        self.packet_speed = new_packet_speed
        self.current_tick_duration = 50.0 / max(self.packet_speed, 1.0)

    def update(self, dt):
        if self.is_playing and self.current_tick_duration > 0:
            midi_clock_interval = self.current_tick_duration / 6.0
            self._time_since_last_midi_clock += dt
            while self._time_since_last_midi_clock >= midi_clock_interval:
                self.send_midi_transport(0xF8) #MIDI Clock
                self._time_since_last_midi_clock -= midi_clock_interval

        if self.current_tick_duration > 0:
            self._time_since_last_quarter_note += dt
            quarter_note_duration = self.current_tick_duration * 4.0
            if self._time_since_last_quarter_note >= quarter_note_duration:
                self._quarter_note_counter = getattr(self, "_quarter_note_counter", 0) + 1

                if self._quarter_note_counter >= self.quarter_notes_per_trigger:
                    if self.pending_session_file:
                        file_to_load = self.pending_session_file
                        self.pending_session_file = None
                        session_manager.load_session_from_file(self, file_to_load)
                    if self.on_quarter_note_callback:
                        self.on_quarter_note_callback()
                    self._quarter_note_counter = 0
                    self._time_since_last_quarter_note -= quarter_note_duration * self.quarter_notes_per_trigger
                else:
                    self._time_since_last_quarter_note -= quarter_note_duration

        if self.packets:
            self._just_triggered = False

        if self.is_playing and not self.packets and not self._just_triggered:
            self.trigger_all_play_nodes()
            self._just_triggered = True

        if self.current_tick_duration > 0:
            elapsed_since_change = time.time() - self.last_tempo_change_time
            new_ticks = int(elapsed_since_change / self.current_tick_duration)
            self.master_tick = self.committed_ticks + new_ticks
            self.tick_progress = (elapsed_since_change % self.current_tick_duration) / self.current_tick_duration
        self.update_connections()
        self.update_packets(dt)

        for circle in self.circles[:]:
            if circle.get('movement_enabled', True):
                x, y, (speed_x, speed_y), size = *circle['pos'], circle['speed'], circle['size']
                new_x, new_y = x + speed_x * self.node_speed_multiplier, y + speed_y * self.node_speed_multiplier
                if new_x <= 0 or new_x + size >= self.width: speed_x *= -1; new_x = max(0, min(new_x, self.width - size))
                if new_y <= 0 or new_y + size >= self.height: speed_y *= -1; new_y = max(0, min(new_y, self.height - size))
                collided_boundary = self.check_collision(new_x, new_y, size)
                if collided_boundary and not self.check_collision(x, y, size):
                    cx, cy = x + size/2, y + size/2
                    bx, bw, bh = collided_boundary['x_start'], collided_boundary['x_end'] - collided_boundary['x_start'], collided_boundary['min_y']
                    dx, dy = cx - (bx + bw/2), cy - (0 + bh/2)
                    if abs(dx) / ((bw + size)/2) > abs(dy) / ((bh + size)/2):
                        speed_x *= -1
                        new_x = collided_boundary['x_end'] if dx > 0 else collided_boundary['x_start'] - size
                    else:
                        speed_y *= -1
                        new_y = collided_boundary['min_y'] if dy > 0 else -size
                circle['speed'], circle['pos'] = (speed_x, speed_y), (new_x, new_y)

            one_shot_anim_key = circle.get('play_animation_once')

            if one_shot_anim_key:
                active_frames = circle.get(one_shot_anim_key)
            else:
                active_frames = circle['animation_frames']

            if active_frames:
                circle['current_frame_index'] += self.animation_fps * dt
                if circle['current_frame_index'] >= len(active_frames):
                    circle['current_frame_index'] = 0
                    if one_shot_anim_key:
                        circle['play_animation_once'] = None

                frame_index = int(circle['current_frame_index']) % len(active_frames)
                circle['rect'].texture = active_frames[frame_index]

            if 'rect' in circle:
                circle['rect'].pos, circle['rect'].size = circle['pos'], (circle['size'], circle['size'])

        if self.last_selected_circle and hasattr(self, '_sel_line_instr'):
            c = self.last_selected_circle
            gap = 4
            self._sel_line_instr.rectangle = (
                c['pos'][0] - gap,
                c['pos'][1] - gap,
                c['size'] + gap*2,
                c['size'] + gap*2
            )

    def cleanup_soft(self):
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(on_key_up=self._on_key_up)

        self.send_panic()

    def cleanup_full(self):
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(on_key_up=self._on_key_up)

        self.send_panic()

        if platform == 'android':
            if self.android_midi: self.android_midi.close()
        else:
            if self.midi_in: self.midi_in.close_port()
            if self.midi_out: self.midi_out.close_port()

    def reset_aggressive(self, callback=None):
        self._reset_finished_cb = callback
        self._reset_stage = 'circles'
        self._reset_circle_index = 0
        Clock.schedule_interval(self._reset_step, 0.05)

    def _reset_step(self, dt):
        if self._reset_stage == 'packets':
            if self._reset_packet_index < len(self.packets):
                pkt = self.packets.pop(self._reset_packet_index)
                if pkt.get('graphic') and pkt['graphic'] in self.canvas.children: self.canvas.remove(pkt['graphic'])
                return True
            self._reset_stage, self._reset_circle_index = 'circles', 0
            return True
        if self._reset_stage == 'circles':
            if self._reset_circle_index < len(self.circles):
                circ = self.circles.pop(self._reset_circle_index)
                for c1, c2, line in list(self.connection_data):
                    if c1 is circ or c2 is circ:
                        if line in self.canvas.before.children: self.canvas.before.remove(line)
                        self.connection_data.remove((c1, c2, line))
                        if line in self.all_connections: self.all_connections.remove(line)
                if 'rect' in circ and circ['rect'] in self.canvas.after.children: self.canvas.after.remove(circ['rect'])
                if self._current_dup and getattr(self._current_dup, 'source_circle', None) is circ:
                    if self._dup_parent and self._current_dup in self._dup_parent.children:
                        self._dup_parent.remove_widget(self._current_dup)
                    self._current_dup = None
                self.circle_id_to_circle.pop(circ.get('id'), None)
                return True
            self._reset_stage = 'finalise'
            return True
        if self._reset_stage == 'finalise':
            self._update_selection_rect(None)
            self.last_selected_circle = None
            self.packets.clear(); self.connection_data.clear(); self.all_connections.clear()
            self.circle_id_to_circle.clear(); self.circles.clear(); self._line_colour_map.clear()
            self._current_dup, self._dup_parent = None, None
            self.is_playing = False
            self._just_triggered = False
            root_layout = self.root_layout_ref
            if root_layout and hasattr(root_layout, 'play_pause_button'):
                play_pause_button = root_layout.play_pause_button
                play_pause_button.play_state = 'pause'
                play_pause_button.source = 'assets/pause.png'
            Clock.unschedule(self._reset_step)
            if hasattr(self, "_reset_finished_cb") and callable(self._reset_finished_cb):
                try: self._reset_finished_cb()
                finally: self._reset_finished_cb = None
            return False
        return False

    def _trigger_hard_reset(self):
        if self._hard_reset_running:
            return
        self._hard_reset_running = True

        self._packet_animator = FrameAnimator(self, OVERLOADED_PACKETS_DIR, 30)
        self._packet_animator.start(center_offset=(0, 200))

        def after_reset():
            if hasattr(self, "_packet_animator"):
                try:
                    self._packet_animator.stop()
                except Exception as e:
                    logging.warning(f"Failed to stop _packet_animator: {e}")
                del self._packet_animator
            self._hard_reset_running = False

        self.reset_aggressive(callback=after_reset)


    def _trigger_shape_reset(self):
        if self._hard_reset_running:
            return
        self._hard_reset_running = True

        self._shape_animator = FrameAnimator(self, OVERLOADED_SHAPES_DIR, 30)
        self._shape_animator.start(center_offset=(0, 200))

        def after_reset():
            if hasattr(self, "_shape_animator"):
                try:
                    self._shape_animator.stop()
                except Exception as e:
                    logging.warning(f"Failed to stop _shape_animator: {e}")
                del self._shape_animator
            self._hard_reset_running = False

        self.reset_aggressive(callback=after_reset)



class ResetButton(ButtonBehavior, Image):
    STATE_DISARMED, STATE_ARMED, STATE_EXECUTING = 'disarmed', 'armed', 'executing'
    state_name = StringProperty(STATE_DISARMED)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint, self.size = (None, None), (120, 120)
        base_dir = os.path.abspath(os.path.dirname(__file__))
        self._frames_dir = {
            self.STATE_DISARMED: os.path.join(base_dir, "assets/disarmed"),
            self.STATE_ARMED: os.path.join(base_dir, "assets/armed"),
            self.STATE_EXECUTING: os.path.join(base_dir, "assets/executing"),
        }
        self._frame_cycle, self._anim_event, self._frame_rate = None, None, 30.0
        self._state_textures = self._load_all_textures()
        self.set_state(self.STATE_DISARMED, force_reload=True)
        self._long_press_event = None
        self.long_press_time = 1.0
        self.bind(on_press=self._on_press, on_release=self._on_release)

    def _load_state_textures(self, state):
        folder = self._frames_dir[state]
        if not os.path.exists(folder):
            logging.warning(f"ResetButton: Frame folder not found: {folder}")
            return []

        png_files = sorted(f for f in os.listdir(folder) if f.lower().endswith('.png'))
        if not png_files:
            logging.warning(f"ResetButton: No PNG frames found in {folder}")
            return []

        return [CoreImage(os.path.join(folder, fn)).texture for fn in png_files]

    def _load_all_textures(self):
        all_textures = {}
        for state in self._frames_dir:
            all_textures[state] = self._load_state_textures(state)
        return all_textures


    def set_state(self, new_state: str, force_reload=False):
        if self.state_name == new_state and hasattr(self, 'texture') and not force_reload:
            return
        if new_state not in self._frames_dir: raise ValueError(f'Invalid state: {new_state!r}')

        self.state_name = new_state
        textures = self._state_textures.get(new_state)

        if not textures:
             return

        self._frame_cycle = cycle(textures)
        if self._anim_event: self._anim_event.cancel()
        self.texture = next(self._frame_cycle)
        self._anim_event = Clock.schedule_interval(self._next_frame, 1.0 / self._frame_rate)

    def _next_frame(self, dt):
        try:
            if self._frame_cycle:
                self.texture = next(self._frame_cycle)
        except Exception as e:
            logging.warning(f"ResetButton: Failed to get next frame: {e}")
            if self._anim_event:
                self._anim_event.cancel()
                self._anim_event = None

    def _on_press(self, *args):
        self._long_press_event = Clock.schedule_once(self._do_long_press, self.long_press_time)

    def _on_release(self, *args):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            self._do_short_press()

    def _do_short_press(self):
        if self.state_name == self.STATE_ARMED:
            self.set_state(self.STATE_EXECUTING)
            if hasattr(self, "visualizer"):
                self.visualizer.reset_aggressive(callback=self._reset_done)
            else:
                self._reset_done()

        elif self.state_name == self.STATE_DISARMED:
            logging.info("ResetButton: Short press. Opening Goodies Menu.")
            app = App.get_running_app()
            if app:
                app.switch_to_widget('goodies_menu')

    def _do_long_press(self, dt):
        self._long_press_event = None

        if self.state_name == self.STATE_DISARMED:
            logging.info("ResetButton: Long press. Button ARMED.")
            self.set_state(self.STATE_ARMED)

    def _reset_done(self, *_, **__):
        self.set_state(self.STATE_DISARMED)

    def on_touch_down(self, touch):
        if (self.state_name == self.STATE_ARMED and
            self.parent and
            not self.collide_point(*touch.pos)):
            self.set_state(self.STATE_DISARMED)
            return False

        return super().on_touch_down(touch)

    def on_parent(self, widget, parent):
        if parent is None:
            if self._anim_event:
                self._anim_event.cancel()
                self._anim_event = None


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
            self.settings_menu_widget = SettingsMenu(
                app_switcher=self.switch_to_widget,
                midi_manager=midi_mgr,
                visualizer=self.midi_visualizer
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
