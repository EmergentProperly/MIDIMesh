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

import logging
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation

DEBUG_LAYOUTS = False

BACKGROUND_IMAGE = 'assets/panel_03.png'
BTN_NORMAL = 'assets/flat_button_grey.png'
BTN_PRESSED = 'assets/flat_button_grey_pressed.png'

ANIM_FONTS = [
    'assets/Handwrite-01.ttf',
    'assets/Handwrite-02.ttf',
    'assets/Handwrite-03.ttf'
]

ANIM_ARROWS = [
    'assets/Arrows/arrow-01.png',
    'assets/Arrows/arrow-02.png',
    'assets/Arrows/arrow-03.png',
    'assets/Arrows/arrow-04.png',
    'assets/Arrows/arrow-05.png',
]

DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080
FONT_SIZE_TITLE = 50
FONT_SIZE_BODY = 36
FONT_SIZE_BUTTON = 36
BUTTON_HEIGHT = 120
ROW_HEIGHT = 100
MARGIN = 50

settings_store = JsonStore('user_settings.json')

#For debugging
class MockDevice:
    def __init__(self, id, name):
        self._id = id
        self._name = name
    def getId(self): return self._id
    def getProperties(self):
        return type('Props', (object,), {'getString': lambda s, k: self._name})()

class MockMidiManager:
    def __init__(self):
        self.connected_ids = set()
        self.connection_mode = 'client'
    def get_host_devices(self):
        return [("Debug Synth 1 (USB)", MockDevice(1, "Debug Synth 1")),
                ("Roland Fake-09", MockDevice(2, "Roland Fake-09")),
                ("Korg Imaginary", MockDevice(3, "Korg Imaginary"))]
    def get_connected_host_device_ids(self): return list(self.connected_ids)
    def connect_to_device(self, device): self.connected_ids.add(device.getId())
    def disconnect_device(self, device_id):
        if device_id in self.connected_ids: self.connected_ids.remove(device_id)
    def set_connection_mode(self, mode): self.connection_mode = mode
    def open_output(self): pass

class Fit16x9Layout(FloatLayout):
    def do_layout(self, *args):
        if not self.children: return
        content = self.children[0]
        win_w, win_h = self.size
        content_w, content_h = DESIGN_WIDTH, DESIGN_HEIGHT

        if win_w == 0 or win_h == 0: return

        scale = min(win_w / content_w, win_h / content_h)
        new_pos_x = (win_w - (content_w * scale)) / 2
        new_pos_y = (win_h - (content_h * scale)) / 2

        epsilon = 1e-6
        if (abs(content.scale - scale) > epsilon or
            abs(content.pos[0] - new_pos_x) > epsilon or
            abs(content.pos[1] - new_pos_y) > epsilon):

            if hasattr(content, 'scale'):
                content.scale = scale
            content.pos = (new_pos_x, new_pos_y)

class ScalableContent(ScatterLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (DESIGN_WIDTH, DESIGN_HEIGHT)
        self.do_rotation = False
        self.do_scale = False
        self.do_translation = False
        self.auto_bring_to_front = False

class BigCheckBox(ScatterLayout):
    active = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (60, 60)
        self.do_rotation = False
        self.do_scale = False
        self.do_translation = False
        self.auto_bring_to_front = False
        self.scale = 2
        self.checkbox = CheckBox(size_hint=(None, None), size=(32, 32))
        self.checkbox.pos_hint = {'center_x': 0.3, 'center_y': 0.2}
        self.checkbox.bind(active=self._on_checkbox_active)
        self.add_widget(self.checkbox)

    def _on_checkbox_active(self, instance, value):
        self.active = value
    def on_active(self, instance, value):
        self.checkbox.active = value
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if self.checkbox.collide_point(*touch.pos):
                self.checkbox.on_touch_down(touch)
                touch.pop()
                return True
            touch.pop()
        return False

class DontShowAgainRow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (640, 100)
        self.spacing = 40
        chk_wrapper = AnchorLayout(size_hint=(None, 1), width=100, anchor_x='center', anchor_y='center')
        self.checkbox = BigCheckBox()
        chk_wrapper.add_widget(self.checkbox)
        self.label = Label(
            text="Don't show this automatically",
            font_size=FONT_SIZE_BODY,
            halign='left',
            valign='middle',
            size_hint=(1, 1)
        )
        self.label.bind(size=self.label.setter('text_size'), on_touch_down=self._toggle_checkbox)
        self.add_widget(chk_wrapper)
        self.add_widget(self.label)

    def _toggle_checkbox(self, instance, touch):
        if self.label.collide_point(*touch.pos):
            self.checkbox.active = not self.checkbox.active
    def is_checked(self):
        return self.checkbox.active

def save_skip_preference(should_skip):
    if should_skip:
        settings_store.put('skip_midi_setup', value=True)
        logging.info("Guided Popups: 'Don't show again' saved.")

class BaseFullLayoutPopup(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.auto_dismiss = False
        self.background = ''
        self.background_color = (0, 0, 0, 0)
        self.border = (0, 0, 0, 0)
        self.scaler_root = Fit16x9Layout()
        self.workspace = ScalableContent()
        with self.workspace.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(source=BACKGROUND_IMAGE, size=(DESIGN_WIDTH, DESIGN_HEIGHT), pos=(0,0))
        self.scaler_root.add_widget(self.workspace)
        self.add_widget(self.scaler_root)
    def add_content_widget(self, widget):
        self.workspace.add_widget(widget)

class CombinedCoachMarkPopup(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.overlay_color = (0, 0, 0, 0)
        self.background = ''
        self.background_color = (0, 0, 0, 0)
        self.auto_dismiss = False
        self.scaler_root = Fit16x9Layout()
        self.workspace = ScalableContent()
        self.workspace.opacity = 0
        self.scaler_root.add_widget(self.workspace)
        self.add_widget(self.scaler_root)

        self.lbl_settings = Label(
            text="Settings and other goodies\ncan be found here",
            font_size=48,
            font_name=ANIM_FONTS[0],
            halign='center',
            valign='center',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(1000, 200),
            pos=(750,880)
        )
        self.workspace.add_widget(self.lbl_settings)

        self.img_arrow_settings = Image(
            source=ANIM_ARROWS[0],
            size_hint=(None, None),
            size=(200, 200),
            pos=(1575,900),
            allow_stretch=True
        )
        self.workspace.add_widget(self.img_arrow_settings)

        self.lbl_help = Label(
            text="For a detailed rundown of the controls etc,\npress the 'HELP' button",
            font_size=48,
            font_name=ANIM_FONTS[0],
            halign='center',
            valign='center',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(1000, 200),
            pos=(420, 500)
        )
        self.workspace.add_widget(self.lbl_help)

        self.img_arrow_help = Image(
            source=ANIM_ARROWS[0],
            size_hint=(None, None),
            size=(200, 200),
            pos=(160, 540),
            allow_stretch=True
        )

        with self.img_arrow_help.canvas.before:
             PushMatrix()
             Rotate(angle=-180, origin=self.img_arrow_help.center)
        with self.img_arrow_help.canvas.after:
             PopMatrix()

        self.workspace.add_widget(self.img_arrow_help)
        self.anim_font_idx = 0
        self.anim_arrow_idx = 0
        self.anim_event = Clock.schedule_interval(self._animate_step, 0.125)

    def on_open(self):
        super().on_open()
        anim = Animation(opacity=1, duration=0.5)
        anim.start(self.workspace)

    def _animate_step(self, dt):
        self.anim_font_idx = (self.anim_font_idx + 1) % len(ANIM_FONTS)
        self.anim_arrow_idx = (self.anim_arrow_idx + 1) % len(ANIM_ARROWS)

        current_font = ANIM_FONTS[self.anim_font_idx]
        current_arrow = ANIM_ARROWS[self.anim_arrow_idx]

        try:
            self.lbl_settings.font_name = current_font
            self.img_arrow_settings.source = current_arrow
            self.lbl_help.font_name = current_font
            self.img_arrow_help.source = current_arrow
        except Exception:
            pass

    def on_touch_down(self, touch):
        Clock.schedule_once(lambda dt: self.dismiss(), 0)
        return True

    def on_dismiss(self):
        if self.anim_event:
            self.anim_event.cancel()
        return super().on_dismiss()


class MidiDeviceSelectorPopup(BaseFullLayoutPopup):
    def __init__(self, midi_manager, device_list, on_connect_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.midi_manager = midi_manager
        self.on_connect_callback = on_connect_callback
        self.current_device_list = device_list
        try:
            self.connected_ids = self.midi_manager.get_connected_host_device_ids()
        except Exception as e:
            logging.error(f"Guided Popups: Failed to get connected IDs: {e}")
            self.connected_ids = []

        main_layout = BoxLayout(
            orientation='vertical',
            padding=[100, 50, 100, 50],
            spacing=30,
            size_hint=(1, 1)
        )
        title_lbl = Label(text="Select MIDI Devices", font_size=FONT_SIZE_TITLE, size_hint_y=None, height=120, bold=True)
        main_layout.add_widget(title_lbl)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        main_layout.add_widget(self.scroll)
        self.populate_device_list()
        bottom_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=BUTTON_HEIGHT + 20, spacing=20)
        bt_wrapper = AnchorLayout(anchor_x='left', anchor_y='center', size_hint=(None, 1), width=280)
        bt_btn = Button(text="Setup Bluetooth", font_size=32, background_normal=BTN_NORMAL, background_down=BTN_PRESSED, size_hint=(1, None), height=BUTTON_HEIGHT)
        bt_btn.bind(on_release=self.open_bluetooth_settings)
        bt_wrapper.add_widget(bt_btn)
        bottom_row.add_widget(bt_wrapper)
        refresh_wrapper = AnchorLayout(anchor_x='left', anchor_y='center', size_hint=(None, 1), width=200)
        refresh_btn = Button(text="Refresh", font_size=32, background_normal=BTN_NORMAL, background_down=BTN_PRESSED, size_hint=(1, None), height=BUTTON_HEIGHT)
        refresh_btn.bind(on_release=self.refresh_list)
        refresh_wrapper.add_widget(refresh_btn)
        bottom_row.add_widget(refresh_wrapper)
        done_wrapper = AnchorLayout(anchor_x='right', anchor_y='center', size_hint=(None, 1), width=400)
        done_btn = Button(text="Done", font_size=FONT_SIZE_BODY, background_normal='assets/flat_button_green.png', background_down='assets/flat_button_green_pressed.png', size_hint=(1, None), height=BUTTON_HEIGHT)
        done_btn.bind(on_release=self.close_popup)
        done_wrapper.add_widget(done_btn)
        bottom_row.add_widget(done_wrapper)
        self.dont_show_row = DontShowAgainRow()
        bottom_row.add_widget(self.dont_show_row)
        main_layout.add_widget(bottom_row)
        self.add_content_widget(main_layout)

    def populate_device_list(self):
        try:
            self.list_layout.clear_widgets()
            if not self.current_device_list:
                lbl = Label(text="No devices found.\nCheck connections or Refresh.", font_size=FONT_SIZE_BODY, size_hint_y=None, height=200)
                self.list_layout.add_widget(lbl)
                return
            for name, device_obj in self.current_device_list:
                if name is None:
                    name = "Unknown MIDI Device"
                    logging.warning("Guided Popups: Device name was None, replaced with generic label.")

                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=ROW_HEIGHT)
                lbl_anchor = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=0.85, padding=[20, 0, 0, 0])
                lbl = Label(text=str(name), font_size=FONT_SIZE_BODY, size_hint=(1, None), height=ROW_HEIGHT, halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                lbl_anchor.add_widget(lbl)

                chk_container = AnchorLayout(size_hint_x=0.15, anchor_x='center', anchor_y='center', padding=[0, 15, 0, 0])
                chk = BigCheckBox()
                chk.device_obj = device_obj
                if device_obj.getId() in self.connected_ids:
                    chk.active = True
                chk.bind(active=self._on_checkbox_active)
                chk_container.add_widget(chk)
                row.add_widget(lbl_anchor)
                row.add_widget(chk_container)
                self.list_layout.add_widget(row)
        except Exception as e:
            logging.error(f"Guided Popups: Error populating device list: {e}")
            self.list_layout.clear_widgets()
            error_lbl = Label(text="Error loading devices. Please refresh.", font_size=FONT_SIZE_BODY, color=(1, 0, 0, 1))
            self.list_layout.add_widget(error_lbl)

    def refresh_list(self, instance):
        logging.info("Guided Popups: Refreshing device list...")
        try:
            self.current_device_list = self.midi_manager.get_host_devices()
            self.populate_device_list()
        except Exception as e:
            logging.error(f"Guided Popups: Error refreshing list: {e}")

    def open_bluetooth_settings(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
                current_activity = PythonActivity.mActivity
                current_activity.startActivity(intent)
            except Exception as e:
                logging.error(f"Guided Popups: Failed to open Bluetooth settings: {e}")
        else:
            logging.info("Guided Popups: 'Setup Bluetooth' clicked (Not on Android).")

    def _on_checkbox_active(self, checkbox, value):
        device = getattr(checkbox, 'device_obj', None)
        if not device: return
        try:
            if value:
                self.midi_manager.connect_to_device(device)
            else:
                self.midi_manager.disconnect_device(device.getId())
        except Exception as e:
            logging.error(f"Guided Popups: Error toggling connection: {e}")

    def close_popup(self, instance):
        if self.dont_show_row.is_checked():
            save_skip_preference(True)
        self.dismiss()
        if self.on_connect_callback:
            self.on_connect_callback()


class AndroidModeSelectorPopup(BaseFullLayoutPopup):
    def __init__(self, midi_manager, on_connect_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.midi_manager = midi_manager
        self.on_connect_callback = on_connect_callback

        layout = BoxLayout(
            orientation='vertical',
            padding=[100, 100, 100, 100],
            spacing=50,
            size_hint=(1, 1)
        )

        lbl = Label(
            text="How are you using this device?",
            font_size=FONT_SIZE_TITLE,
            size_hint_y=None,
            height=120,
            bold=True
        )
        layout.add_widget(lbl)

        spacer_1 = Label(
            text="",
            size_hint_y=None,
            height=5,
        )
        layout.add_widget(spacer_1)

        content_grid = BoxLayout(orientation='horizontal', spacing=100)

        host_col = BoxLayout(orientation='vertical', spacing=20)
        img_host = Image(
            source='assets/hardware.png',
            size_hint=(1, None),
            height=250,
            allow_stretch=True
        )
        host_col.add_widget(img_host)

        self.lbl_host = Label(
            text="I am plugging external\nhardware into this device.",
            font_size='42px',
            font_name=ANIM_FONTS[0],
            halign='center',
            valign='center',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.lbl_host.bind(size=self.lbl_host.setter('text_size'))
        btn_host = Button(
            text="HOST / OTG",
            font_size=FONT_SIZE_BUTTON,
            background_normal=BTN_NORMAL,
            background_down=BTN_PRESSED,
            background_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=BUTTON_HEIGHT
        )
        btn_host.bind(on_release=self.set_host_mode)
        host_col.add_widget(self.lbl_host)
        host_col.add_widget(btn_host)

        guest_col = BoxLayout(orientation='vertical', spacing=20)
        img_guest = Image(
            source='assets/software.png',
            size_hint=(1, None),
            height=250,
            allow_stretch=True
        )
        guest_col.add_widget(img_guest)

        self.lbl_guest = Label(
            text="I am plugging this device into\na computer or MIDI hub.",
            font_size='42px',
            font_name=ANIM_FONTS[0],
            halign='center',
            valign='center',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.lbl_guest.bind(size=self.lbl_guest.setter('text_size'))
        btn_guest = Button(
            text="GUEST",
            font_size=FONT_SIZE_BUTTON,
            background_normal=BTN_NORMAL,
            background_down=BTN_PRESSED,
            background_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=BUTTON_HEIGHT
        )
        btn_guest.bind(on_release=self.set_guest_mode)
        guest_col.add_widget(self.lbl_guest)
        guest_col.add_widget(btn_guest)

        content_grid.add_widget(host_col)
        content_grid.add_widget(guest_col)
        layout.add_widget(content_grid)

        footer = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        footer.add_widget(Widget())
        self.dont_show_row = DontShowAgainRow()
        footer.add_widget(self.dont_show_row)
        footer.add_widget(Widget())
        layout.add_widget(footer)

        self.add_content_widget(layout)
        self.anim_font_idx = 0
        self.anim_event = Clock.schedule_interval(self._animate_step, 0.125)

    def _animate_step(self, dt):
        self.anim_font_idx = (self.anim_font_idx + 1) % len(ANIM_FONTS)
        try:
            current_font = ANIM_FONTS[self.anim_font_idx]
            self.lbl_host.font_name = current_font
            self.lbl_guest.font_name = current_font
        except Exception:
            pass

    def on_dismiss(self):
        if self.anim_event:
            self.anim_event.cancel()
        return super().on_dismiss()

    def _check_save_pref(self):
        if self.dont_show_row.is_checked():
            save_skip_preference(True)

    def set_host_mode(self, instance):
        self._check_save_pref()
        self.dismiss()
        self.midi_manager.set_connection_mode('host')
        devices = self.midi_manager.get_host_devices()
        MidiDeviceSelectorPopup(self.midi_manager, devices, on_connect_callback=self.on_connect_callback).open()

    def set_guest_mode(self, instance):
        self._check_save_pref()
        self.dismiss()
        self.midi_manager.set_connection_mode('client')
        self.midi_manager.open_output()
        if self.on_connect_callback:
            self.on_connect_callback()

def show_midi_configuration(midi_manager, is_auto_launch=False, on_done_callback=None):

    def on_midi_sequence_finished():
        if on_done_callback:
            on_done_callback()
        else:
            Clock.schedule_once(lambda dt: CombinedCoachMarkPopup().open(), 0.5)

    if is_auto_launch:
        if settings_store.exists('skip_midi_setup') and settings_store.get('skip_midi_setup')['value']:
            logging.info("Guided Popups: Skipping MIDI setup per user preference.")
            if platform == 'android':
                midi_manager.set_connection_mode('client')
                midi_manager.open_output()
            return

    current_platform = platform
    if DEBUG_LAYOUTS and current_platform not in ('android', 'win'):
        logging.warning("Guided Popups: DEBUG MODE - Simulating Android flow.")
        current_platform = 'android'
        midi_manager = MockMidiManager()

    if current_platform == 'android':
        AndroidModeSelectorPopup(midi_manager, on_connect_callback=on_midi_sequence_finished).open()
    elif current_platform == 'win':
        if DEBUG_LAYOUTS and platform != 'win': midi_manager = MockMidiManager()
        devices = midi_manager.get_host_devices()
        MidiDeviceSelectorPopup(midi_manager, devices, on_connect_callback=on_midi_sequence_finished).open()
    else:
        logging.info("Guided Popups: Linux/MacOS detected. Skipping wizard.")
        on_midi_sequence_finished()
