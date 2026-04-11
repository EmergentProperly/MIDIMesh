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
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import os
import sys


try:
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
except NameError:
    assets_dir = os.path.join(os.path.abspath(os.getcwd()), 'assets')


VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080


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
        if (abs(getattr(content, 'scale', 1.0) - scale) > epsilon or
            abs(content.pos[0] - new_pos_x) > epsilon or
            abs(content.pos[1] - new_pos_y) > epsilon):

            if hasattr(content, 'scale'):
                content.scale = scale
            content.pos = (new_pos_x, new_pos_y)


class HelpWorld(FloatLayout):
    def __init__(self, app_switcher=None, **kwargs):
        super().__init__(**kwargs)
        self.app_switcher = app_switcher

        self.size_hint = (None, None)
        self.size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.menu_buttons = []
        self.popup_elements = []

        self.bg_image = Image(
            source='assets/help_bg.png',
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            pos=(0, 0),
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.bg_image)

        self.btn_play = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(120, 960),
            on_release=partial(
                self.show_generic_help,
                "PLAY / PAUSE:\n\nShort-press triggers nodes with 'PLAY SPAWN' activated.\n\nLong-press activates MIDI clock pulse (tied to grid timing).",
                (130, 900),
                155,
                (260, 360)
            )
        )
        self.add_widget(self.btn_play)
        self.menu_buttons.append(self.btn_play)

        self.btn_load_save = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(120, 800),
            on_release=partial(
                self.show_generic_help,
                "LOAD / SAVE:\n\nSave button: Saves your current configuration.\n\nLoad Button: Short-press brings up the LOAD MENU.\n"
                "Long-press loads the next sequential save into memory.\nReleasing long-press switches to the loaded save on \nthe next step.\n"
                "WARNING: long-press loading is currently experimental.\nHandle with care.",
                (130, 790),
                180,
                (260, 320)
            )
        )
        self.add_widget(self.btn_load_save)
        self.menu_buttons.append(self.btn_load_save)

        self.btn_help = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(120, 600),
            on_release=partial(
                self.show_generic_help,
                "HELP MODE:\n\nYou are currently here.\n\nTap on question marks to see more info.\n\nTap 'DONE' to exit help mode.",
                (130, 580),
                180,
                (260, 140)
            )
        )
        self.add_widget(self.btn_help)
        self.menu_buttons.append(self.btn_help)

        self.btn_conn_length = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(225, 410),
            on_release=partial(
                self.show_generic_help,
                "CONNECTION LENGTH:\n\nSets maximum distance between nodes for\nestablishing a connection.\n\n""Can be overidden with the 'LOCK CONNECTIONS'\nbutton and multi-touch"
                "\n\nSee 'LOCK CONNECTIONS' for more information.",
                (300, 420),
                200,
                (400, 400)
            )
        )
        self.add_widget(self.btn_conn_length)
        self.menu_buttons.append(self.btn_conn_length)

        self.btn_max_conn = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(225, 315),
            on_release=partial(
                self.show_generic_help,
                "MAX CONNECTIONS:\n\nLimits the number of connections per node.",
                (300, 330),
                -155,
                (400, 340)
            )
        )
        self.add_widget(self.btn_max_conn)
        self.menu_buttons.append(self.btn_max_conn)

        self.btn_node_speed = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(255, 218),
            on_release=partial(
                self.show_generic_help,
                "NODE SPEED:\n\nControls how fast nodes move when they are\nnot locked to the grid.",
                (305, 240),
                -155,
                (400, 260)
            )
        )
        self.add_widget(self.btn_node_speed)
        self.menu_buttons.append(self.btn_node_speed)

        self.btn_packet_life = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(404, 123),
            on_release=partial(
                self.show_generic_help,
                "PACKET LIFE:\n\nDetermines how long a packet survives before expiring.",
                (460, 143),
                -135,
                (400, 240)
            )
        )
        self.add_widget(self.btn_packet_life)
        self.menu_buttons.append(self.btn_packet_life)

        self.btn_packet_speed = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(225, 26),
            on_release=partial(
                self.show_generic_help,
                "PACKET SPEED:\n\nControls how fast packets travel along connections.\n\nDetermines BPM for patterns on the grid",
                (280, 65),
                -135,
                (300, 140)
            )
        )
        self.add_widget(self.btn_packet_speed)
        self.menu_buttons.append(self.btn_packet_speed)

        self.btn_conn = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(885, 926),
            on_release=partial(
                self.show_generic_help,
                "CONNECTIONS:\n\nThe connection between nodes on which packets can travel.\n\nDouble-tap a connection to remove it."
                "\n\nNOTE: Unlocked nodes may reconnect automatically if in\nrange.",
                (885, 770),
                90,
                (160, 200)
            )
        )
        self.add_widget(self.btn_conn)
        self.menu_buttons.append(self.btn_conn)

        self.btn_packet = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(555, 866),
            on_release=partial(
                self.show_generic_help,
                "PACKET:\n\nEssentially a playhead.\n\nWhen a packet arrives at a node, it triggers the saved\nMIDI Note data tied to that node."
                "\n\nWARNING: When the system becomes overloaded with\npackets, the system will dismantle itself.",
                (528, 818),
                90,
                (260, 250)
            )
        )
        self.add_widget(self.btn_packet)
        self.menu_buttons.append(self.btn_packet)

        self.btn_node = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(925, 666),
            on_release=partial(
                self.show_generic_help,
                "NODE:\n\nCreated by playing a note. Stores MIDI note data (octave,\nnote length, velocity...). Double-tap accesses node timing."
                "\n\nThe node's colour reflects the MIDI Channel the\nnode is set to."
                "\n\nWARNING: When the system becomes overloaded with\nnodes, the system will dismantle itself.",
                (810, 540),
                90,
                (160, 10)
            )
        )
        self.add_widget(self.btn_node)
        self.menu_buttons.append(self.btn_node)

        self.group_node = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(540, 666),
            on_release=partial(
                self.show_generic_help,
                "GROUP NODE:\n\nStack nodes on the grid and double-tap them to create\na group node.\n\n"
                "Additional double-taps access node timing.",
                (450, 540),
                90,
                (160, 10)
            )
        )
        self.add_widget(self.group_node)
        self.menu_buttons.append(self.group_node)

        self.btn_keys = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(625, 340),
            on_release=partial(
                self.show_generic_help,
                "KEYBOARD:\n\nPlay notes to create nodes.\n\nTop red button: Octave up.\n\nBottom red button: Octave down."
                "\n\nSlider controls note velocity.",
                (860, 350),
                -90,
                (160, 440)
            )
        )
        self.add_widget(self.btn_keys)
        self.menu_buttons.append(self.btn_keys)

        self.btn_goodies = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1700, 940),
            on_release=partial(
                self.show_generic_help,
                "SETTINGS (etc) and RESET:\n\nShort-press: access extra features and settings."
                "\n\nLong-press: arms the 'HARD RESET', an additional\nshort-press "
                "resets the system.",
                (1645, 880),
                35,
                (100, 400)
            )
        )
        self.add_widget(self.btn_goodies)
        self.menu_buttons.append(self.btn_goodies)

        self.btn_kill_pkts = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1710, 815),
            on_release=partial(
                self.show_generic_help,
                "KILL PACKETS:\n\nInstantly removes all active packets from the system.\n\n"
                "NOTE: Nodes with PLAY SPAWN activated will\nimmediately spawn new packets",
                (1655, 755),
                35,
                (100, 300)
            )
        )
        self.add_widget(self.btn_kill_pkts)
        self.menu_buttons.append(self.btn_kill_pkts)

        self.btn_hide = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1710, 710),
            on_release=partial(
                self.show_generic_help,
                "HIDE UI:\n\nHides the main controls.",
                (1645, 660),
                20,
                (100, 200)
            )
        )
        self.add_widget(self.btn_hide)
        self.menu_buttons.append(self.btn_hide)

        self.btn_duplicate = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1445, 360),
            on_release=partial(
                self.show_generic_help,
                "SELECTED NODE:\n\nTap to trigger packets.\n\nLong-press to lock the selected node to the grid.\n\nLong-press again to unlock",
                (1345, 400),
                -35,
                (0, 480)
            )
        )
        self.add_widget(self.btn_duplicate)
        self.menu_buttons.append(self.btn_duplicate)

        self.btn_packet_logic = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1645, 420),
            on_release=self.show_packet_logic_help
        )
        self.add_widget(self.btn_packet_logic)
        self.menu_buttons.append(self.btn_packet_logic)

        self.btn_conn_logic = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1757, 365),
            on_release=partial(
                self.show_generic_help,
                "LOCK CONNECTIONS:\n\nWhen toggled, the selected node will not establish any\nfurther connections, and any connected nodes will remain\nconnected (unless manually disconnected).\n\n"
                "If toggled, press and hold the node, and then press another\ntoggled node to connect them (this bypasses\nCONNECTION LENGTH). Use Ctrl + click on toggled\nnodes to connect them on PC.",
                (1637, 405),
                -35,
                (80, 440)
            )
        )
        self.add_widget(self.btn_conn_logic)
        self.menu_buttons.append(self.btn_conn_logic)

        self.btn_midi = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1685, 145),
            on_release=partial(
                self.show_generic_help,
                "MIDI:\n\nNODE CH. (node Channel) determines the MIDI channel of\nthe selected node.\n\nGLBL CH. (Global Channel) determines the default channel\nfor newly created nodes. Long-press GLBL CH. to "
                "access\nconnected MIDI devices.\n\nNodes reflect their channel's colour.",
                (1495, 268),
                -40,
                (40, 360)
            )
        )
        self.add_widget(self.btn_midi)
        self.menu_buttons.append(self.btn_midi)

        self.btn_del = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1445, 75),
            on_release=partial(
                self.show_generic_help,
                "DELETE SELECTED NODE:\n\nPress once to arm, press again to delete.",
                (1385, 150),
                -70,
                (40, 240)
            )
        )
        self.add_widget(self.btn_del)
        self.menu_buttons.append(self.btn_del)

        self.btn_move = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1445, 215),
            on_release=partial(
                self.show_generic_help,
                "ENABLE/DISABLE DRIFT:\n\nStops nodes from drifting (without locking them to the\ngrid), allowing for looser pattern building and unusual\nsyncopation.",
                (1385, 295),
                -70,
                (40, 400)
            )
        )
        self.add_widget(self.btn_move)
        self.menu_buttons.append(self.btn_move)

        self.btn_grid = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1445, 715),
            on_release=partial(
                self.show_generic_help,
                "GRID:\n\nEnables time-based pattern building, and determines\nMIDI CLOCK SEND. Nodes can be locked to the grid.\n\n"
                "Pinch-zoom for closer scrutiny (mouse wheel if on PC)",
                (1318, 555),
                90,
                (100, 0)
            )
        )
        self.add_widget(self.btn_grid)
        self.menu_buttons.append(self.btn_grid)

        self.btn_noteoff = Button(
            text="?",
            font_size=60,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),
            background_normal='',
            size_hint=(None, None),
            size=(100, 100),
            pos=(1710, 600),
            on_release=partial(
                self.show_generic_help,
                "NOTE OFF (A.K.A MIDI PANIC):\n\nSends a global note off message. Useful as a playable tool\nand for killing stuck notes.",
                (1650, 580),
                0,
                (100, 300)
            )
        )
        self.add_widget(self.btn_noteoff)
        self.menu_buttons.append(self.btn_noteoff)


        self.btn_done = Button(
            text="DONE",
            font_size=40,
            font_name=ANIM_FONTS[0],
            color=(1, 1, 1, 1),
            background_normal='assets/messy_button_02.png',
            background_down='assets/messy_button_02.png',
            border=(0, 0, 0, 0),
            size_hint=(None, None),
            size=(300, 120),
            pos=(820, 400),
            on_release=self.close_help
        )
        self.add_widget(self.btn_done)
        self.menu_buttons.append(self.btn_done)

        self.anim_font_idx = 0
        self.anim_arrow_idx = 0
        self.anim_event = Clock.schedule_interval(self._animate_step, 0.125)
        self.popup_bg = None
        self.popup_label = None
        self.img_arrow = None

    def _update_rotation_center(self, instance, value):
        if hasattr(self, 'rot') and self.rot:
            self.rot.origin = instance.center

    def show_packet_logic_help(self, instance):

        for btn in self.menu_buttons:
            btn.opacity = 0
            btn.disabled = True

        self.popup_bg = Button(
            background_color=(0, 0, 0, 0.95),
            background_normal='',
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            pos=(0, 0),
            on_release=self.dismiss_popup
        )
        self.add_widget(self.popup_bg)
        self.popup_elements.append(self.popup_bg)

        logic_items = [
            (
                'assets/help/play_spawn.png',
                "PLAY SPAWN: When 'PLAY' is pressed, the node will spawn a packet. The node will respawn a packet if all packets in the system expire."
            ),
            (
                'assets/help/consume_packets.png',
                "CONSUME PACKETS: The node will consume any packet upon arrival. The packet is effectively removed from the system."
            ),
            (
                'assets/help/pass_and_spawn.png',
                "PASS AND SPAWN: The node will pass packets along to the next node. If the next node consumes packets, the 'PASS AND SPAWN' node will spawn a new packet upon consumption."
            ),
            (
                'assets/help/pass_no_spawn.png',
                "PASS (NO SPAWN): The node will pass the packet along to the next node. If the next node consumes packets, 'PASS (NO SPAWN)' nodes will NOT spawn a new packet upon consumption."
            ),
            (
                'assets/help/packet_spawn.png',
                "PACKET SPAWN: The node will spawn a second packet when a packet arrives at the node. WARNING: this can quickly overload the system (triggering self-destruct). For stability, ensure there are enough nodes with 'CONSUME PACKETS' enabled. Press 'KILL PKTS' in an emergency."
            ),
        ]

        start_y = 960
        row_height = 220

        for i, (img_path, txt) in enumerate(logic_items):
            current_y = start_y - (i * row_height)

            img = Image(
                source=img_path,
                size_hint=(None, None),
                size=(100, 100),
                pos=(50, current_y),
                allow_stretch=True
            )
            self.add_widget(img)
            self.popup_elements.append(img)

            lbl = Label(
                text=txt,
                font_name=ANIM_FONTS[0],
                font_size=42,
                color=(1, 1, 1, 1),
                text_size=(1700, None),
                halign='left',
                valign='middle',
                size_hint=(None, None),
                size=(1700, 100),
                pos=(180, current_y)
            )
            self.add_widget(lbl)
            self.popup_elements.append(lbl)
            
    def on_touch_down(self, touch):

        if self.popup_elements:          
            self.dismiss_popup(None)     
            return True                  
        return super().on_touch_down(touch)

    def show_generic_help(self, text, arrow_pos, arrow_angle, popup_pos, instance):
        for btn in self.menu_buttons:
            btn.opacity = 0
            btn.disabled = True

        self.img_arrow = Image(
            source=ANIM_ARROWS[0],
            size_hint=(None, None),
            size=(150, 150),
            pos=arrow_pos,
            allow_stretch=True
        )
        with self.img_arrow.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=arrow_angle, origin=self.img_arrow.center)
        with self.img_arrow.canvas.after:
            PopMatrix()
        self.img_arrow.bind(pos=self._update_rotation_center,
                           size=self._update_rotation_center)

        self.popup_bg = Button(
            background_color=(0, 0, 0.1, 1),
            background_normal='',
            size_hint=(None, None),
            size=(1600, 600),
            pos=popup_pos,
            on_release=self.dismiss_popup
        )
        with self.popup_bg.canvas.after:
            Color(1, 1, 1, 1)
            Line(rectangle=(
                self.popup_bg.x + 0.5,
                self.popup_bg.y + 0.5,
                self.popup_bg.width - 1,
                self.popup_bg.height - 1
            ), width=2)

        self.add_widget(self.img_arrow)          
        self.add_widget(self.popup_bg)           
        self.popup_elements.append(self.popup_bg)

        label_pos = (popup_pos[0] + 150, popup_pos[1] + 50)

        self.popup_label = Label(
            text=text,
            font_name=ANIM_FONTS[0],   
            font_size=48,
            halign='left',
            valign='middle',
            size_hint=(None, None),
            size=(1300, 500),
            pos=label_pos
        )
        self.popup_label.bind(size=self.popup_label.setter('text_size'))
        self.add_widget(self.popup_label)
        self.popup_elements.append(self.popup_label)
        self.popup_elements.append(self.img_arrow)

    def dismiss_popup(self, instance):
        for widget in self.popup_elements:
            self.remove_widget(widget)
        self.popup_elements.clear()

        self.popup_bg = None
        self.popup_label = None
        self.img_arrow = None

        for btn in self.menu_buttons:
            btn.opacity = 1
            btn.disabled = False

    def _animate_step(self, dt):

        self.anim_font_idx = (self.anim_font_idx + 1) % len(ANIM_FONTS)
        current_font = ANIM_FONTS[self.anim_font_idx]

        self.anim_arrow_idx = (self.anim_arrow_idx + 1) % len(ANIM_ARROWS)
        current_arrow = ANIM_ARROWS[self.anim_arrow_idx]

        try:
            for btn in self.menu_buttons:
                if hasattr(btn, 'font_name'):
                    btn.font_name = current_font

            if self.img_arrow:
                self.img_arrow.source = current_arrow

        except Exception:
            pass

    def cleanup(self):
        if hasattr(self, 'anim_event') and self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None

    def close_help(self, instance):
        if self.app_switcher:
            self.app_switcher('main_app')
        else:
            app = App.get_running_app()
            if app:
                app.stop()


class HelpApp(App):
    def build(self):
        root = FitLayout()

        self.help_world = HelpWorld()

        from kivy.uix.scatterlayout import ScatterLayout

        container = ScatterLayout(
            size_hint=(None, None),
            size=(VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
            do_rotation=False,
            do_translation=False,
            do_scale=False,
            auto_bring_to_front=False
        )

        container.add_widget(self.help_world)
        root.add_widget(container)

        return root

if __name__ == '__main__':
    HelpApp().run()
