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
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.button import ButtonBehavior
from kivy.graphics import Color, Line
from kivy.uix.label import Label
from kivy.animation import Animation




def get_tracker_save_dir():
    save_dir = ""

    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            app_storage_path = context.getExternalFilesDir(None).getAbsolutePath()
            save_dir = os.path.join(app_storage_path, "saves", "tracker")
        except Exception as e:
            print(f"Android storage error: {e}")
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves", "tracker")
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(root_dir, "../saves", "tracker")
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
            print(f"Created tracker save directory: {save_dir}")
        except Exception as e:
            print(f"Error creating tracker save directory {save_dir}: {e}")

    return save_dir

class TrackerScreenshotImage(ButtonBehavior, Image):
    popup = None
    json_path = ''
    png_path = ''
    load_state = 'normal'

    def __init__(self, **kwargs):
        self.popup = kwargs.pop('popup', None)
        self.json_path = kwargs.pop('json_path', '')
        self.png_path = kwargs.pop('png_path', '')
        super().__init__(**kwargs)
        self._long_press_event = None
        self._flash_event = None
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.after.clear()
        if self._flash_event:
            self._flash_event.cancel()
            self._flash_event = None

        if self.load_state == 'armed_load':
            with self.canvas.after:
                Color(0.2, 0.8, 0.2, 1)
                Line(rectangle=(self.x + 2, self.y + 2, self.width - 4, self.height - 4), width=2)
        elif self.load_state == 'armed_delete':
            def flash_border(dt):
                is_on = int(time.time() * 5) % 2 == 0
                self.canvas.after.clear()
                if is_on:
                    with self.canvas.after:
                        Color(1, 0, 0, 1)
                        Line(rectangle=(self.x + 2, self.y + 2, self.width - 4, self.height - 4), width=2)
            self._flash_event = Clock.schedule_interval(flash_border, 0.1)

    def on_press(self):
        self._long_press_event = Clock.schedule_once(self._do_long_press, 0.6)

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
            self.update_canvas()

class TrackerLoadPopup(Popup):
    def __init__(self, tracker_app, **kwargs):
        super().__init__(**kwargs)
        self.tracker_app = tracker_app
        self.title = 'LOAD SESSION'
        self.title_size = '24sp'
        self.title_font = 'RobotoMono-Regular'
        self.size_hint = (0.9, 0.9)
        self.separator_color = [0.2, 0.8, 0.2, 1]
        self.grid = GridLayout(cols=3, spacing=20, size_hint_y=None, padding=20)
        self.grid.bind(minimum_height=self.grid.setter('height'))

        scroll = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        scroll.add_widget(self.grid)

        self.content = scroll
        self.armed_image = None
        self.populate_grid()

    def populate_grid(self):
        self.grid.clear_widgets()
        save_dir = get_tracker_save_dir()
        if not os.path.exists(save_dir): return
        files = [f for f in os.listdir(save_dir) if f.endswith('.json')]
        full_paths = [os.path.join(save_dir, f) for f in files]

        if not files: return

        files_sorted = sorted(zip(files, full_paths), key=lambda x: os.path.getmtime(x[1]), reverse=True)

        for json_file, full_json_path in files_sorted:
            base_name = json_file[:-5]
            png_path = os.path.join(save_dir, f"{base_name}.png")

            if os.path.exists(png_path):
                img = TrackerScreenshotImage(
                    source=png_path,
                    json_path=full_json_path,
                    png_path=png_path,
                    popup=self,
                    size_hint_y=None,
                    keep_ratio=True,
                    allow_stretch=True
                )
                img.bind(width=lambda instance, width: setattr(instance, 'height', width * 9/16))
                self.grid.add_widget(img)

    def handle_tap(self, image_widget):
        if self.armed_image != image_widget:
            if self.armed_image:
                self.armed_image.load_state = 'normal'
                self.armed_image.update_canvas()

            self.armed_image = image_widget
            image_widget.load_state = 'armed_load'
            image_widget.update_canvas()
        else:
            if image_widget.load_state == 'armed_load':
                load_tracker_session(self.tracker_app, image_widget.json_path)
                self.dismiss()
            elif image_widget.load_state == 'armed_delete':
                try:
                    os.remove(image_widget.json_path)
                    os.remove(image_widget.png_path)
                except Exception as e:
                    print(f"Error deleting: {e}")
                self.armed_image = None
                self.populate_grid()

    def handle_long_press(self, image_widget):
        if self.armed_image and self.armed_image != image_widget:
            self.armed_image.load_state = 'normal'
            self.armed_image.update_canvas()

        self.armed_image = image_widget
        image_widget.load_state = 'armed_delete'
        image_widget.update_canvas()

def _capture_screenshot(widget_to_capture, png_path):
    try:
        if widget_to_capture:
            widget_to_capture.export_to_png(png_path)
            print(f"Screenshot saved to {png_path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")

def _perform_final_tracker_save(tracker_interface, json_path, png_path, label_widget):
    grid = tracker_interface.tracker_grid
    rows_data = []
    for row in grid.data:
        tracks_clean = {str(k): v for k, v in row.get('tracks', {}).items()}
        rows_data.append(tracks_clean)

    session_data = {
        "meta": {
            "bpm": tracker_interface.bpm,
            "track_count": grid.track_count,
            "loop_start": grid.loop_start,
            "loop_end": grid.loop_end,
            "loop_enabled": grid.loop_enabled,
            "view_offset_x": grid.view_offset_x
        },
        "rows": rows_data
    }

    try:
        with open(json_path, 'w') as f:
            json.dump(session_data, f, indent=4)
        print(f"Session data saved to {json_path}")

        _capture_screenshot(tracker_interface, png_path)

        if label_widget:
            anim = Animation(opacity=0, duration=0.8)
            anim.bind(on_complete=lambda *args: tracker_interface.remove_widget(label_widget))
            anim.start(label_widget)

    except Exception as e:
        print(f"Failed to save session: {e}")
        if label_widget:
            tracker_interface.remove_widget(label_widget)


def save_tracker_session(tracker_interface):
    grid = tracker_interface.tracker_grid
    if not grid: return

    save_dir = get_tracker_save_dir()

    existing = [f for f in os.listdir(save_dir) if f.startswith("trk_") and f.endswith(".json")]
    next_num = 1
    if existing:
        try:
            numbers = [int(f[4:-5]) for f in existing]
            next_num = max(numbers) + 1
        except:
            pass

    base_name = f"trk_{next_num:03d}"
    json_path = os.path.join(save_dir, f"{base_name}.json")
    png_path = os.path.join(save_dir, f"{base_name}.png")

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

    tracker_interface.add_widget(save_label)

    Clock.schedule_once(
        lambda dt: _perform_final_tracker_save(tracker_interface, json_path, png_path, save_label),
        0.1
    )

def load_tracker_session(tracker_interface, filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return

    grid = tracker_interface.tracker_grid
    meta = data.get("meta", {})
    rows = data.get("rows", [])

    tracker_interface.stop_playback()
    tracker_interface.bpm = meta.get("bpm", 120)

    grid.track_count = meta.get("track_count", 4)
    grid.loop_start = meta.get("loop_start", 0)
    grid.loop_end = meta.get("loop_end", 15)
    grid.loop_enabled = meta.get("loop_enabled", True)
    grid.view_offset_x = meta.get("view_offset_x", 0)

    if hasattr(tracker_interface, 'ids') and 'track_header' in tracker_interface.ids:
        header = tracker_interface.ids.track_header
        if header: header.track_count = grid.track_count

    reconstructed_data = []
    for row_dict in rows:
        tracks_str_keys = row_dict
        tracks_int_keys = {int(k): v for k, v in tracks_str_keys.items()}
        reconstructed_data.append({'tracks': tracks_int_keys})

    while len(reconstructed_data) < 256:
        reconstructed_data.append({'tracks': {}})

    grid.data = reconstructed_data
    grid.refresh_from_data()
    tracker_interface.current_filename = filename
    print(f"Loaded {filename} successfully.")


def get_next_session_filename(current_filename):
    save_dir = get_tracker_save_dir()
    if not os.path.exists(save_dir):
        return None

    files = sorted([f for f in os.listdir(save_dir) if f.endswith('.json')])

    if not files:
        return None

    if not current_filename or os.path.basename(current_filename) not in files:
        return os.path.join(save_dir, files[0])

    current_basename = os.path.basename(current_filename)
    try:
        curr_index = files.index(current_basename)
        next_index = (curr_index + 1) % len(files)
        return os.path.join(save_dir, files[next_index])
    except ValueError:
        return os.path.join(save_dir, files[0])

def load_session_data_raw(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data, filename
    except Exception as e:
        print(f"Error reading raw session {filename}: {e}")
        return None, None

def apply_loaded_data(tracker_interface, data, filename):
    grid = tracker_interface.tracker_grid
    meta = data.get("meta", {})
    rows = data.get("rows", [])
    tracker_interface.bpm = meta.get("bpm", 120)
    grid.track_count = meta.get("track_count", 4)
    grid.loop_start = meta.get("loop_start", 0)
    grid.loop_end = meta.get("loop_end", 15)
    grid.loop_enabled = meta.get("loop_enabled", True)
    grid.view_offset_x = meta.get("view_offset_x", 0)

    if hasattr(tracker_interface, 'ids') and 'track_header' in tracker_interface.ids:
        header = tracker_interface.ids.track_header
        if header: header.track_count = grid.track_count

    reconstructed_data = []
    for row_dict in rows:
        tracks_str_keys = row_dict
        tracks_int_keys = {int(k): v for k, v in tracks_str_keys.items()}
        reconstructed_data.append({'tracks': tracks_int_keys})

    while len(reconstructed_data) < 256:
        reconstructed_data.append({'tracks': {}})

    grid.data = reconstructed_data
    grid.refresh_from_data()

    tracker_interface.current_filename = filename
    print(f"Live Switched to {os.path.basename(filename)}")
