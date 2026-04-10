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
from kivy.utils import platform
rtmidi = None
AndroidMidi = None

if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("Tracker: Successfully imported AndroidMidi")
    except ImportError:
        print("Tracker: Could not import AndroidMidi")

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import rtmidi
        print("Tracker: Successfully imported WindowsMidi (aliased) and rtmidi")
    except ImportError:
        print("Tracker: Could not import windows_midi or rtmidi")

else:
    try:
        import rtmidi
        print("Tracker: Successfully imported rtmidi")
    except ImportError:
        print("Tracker: rtmidi not found.")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle

import miniapps.tracker_session_manager

try:
    from midimesh.main.control_panel.onscreen_minikeys import OnScreenKeyboards
except ImportError:
    print("Error: onscreen_keyboard.py not found. Please ensure it is in the same directory.")
    OnScreenKeyboards = None

CURRENT_TRACKER_INTERFACE = None

def get_tracker_interface():
    return CURRENT_TRACKER_INTERFACE

class MidiEngine:
    def __init__(self):
        self.midi_out = None
        self.active_notes = {}
        self.is_external_port = False

    def init_midi(self, external_port=None):
        if external_port:
            self.midi_out = external_port
            self.is_external_port = True
            print("Tracker: Using Main App MIDI Port (External/Shared)")
        elif platform in ('android', 'win') and AndroidMidi:
            print(f"Tracker: Initializing MIDI Out via wrapper ({platform})...")
            try:
                self.midi_out = AndroidMidi()
                if hasattr(self.midi_out, 'open_output'):
                    self.midi_out.open_output()
                if platform == 'win' and hasattr(self.midi_out, 'get_host_devices'):
                    devs = self.midi_out.get_host_devices()
                    if devs:
                        print(f"Tracker: Auto-connecting to: {devs[0][0]}")
                        self.midi_out.connect_to_device(devs[0][1])
                self.is_external_port = False
            except Exception as e:
                print(f"Tracker: MIDI Out wrapper error: {e}")
                self.midi_out = None
        elif rtmidi is not None:
            try:
                self.midi_out = rtmidi.MidiOut()
                available_ports = self.midi_out.get_ports()
                if available_ports:
                    self.midi_out.open_port(0)
                else:
                    self.midi_out.open_virtual_port("KivyTracker Out")
                self.is_external_port = False
                print("Tracker: Created Local MIDI Port (rtmidi)")
            except Exception as e:
                print(f"Tracker: rtmidi Init Error: {e}")
                self.midi_out = None
        else:
            print("Tracker: No MIDI backend available.")
            self.midi_out = None

    def close(self):
        if not self.is_external_port and self.midi_out and rtmidi:
            self.midi_out.close_port()
            self.midi_out = None

    def send_note_on(self, track_idx, channel, note, velocity):
        if not self.midi_out: return
        self.stop_active_note(track_idx, channel)
        status = 0x90 + (channel & 0x0F)
        try:
            self.midi_out.send_message([status, note, velocity])
        except Exception as e:
            print(f"Tracker MIDI Error: {e}")
        if track_idx not in self.active_notes:
            self.active_notes[track_idx] = {}
        self.active_notes[track_idx][channel] = note

    def send_note_off(self, channel, note):
        if not self.midi_out: return
        status = 0x80 + (channel & 0x0F)
        try:
            self.midi_out.send_message([status, note, 0])
        except Exception as e:
            print(f"Tracker MIDI Error: {e}")

    def stop_active_note(self, track_idx, channel):
        if track_idx in self.active_notes:
            if channel in self.active_notes[track_idx]:
                prev_note = self.active_notes[track_idx][channel]
                if prev_note is not None:
                    self.send_note_off(channel, prev_note)
                del self.active_notes[track_idx][channel]

midi_engine = MidiEngine()

#Keyboard for thee tracker enthusiasts
KEY_TO_NOTE = {
    'z': 60, 's': 61, 'x': 62, 'd': 63, 'c': 64, 'v': 65, 'g': 66, 'b': 67, 'h': 68, 'n': 69, 'j': 70, 'm': 71,
    ',': 72, 'l': 73, '.': 74, ';': 75, '/': 76,
    'q': 72, '2': 73, 'w': 74, '3': 75, 'e': 76, '4': 77, 'r': 78, '5': 79, 't': 80, '6': 81, 'y': 82, '7': 83, 'u': 84
}



class ClearConfirmationPopup(FloatLayout):
    callback = ObjectProperty(None)

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        return True

    def confirm(self):
        if self.callback:
            self.callback()
        self.dismiss()

    def dismiss(self):
        if self.parent:
            self.parent.remove_widget(self)

class TrackHeader(BoxLayout):
    track_count = NumericProperty(4)

    def on_track_count(self, instance, value):
        self.update_labels()

    def update_labels(self):
        interface = get_tracker_interface()
        if not interface or not interface.tracker_grid: return
        offset = interface.tracker_grid.view_offset_x
        for i in range(4):
            lbl = self.ids.get(f'h{i}')
            if not lbl: continue
            track_idx = offset + i
            if track_idx < self.track_count:
                lbl.text = f"TRK {track_idx + 1}"
                lbl.opacity = 1
            else:
                lbl.text = ""
                lbl.opacity = 0

class RowWidget(RecycleDataViewBehavior, BoxLayout):
    index = NumericProperty(0)
    is_current_line = BooleanProperty(False)
    is_loop_start = BooleanProperty(False)
    is_loop_end = BooleanProperty(False)
    is_focused_point = BooleanProperty(False)
    bg_color = ListProperty([0.1, 0.1, 0.1, 1])
    visible_tracks = NumericProperty(2)
    owner_grid = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        self.owner_grid = rv
        self.index = index
        self.ids.row_num.text = f"{index:02X}"
        self.visible_tracks = rv.track_count

        self.is_loop_start = (index == rv.loop_start) and rv.loop_enabled
        self.is_loop_end = (index == rv.loop_end) and rv.loop_enabled

        if rv.loop_focus == 'start' and self.is_loop_start:
            self.is_focused_point = True
        elif rv.loop_focus == 'end' and self.is_loop_end:
            self.is_focused_point = True
        else:
            self.is_focused_point = False

        self.is_current_line = (index == rv.current_playhead)
        if self.is_current_line:
            self.bg_color = [0.3, 0.3, 0.4, 1]
        elif index % 4 == 0:
            self.bg_color = [0.15, 0.15, 0.15, 1]
        else:
            self.bg_color = [0.1, 0.1, 0.1, 1]

        row_data = data.get('tracks', {})
        is_cursor_row = (index == rv.cursor_y)
        default_val = "--- 0 64"
        offset = rv.view_offset_x

        for ui_index in range(4):
            lbl = self.ids[f't{ui_index}']
            real_track_index = offset + ui_index

            if real_track_index < self.visible_tracks:
                lbl.opacity = 1
                raw_text = row_data.get(real_track_index, default_val)
                if is_cursor_row and real_track_index == rv.cursor_x:
                    lbl.is_cursor = True
                    parts = raw_text.split()
                    if len(parts) < 3: parts = ["---", "0", "64"]
                    note_str, ch_str, vel_str = parts[0], parts[1], parts[2]
                    if rv.granular_mode:
                        sub = rv.cursor_sub
                        if sub == 0:
                            lbl.text = f"[b][color=ffff00]{note_str}[/color][/b] {ch_str} {vel_str}"
                        elif sub == 1:
                            lbl.text = f"{note_str} [b][color=ffff00]{ch_str}[/color][/b] {vel_str}"
                        elif sub == 2:
                            lbl.text = f"{note_str} {ch_str} [b][color=ffff00]{vel_str}[/color][/b]"
                        else:
                            lbl.text = raw_text
                    else:
                        lbl.text = f"[b][color=ffff00]{raw_text}[/color][/b]"
                else:
                    lbl.is_cursor = False
                    lbl.text = raw_text
            else:
                lbl.opacity = 0
                lbl.is_cursor = False
                lbl.text = ""
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        rv = self.owner_grid
        if not rv:
            interface = get_tracker_interface()
            if interface: rv = interface.tracker_grid
        if not rv: return super().on_touch_down(touch)

        if self.ids.row_num.collide_point(*touch.pos):
            self.update_loop_logic(rv)
            return super().on_touch_down(touch)

        for ui_index in range(4):
            lbl = self.ids[f't{ui_index}']
            if lbl.collide_point(*touch.pos):
                real_track_index = rv.view_offset_x + ui_index
                if real_track_index < rv.track_count:
                    rv.cursor_x = real_track_index
                    rv.cursor_y = self.index
                    rv.set_edit_mode(False)
                    rv.update_selection_metrics()
                    if touch.is_double_tap:
                        self.handle_double_tap(rv)
                return super().on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and self.ids.row_num.collide_point(*touch.pos):
            interface = get_tracker_interface()
            if interface:
                rv = interface.tracker_grid
                if rv.loop_focus != 'none':
                    self.update_loop_logic(rv)
        return super().on_touch_move(touch)

    def update_loop_logic(self, rv):
        if rv.loop_focus == 'start':
            rv.loop_start = self.index
        elif rv.loop_focus == 'end':
            rv.loop_end = self.index
        elif self.is_loop_start:
            rv.set_loop_focus('start')
        elif self.is_loop_end:
            rv.set_loop_focus('end')
        rv.refresh_from_data()

    def handle_double_tap(self, rv):
        rv.delete_cell_content()


class TrackerGrid(RecycleView):
    current_playhead = NumericProperty(0)
    cursor_x = NumericProperty(0)
    cursor_y = NumericProperty(0)
    cursor_sub = NumericProperty(0)
    granular_mode = BooleanProperty(False)
    track_count = NumericProperty(4)
    loop_enabled = BooleanProperty(True)
    loop_start = NumericProperty(0)
    loop_end = NumericProperty(15)
    loop_focus = StringProperty('none')
    edit_mode = BooleanProperty(False)
    selected_velocity = NumericProperty(100)
    view_offset_x = NumericProperty(0)
    MAX_VISIBLE_COLS = 4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = [{'tracks': {}} for _ in range(256)]
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def toggle_granular_mode(self):
        self.granular_mode = not self.granular_mode
        self.refresh_from_data()

    def on_granular_mode(self, instance, value):
        interface = get_tracker_interface()
        if interface:
            interface.cursor_mode_text = "CURSOR: CELL" if value else "CURSOR: TRACK"

    def on_loop_enabled(self, instance, value):
        self.refresh_from_data()

    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        self.do_scroll_y = not enabled
        self.refresh_from_data()

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            if self.edit_mode: self.set_edit_mode(False)
            if self.loop_focus != 'none': self.clear_loop_focus()
            return True
        return False

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            if abs(touch.dx) > abs(touch.dy) and abs(touch.dx) > 10:
                if touch.dx > 0:
                    self.scroll_view_horizontal(-1)
                else:
                    self.scroll_view_horizontal(1)
                return True
        return super().on_touch_move(touch)

    def scroll_view_horizontal(self, direction):
        new_offset = self.view_offset_x + direction
        max_offset = max(0, self.track_count - self.MAX_VISIBLE_COLS)
        self.view_offset_x = max(0, min(max_offset, new_offset))
        self.refresh_from_data()
        interface = get_tracker_interface()
        if interface and interface.ids.track_header:
            interface.ids.track_header.update_labels()

    def set_loop_focus(self, focus_type):
        self.loop_focus = focus_type
        self.do_scroll_y = True
        self.refresh_from_data()

    def clear_loop_focus(self):
        self.loop_focus = 'none'
        self.do_scroll_y = True
        self.refresh_from_data()

    def update_track_count(self, count):
        self.track_count = count
        self.refresh_from_data()

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def get_current_cell_data(self):
        row = self.data[self.cursor_y]
        content = row['tracks'].get(self.cursor_x, "--- 0 64")
        parts = content.split()
        if len(parts) < 3: parts = ["---", "0", "64"]
        return parts

    def set_current_cell_data(self, note, ch, vel):
        row = self.data[self.cursor_y]
        row['tracks'][self.cursor_x] = f"{note} {ch} {vel}"
        self.refresh_from_data()
        self.update_selection_metrics()

    def delete_cell_content(self):
        row = self.data[self.cursor_y]
        if self.cursor_x in row['tracks']:
            del row['tracks'][self.cursor_x]
        self.refresh_from_data()
        self.update_selection_metrics()

    def clear_all_pattern(self):
        self.data = [{'tracks': {}} for _ in range(256)]
        self.refresh_from_data()
        self.update_selection_metrics()

    def insert_note_off(self):
        parts = self.get_current_cell_data()
        self.set_current_cell_data("OFF", parts[1], parts[2])
        self.advance_cursor()

    def advance_cursor(self):
        self.cursor_y = min(len(self.data) - 1, self.cursor_y + 1)
        self.scroll_to_cursor()

    def handle_input_from_keyboard(self, message_type, note, velocity):
        if message_type == 'note_on':
            note_name = ["C-", "C#", "D-", "D#", "E-", "F-", "F#", "G-", "G#", "A-", "A#", "B-"][note % 12]
            octave = (note // 12) - 1
            note_str = f"{note_name}{octave}"
            parts = self.get_current_cell_data()
            new_note = note_str
            new_ch = parts[1]
            new_vel = parts[2]
            self.set_current_cell_data(new_note, new_ch, new_vel)
            try:
                ch_int = int(new_ch, 16)
            except:
                ch_int = 0
            try:
                vel_int = int(new_vel, 16)
                vel_int = min(127, vel_int)
            except:
                vel_int = 100
            midi_engine.send_note_on(self.cursor_x, ch_int, note, vel_int)
            Clock.schedule_once(lambda dt: midi_engine.send_note_off(ch_int, note), 0.2)
            self.advance_cursor()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key == 'up':
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == 'down':
            self.cursor_y = min(len(self.data) - 1, self.cursor_y + 1)
        elif key == 'left':
            if self.granular_mode:
                if self.cursor_sub > 0:
                    self.cursor_sub -= 1
                else:
                    if self.cursor_x > 0:
                        self.move_cursor_x(-1)
                        self.cursor_sub = 2
            else:
                self.move_cursor_x(-1)
        elif key == 'right':
            if self.granular_mode:
                if self.cursor_sub < 2:
                    self.cursor_sub += 1
                else:
                    if self.cursor_x < self.track_count - 1:
                        self.move_cursor_x(1)
                        self.cursor_sub = 0
            else:
                self.move_cursor_x(1)
        elif key == 'delete':
            self.delete_cell_content()
        elif key == '0' or key == 'numpad0':
            if not self.granular_mode or self.cursor_sub == 0:
                self.insert_note_off()
                return True
            pass
        is_numeric_col = self.granular_mode and self.cursor_sub > 0
        is_hex_key = key in ['a', 'b', 'c', 'd', 'e', 'f']
        hex_map = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F'}
        if text and text.isdigit():
            hex_map[text] = text
        if is_numeric_col:
            parts = self.get_current_cell_data()
            if self.cursor_sub == 1:
                input_char = None
                if is_hex_key: input_char = hex_map[key]
                elif text and text.isdigit(): input_char = text
                if input_char:
                    self.set_current_cell_data(parts[0], input_char, parts[2])
                    return True
            elif self.cursor_sub == 2:
                input_char = None
                if is_hex_key: input_char = hex_map[key]
                elif text and text.isdigit(): input_char = text
                if input_char:
                    current_val = parts[2]
                    prev_char = current_val[-1] if len(current_val) > 0 else "0"
                    new_vel = (prev_char + input_char).upper()
                    self.set_current_cell_data(parts[0], parts[1], new_vel)
                    return True
        if key in KEY_TO_NOTE:
            if not self.granular_mode or self.cursor_sub == 0:
                self.handle_input_from_keyboard('note_on', KEY_TO_NOTE[key], 100)
        self.scroll_to_cursor()
        return True

    def move_cursor_x(self, direction):
        new_x = self.cursor_x + direction
        self.cursor_x = max(0, min(self.track_count - 1, new_x))
        if self.cursor_x < self.view_offset_x:
            self.view_offset_x = self.cursor_x
        elif self.cursor_x >= self.view_offset_x + self.MAX_VISIBLE_COLS:
            self.view_offset_x = self.cursor_x - self.MAX_VISIBLE_COLS + 1
        self.scroll_to_cursor()
        interface = get_tracker_interface()
        if interface and interface.ids.track_header:
            interface.ids.track_header.update_labels()

    def move_cursor_y(self, direction):
        new_y = self.cursor_y + direction
        self.cursor_y = max(0, min(len(self.data) - 1, new_y))
        self.scroll_to_cursor()

    def adjust_channel(self, delta):
        parts = self.get_current_cell_data()
        try:
            current_ch = int(parts[1], 16)
        except ValueError:
            current_ch = 0
        new_ch = max(0, min(15, current_ch + delta))
        self.set_current_cell_data(parts[0], f"{new_ch:X}", parts[2])

    def scroll_to_cursor(self):
        self.refresh_from_data()
        self.update_selection_metrics()

    def update_selection_metrics(self):
        parts = self.get_current_cell_data()
        try:
            vel_int = int(parts[2], 16)
            self.selected_velocity = vel_int
        except ValueError:
            self.selected_velocity = 100

    def set_velocity_from_slider(self, value):
        new_vel_int = int(value)
        if new_vel_int == self.selected_velocity: return
        parts = self.get_current_cell_data()
        new_vel_str = f"{new_vel_int:02X}"
        row = self.data[self.cursor_y]
        row['tracks'][self.cursor_x] = f"{parts[0]} {parts[1]} {new_vel_str}"
        self.refresh_from_data()
        self.selected_velocity = new_vel_int

    def scroll_to_index_centered(self, row_index):
        row_height = 50
        total_rows = len(self.data)
        total_content_height = total_rows * row_height
        viewport_height = self.height
        scrollable_distance = total_content_height - viewport_height
        if scrollable_distance <= 0:
            self.scroll_y = 1.0
            return
        target_center_from_top = (row_index * row_height) + (row_height / 2)
        target_viewport_top = target_center_from_top - (viewport_height / 2)
        if target_viewport_top < 0: target_viewport_top = 0
        new_scroll_y = 1.0 - (target_viewport_top / scrollable_distance)
        self.scroll_y = max(0.0, min(1.0, new_scroll_y))

class FitLayout(FloatLayout):
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
        if (abs(content.scale - scale) > epsilon or
            abs(content.pos[0] - new_pos_x) > epsilon or
            abs(content.pos[1] - new_pos_y) > epsilon):
            content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

class LoadButton(Button):
    long_press_time = NumericProperty(0.5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._clock_event = None
        self._is_long_press = False

    def on_state(self, instance, value):
        if value == 'down':
            self._is_long_press = False
            self._clock_event = Clock.schedule_once(self._trigger_long_press, self.long_press_time)
        elif value == 'normal':
            if self._clock_event:
                self._clock_event.cancel()
                self._clock_event = None
            interface = get_tracker_interface()
            if self._is_long_press:
                if interface: interface.trigger_armed_load()
                self.text = "LOAD"
                self.background_color = [1, 1, 1, 1]
            else:
                if interface: interface.open_load_popup()

    def _trigger_long_press(self, dt):
        self._is_long_press = True
        self._clock_event = None
        self.text = "ARMED"
        self.background_color = [1, 0.5, 0, 1]

        interface = get_tracker_interface()
        if interface:
            interface.load_armed = True
            interface.arm_next_session()

class TrackerInterface(FloatLayout):
    is_playing = BooleanProperty(False)
    bpm = NumericProperty(125)
    current_line = NumericProperty(0)
    cursor_mode_text = StringProperty("CURSOR: TRACK")
    current_filename = StringProperty(None, allownone=True)
    armed_session_data = ObjectProperty(None, allownone=True)
    armed_filename = StringProperty(None, allownone=True)
    pending_load_switch = BooleanProperty(False)
    pending_load_switch = BooleanProperty(False)
    _prev_line = NumericProperty(-1)
    tracker_grid = ObjectProperty(None)
    app_switcher = ObjectProperty(None)
    load_armed = BooleanProperty(False)

    def on_parent(self, instance, value):
        global CURRENT_TRACKER_INTERFACE
        if value:
            CURRENT_TRACKER_INTERFACE = self
            if self.ids.track_header:
                self.ids.track_header.update_labels()

    def __init__(self, app_switcher=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        global CURRENT_TRACKER_INTERFACE
        CURRENT_TRACKER_INTERFACE = self

    def on_kv_post(self, base_widget):
        self.tracker_grid = self.ids.tracker_grid
        if OnScreenKeyboards:
            kb = OnScreenKeyboards(midi_callback=self.on_keyboard_midi)
            self.ids.keyboard_container.add_widget(kb)

    def on_keyboard_midi(self, msg_type, note, vel):
        if self.tracker_grid:
            self.tracker_grid.handle_input_from_keyboard(msg_type, note, vel)

    def on_bpm(self, instance, value):
        if self.is_playing:
            if hasattr(self, 'playback_event'):
                self.playback_event.cancel()
            tick_time = 60.0 / (value * 4)
            self.playback_event = Clock.schedule_interval(self.advance_step, tick_time)

    def toggle_playback(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            tick_time = 60.0 / (self.bpm * 4)
            self.playback_event = Clock.schedule_interval(self.advance_step, tick_time)
        else:
            if hasattr(self, 'playback_event'):
                self.playback_event.cancel()
            for track in midi_engine.active_notes:
                for ch in midi_engine.active_notes[track]:
                    note = midi_engine.active_notes[track][ch]
                    midi_engine.send_note_off(ch, note)
            midi_engine.active_notes.clear()

    def stop_playback(self):
        self.is_playing = False
        if hasattr(self, 'playback_event'):
            self.playback_event.cancel()
        for track in midi_engine.active_notes:
            for ch in midi_engine.active_notes[track]:
                note = midi_engine.active_notes[track][ch]
                midi_engine.send_note_off(ch, note)
        midi_engine.active_notes.clear()
        grid = self.tracker_grid
        if grid and grid.loop_start > 0:
            self.current_line = grid.loop_start
        else:
            self.current_line = 0
        if self.tracker_grid:
            self.tracker_grid.current_playhead = self.current_line
            self.tracker_grid.cursor_y = self.current_line
            self.tracker_grid.cursor_x = 0
            self.tracker_grid.view_offset_x = 0
            self.tracker_grid.scroll_to_cursor()
            self.tracker_grid.refresh_from_data()
            if self.ids.track_header:
                self.ids.track_header.update_labels()



    def _maybe_trigger_armed_load(self):
        if not self.load_armed:
            return
        grid = self.tracker_grid
        if not grid:
            return
        target_line = grid.loop_start if grid.loop_enabled else grid.loop_end
        if self.current_line == target_line and self._prev_line != target_line:
            self._execute_armed_load()


    def _execute_armed_load(self):
        self.load_armed = False
        self.pending_load_switch = True


    def add_track(self):
        if self.tracker_grid and self.tracker_grid.track_count < 8:
            new_count = self.tracker_grid.track_count + 1
            self.tracker_grid.update_track_count(new_count)
            self.ids.track_header.track_count = new_count

    def arm_next_session(self):
        next_file = miniapps.tracker_session_manager.get_next_session_filename(self.current_filename)
        if next_file:
            data, filename = miniapps.tracker_session_manager.load_session_data_raw(next_file)
            if data:
                self.armed_session_data = data
                self.armed_filename = filename
                print(f"Session Armed: {os.path.basename(filename)}")

    def trigger_armed_load(self):
        if self.armed_session_data:
            self.pending_load_switch = True
            print("Switch queued for next step.")

    def open_clear_popup(self):
        def do_clear():
            if self.tracker_grid:
                self.tracker_grid.clear_all_pattern()

        popup = ClearConfirmationPopup()
        popup.callback = do_clear
        self.add_widget(popup)

    def advance_step(self, dt):
        self._prev_line = self.current_line

        if self.pending_load_switch and self.armed_session_data:
            for track in midi_engine.active_notes:
                for ch in midi_engine.active_notes[track]:
                    note = midi_engine.active_notes[track][ch]
                    midi_engine.send_note_off(ch, note)
            midi_engine.active_notes.clear()
            miniapps.tracker_session_manager.apply_loaded_data(self, self.armed_session_data, self.armed_filename)
            self.pending_load_switch = False
            try:
                self.armed_session_data = None
                self.armed_filename = None
            except Exception as e:
                print(f"Warning clearing armed data: {e}")
            if self.tracker_grid:
                self.current_line = self.tracker_grid.loop_start
            else:
                self.current_line = 0

        grid = self.tracker_grid
        if not grid: return

        row_data = grid.data[self.current_line]['tracks']
        for track_idx, cell_content in row_data.items():
            parts = cell_content.split()
            if len(parts) >= 3:
                note_str = parts[0]
                ch_str = parts[1]
                vel_str = parts[2]
                try:
                    channel = int(ch_str, 16)
                    velocity = int(vel_str, 16)
                    velocity = min(127, max(0, velocity))
                except ValueError:
                    channel = 0
                    velocity = 100
                if note_str == "OFF":
                    midi_engine.stop_active_note(track_idx, channel)
                elif note_str != "---":
                    try:
                        note_name = note_str[:2]
                        octave = int(note_str[-1])
                        names = ["C-", "C#", "D-", "D#", "E-", "F-", "F#", "G-", "G#", "A-", "A#", "B-"]
                        if note_name in names:
                            semi = names.index(note_name)
                            midi_note = (octave + 1) * 12 + semi
                            midi_engine.send_note_on(track_idx, channel, midi_note, velocity)
                    except:
                        pass
        grid.current_playhead = self.current_line
        grid.scroll_to_index_centered(self.current_line)
        grid.refresh_from_data()
        self.current_line += 1
        if grid.loop_enabled and self.current_line > grid.loop_end:
            self.current_line = grid.loop_start
        if self.current_line >= len(grid.data):
             self.current_line = 0

        self._maybe_trigger_armed_load()

    def save_session(self):
        miniapps.tracker_session_manager.save_tracker_session(self)

    def open_load_popup(self):
        miniapps.tracker_session_manager.TrackerLoadPopup(tracker_app=self).open()

    def go_back(self):
        self.stop_playback()
        if self.app_switcher:
            self.app_switcher('goodies_menu')

class TrackerRoot(FitLayout):
    def __init__(self, app_switcher=None, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        midi_engine.init_midi(main_midi_out)
        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(1920, 1080),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False,
        )
        self.content_ui = TrackerInterface(app_switcher=app_switcher)
        self.scatter.add_widget(self.content_ui)
        self.add_widget(self.scatter)

    def cleanup_app(self):
        if self.content_ui:
            self.content_ui.stop_playback()
        global CURRENT_TRACKER_INTERFACE
        CURRENT_TRACKER_INTERFACE = None
        midi_engine.close()

KV = """
<TrackCell@Label>:
    font_name: "RobotoMono-Regular"
    font_size: '30px'
    color: 0, 1, 0, 1
    markup: True
    is_cursor: False
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.2, 0.5
        Line:
            width: 1
            points: [self.x, self.y, self.x, self.top]
        Color:
            rgba: (0.2, 0.6, 1, 0.4) if self.is_cursor else (0, 0, 0, 0)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: (0.4, 0.8, 1, 1) if self.is_cursor else (0, 0, 0, 0)
        Line:
            width: 2
            rectangle: (self.x, self.y, self.width, self.height)

<ClearConfirmationPopup>:
    size_hint: 1, 1

    # Background Dimmer (Semi-transparent black)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.8
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        size_hint: None, None
        size: 1920, 1080
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        padding: 50
        spacing: 40

        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
                source: 'assets/panel_square_01.png'

        Widget:
            size_hint_y: 0.2

        Label:
            text: "CLEAR PATTERN?"
            font_size: '50px'
            font_name: "RobotoMono-Regular"
            size_hint_y: None
            height: 60
            color: 1, 1, 1, 1

        Label:
            text: "Are you sure?"
            font_size: '30px'
            font_name: "RobotoMono-Regular"
            size_hint_y: None
            height: 40
            color: 0.8, 0.8, 0.8, 1

        Widget:
            size_hint_y: 0.1

        BoxLayout:
            orientation: 'horizontal'
            spacing: 50
            size_hint_y: None
            size_hint_x: 0.5
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            height: 100

            Button:
                text: "YES"
                font_size: '30px'
                background_normal: 'assets/flat_button_green.png'
                background_down: 'assets/flat_button_green_pressed.png'
                on_release: root.confirm()

            Button:
                text: "NO"
                font_size: '30px'
                background_normal: 'assets/flat_button_red.png'
                background_down: 'assets/flat_button_red_pressed.png'
                on_release: root.dismiss()

        Widget:
            size_hint_y: 0.2

<RowWidget>:
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            size: self.size
            pos: self.pos
    Label:
        id: row_num
        text: "00"
        font_size: '30px'
        size_hint_x: None
        width: 60
        color: (0, 0, 0, 1) if (root.is_loop_start or root.is_loop_end) else (0.5, 0.5, 0.5, 1)
        font_name: "RobotoMono-Regular"
        canvas.before:
            Color:
                rgba: (0, 1, 1, 1) if root.is_loop_start else (0, 0, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: (1, 0, 1, 1) if root.is_loop_end else (0, 0, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: (1, 1, 1, 1) if root.is_focused_point else (0, 0, 0, 0)
            Line:
                width: 2
                rectangle: (self.x, self.y, self.width, self.height)
    TrackCell:
        id: t0
    TrackCell:
        id: t1
    TrackCell:
        id: t2
    TrackCell:
        id: t3

<TrackHeader>:
    size_hint_y: None
    height: 50
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.05, 1
        Rectangle:
            size: self.size
            pos: self.pos
    Label:
        text: "#"
        font_size: '30px'
        size_hint_x: None
        width: 60
    Label:
        id: h0
        text: "TRK 1"
        font_size: '30px'
    Label:
        id: h1
        text: "TRK 2"
        font_size: '30px'
    Label:
        id: h2
        text: "TRK 3"
        font_size: '30px'
    Label:
        id: h3
        text: "TRK 4"
        font_size: '30px'

<TrackerInterface>:
    size_hint: None, None
    size: 1920, 1080
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'assets/tracker_bg.png'

    BoxLayout:
        orientation: 'horizontal'
        padding: 20
        spacing: 20
        size: root.size

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.5
            spacing: 10

            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 0.65
                padding: 10
                spacing: 5

                GridLayout:
                    cols: 5
                    size_hint_y: None
                    height: 100
                    spacing: 5
                    Button:
                        text: "PAUSE" if root.is_playing else "PLAY"
                        font_size: '30px'
                        on_release: root.toggle_playback()
                        background_normal: 'assets/flat_button_green.png'
                        background_down: 'assets/flat_button_green_pressed.png'
                        background_color: (0.2, 0.8, 0.2, 1) if root.is_playing else (1, 1, 1, 1)
                    Button:
                        text: "STOP"
                        font_size: '30px'
                        on_release: root.stop_playback()
                        background_normal: 'assets/flat_button_red.png'
                        background_down: 'assets/flat_button_red_pressed.png'
                        background_color:  1, 1, 1, 1
                    Button:
                        text: "+ TRK"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        on_release: root.add_track()
                        disabled: (root.tracker_grid.track_count >= 8) if root.tracker_grid else True
                    Button:
                        text: "BACK"
                        font_size: '30px'
                        size_hint_x: None
                        width: 140
                        background_normal: 'assets/flat_button_red.png'
                        background_down: 'assets/flat_button_red_pressed.png'
                        background_color: (1, 1, 1, 1)
                        on_release: root.go_back()

                Widget:
                    size_hint_y: None
                    height: 5

                GridLayout:
                    cols: 4
                    size_hint_y: None
                    height: 200
                    spacing: 5
                    Button:
                        text: "SAVE"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        on_release: root.save_session()
                    ToggleButton:
                        text: "LOOP"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        background_color: (1, 1, 1, 1)
                        state: 'down' if (root.tracker_grid and root.tracker_grid.loop_enabled) else 'normal'
                        on_release: if root.tracker_grid: root.tracker_grid.loop_enabled = (self.state == 'down')
                    Button:
                        text: "UP"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        background_color: (0.8, 0.5, 0.5, 1)
                        on_release: root.tracker_grid.move_cursor_y(-1)
                    ToggleButton:
                        text: 'CURSOR'
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        on_release: root.tracker_grid.toggle_granular_mode()
                    LoadButton:
                        text: "LOAD"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                    Button:
                        text: "LEFT"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        background_color: (0.8, 0.5, 0.5, 1)
                        on_release: root.tracker_grid.move_cursor_x(-1)
                    Button:
                        text: "DOWN"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        background_color: (0.8, 0.5, 0.5, 1)
                        on_release: root.tracker_grid.move_cursor_y(1)
                    Button:
                        text: "RIGHT"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        background_color: (0.8, 0.5, 0.5, 1)
                        on_release: root.tracker_grid.move_cursor_x(1)

                Widget:
                    size_hint_y: None
                    height: 5

                GridLayout:
                    cols: 4
                    size_hint_y: None
                    height: 100
                    spacing: 10
                    Button:
                        text: "DELETE"
                        font_size: '30px'
                        background_color: 1, 1, 1, 1
                        on_release: root.tracker_grid.delete_cell_content()
                        background_normal: 'assets/flat_button_red.png'
                        background_down: 'assets/flat_button_red_pressed.png'
                    Button:
                        text: "CLEAR"
                        font_size: '30px'
                        background_color: 1, 1, 1, 1
                        on_release: root.open_clear_popup()
                        background_normal: 'assets/flat_button_red.png'
                        background_down: 'assets/flat_button_red_pressed.png'
                    Button:
                        text: "OFF"
                        font_size: '30px'
                        background_normal: 'assets/flat_button_grey.png'
                        background_down: 'assets/flat_button_grey_pressed.png'
                        on_release: root.tracker_grid.insert_note_off()
                    BoxLayout:
                        orientation: 'vertical'
                        Label:
                            text: "MIDI CH"
                            font_size: '30px'
                            size_hint_y: None
                            height: 50
                        GridLayout:
                            cols: 2
                            spacing: 5
                            Button:
                                text: "-"
                                font_size: '30px'
                                on_release: root.tracker_grid.adjust_channel(-1)
                                background_normal: 'assets/flat_button_red.png'
                                background_down: 'assets/flat_button_red_pressed.png'
                            Button:
                                text: "+"
                                font_size: '30px'
                                on_release: root.tracker_grid.adjust_channel(1)
                                background_normal: 'assets/flat_button_red.png'
                                background_down: 'assets/flat_button_red_pressed.png'

                Widget:
                    size_hint_y: None
                    height: 40

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_x: 1
                    height: 100
                    spacing: 20
                    Label:
                        text: "VEL:"
                        font_size: '30px'
                        size_hint_x: 0.2
                        height: 20
                        font_name: "RobotoMono-Regular"
                        padding: [60, 0, 0, 0]
                    Slider:
                        min: 0
                        max: 127
                        step: 1
                        size_hint_x: 0.8
                        background_horizontal: 'assets/single_slider_bg.png'
                        border_horizontal: (0, 0, 0, 0)
                        background_width: 40
                        orientation: 'horizontal'
                        value_track_color: (0, 0, 0, 0)
                        cursor_image: 'assets/node_mini_app.png'
                        cursor_size: (100, 100)
                        value: root.tracker_grid.selected_velocity if root.tracker_grid else 100
                        on_value: if root.tracker_grid: root.tracker_grid.set_velocity_from_slider(self.value)
                        padding: 60

                Widget:
                    size_hint_y: None
                    height: 40

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_x: 1
                    height: 100
                    spacing: 20
                    Label:
                        text: f"BPM: {int(root.bpm)}"
                        font_size: '30px'
                        size_hint_x: 0.2
                        height: 20
                        font_name: "RobotoMono-Regular"
                        padding: [60, 0, 0, 0]
                    Slider:
                        min: 40
                        max: 200
                        step: 1
                        size_hint_x: 0.8
                        background_horizontal: 'assets/single_slider_bg.png'
                        border_horizontal: (0, 0, 0, 0)
                        background_width: 40
                        orientation: 'horizontal'
                        value_track_color: (0, 0, 0, 0)
                        cursor_image: 'assets/node_mini_app.png'
                        cursor_size: (100, 100)
                        value: root.bpm
                        on_value: root.bpm = self.value
                        padding: 60

                Widget:
                    size_hint_y: None
                    height: 10

            AnchorLayout:
                id: keyboard_container
                anchor_x: 'center'
                anchor_y: 'bottom'
                size_hint_y: 0.3
                padding: [0, 20, 0, 0]

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.5
            canvas.before:
                Color:
                    rgba: 0.05, 0.05, 0.05, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            TrackHeader:
                id: track_header
            TrackerGrid:
                id: tracker_grid
                viewclass: 'RowWidget'
                RecycleBoxLayout:
                    default_size: None, 50
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
                    orientation: 'vertical'
"""

Builder.load_string(KV)
