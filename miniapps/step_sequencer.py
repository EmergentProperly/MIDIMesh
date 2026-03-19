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

import os
from pathlib import Path
import json
import time
import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.clock import Clock
from kivy.utils import platform
from kivy.animation import Animation

VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_ROOT))

from midimesh.main.control_panel.onscreen_keyboard import OnScreenKeyboard

from misc.grid import Grid

rtmidi = None
AndroidMidi = None

if platform == 'android':
    try:
        from midimesh.main.android_midi import AndroidMidi
        print("Successfully imported AndroidMidi")
    except ImportError:
        print("Could not import AndroidMidi")

elif platform == 'win':
    try:
        from midimesh.main.windows_midi import WindowsMidi as AndroidMidi
        import rtmidi
        print("Successfully imported WindowsMidi (aliased) and rtmidi")
    except ImportError:
        print("Could not import windows_midi or rtmidi")
else:
    try:
        import rtmidi
        print("Successfully imported rtmidi")
    except ImportError:
        print("Could not import rtmidi")

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



def get_sequencer_save_dir():
    save_dir = ""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            app_storage_path = context.getExternalFilesDir(None).getAbsolutePath()
            save_dir = os.path.join(app_storage_path, "saves", "sequencer")
        except Exception as e:
            print(f"Android storage error: {e}")
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves", "sequencer")
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(root_dir, "../saves", "sequencer")

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except Exception as e:
            print(f"Error creating sequencer save directory {save_dir}: {e}")

    return save_dir

class SequencerScreenshotImage(Image):
    load_state = StringProperty('normal')

    def __init__(self, popup, json_path, png_path, **kwargs):
        super().__init__(**kwargs)
        self.popup = popup
        self.json_path = json_path
        self.png_path = png_path
        self._long_press_event = None
        self._flash_event = None
        self.bind(load_state=self.on_load_state_change, pos=self.on_load_state_change, size=self.on_load_state_change)

    def on_load_state_change(self, *args):
        self.canvas.after.clear()
        if self._flash_event:
            self._flash_event.cancel()
            self._flash_event = None

        if self.load_state == 'armed_load':
            with self.canvas.after:
                Color(0.2, 0.8, 0.2, 1)
                Line(rectangle=(self.x + 2, self.y + 2, self.width - 4, self.height - 4), width=3)
        elif self.load_state == 'armed_delete':
            def flash_border(dt):
                is_on = int(time.time() * 5) % 2 == 0
                self.canvas.after.clear()
                if is_on:
                    with self.canvas.after:
                        Color(0.8, 0.0, 0.0, 1)
                        Line(rectangle=(self.x + 2, self.y + 2, self.width - 4, self.height - 4), width=3)
            self._flash_event = Clock.schedule_interval(flash_border, 0.1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._long_press_event = Clock.schedule_once(self._do_long_press, 0.6)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            if self.collide_point(*touch.pos):
                self.popup.handle_tap(self)
            return True
        return super().on_touch_up(touch)

    def _do_long_press(self, dt):
        self._long_press_event = None
        self.popup.handle_long_press(self)

class SequencerLoadPopup(Popup):
    def __init__(self, sequencer, **kwargs):
        super().__init__(**kwargs)
        self.sequencer = sequencer
        self.title = 'LOAD SEQUENCE'
        self.title_size = '20sp'
        self.title_font = "assets/DSEG7Modern-Regular.ttf"
        self.size_hint = (0.85, 0.85)
        self.background_color = (0.1, 0.1, 0.1, 0.95)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.grid = GridLayout(cols=2, spacing=20, size_hint_y=None, padding=20)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.content = self.scroll

        self.armed_image = None
        self.populate_grid()

    def populate_grid(self):
        self.grid.clear_widgets()
        save_dir = get_sequencer_save_dir()
        if not os.path.exists(save_dir): return
        saves = sorted([f for f in os.listdir(save_dir) if f.endswith('.json')], reverse=True)

        for json_file in saves:
            base_name = json_file[:-5]
            png_path = os.path.join(save_dir, f"{base_name}.png")
            json_path = os.path.join(save_dir, json_file)

            if os.path.exists(png_path):
                img = SequencerScreenshotImage(
                    popup=self,
                    json_path=json_path,
                    png_path=png_path,
                    source=png_path,
                    size_hint_y=None,
                    keep_ratio=True,
                    allow_stretch=True
                )
                img.bind(width=lambda inst, w: setattr(inst, 'height', w * 0.56))
                self.grid.add_widget(img)

    def handle_tap(self, img_widget):
        if self.armed_image != img_widget:
            if self.armed_image: self.armed_image.load_state = 'normal'
            self.armed_image = img_widget
            img_widget.load_state = 'armed_load'
        else:
            if img_widget.load_state == 'armed_load':
                self.sequencer.load_session(img_widget.json_path)
                self.dismiss()
            elif img_widget.load_state == 'armed_delete':
                try:
                    os.remove(img_widget.json_path)
                    os.remove(img_widget.png_path)
                except Exception as e:
                    print(f"Delete failed: {e}")
                self.armed_image = None
                self.populate_grid()

    def handle_long_press(self, img_widget):
        if self.armed_image and self.armed_image != img_widget:
            self.armed_image.load_state = 'normal'
        self.armed_image = img_widget
        img_widget.load_state = 'armed_delete'

class StepNode(Widget):
    active = BooleanProperty(False)
    is_playhead = BooleanProperty(False)
    is_enabled = BooleanProperty(True)
    sequencer = ObjectProperty(None)
    cancel_interaction = BooleanProperty(False)
    inactive_src = StringProperty("assets/seq_flat_button_grey.png")
    active_src   = StringProperty("assets/seq_flat_button_red.png")
    disabled_src = StringProperty("assets/seq_flat_button_grey_pressed.png")
    playhead_empty_src = StringProperty("assets/seq_playhead_grey.png")
    playhead_occupied_src = StringProperty("assets/seq_playhead_red.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (120, 120)
        self.img = Image(source=self.inactive_src, size=self.size, pos=self.pos)
        self.add_widget(self.img)
        self.bind(pos=self._update_visuals, size=self._update_visuals)
        self.bind(active=self.update_node_visual)
        self.bind(is_enabled=self.update_node_visual)
        self.bind(is_playhead=self.update_playhead_visual)
        self.update_node_visual()

    def _update_visuals(self, *_):
        self.img.pos = self.pos
        self.img.size = self.size
        self.update_playhead_visual()
        self.update_node_visual()

    def update_node_visual(self, *args):
        if not self.is_enabled:
            self.img.source = self.disabled_src
        elif self.active:
            self.img.source = self.active_src
        else:
            self.img.source = self.inactive_src
        if self.is_playhead:
            self.update_playhead_visual()

    def update_playhead_visual(self, *args):
        self.canvas.after.clear()
        if self.is_playhead:
            with self.canvas.after:
                Color(1, 1, 1, 1)
                source_img = self.playhead_occupied_src if self.active else self.playhead_empty_src
                Rectangle(source=source_img, pos=self.pos, size=self.size)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.cancel_interaction = False
            if self.sequencer:
                self.sequencer.handle_step_touch_down(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if self.sequencer:
                self.sequencer.handle_step_touch_up(self)
            return True
        return super().on_touch_up(touch)


class ImgButton(Widget):
    normal_src = StringProperty("")
    pressed_src = StringProperty("")
    text = StringProperty("")
    callback = ObjectProperty(None)
    long_press_callback = ObjectProperty(None)
    release_callback = ObjectProperty(None)

    allow_release_reset = BooleanProperty(True)
    long_press_time = 0.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (120, 120)
        self.img = Image(source=self.normal_src, size=self.size, pos=self.pos)
        self.add_widget(self.img)
        self.label = Label(
            text=self.text,
            font_size=26,
            bold=True,
            color=(1, 1, 1, 0.7),
            center=self.center
        )

        self.add_widget(self.label)
        self.bind(pos=self._sync_widgets, size=self._sync_widgets, text=self._update_text)
        self._long_press_schedule = None
        self._is_long_press = False

    def _sync_widgets(self, *_):
        self.img.pos = self.pos
        self.img.size = self.size
        self.label.center = self.center

    def _update_text(self, *args):
        self.label.text = self.text

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.img.source = self.pressed_src
            self._is_long_press = False
            self._long_press_schedule = Clock.schedule_once(self._trigger_long_press, self.long_press_time)
            return True
        return super().on_touch_down(touch)

    def _trigger_long_press(self, dt):
        self._is_long_press = True
        if callable(self.long_press_callback):
            self.long_press_callback()

    def on_touch_up(self, touch):
        if self._long_press_schedule:
            self._long_press_schedule.cancel()
            self._long_press_schedule = None

            if self.collide_point(*touch.pos):
                if self._is_long_press:
                    if callable(self.release_callback):
                        self.release_callback()
                else:
                    if callable(self.callback):
                        self.callback()

                if self.allow_release_reset:
                    self.img.source = self.normal_src
            else:
                if self.allow_release_reset:
                    self.img.source = self.normal_src
            return True
        return super().on_touch_up(touch)

class SequencerContent(FloatLayout):
    def __init__(self, app_switcher=None, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.main_midi_out = main_midi_out
        self.midi_in = None
        self.midi_out = None
        self.is_playing = False
        self.shuffle_percent = 0
        self._last_extra_delay = 0.0
        self._min_interval = 0.001
        self.playback_event = None
        self.pages_data = [[None] * 128 for _ in range(16)]
        self.page_channels = [i for i in range(16)]
        self.current_page_index = 0
        self.current_step = 0
        self.pattern_length = 128
        self.selected_midi_channel = 1
        self.current_save_filename = None
        self.pending_load_data = None
        self.arm_quantized_load = False
        self.held_steps = set()
        self.clipboard_data = None
        self.clipboard_type = None
        self._ctrl_copy_start = None
        self._ctrl_is_down   = False
        self._active_note_start = {}
        self._awaiting_paste = False

        Window.bind(on_key_down=self._on_key_down,
            on_key_up=self._on_key_up)

        if Grid:
            self.bg_grid = Grid(size_hint=(1, 1))
            self.add_widget(self.bg_grid)

        self.panel_bg = Image(
            source="assets/panel_rect_01.png",
            size_hint=(None, None),
            size=(1760, 1080),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=False
        )

        self.add_widget(self.panel_bg)
        self.grid = GridLayout(
            cols=16, rows=8, spacing=0,
            size_hint=(0.646, 0.575), pos=(135,410)
        )

        self.nodes = []
        for _ in range(8 * 16):
            node = StepNode(sequencer=self)
            self.nodes.append(node)
            self.grid.add_widget(node)

        self.nodes[self.current_step].is_playhead = True
        self.add_widget(self.grid)

        self.page_button_layout = GridLayout(
            cols=4, spacing=2, size_hint=(None, None),
            size=(335, 335), pos=(135, 40)
        )

        self.page_buttons = []
        for i in range(16):
            btn = ImgButton(
                normal_src="assets/node-disabled.png",
                pressed_src="assets/node-flipped.png",
                size_hint=(1,1),
                allow_release_reset=False
            )
            btn.callback = lambda i=i: self.select_page(i)
            self.page_buttons.append(btn)
            self.page_button_layout.add_widget(btn)

        self.add_widget(self.page_button_layout)
        self.page_buttons[0].img.source = "assets/node-flipped.png"

        self.play_btn = ImgButton(
            normal_src="assets/flat_button_green.png",
            pressed_src="assets/flat_button_green_pressed.png",
            text="PLAY",
            size_hint=(None, None), size=(100,100), pos=(1380, 922),
            allow_release_reset=False
        )
        self.play_btn.callback = self.on_play_pressed
        self.add_widget(self.play_btn)

        self.stop_btn = ImgButton(
            normal_src="assets/flat_button_red.png",
            pressed_src="assets/flat_button_red_pressed.png",
            text="STOP",
            size_hint=(None, None), size=(100,100), pos=(1380, 818),
        )
        self.stop_btn.callback = self.on_stop_pressed
        self.add_widget(self.stop_btn)

        self.next_btn = ImgButton(
            normal_src="assets/flat_button_grey.png",
            pressed_src="assets/flat_button_grey_pressed.png",
            text="NEXT",
            size_hint=(None, None), size=(100,100), pos=(1380, 714),
        )
        self.next_btn.callback = self.advance_playhead
        self.add_widget(self.next_btn)

        self.del_btn = ImgButton(
            normal_src="assets/flat_button_red.png",
            pressed_src="assets/flat_button_red_pressed.png",
            text="DEL",
            size_hint=(None, None), size=(100,100), pos=(1380, 610),
        )
        self.del_btn.callback = self.on_delete_pressed
        self.add_widget(self.del_btn)

        self.save_btn = ImgButton(
            normal_src="assets/flat_button_grey.png",
            pressed_src="assets/flat_button_grey_pressed.png",
            text="SAVE",
            size_hint=(None, None), size=(100,100), pos=(1380, 506),
        )
        self.save_btn.callback = self.save_session_action
        self.add_widget(self.save_btn)

        self.load_btn = ImgButton(
            normal_src="assets/flat_button_grey.png",
            pressed_src="assets/flat_button_grey_pressed.png",
            text="LOAD",
            size_hint=(None, None), size=(100,100), pos=(1380, 402),
        )
        self.load_btn.callback = self.open_load_popup
        self.load_btn.long_press_callback = self.prepare_next_sequence
        self.load_btn.release_callback = self.arm_sequence_switch
        self.add_widget(self.load_btn)

        self.main_app_btn = ImgButton(
            normal_src="assets/flat_button_red.png",
            pressed_src="assets/flat_button_red_pressed.png",
            text="BACK",
            size_hint=(None, None), size=(120,120), pos=(1680, 20),
            allow_release_reset=True
        )
        self.main_app_btn.callback = self.go_to_menu
        self.add_widget(self.main_app_btn)

        self.keyboard = OnScreenKeyboard(midi_callback=self.handle_midi)
        self.keyboard.size_hint = (None, None)
        self.keyboard.width = 840
        self.keyboard.height = 335
        self.keyboard.pos = (510, 40)
        self.add_widget(self.keyboard)

        self.midi_selector_layout = BoxLayout(
            orientation='vertical', spacing=10, size_hint=(None, None),
            size=(80, 200), pos=(1389, 27))
        self.channel_label = Label(
            text=f"{self.page_channels[0] + 1:02d}",
            font_name="assets/DSEG7Modern-Regular.ttf",
            font_size=46, halign='right', color=(1, 0, 0, 1),
            size_hint=(None, None), size=(100, 80), padding=(20,0,0,0)
        )
        self.channel_btn = ImgButton(
            normal_src="assets/din-miniapp-01.png",
            pressed_src="assets/din-miniapp-02.png",
            size_hint=(None, None), size=(80, 80)
        )
        self.channel_btn.callback = self.cycle_midi_channel
        self.midi_selector_layout.add_widget(self.channel_label)
        self.midi_selector_layout.add_widget(self.channel_btn)
        self.add_widget(self.midi_selector_layout)

        self.slider_layout = BoxLayout(
            orientation='horizontal', spacing=10, size_hint=(None, 0.765),
            width=300, pos=(1515,200)
        )


        self.shuffle_box = BoxLayout(orientation='vertical', size_hint_x=1)

        self.shuffle_label = Label(
            text="000", font_name="assets/DSEG7Modern-Regular.ttf",
            font_size=24, color=(1, 0, 0, 1), size_hint_y=None, halign='right',
            valign='middle', height=80, padding=(10, 0, 18, 0)
        )

        self.shuffle_slider = Slider(
            orientation='vertical', min=0, max=99, value=0, step=1, size_hint_y=1,
            background_vertical='assets/single_slider_bg_vertical.png',
            border_vertical=(0, 0, 0, 0), background_width=40, value_track_color=(0, 0, 0, 0),
            cursor_image='assets/node_mini_app.png', cursor_size=(80, 80), padding=80
        )

        self.shuffle_slider.bind(
            value=lambda inst, val: setattr(self.shuffle_label, 'text', f"0{int(val):02d}")
        )

        self.shuffle_slider.bind(value=self._on_shuffle_change)
        self.shuffle_box.add_widget(self.shuffle_label)
        self.shuffle_box.add_widget(self.shuffle_slider)

        self.tempo_box = BoxLayout(orientation='vertical', size_hint_x=1)
        self.tempo_label = Label(
            text="120", font_name="assets/DSEG7Modern-Regular.ttf", font_size=24,
            color=(1, 0, 0, 1), size_hint_y=None, halign='right',
            valign='middle', height=80, padding=(0, 0, 18, 0)
        )
        self.tempo_label.bind(size=self.tempo_label.setter('text_size'))
        self.tempo_slider = Slider(
            orientation='vertical', min=40, max=240, value=120, step=1,
            size_hint_y=1, background_vertical='assets/single_slider_bg_vertical.png',
            border_vertical=(0, 0, 0, 0), background_width=40,
            value_track_color=(0, 0, 0, 0), cursor_image='assets/node_mini_app.png',
            cursor_size=(80, 80), padding=80
        )
        self.tempo_slider.bind(value=self.on_tempo_change)
        self.tempo_box.add_widget(self.tempo_label)
        self.tempo_box.add_widget(self.tempo_slider)

        self.length_box = BoxLayout(orientation='vertical', size_hint_x=1)
        self.length_label = Label(
            text="128", font_name="assets/DSEG7Modern-Regular.ttf", font_size=24,
            color=(1, 0, 0, 1), size_hint_y=None, halign='right',
            valign='middle', height=80, padding=(0, 0, 20, 0)
        )
        self.length_label.bind(size=self.length_label.setter('text_size'))
        self.length_slider = Slider(
            orientation='vertical', min=1, max=128, value=128, step=1,
            size_hint_y=1, background_vertical='assets/single_slider_bg_vertical.png',
            border_vertical=(0, 0, 0, 0), background_width=40,
            value_track_color=(0, 0, 0, 0), cursor_image='assets/node_mini_app.png',
            cursor_size=(80, 80), padding=80
        )
        self.length_slider.bind(value=self.on_length_change)
        self.length_box.add_widget(self.length_label)
        self.length_box.add_widget(self.length_slider)

        self.slider_layout.add_widget(self.tempo_box)
        self.slider_layout.add_widget(self.length_box)
        self.slider_layout.add_widget(self.shuffle_box)
        self.add_widget(self.slider_layout)

        Clock.schedule_once(self.init_midi)

    def _is_last_step(self):
        return self.current_step == (self.pattern_length - 1)

    def handle_step_touch_down(self, node):
        try:
            idx = self.nodes.index(node)
        except ValueError:
            return

        self.held_steps.add(idx)
        if len(self.held_steps) >= 2:
            self.check_for_copy_paste_gesture()

        if not self._ctrl_is_down:
            return

        if self._awaiting_paste:
            if self.clipboard_type == 'row':
                dest_row = idx // 16
                start_idx = dest_row * 16
                end_idx   = start_idx + 15
                self._handle_row_gesture(dest_row, start_idx, end_idx)
                self._awaiting_paste = False
                self._ctrl_copy_start = None
                return

            if self.clipboard_type == 'page':
                self._handle_page_gesture()
                self._awaiting_paste = False
                self._ctrl_copy_start = None
                return

            self._awaiting_paste = False
            self._ctrl_copy_start = None
            return

        if self._ctrl_copy_start is None:
            self._ctrl_copy_start = idx
            self.nodes[idx].load_state = 'armed_load'
            return

        start = self._ctrl_copy_start
        end   = idx

        self.nodes[start].load_state = 'normal'

        if start == 0 and end == 127:
            self._handle_page_gesture()
            self._awaiting_paste = True
            self._ctrl_copy_start = None
            return

        if (start % 16 == 0) and (end == start + 15):
            row_index = start // 16
            self._handle_row_gesture(row_index, start, end)
            self._awaiting_paste = True
            self._ctrl_copy_start = None
            return

        self._ctrl_copy_start = None

    def handle_step_touch_up(self, node):

        try:
            idx = self.nodes.index(node)
        except ValueError:
            return

        if idx in self.held_steps:
            self.held_steps.remove(idx)

        if not node.cancel_interaction:
            if self.clipboard_data is not None:
                self.clipboard_data = None
                self.clipboard_type = None
            self.move_playhead_to_node(node)
        else:
            node.cancel_interaction = False

    def on_delete_pressed(self):
        current_data = self.pages_data[self.current_page_index]
        current_data[self.current_step] = None
        self.nodes[self.current_step].active = False
        print(f"Deleted note at step {self.current_step}")
        self.advance_playhead()

    def delete_current_step(self):
        cur_page = self.pages_data[self.current_page_index]
        cur_page[self.current_step] = None
        self.nodes[self.current_step].active = False
        print(f"[Sequencer] Deleted note at step {self.current_step}")
        self.advance_playhead()

    def check_for_copy_paste_gesture(self):
        if len(self.held_steps) < 2: return
        held_list = sorted(list(self.held_steps))
        start = held_list[0]
        end = held_list[-1]

        if start == 0 and end == 127:
            self._handle_page_gesture()
            return

        if (start % 16 == 0) and (end == start + 15):
            row_index = start // 16
            self._handle_row_gesture(row_index, start, end)
            return

    def _handle_row_gesture(self, row_index, start_idx, end_idx):
        for idx in self.held_steps:
            self.nodes[idx].cancel_interaction = True

        current_page_data = self.pages_data[self.current_page_index]
        if self.clipboard_type == 'row' and self.clipboard_data:
            print(f"PASTING Row to index {row_index}")
            for i in range(16):
                target_step = start_idx + i
                src_val = self.clipboard_data[i]
                if src_val:
                    current_page_data[target_step] = src_val.copy()
                else:
                    current_page_data[target_step] = None
            self._flash_nodes(range(start_idx, end_idx + 1), (0, 1, 0, 1))
            self.refresh_grid()
        else:
            print(f"COPYING Row {row_index}")
            row_data = current_page_data[start_idx : end_idx + 1]
            self.clipboard_data = [d.copy() if d else None for d in row_data]
            self.clipboard_type = 'row'
            self._flash_nodes(range(start_idx, end_idx + 1), (0, 1, 1, 1))

    def _handle_page_gesture(self):
        for idx in self.held_steps:
            self.nodes[idx].cancel_interaction = True

        if self.clipboard_type == 'page' and self.clipboard_data:
            print("PASTING Page")
            new_page = [d.copy() if d else None for d in self.clipboard_data]
            self.pages_data[self.current_page_index] = new_page
            self._flash_nodes(range(0, 128), (0, 1, 0, 1))
            self.refresh_grid()
        else:
            print("COPYING Page")
            current_data = self.pages_data[self.current_page_index]
            self.clipboard_data = [d.copy() if d else None for d in current_data]
            self.clipboard_type = 'page'
            self._flash_nodes(range(0, 128), (0, 1, 1, 1))

    def _flash_nodes(self, indices, color_rgba):
        for idx in indices:
            if 0 <= idx < len(self.nodes):
                node = self.nodes[idx]
                with node.canvas.after:
                    Color(*color_rgba)
                    Line(rectangle=(node.x, node.y, node.width, node.height), width=3)

        def clear_flash(dt):
            for idx in indices:
                if 0 <= idx < len(self.nodes):
                    self.nodes[idx].update_playhead_visual()

        Clock.schedule_once(clear_flash, 0.3)

    def get_sorted_saves(self):
        save_dir = get_sequencer_save_dir()
        if not os.path.exists(save_dir): return []
        return sorted([f for f in os.listdir(save_dir) if f.endswith('.json')])

    def prepare_next_sequence(self):
        saves = self.get_sorted_saves()
        if not saves: return

        next_index = 0
        if self.current_save_filename in saves:
            current_index = saves.index(self.current_save_filename)
            next_index = (current_index + 1) % len(saves)

        next_file = saves[next_index]
        full_path = os.path.join(get_sequencer_save_dir(), next_file)
        try:
            with open(full_path, 'r') as f:
                self.pending_load_data = json.load(f)
                self.pending_load_data['filename'] = next_file
            self.load_btn.img.color = (0, 1, 0, 1)
        except Exception as e:
            print(f"Error staging file: {e}")
            self.pending_load_data = None

    def arm_sequence_switch(self):
        if self.pending_load_data:
            self.arm_quantized_load = True
            self.load_btn.img.color = (1, 1, 1, 1)
        else:
            self.load_btn.img.color = (1, 1, 1, 1)

    def apply_pending_session(self):
        data = self.pending_load_data
        if not data: return
        if 'tempo' in data: self.tempo_slider.value = data['tempo']
        if 'length' in data:
            self.pattern_length = int(data['length'])
            self.length_slider.value = self.pattern_length
        if 'shuffle' in data:
            self.shuffle_slider.value = data['shuffle']
        if 'page_channels' in data: self.page_channels = data['page_channels']
        if 'pages_data' in data:
            loaded_pages = data['pages_data']
            if len(loaded_pages) == 16:
                sanitized_pages = []
                for p in loaded_pages:
                    if len(p) < 128: p = p + [None] * (128 - len(p))
                    elif len(p) > 128: p = p[:128]
                    sanitized_pages.append(p)
                self.pages_data = sanitized_pages
        if 'filename' in data:
            self.current_save_filename = data['filename']

        cur_chan = self.page_channels[self.current_page_index]
        self.channel_label.text = f"{cur_chan + 1:02d}"
        self.refresh_grid()
        self.pending_load_data = None
        self.arm_quantized_load = False
        print(f"Switched to {self.current_save_filename} at Step 0")

    def go_to_menu(self):
        self.stop_playback()
        if self.app_switcher:
            self.app_switcher('goodies_menu')

    def cycle_midi_channel(self):
        current_chan = self.page_channels[self.current_page_index]
        new_chan = (current_chan + 1) % 16
        self.page_channels[self.current_page_index] = new_chan
        self.channel_label.text = f"{new_chan + 1:02d}"

    def init_midi(self, *args):
        if self.main_midi_out:
            print("Sequencer: Using shared main app MIDI Out.")
            self.midi_out = self.main_midi_out
        else:
            if platform in ('android', 'win') and AndroidMidi:
                try:
                    self.midi_out = AndroidMidi()
                    if hasattr(self.midi_out, 'open_output'):
                        self.midi_out.open_output()
                    if platform == 'win' and hasattr(self.midi_out, 'get_host_devices'):
                        devs = self.midi_out.get_host_devices()
                        if devs:
                            self.midi_out.connect_to_device(devs[0][1])
                except Exception as e:
                    print(f"MIDI Out wrapper error: {e}")
            elif rtmidi:
                try:
                    self.midi_out = rtmidi.MidiOut()
                    ports = self.midi_out.get_ports()
                    if ports: self.midi_out.open_port(0)
                    else: self.midi_out.open_virtual_port("Step Sequencer Out")
                except Exception as e:
                    print(f"Failed to initialize rtmidi Out: {e}")

        if platform == 'android' and AndroidMidi:
             try:
                 self.midi_in = AndroidMidi()
                 if hasattr(self.midi_in, 'open_input'):
                     self.midi_in.open_input(self.rtmidi_callback)
             except Exception as e:
                 print(f"AndroidMidi Input Init Error: {e}")
        elif rtmidi:
            try:
                self.midi_in = rtmidi.MidiIn()
                ports = self.midi_in.get_ports()
                if ports:
                    self.midi_in.open_port(0)
                    self.midi_in.set_callback(self.rtmidi_callback)
            except Exception as e:
                print(f"Failed to initialize rtmidi In: {e}")

    def rtmidi_callback(self, message_tuple, data):
        message, deltatime = message_tuple
        if len(message) < 3: return
        status, note, velocity = message[0], message[1], message[2]
        if (status & 0xF0) == 144 and velocity > 0:
            self.handle_midi('note_on', note, velocity)
        elif (status & 0xF0) == 128 or ((status & 0xF0) == 144 and velocity == 0):
            self.handle_midi('note_off', note, velocity)

    def handle_midi(self, message_type, note, velocity):
        page_idx = self.current_page_index

        if message_type == 'note_on' and velocity > 0:
            node = self.nodes[self.current_step]
            step_index = self.current_step

            self._active_note_start[(note, page_idx)] = (time.time(),
                                                        step_index)

            note_data = {
                'note': note,
                'vel':  velocity,
                'len': self.calculate_interval()
            }
            self.pages_data[page_idx][step_index] = note_data
            node.active = True

            if self.midi_out:
                channel = self.page_channels[page_idx]
                note_on_msg  = [144 + channel, note, velocity]
                note_off_msg = [128 + channel, note, 0]
                try:
                    self.midi_out.send_message(note_on_msg)

                except Exception as e:
                    print(f"Input Feedback Error: {e}")

            self.advance_playhead()
            return

        if message_type == 'note_off' or (message_type == 'note_on' and velocity == 0):
            key = (note, page_idx)
            if key in self._active_note_start:
                start_ts, step_idx = self._active_note_start.pop(key)
                duration = time.time() - start_ts

                nd = self.pages_data[page_idx][step_idx]
                if nd is not None:
                    nd['len'] = duration

            if self.midi_out:
                channel = self.page_channels[page_idx]
                note_off_msg = [128 + channel, note, 0]
                try:
                    self.midi_out.send_message(note_off_msg)
                except Exception as e:
                    print(f"MIDI Off Error: {e}")
            return

    def refresh_grid(self):
        current_state = self.pages_data[self.current_page_index]
        for i, node in enumerate(self.nodes):
            node.active = (current_state[i] is not None)

    def select_page(self, page_index):
        if page_index == self.current_page_index:
            return
        self.current_page_index = page_index
        for i, btn in enumerate(self.page_buttons):
            btn.img.source = btn.pressed_src if i == self.current_page_index else btn.normal_src
        stored_channel = self.page_channels[self.current_page_index]
        self.channel_label.text = f"{stored_channel + 1:02d}"
        self.refresh_grid()

    def move_playhead_to_node(self, node):
        try:
            new_step_index = self.nodes.index(node)
            self.nodes[self.current_step].is_playhead = False
            self.current_step = new_step_index
            self.nodes[self.current_step].is_playhead = True
            if self.is_playing:
                self.trigger_current_step_notes()
        except ValueError:
            pass

    def advance_playhead(self):
        self.nodes[self.current_step].is_playhead = False
        self.current_step = (self.current_step + 1) % self.pattern_length
        self.nodes[self.current_step].is_playhead = True

    def _perform_final_save(self, json_path, png_path, data, label_widget):
        try:
            with open(json_path, 'w') as f:
                json.dump(data, f)
            print(f"Saved: {json_path}")
            self.current_save_filename = os.path.basename(json_path)
            target = self.parent if self.parent else self
            self._export_screenshot(target, png_path)
            if label_widget:
                anim = Animation(opacity=0, duration=0.8)
                anim.bind(on_complete=lambda *args: self.remove_widget(label_widget))
                anim.start(label_widget)
        except Exception as e:
            print(f"Save failed: {e}")
            if label_widget: self.remove_widget(label_widget)

    def save_session_action(self):
        save_dir = get_sequencer_save_dir()
        existing = [f for f in os.listdir(save_dir) if f.startswith("seq_") and f.endswith(".json")]
        next_num = 1
        if existing:
            try:
                numbers = []
                for f in existing:
                    if f.startswith("seq_") and f[4:7].isdigit():
                        numbers.append(int(f[4:7]))
                if numbers:
                    next_num = max(numbers) + 1
            except:
                pass

        base_name = f"seq_{next_num:03d}"
        json_path = os.path.join(save_dir, f"{base_name}.json")
        png_path = os.path.join(save_dir, f"{base_name}.png")

        data = {
            "version": "1.0",
            "tempo": self.tempo_slider.value,
            "length": self.pattern_length,
            "page_channels": self.page_channels,
            "pages_data": self.pages_data,
            "shuffle": self.shuffle_slider.value,
        }

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
        self.add_widget(save_label)
        Clock.schedule_once(
            lambda dt: self._perform_final_save(json_path, png_path, data, save_label),
            0.1
        )

    def _export_screenshot(self, widget, path):
        try:
            widget.export_to_png(path)
        except Exception as e:
            print(f"Screenshot failed: {e}")

    def open_load_popup(self):
        popup = SequencerLoadPopup(sequencer=self)
        popup.open()

    def load_session(self, filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Load failed: {e}")
            return
        self.on_stop_pressed()
        self._apply_data(data)
        self.current_save_filename = os.path.basename(filepath)
        print(f"Loaded: {self.current_save_filename}")

    def _apply_data(self, data):
        if 'tempo' in data: self.tempo_slider.value = data['tempo']
        if 'length' in data:
            self.pattern_length = int(data['length'])
            self.length_slider.value = self.pattern_length
        if 'shuffle' in data:
            self.shuffle_slider.value = data['shuffle']
        if 'page_channels' in data: self.page_channels = data['page_channels']
        if 'pages_data' in data:
            loaded_pages = data['pages_data']
            if len(loaded_pages) == 16:
                sanitized_pages = []
                for p in loaded_pages:
                    if len(p) < 128: p = p + [None] * (128 - len(p))
                    elif len(p) > 128: p = p[:128]
                    sanitized_pages.append(p)
                self.pages_data = sanitized_pages
        cur_chan = self.page_channels[self.current_page_index]
        self.channel_label.text = f"{cur_chan + 1:02d}"
        for i, btn in enumerate(self.page_buttons):
            btn.img.source = btn.pressed_src if i == self.current_page_index else btn.normal_src
        self.refresh_grid()

    def on_play_pressed(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.img.source = self.play_btn.pressed_src
            self.start_playback()
        else:
            self.play_btn.img.source = self.play_btn.normal_src
            self.stop_playback()

    def on_stop_pressed(self):
        if self.is_playing:
            self.is_playing = False
            self.stop_playback()
            self.play_btn.img.source = self.play_btn.normal_src
        self.nodes[self.current_step].is_playhead = False
        self.current_step = 0
        self.nodes[self.current_step].is_playhead = True

    def calculate_interval(self):
        bpm = self.tempo_slider.value
        steps_per_beat = 4
        beats_per_second = bpm / 60.0
        steps_per_second = beats_per_second * steps_per_beat
        if steps_per_second == 0: return 0.1
        return 1.0 / steps_per_second

    def _schedule_next_step(self):
        base_interval = self.calculate_interval()
        next_index = (self.current_step + 1) % self.pattern_length
        max_extra = base_interval * 0.5
        desired_extra = (self.shuffle_percent / 100.0) * max_extra
        if next_index % 2 == 1:
            extra = desired_extra
            self._last_extra_delay = extra
            final_interval = base_interval + extra
        else:
            extra = -self._last_extra_delay
            final_interval = max(base_interval + extra, self._min_interval)
            self._last_extra_delay = 0.0
        self.playback_event = Clock.schedule_once(self.sequencer_tick, final_interval)

    def start_playback(self):
        self.stop_playback()
        self.is_playing = True
        self.trigger_current_step_notes()
        self._schedule_next_step()

    def stop_playback(self):
        if self.playback_event:
            self.playback_event.cancel()
            self.playback_event = None

    def on_tempo_change(self, instance, value):
        self.tempo_label.text = f"{int(value)}"
        if self.is_playing:
            self.start_playback()

    def on_length_change(self, instance, value):
        self.length_label.text = f"{int(value)}"
        self.pattern_length = int(value)
        for i, node in enumerate(self.nodes):
            node.is_enabled = (i < self.pattern_length)
        if self.current_step >= self.pattern_length:
            self.nodes[self.current_step].is_playhead = False
            self.current_step = 0
            self.nodes[self.current_step].is_playhead = True

    def _on_shuffle_change(self, instance, value):
        self.shuffle_percent = int(value)

    def sequencer_tick(self, dt):
        if self.arm_quantized_load and self._is_last_step():
            self.apply_pending_session()
            self.arm_quantized_load = False
            self.current_step = -1

        self.advance_playhead()
        self.trigger_current_step_notes()

        if self.is_playing:
            self._schedule_next_step()

    def trigger_current_step_notes(self):
        if not self.midi_out: return
        step_index = self.current_step
        for page_index, page_data in enumerate(self.pages_data):
            note_data = page_data[step_index]
            if note_data:
                note = note_data['note']
                vel = note_data['vel']
                note_len = note_data.get('len', self.calculate_interval())
                channel = self.page_channels[page_index]
                note_on_msg  = [144 + channel, note, vel]
                note_off_msg = [128 + channel, note, 0]
                try:
                    self.midi_out.send_message(note_on_msg)

                    Clock.schedule_once(
                        lambda dt, msg=note_off_msg: self.send_midi_off(msg),
                        note_len
                    )
                except Exception as e:
                    print(f"MIDI Send Error: {e}")

    def send_midi_off(self, msg):
        if self.midi_out:
            try:
                self.midi_out.send_message(msg)
            except:
                pass

    def _on_key_down(self, window, keycode, scancode, codepoint, modifiers):
        if 'ctrl' in modifiers:
            self._ctrl_is_down = True

        numeric_key, name_key = keycode if isinstance(keycode, (list, tuple)) else (keycode, '')

        is_delete = (
            numeric_key == 127
            or name_key.lower() in ('delete', 'del')
        )

        if is_delete:
            if not self._ctrl_is_down:
                self.delete_current_step()
                return True

        return False

    def _on_key_up(self, window, key, scancode):
        if key in (272, 273) or getattr(Window, 'keyboard', None) is None:
            self._ctrl_is_down = False
            self._ctrl_copy_start = None
        return False

class SequencerRoot(FitLayout):
    def __init__(self, app_switcher=None, main_midi_out=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher
        self.main_midi_out = main_midi_out

        self.scatter = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False, do_translation=False,
            do_scale=False, auto_bring_to_front=False,
        )

        self.content = SequencerContent(
            app_switcher=app_switcher,
            main_midi_out=main_midi_out,
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        )

        self.scatter.add_widget(self.content)
        self.add_widget(self.scatter)

    def cleanup_app(self):
        if self.content:
            self.content.stop_playback()
            if self.content.midi_in and hasattr(self.content.midi_in, 'close_port'):
                 self.content.midi_in.close_port()
            if self.content.midi_out and self.content.midi_out != self.main_midi_out:
                if hasattr(self.content.midi_out, 'close_port'):
                    self.content.midi_out.close_port()
                elif hasattr(self.content.midi_out, 'close'):
                    self.content.midi_out.close()
        Window.unbind(on_key_down=self._on_key_down,
            on_key_up=self._on_key_up)

class StepSequencerApp(App):
    def build(self):
        Window.size = (1920, 1080)
        self.root_widget = SequencerRoot()
        return self.root_widget

    def on_stop(self):
        if hasattr(self, 'root_widget'):
            self.root_widget.cleanup_app()

if __name__ == "__main__":
    StepSequencerApp().run()
