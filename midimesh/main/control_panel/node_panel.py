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

import time
import os
import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.utils import platform
from kivy.logger import Logger

from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.core.window import Window


import midimesh.main.main_canvas.midi_manager as midi_manager

class ToggleImageButton(ButtonBehavior, Image):
    toggled = BooleanProperty(True)

    def __init__(self, on_src, off_src, **kwargs):
        super().__init__(**kwargs)
        self.on_src  = on_src
        self.off_src = off_src
        self.source = self.on_src if self.toggled else self.off_src

    def on_press(self):
        self.toggled = not self.toggled
        self.source = self.on_src if self.toggled else self.off_src
        if hasattr(self.parent, "toggle_movement"):
            self.parent.toggle_movement()


class ConnectionModeButton(ButtonBehavior, Image):
    # 0 = allow, 1 = lock
    mode = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sources = [
            os.path.join(os.path.dirname(__file__),"assets", "allow_connection.png"),
            os.path.join(os.path.dirname(__file__),"assets", "lock_connection.png"),
        ]
        self.source = self.sources[self.mode]

    def on_press(self):
        self.mode = (self.mode + 1) % 2
        self.source = self.sources[self.mode]
        if hasattr(self.parent, "set_connection_mode"):
            self.parent.set_connection_mode(self.mode)

class ToggleStateButton(ButtonBehavior, Image):
    toggled = BooleanProperty(False)

    def __init__(self, on_src, off_src, **kwargs):
        super().__init__(**kwargs)
        self.on_src = on_src
        self.off_src = off_src
        self.source = self.off_src if not self.toggled else self.on_src
        self.bind(toggled=self._on_toggled)

    def _on_toggled(self, instance, value):
        self.source = self.on_src if value else self.off_src

    def on_press(self):
        self.toggled = not self.toggled
        if hasattr(self.parent, "on_button_state_change"):
            self.parent.on_button_state_change(self, self.toggled)


class DeleteImageButton(ButtonBehavior, Image):
    armed = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_dir = os.path.join(os.path.dirname(__file__), "assets")

        self.disarmed_normal = os.path.join(base_dir, "delete_null.png")
        self.disarmed_pressed = os.path.join(base_dir, "delete_null_pressed.png")
        self.armed_normal = os.path.join(base_dir, "delete.png")
        self.armed_pressed = os.path.join(base_dir, "delete_pressed.png")
        self.source = self.disarmed_normal

    def on_press(self):
        if self.armed:
            self.source = self.armed_pressed
        else:
            self.source = self.disarmed_pressed

    def on_release(self):
        if self.armed:
            if hasattr(self.parent, 'delete_last_selected_circle'):
                self.parent.delete_last_selected_circle()
            self.disarm()
        else:
            self.armed = True
            self.source = self.armed_normal

    def disarm(self):
        self.armed = False
        self.source = self.disarmed_normal

class MidiDevicePopup(Popup):
    def __init__(self, devices_list, android_midi_ref, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Select MIDI Host (OTG) Devices'
        self.size_hint = (0.8, 0.8)
        self.android_midi_ref = android_midi_ref
        self.auto_dismiss = False

        try:
            self.connected_ids = self.android_midi_ref.get_connected_host_device_ids()
        except Exception as e:
            Logger.error(f"MidiDevicePopup: Failed to get connected_ids: {e}")
            self.connected_ids = []


        root_layout = BoxLayout(orientation='vertical')

        scroll = ScrollView(size_hint=(1, 0.85))
        self.row_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        self.row_container.bind(minimum_height=self.row_container.setter('height'))

        if not devices_list:
            self.row_container.add_widget(Label(text="No OTG/Host devices found.", height=40))

        for device_name, device_info in devices_list:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

            row_label = Label(text=device_name, size_hint_x=0.8, halign='left', valign='middle')
            row_label.bind(size=row_label.setter('text_size'))

            row_check = CheckBox(size_hint_x=0.2)
            row_check.device_info = device_info

            if device_info.getId() in self.connected_ids:
                row_check.active = True

            row_check.bind(active=self._on_checkbox_active)

            row.add_widget(row_label)
            row.add_widget(row_check)
            self.row_container.add_widget(row)

        scroll.add_widget(self.row_container)
        root_layout.add_widget(scroll)

        dismiss_button = Button(text='Dismiss', size_hint=(1, 0.15))
        dismiss_button.bind(on_press=self.dismiss)
        root_layout.add_widget(dismiss_button)

        self.content = root_layout

    def _on_checkbox_active(self, checkbox_instance, is_active):
        info = checkbox_instance.device_info
        if not info:
            Logger.error("MidiDevicePopup: Checkbox missing device_info!")
            return

        device_name = "Unknown"
        try:
            device_name = info.getProperties().getString('name')
            if is_active:
                Logger.info(f"MidiDevicePopup: Requesting connection to {device_name}")
                self.android_midi_ref.connect_to_device(info)
            else:
                Logger.info(f"MidiDevicePopup: Requesting disconnect from {device_name}")
                self.android_midi_ref.disconnect_device(info.getId())
        except Exception as e:
            Logger.error(f"MidiDevicePopup: Error (dis)connecting '{device_name}': {e}")

class DeleteImageButton(ButtonBehavior, Image):
    armed = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_dir = os.path.join(os.path.dirname(__file__), "assets")

        self.disarmed_normal = os.path.join(base_dir, "delete_null.png")
        self.disarmed_pressed = os.path.join(base_dir, "delete_null_pressed.png")
        self.armed_normal = os.path.join(base_dir, "delete.png")
        self.armed_pressed = os.path.join(base_dir, "delete_pressed.png")
        self.source = self.disarmed_normal

    def on_press(self):
        if self.armed:
            self.source = self.armed_pressed
        else:
            self.source = self.disarmed_pressed

    def on_release(self):
        if self.armed:
            if hasattr(self.parent, 'delete_last_selected_circle'):
                self.parent.delete_last_selected_circle()
            self.disarm()
        else:
            self.armed = True
            self.source = self.armed_normal

    def disarm(self):
        self.armed = False
        self.source = self.disarmed_normal


class MiscControls(FloatLayout):
    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.size = (500, 500)
        self.size_hint = (None, None)
        self.pos = (1400, 20)

        self.bg_image = Image(
            source=os.path.join(os.path.dirname(__file__), "assets", "node_panel_bg.png"),
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.bg_image)


        self.movement_btn = ToggleImageButton(
            on_src=os.path.join(os.path.dirname(__file__), "assets", "movement.png"),
            off_src=os.path.join(os.path.dirname(__file__), "assets", "movement_stopped.png"),
            size_hint=(None, None), size=(80, 80),
            pos_hint={'x': 0.1092, 'y': 0.4211}
        )
        self.add_widget(self.movement_btn)

        self.conn_mode_btn = ConnectionModeButton(
            size_hint=(None, None), size=(80, 80),
            pos_hint={'x': 0.732, 'y': 0.708}
        )

        self._sync_button_with_circle(None)

        self.button_a = ToggleStateButton(
            on_src=os.path.join(os.path.dirname(__file__), "assets", "null.png"),
            off_src=os.path.join(os.path.dirname(__file__), "assets", "packet_1.png"),
            size_hint=(None, None), size=(50, 50),
            pos_hint={'x': 0.519, 'y': 0.744}
        )

        self.button_b = ToggleStateButton(
            on_src=os.path.join(os.path.dirname(__file__), "assets", "packet_1.png"),
            off_src=os.path.join(os.path.dirname(__file__), "assets", "null.png"),
            size_hint=(None, None), size=(50, 50),
            pos_hint={'x': 0.378, 'y': 0.744}
        )
        self.add_widget(self.button_a)
        self.add_widget(self.button_b)

        self.delete_button = DeleteImageButton(
            size_hint=(None, None), size=(95, 95),
            pos_hint={'x': 0.095, 'y': 0.12}
        )

        self.add_widget(self.conn_mode_btn)
        self.add_widget(self.delete_button)

        self.delete_label = Label(
            text="DEL",
            font_size='28px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None), size=(95, 95),
            pos_hint={'x': 0.095, 'y': 0.12}
        )
        self.add_widget(self.delete_label)

        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)

        self.bind(pos=self._update_rects, size=self._update_rects)
        
        self._key_handler = lambda win, key, scancode, codepoint, modifier: \
            self._on_key_down(win, key, scancode, codepoint, modifier)
        Window.bind(on_key_down=self._key_handler)
        
    def _handle_delete_key(self):
        if self.delete_button.armed:
            self.delete_button.dispatch('on_release')
        else:
            self.delete_button.armed = True
            self.delete_button.source = self.delete_button.armed_normal
            Clock.schedule_once(lambda dt: self.delete_button.disarm(), 3)
            
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        DELETE_KEYS = {127, 8}          
        if key in DELETE_KEYS:
            self._handle_delete_key()
            return True
        if self.delete_button.armed:
            self.delete_button.disarm()
        return False
        
    def on_parent(self, widget, parent):
        if not parent and hasattr(self, "_key_handler"):
            from kivy.core.window import Window
            Window.unbind(on_key_down=self._key_handler)

    def _update_rects(self, instance, value):
        self.border.rectangle = (self.x, self.y, self.width, self.height)

    def on_touch_down(self, touch):

        if self.disabled:
            return False

        if self.delete_button.armed:
            if not self.delete_button.collide_point(*touch.pos):
                self.delete_button.disarm()

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.disabled:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.disabled:
            return False
        return super().on_touch_up(touch)

    def on_button_state_change(self, button, toggled):
        if button is self.button_a:
            if self.visualizer.last_selected_circle:
                self.visualizer.last_selected_circle['packet_state_a'] = toggled
        elif button is self.button_b:
            if self.visualizer.last_selected_circle:
                self.visualizer.last_selected_circle['packet_state_b'] = toggled

    def set_connection_mode(self, mode):
        if self.visualizer:
            self.visualizer.set_last_circle_connection_mode(mode)

    def sync_connection_mode_button(self, circle):
        if not circle:
            self.conn_mode_btn.mode = 0
            self.conn_mode_btn.source = self.conn_mode_btn.sources[0]
            return
        self.conn_mode_btn.mode = circle.get('connection_mode', 0)
        self.conn_mode_btn.source = self.conn_mode_btn.sources[self.conn_mode_btn.mode]

    def sync_movement_button(self, circle):
        self._sync_button_with_circle(circle)

    def _sync_button_with_circle(self, circle):
        if circle is None:
            self.movement_btn.toggled = False
            self.movement_btn.source = self.movement_btn.off_src
            return

        enabled = circle.get('movement_enabled', True)
        self.movement_btn.toggled = enabled
        self.movement_btn.source = (
            self.movement_btn.on_src if enabled else self.movement_btn.off_src
        )

    def toggle_movement(self):
        circ = self.visualizer.last_selected_circle
        if not circ:
            return

        circ['movement_enabled'] = not circ.get('movement_enabled', True)
        self._sync_button_with_circle(circ)

    def delete_last_selected_circle(self):
        viz = self.visualizer
        if not viz or not viz.last_selected_circle:
            return

        circle = viz.last_selected_circle

        if circle in viz.circles:
            viz.circles.remove(circle)

        connections_to_remove = []
        for i, (c1, c2, line) in enumerate(viz.connection_data):
            if c1 is circle or c2 is circle:
                connections_to_remove.append(i)

        for i in reversed(connections_to_remove):
            c1, c2, line = viz.connection_data.pop(i)
            viz.canvas.before.remove(line)
            if line in viz.all_connections:
                viz.all_connections.remove(line)

        packets_to_remove = []
        for packet in viz.packets:
            if packet['start_circle'] is circle or packet['target_circle'] is circle:
                packets_to_remove.append(packet)

        for packet in packets_to_remove:
            if packet.get('color_instruction') in viz.canvas.children:
                viz.canvas.remove(packet.get('color_instruction'))
            if packet.get('graphic') in viz.canvas.children:
                viz.canvas.remove(packet.get('graphic'))
            viz.packets.remove(packet)

        if 'rect' in circle and circle.get('rect') in viz.canvas.after.children:
            if circle.get('color_instruction') in viz.canvas.after.children:
                viz.canvas.after.remove(circle['color_instruction'])
            viz.canvas.after.remove(circle['rect'])

        if hasattr(viz, '_update_selection_rect'):
            viz._update_selection_rect(None)

        viz.last_selected_circle = None

        if viz._current_dup and viz._current_dup.source_circle is circle:
            if hasattr(viz._current_dup, '_anim_event'):
                viz._current_dup._anim_event.cancel()
            viz._dup_parent.remove_widget(viz._current_dup)
            viz._current_dup = None

    def sync_packet_buttons(self, circle):
        if circle is None:
            self.button_a.toggled = False
            self.button_b.toggled = False
            return

        self.button_a.toggled = circle.get('packet_state_a', False)
        self.button_b.toggled = circle.get('packet_state_b', False)


class AnimatedImage(ButtonBehavior, Image):
    def __init__(self, frames, fps=30, **kwargs):
        super().__init__(**kwargs)
        self.frames = frames
        self.fps = fps
        self.current_frame = 0
        self.source = self.frames[self.current_frame]
        self.circle_button = os.path.join(os.path.dirname(__file__), "assets", "circle-button.png")
        self.anim_event = None
        self._long_press_event = None
        Clock.schedule_once(self._start_animation)

    def _start_animation(self, dt):
        if not self.anim_event:
            self.anim_event = Clock.schedule_interval(self.next_frame, 1.0 / self.fps)

    def next_frame(self, dt):
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.source = self.frames[self.current_frame]

    def on_parent(self, widget, parent):
        if parent:
            self._start_animation(0)
        else:
            if self.anim_event:
                self.anim_event.cancel()
                self.anim_event = None

    def _do_long_press(self, dt):

        Logger.info("AnimatedImage: _do_long_press fired")
        self._long_press_event = None
        if hasattr(self.parent, 'on_long_press'):
            self.parent.on_long_press(self)

    def on_press(self):
        self._long_press_event = Clock.schedule_once(self._do_long_press, 0.5)

        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None
        self.source = self.circle_button

    def on_release(self):
        self.source = self.frames[self.current_frame]
        self._start_animation(0)

        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            if hasattr(self.parent, 'on_short_press'):
                self.parent.on_short_press(self)

class MidiChannelSelector(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (240, 188)
        self.size_hint = (None, None)
        self.pos_hint = {'x': 202/500, 'y': 45/400}

        self.global_btn = ImageButton(
            "assets/flat_button_grey.png",
            "assets/flat_button_grey_pressed.png",
            color=(1, 0.1, 0.2, 1),
            size_hint=(None, None),
            size=(95, 95),
            pos=(1606,  79)
        )
        self.add_widget(self.global_btn)

        self.btn_label = Label(
            text="GLBL\nCH.",
            font_size='28px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(95, 95),
            pos=(1606,  79)
        )
        self.add_widget(self.btn_label)

        self.channel_image = Image(
            source="assets/shape_1.png",
            size_hint=(None, None),
            size=(80, 80),
            pos=(1767,  88)
        )
        self.add_widget(self.channel_image)

        self.current_channel = 1

    def on_parent(self, widget, parent):
        if parent and parent.children[0] != self:
            parent.remove_widget(self)


    def on_short_press(self, *args):
        self.current_channel = (self.current_channel % 16) + 1
        self.channel_image.source = f"assets/shape_{self.current_channel}.png"
        midi_manager.MIDI_CHANNEL = self.current_channel

    def on_long_press(self, *args):
        Logger.info("MidiChannelSelector: on_long_press fired")
        if platform != 'android':
            Logger.info("MIDI Host/Client toggle is only available on Android.")
            return

        viz = getattr(self.parent, 'visualizer', None)

        if not viz or not hasattr(viz, 'android_midi') or not viz.android_midi:
            Logger.warning("AndroidMidi backend NOT FOUND or is None.")
            return

        Logger.info("AndroidMidi backend found, toggling mode.")
        android_midi = viz.android_midi

        try:
            current_mode = getattr(android_midi, 'connection_mode', 'client')

            if current_mode == 'client':
                new_mode = 'host'
                Logger.info(f"MidiChannelSelector: Toggling mode to '{new_mode}'")
                android_midi.set_connection_mode(new_mode)

                def scan_for_hosts(dt):
                    Logger.info("MidiChannelSelector: Delayed scan for hosts...")
                    host_devices = android_midi.get_host_devices()
                    popup = MidiDevicePopup(
                        devices_list=host_devices,
                        android_midi_ref=android_midi
                    )
                    popup.open()

                Clock.schedule_once(scan_for_hosts, 0.1)
                self.global_btn.color = (0.7, 1, 0.7, 1) # Green tint feedback

            else:
                new_mode = 'client'
                Logger.info(f"MidiChannelSelector: Toggling mode to '{new_mode}'")
                android_midi.set_connection_mode(new_mode)
                android_midi.open_output()
                self.global_btn.color = (1, 1, 1, 1) # Reset color

        except Exception as e:
            Logger.error(f"Failed to toggle MIDI mode: {e}")


class CircleMidiChannelSelector(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (240, 188)
        self.size_hint = (None, None)
        self.pos_hint = {'x': 182/429, 'y': 169/400}

        self.local_btn = ImageButton(
            "assets/flat_button_grey.png",
            "assets/flat_button_grey_pressed.png",
            color=(0.6, 0.2, 0.5, 0.7),
            size_hint=(None, None),
            size=(95, 95),
            pos=(1606,  224)
        )
        self.add_widget(self.local_btn)

        self.btn_label = Label(
            text="NODE\nCH.",
            font_size='28px',
            bold=True,
            halign='center',
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(95, 95),
            pos=(1606,  225)
        )
        self.add_widget(self.btn_label)

        self.channel_image = Image(
            source="assets/shape_1.png",
            size_hint=(None, None),
            size=(80, 80),
            pos=(1767,  230),
            color=(1, 1, 1, 0.8)
        )
        self.add_widget(self.channel_image)

        self.current_channel = 1

    def on_parent(self, widget, parent):
        if parent and parent.children[0] != self:
            parent.remove_widget(self)

    def on_short_press(self, *args):
        self.current_channel = (self.current_channel % 16) + 1
        self.channel_image.source = f"assets/shape_{self.current_channel}.png"

        viz = getattr(self.parent, 'visualizer', None)
        if viz:
            if getattr(viz, 'last_selected_circle', None):
                viz.last_selected_circle['midi_channel'] = self.current_channel
                if hasattr(viz, 'update_circle_color'):
                    viz.update_circle_color(viz.last_selected_circle)
            else:
                import midimesh.main.main_canvas.midi_manager as midi_manager
                midi_manager.MIDI_CHANNEL = self.current_channel

    def on_long_press(self, *args):
        Logger.info("CircleMidiChannelSelector: Long press detected (no action assigned).")


class ImageButton(ButtonBehavior, Image):
    def __init__(self, normal_source, down_source, **kwargs):
        super().__init__(**kwargs)
        self.normal_source = normal_source
        self.down_source = down_source
        self.source = self.normal_source
        self._long_press_event = None

    def _do_long_press(self, dt):
        self._long_press_event = None
        if hasattr(self.parent, 'on_long_press'):
            self.parent.on_long_press(self)

    def on_press(self):
        self._long_press_event = Clock.schedule_once(self._do_long_press, 0.5)
        self.source = self.down_source

    def on_release(self):
        self.source = self.normal_source

        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
            if hasattr(self.parent, 'on_short_press'):
                self.parent.on_short_press(self)

class NodePanel(App):
    def build(self):
        return MiscControls(visualizer=None)

if __name__ == '__main__':
    NodePanel().run()
