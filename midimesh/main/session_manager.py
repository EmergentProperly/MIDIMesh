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
import json
import uuid
import time
import gc

from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.uix.button import ButtonBehavior
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.label import Label
from kivy.animation import Animation

from misc.animated_fonts import AnimatedLabel

def _norm_pair(id1, id2):
    return tuple(sorted((str(id1), str(id2))))

def get_save_dir():
    if platform == 'android':
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = PythonActivity.mActivity
        app_storage_path = context.getExternalFilesDir(None).getAbsolutePath()
        app_save_dir = os.path.join(app_storage_path, "saves")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(script_dir))
        app_save_dir = os.path.join(root_dir, "saves")

    if not os.path.exists(app_save_dir):
        try:
            os.makedirs(app_save_dir)
        except Exception as e:
            print(f"Error creating save directory {app_save_dir}: {e}")
    return app_save_dir

class ScreenshotImage(ButtonBehavior, Image):
    popup = ObjectProperty(None)
    json_path = StringProperty('')
    png_path = StringProperty('')
    load_state = StringProperty('normal')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.popup = kwargs.get('popup')
        self._long_press_event = None
        self._flash_event = None
        self.bind(load_state=self.on_load_state_change,
                  pos=self.on_load_state_change,
                  size=self.on_load_state_change)

    def on_load_state_change(self, *args):
        self.canvas.after.clear()
        if self._flash_event:
            self._flash_event.cancel()
            self._flash_event = None

        if self.load_state == 'armed_load':
            with self.canvas.after:
                Color(1, 1, 1, 1)
                Line(rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2), width=2)
        elif self.load_state == 'armed_delete':
            def flash_border(dt):
                is_on = int(time.time() * 5) % 2 == 0
                self.canvas.after.clear()
                if is_on:
                    with self.canvas.after:
                        Color(0.7, 0.0, 0.2, 1)
                        Line(rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2), width=2)
            self._flash_event = Clock.schedule_interval(flash_border, 0.1)

    def on_press(self):
        self._long_press_event = Clock.schedule_once(self._do_long_press, 0.5)

    def on_release(self):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            if self.popup:
                self.popup.handle_tap(self)

    def _do_long_press(self, dt):
        self._long_press_event = None
        if self.popup:
            self.popup.handle_long_press(self)


class CycleLoadButton(ButtonBehavior, Image):
    def __init__(self, popup, **kwargs):
        super().__init__(**kwargs)
        self.popup = popup
        self.size_hint = (0.125, 0.8)
        self.allow_stretch=True
        self.keep_ratio=True
        self.mode = 'load'
        self._refresh_source()
        self.bind(disabled=self._on_disabled_change)

    def _mode_assets(self):
        if self.mode == 'loop':
            return ('assets/flat_button_loop.png',
                    'assets/flat_button_loop_pressed.png')
        return ('assets/flat_button_grey_load.png',
                'assets/flat_button_grey_load_pressed.png')

    def set_mode(self, mode):
        if mode != self.mode:
            self.mode = mode
            self._refresh_source()

    def _refresh_source(self):
        normal, pressed = self._mode_assets()
        self.source = pressed if self.disabled else normal

    def _on_disabled_change(self, *args):
        self._refresh_source()

    def on_press(self):
        _, pressed = self._mode_assets()
        self.source = pressed

    def on_release(self):
        self._refresh_source()
        if self.disabled or not self.popup.selected_saves:
            return

        if len(self.popup.selected_saves) == 1:
            load_session_from_file(self.popup.visualizer, self.popup.selected_saves[0])
        else:
            ticks = int(self.popup.slider.value)
            self.popup.visualizer.start_pattern_cycling(self.popup.selected_saves, ticks)
        self.popup.dismiss()


class LoadPopup(Popup):
    STAGE_SIZE = (1536, 864)

    def _get_scatter(self):
        app = App.get_running_app()
        container = getattr(app, 'app_container', None)
        return container.scatter if container else None

    def sync_to_stage(self, *args):
        scatter = self._get_scatter()
        if not scatter:
            return
        s = scatter.scale
        self.size_hint = (None, None)
        self.size = (self.STAGE_SIZE[0] * s, self.STAGE_SIZE[1] * s)
        self.pos = (
            scatter.x + (scatter.width - self.STAGE_SIZE[0]) / 2 * s,
            scatter.y + (scatter.height - self.STAGE_SIZE[1]) / 2 * s
        )

    def open(self, **kwargs):
        if self.visualizer.is_cycling:
            self.visualizer.stop_pattern_cycling()
        super().open(**kwargs)
        scatter = self._get_scatter()
        if scatter:
            self.sync_to_stage()
            scatter.bind(scale=self.sync_to_stage, pos=self.sync_to_stage)

    def on_dismiss(self):
        if hasattr(self, 'cycle_label') and isinstance(self.cycle_label, AnimatedLabel):
            self.cycle_label._stop_animation()
        scatter = self._get_scatter()
        if scatter:
            scatter.unbind(scale=self.sync_to_stage, pos=self.sync_to_stage)
        return super().on_dismiss()

    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.size_hint = (None, None)
        self.title = ''
        self.separator_height = 0
        self.background_color = [0.0, 0.0, 0.0, 0.9]
        self.background = ''

        layout = FloatLayout()
        self.grid = GridLayout(cols=2, spacing=26, size_hint_y=None, padding=13)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll_view = ScrollView(
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            do_scroll_x=False
        )
        scroll_view.add_widget(self.grid)
        layout.add_widget(scroll_view)

        self.cycle_layout = BoxLayout(size_hint=(None, None), size=(1920, 200), padding=(10, 10), spacing=20,
                                      pos_hint={'center_x': 0.5, 'y': 0.0})

        self.cycle_layout.canvas.before.clear()

        self.load_button = CycleLoadButton(popup=self)
        self.load_button.size = (200, 200)

        self.slider = Slider(min=1, max=256, step=1, value=1,
                             background_horizontal='assets/single_slider_bg.png',
                             border_horizontal=(0, 0, 0, 0), background_width=40,
                             value_track_color=(0, 0, 0, 0),
                             cursor_image='assets/node_mini_app_disabled.png',
                             cursor_size=(100, 100), padding=60,
                             size_hint=(0.8, 1),
                             pos_hint={'center_x': 0.7, 'y': -0.125})
        self.slider.bind(value=self._on_slider_change)

        self.cycle_label = AnimatedLabel(
            text='1 ticks',
            font_size='46px',
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            size_hint=(0.25, 0.8),
            animation_interval=0.125
        )

        self.cycle_layout.add_widget(self.load_button)
        self.cycle_layout.add_widget(self.slider)
        self.cycle_layout.add_widget(self.cycle_label)

        self.bg_panel = Image(source='assets/panel_02.png', allow_stretch=True, keep_ratio=False, size_hint=(1,0.165),
                              pos_hint={'center_x': 0.5, 'y': 0})
        layout.add_widget(self.bg_panel)
        layout.add_widget(self.cycle_layout)

        self.content = layout

        self.bind(size=self._update_cycle_layout_size)

        self.armed_image = None
        self.selected_saves = []
        self.populate_grid()

    def _update_cycle_layout_size(self, *args):
        if self.width <= 0 or self.height <= 0:
            return

        scale_x = self.width / 1920.0
        scale_y = self.height / 1080.0
        scale = min(scale_x, scale_y)

        self.cycle_layout.size = (1920 * scale, 200 * scale)
        self.bg_panel.size = (1920 * scale, 200 * scale)
        self.load_button.size = (200 * scale, 200 * scale)

        slider_width = 1920 * scale * 0.8
        slider_height = 200 * scale * 0.8
        self.slider.size = (slider_width, slider_height)
        self.slider.cursor_size = (120 * scale, 120 * scale)
        self.slider.background_width = 60 * scale

        label_width = 1920 * scale * 0.25
        label_height = 200 * scale * 0.8
        self.cycle_label.size = (label_width, label_height)
        self.cycle_label.font_size = f"{46 * scale}px"

    def _on_slider_change(self, instance, value):
        self.cycle_label.text = f"{int(value)} ticks"

    def _update_cycle_ui(self):
        is_enabled = len(self.selected_saves) >= 1
        cycle_ready = len(self.selected_saves) >= 2
        self._cycle_interaction_enabled = is_enabled
        self.slider.disabled = False
        self.load_button.set_mode('loop' if len(self.selected_saves) >= 2 else 'load')
        self.load_button.disabled = not is_enabled
        self.slider.cursor_image = 'assets/node_mini_app.png' if cycle_ready else 'assets/node_mini_app_disabled.png'
        self.slider.background_horizontal = 'assets/single_slider_bg.png'
        self.slider.value_track_color = (0, 0, 0, 0) if is_enabled else (0.3, 0.3, 0.3, 0.2)
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.cycle_layout.pos
            self.bg_rect.size = self.cycle_layout.size

        self.load_button.disabled = not is_enabled


    def stop_cycling_if_active(self):
        if self.visualizer.is_cycling:
            self.visualizer.stop_pattern_cycling()
            self.selected_saves = []
            self._update_cycle_ui()
            for img in self.grid.children:
                if isinstance(img, ScreenshotImage):
                    img.load_state = 'normal'


    def populate_grid(self):
        self.grid.clear_widgets()
        save_dir = get_save_dir()
        if not os.path.exists(save_dir): return
        saves = sorted([f for f in os.listdir(save_dir) if f.endswith('.json')], reverse=True)
        for json_file in saves:
            base_name = json_file[:-5]
            png_path = os.path.join(save_dir, f"{base_name}.png")
            json_path = os.path.join(save_dir, json_file)
            if os.path.exists(png_path):
                img = ScreenshotImage(
                    source=png_path, json_path=json_path, png_path=png_path,
                    size_hint_y=None,
                    popup=self,
                    allow_stretch=True, keep_ratio=False
                )

                img.bind(width=lambda instance, width: setattr(instance, 'height', width * 9 / 16))
                self.grid.add_widget(img)

    def handle_tap(self, image_widget):
        json_path = image_widget.json_path
        if image_widget.load_state == 'armed_delete':
            try:
                os.remove(image_widget.json_path)
                os.remove(image_widget.png_path)
            except Exception: pass
            if json_path in self.selected_saves:
                self.selected_saves.remove(json_path)
            self.armed_image = None
            self.populate_grid()
            return

        if json_path in self.selected_saves:
            if len(self.selected_saves) > 1:
                self.selected_saves.remove(json_path)
                image_widget.load_state = 'normal'
                self._update_cycle_ui()
            else:
                self.stop_cycling_if_active()
                load_session_from_file(self.visualizer, json_path)
                self.dismiss()
        else:
            self.selected_saves.append(json_path)
            image_widget.load_state = 'armed_load'
            self._update_cycle_ui()



    def handle_long_press(self, image_widget):
        if self.armed_image and self.armed_image != image_widget:
            self.armed_image.load_state = 'normal'
        self.armed_image = image_widget
        image_widget.load_state = 'armed_delete'

    def on_touch_down(self, touch):
        if super().on_touch_down(touch): return True

        if not getattr(self, '_cycle_interaction_enabled', False):
            if self.cycle_layout.collide_point(*touch.pos):
                return True

        if self.collide_point(*touch.pos) and self.armed_image:
            self.armed_image.load_state = 'normal'
            self.armed_image = None
            return True
        return False

def _do_screenshot(png_filename, json_filename, base_filename):
    try:
        widget_to_capture = App.get_running_app().app_container
        widget_to_capture.export_to_png(png_filename)
        print(f"Saved session to {json_filename} with screenshot {png_filename}")
    except Exception as e:
        print(f"Failed to take screenshot: {e}")

def _perform_final_save(visualizer, json_filename, png_filename, base_filename, label_widget):
    cp = visualizer._get_control_panel()
    save_data = {"circles": [], "connection_data": []}

    root_layout = visualizer.parent

    play_state = 'pause'
    if hasattr(visualizer, 'root_layout_ref') and visualizer.root_layout_ref:
         if hasattr(visualizer.root_layout_ref, 'play_pause_button'):
             play_state = visualizer.root_layout_ref.play_pause_button.play_state

    save_data["play_state"] = play_state

    if cp is not None:
        save_data["sliders"] = {
            "packet_speed": {"value": cp.packet_speed, "pos": cp.control_nodes[0].pos},
            "packet_life": {"value": cp.packet_life, "pos": cp.control_nodes[1].pos},
            "max_connection_distance": {"value": cp.max_connection_distance, "pos": cp.control_nodes[2].pos},
            "node_speed_multiplier": {"value": cp.node_speed_multiplier, "pos": cp.control_nodes[3].pos},
            "max_connections_per_node": {"value": cp.max_connections_per_node, "pos": cp.control_nodes[4].pos}
        }

    uniq_circles = {}
    for circle in visualizer.circles:
        uid = str(circle.get("id", uuid.uuid4()))
        uniq_circles[uid] = {
            "id": uid, "pos": circle["pos"], "size": circle["size"],
            "note": circle["note"], "velocity": circle["velocity"],
            "duration": circle["duration"], "speed": circle["speed"],
            "connection_mode": circle["connection_mode"],
            "midi_channel": circle["midi_channel"],
            "movement_enabled": circle["movement_enabled"],
            "packet_state_a": circle.get("packet_state_a", False),
            "packet_state_b": circle.get("packet_state_b", False),
            "grid_locked": circle.get("grid_locked", False),
            "play_trigger": circle.get("play_trigger", False),
            "is_merged": circle.get("is_merged", False),
            "merged_notes": circle.get("merged_notes", []),
            "strum_delay_ms": circle.get("strum_delay_ms", 0),
            "lag_ticks": circle.get("lag_ticks", 0),
            "locked_connection_index": circle.get("locked_connection_index", 0)
        }
    save_data["circles"] = list(uniq_circles.values())

    _seen_pairs = set()
    for circle1, circle2, line in visualizer.connection_data:
        pair_key = _norm_pair(circle1.get("id"), circle2.get("id"))
        if pair_key in _seen_pairs: continue
        _seen_pairs.add(pair_key)
        save_data["connection_data"].append({
            "circle1_id": str(circle1.get("id")), "circle2_id": str(circle2.get("id")),
            "points": list(line.points), "width": line.width,
            "locked": getattr(line, "locked", False),
            "blocked": getattr(line, "blocked", False)
        })

    with open(json_filename, "w") as f:
        json.dump(save_data, f, indent=4)

    _do_screenshot(png_filename, json_filename, base_filename)

    if label_widget:
        anim = Animation(opacity=0, duration=0.8)
        anim.bind(on_complete=lambda *args: label_widget.parent.remove_widget(label_widget))
        anim.start(label_widget)


def save_session(visualizer):
    save_dir = get_save_dir()
    if not os.path.exists(save_dir): os.makedirs(save_dir)


    existing_files = [f for f in os.listdir(save_dir) if f.startswith("save_") and f.endswith(".json")]
    next_num = 1
    if existing_files:
        numbers = [int(f[5:-5]) for f in existing_files]
        next_num = max(numbers) + 1 if numbers else 1

    base_filename = f"save_{next_num:03d}"
    json_filename = os.path.join(save_dir, f"{base_filename}.json")
    png_filename = os.path.join(save_dir, f"{base_filename}.png")

    target_parent = None
    if hasattr(visualizer, 'root_layout_ref') and visualizer.root_layout_ref:
        target_parent = visualizer.root_layout_ref.ui_container
    else:
        target_parent = visualizer.parent

    save_label = Label(
        text=f"Save {next_num:03d}",
        font_size=150,
        bold=True,
        color=(1, 1, 1, 1),
        outline_width=5,
        outline_color=(0, 0, 0, 1),
        pos_hint={'center_x': 0.5, 'top': 0.95},
        size_hint=(None, None),
        size=(600, 200)
    )

    if target_parent:
        target_parent.add_widget(save_label)

    Clock.schedule_once(
        lambda dt: _perform_final_save(visualizer, json_filename, png_filename, base_filename, save_label),
        0.1
    )

def get_next_session_filename(visualizer):
    save_dir = get_save_dir()
    if not os.path.exists(save_dir):
        print("No saves directory found.")
        return None

    saves = sorted([f for f in os.listdir(save_dir) if f.startswith("save_") and f.endswith(".json")])
    if not saves:
        print("No saved sessions found.")
        return None

    next_index = (visualizer.current_save_index + 1) % len(saves)

    visualizer.current_save_index = next_index

    filename = os.path.join(save_dir, saves[next_index])
    return filename

def load_next_session(visualizer):
    filename = get_next_session_filename(visualizer)
    if filename:
        load_session_from_file(visualizer, filename)

def reset_tick_timer(visualizer):
    visualizer.last_tempo_change_time = time.time()
    visualizer.committed_ticks = 0
    visualizer.master_tick = 0
    visualizer.tick_progress = 0.0
    visualizer._time_since_last_midi_clock = 0.0
    visualizer._time_since_last_quarter_note = 0.0

def _apply_session_data(visualizer, save_data):
    reset_tick_timer(visualizer)

    visualizer.grid.visible = False
    cp = visualizer._get_control_panel()
    sliders = save_data.get("sliders", {})

    if cp is not None and sliders:
        def _fetch(name, default_val, default_pos):
            d = sliders.get(name, {})
            return d.get("value", default_val), d.get("pos", default_pos)

        val, pos = _fetch("packet_speed", cp.packet_speed, cp.control_nodes[0].pos)
        cp.packet_speed = val; cp.control_nodes[0].pos = tuple(pos)
        val, pos = _fetch("packet_life", cp.packet_life, cp.control_nodes[1].pos)
        cp.packet_life = val; cp.control_nodes[1].pos = tuple(pos)
        val, pos = _fetch("max_connection_distance", cp.max_connection_distance, cp.control_nodes[2].pos)
        cp.max_connection_distance = val; cp.control_nodes[2].pos = tuple(pos)
        val, pos = _fetch("node_speed_multiplier", cp.node_speed_multiplier, cp.control_nodes[3].pos)
        cp.node_speed_multiplier = val; cp.control_nodes[3].pos = tuple(pos)
        val, pos = _fetch("max_connections_per_node", cp.max_connections_per_node, cp.control_nodes[4].pos)
        cp.max_connections_per_node = val; cp.control_nodes[4].pos = tuple(pos)

        cp.pending_packet_speed = cp.packet_speed
        visualizer.update_tempo(cp.packet_speed)
        visualizer.update_packet_life(cp, cp.packet_life)
        visualizer.update_max_distance(cp, cp.max_connection_distance)
        visualizer.update_node_speed(cp, cp.node_speed_multiplier)
        visualizer.update_max_connections(cp, cp.max_connections_per_node)

    visualizer.circles.clear()
    visualizer.packets.clear()
    visualizer.connection_data.clear()
    visualizer.all_connections.clear()
    visualizer.circle_id_to_circle.clear()
    visualizer.active_packet_count = 0
    visualizer.active_notes.clear()
    if hasattr(visualizer, '_line_colour_map'):
        visualizer._line_colour_map.clear()
    visualizer.canvas.clear()
    visualizer.canvas.before.clear()
    visualizer.canvas.after.clear()


    if hasattr(visualizer, 'connection_color'):
        if visualizer.connection_color not in visualizer.canvas.before.children:
            visualizer.canvas.before.insert(0, visualizer.connection_color)

    for circle_data in save_data["circles"]:
        circle = visualizer.create_circle(
            circle_data["note"],
            circle_data["velocity"],
            circle_id=circle_data["id"],
            midi_channel=circle_data["midi_channel"],
            ui_feedback=False
        )

        if circle:
            circle["pos"] = circle_data["pos"]; circle["size"] = circle_data["size"]
            if 'rect' in circle:
                circle['rect'].pos = circle["pos"]
                circle['rect'].size = (circle["size"], circle["size"])
            circle["speed"] = circle_data["speed"]; circle["duration"] = circle_data["duration"]
            circle["connection_mode"] = circle_data["connection_mode"]
            circle["movement_enabled"] = circle_data["movement_enabled"]
            circle["packet_state_a"] = circle_data.get("packet_state_a", False)
            circle["packet_state_b"] = circle_data.get("packet_state_b", False)
            circle["grid_locked"] = circle_data.get("grid_locked", False)
            circle["play_trigger"] = circle_data.get("play_trigger", False)
            circle["lag_ticks"] = circle_data.get("lag_ticks", 0)
            circle["locked_connection_index"] = circle_data.get("locked_connection_index", 0)

            if circle_data.get("is_merged", False):
                circle["is_merged"] = True
                circle["merged_notes"] = circle_data.get("merged_notes", [])
                circle["strum_delay_ms"] = circle_data.get("strum_delay_ms", 0)
                if hasattr(visualizer, 'globe_animations') and visualizer.globe_animations:
                    circle["animation_frames"] = visualizer.globe_animations
                    if "rect" in circle:
                        circle["rect"].texture = visualizer.globe_animations[0]

            if circle["grid_locked"]:
                visualizer.grid.visible = True
            visualizer.circle_id_to_circle[circle["id"]] = circle

    for conn_data in save_data["connection_data"]:
        circle1 = visualizer.circle_id_to_circle.get(conn_data["circle1_id"])
        circle2 = visualizer.circle_id_to_circle.get(conn_data["circle2_id"])
        if circle1 and circle2:
            c1_center = visualizer.get_circle_center(circle1)
            c2_center = visualizer.get_circle_center(circle2)
            with visualizer.canvas.before:
                line = Line(points=[c1_center[0], c1_center[1], c2_center[0], c2_center[1]], width=conn_data.get("width", 1.5))
                if conn_data.get("locked"): line.locked = True
                if conn_data.get("blocked"): line.blocked = True
            visualizer.connection_data.append((circle1, circle2, line))
            visualizer.all_connections.append(line)

    visualizer.update_connections()
    visualizer._sync_circle_rects()
    if not visualizer.is_cycling:
        loaded_play_state = save_data.get("play_state", "pause")
        root_layout = visualizer.parent
        if root_layout and hasattr(root_layout, 'play_pause_button'):
            play_pause_button = root_layout.play_pause_button
            play_pause_button.play_state = loaded_play_state

            if loaded_play_state == 'play':
                play_pause_button.source = 'assets/play.png'
                visualizer.is_playing = True
            else:
                play_pause_button.source = 'assets/pause.png'
                visualizer.is_playing = False

    if visualizer.is_playing:
        visualizer._just_triggered = False
        visualizer.trigger_all_play_nodes()
        visualizer._just_triggered = True
    else:
        visualizer._just_triggered = True

    visualizer._select_circle(None)


def load_session_from_file(visualizer, filename):
    try:
        with open(filename, "r") as f:
            save_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading session file {filename}: {e}")
        return

    try:
        save_dir = get_save_dir()
        saves = sorted([f for f in os.listdir(save_dir) if f.startswith("save_") and f.endswith(".json")])
        base_name = os.path.basename(filename)
        if base_name in saves:
            visualizer.current_save_index = saves.index(base_name)
    except Exception as e:
        print(f"Index sync warning: {e}")

    _apply_session_data(visualizer, save_data)
    print(f"Loaded session from {filename}")

def preload_cycle_patterns(patterns):
    preloaded = []
    for path in patterns:
        try:
            with open(path, "r") as f:
                preloaded.append(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to preload pattern {path}: {e}")
            preloaded.append(None)
    return preloaded

