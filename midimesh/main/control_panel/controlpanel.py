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

import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find


from .nodes import ControlNode
from .connections import ControlConnection



class ControlPanel(FloatLayout):
    packet_speed = NumericProperty(0.5)
    packet_life = NumericProperty(5000)
    node_speed_multiplier = NumericProperty(0.0005)
    max_connection_distance = NumericProperty(10)
    max_connections_per_node = NumericProperty(7)



    def __init__(self, visualizer, **kwargs):
        super().__init__(**kwargs)
        self.visualizer = visualizer
        self.nodes = []
        self.connections = []
        self.packets = []
        self.control_nodes = []
        self.distance_indicators = {}
        self.size_hint = (None, None)
        self.size = (500, 500)
        self.pos = (20, 20)
        self._moving_node_timer = 0.0

        # 0: Packet Speed (40%)
        # 1: Packet Life (100%)
        # 2: Node Speed (50%)
        # 3: Max Connections (3 connections -> approx 40% of range 1-6)
        # 4: Max Distance (30%)
        self.slider_ratios = [0.4, 1.0, 0.5, 0.4, 0.4]


        self.pending_packet_speed = self.packet_speed
        self._moving_node_spawn_interval = random.uniform(1.0, 3.0)
        self.horizontal_start = 40
        self.vertical_start = -55
        self._cache_textures()
        MAX_POOL_SIZE = 30
        self.packet_pool = []
        self.moving_node_pool = []

        with self.canvas.before:
            Color(1.0, 1.0, 1.0, 1.0)
            self.fill_rect = Rectangle(
                texture=self.bg_texture,
                pos=(self.x - 2, self.y - 2),
                size=(self.width + 4, self.height + 4)
            )

            for _ in range(MAX_POOL_SIZE):
                p_color = Color(1, 1, 1, 0)
                p_graphic = Rectangle(texture=self.packet_texture_small, size=(10, 10), pos=(-100, -100))
                self.packet_pool.append({'graphic': p_graphic, 'color': p_color, 'in_use': False})

                # Pool for moving nodes
                n_color = Color(1, 1, 1, 0)
                n_graphic = Rectangle(texture=self.moving_node_texture, size=(80, 80), pos=(-100, -100))
                self.moving_node_pool.append({'graphic': n_graphic, 'color': n_color, 'in_use': False})

        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            self.border = Line(rectangle=(
                self.x - 2, self.y - 2,
                self.width + 4, self.height + 4
            ), width=1.5)

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.static_node_visuals = []
        self._preallocate_static_nodes()
        self.create_control_nodes()
        self.bind(pos=self.update_node_positions, size=self.update_node_positions)

        for i in range(len(self.slider_ratios)):
            self.update_control_value(i)

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.disabled:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.disabled:
            return False
        return super().on_touch_up(touch)

    def _cache_textures(self):
        try:
            self.static_node_texture = CoreImage(resource_find("assets/node-02.png")).texture
            self.packet_texture_small = CoreImage(resource_find("assets/packet.png")).texture
            self.packet_texture_large = CoreImage(resource_find("assets/packet.png")).texture
            self.moving_node_texture = CoreImage(resource_find("assets/node-02.png")).texture
            self.bg_texture = CoreImage(resource_find("assets/control_panel_bg.png")).texture
        except Exception as e:
            print(f"Error loading textures: {e}")
            self.static_node_texture = None
            self.packet_texture_small = None
            self.packet_texture_large = None
            self.moving_node_texture = None
            self.bg_texture = None


    def _preallocate_static_nodes(self):
        MAX_CONN_NODES = 7
        with self.canvas.before:
            Color(1, 1, 1, 1)
            for _ in range(MAX_CONN_NODES):
                rect = Rectangle(
                    texture=self.static_node_texture,
                    size=(0, 0)
                )
                self.static_node_visuals.append(rect)

    def create_or_update_distance_indicator(self, index, base_node, control_node):
        bar_height = base_node.height * 0.8
        if index not in self.distance_indicators:
            with self.canvas.before:
                Color(0.5, 0.5, 0.8, 1.0)
                dashed_line = Line(width=1, dash_length=5, dash_offset=5)
                left_bar = Line(width=2)
                right_bar = Line(width=2)
            self.distance_indicators[index] = {
                'dashed_line': dashed_line, 'left_bar': left_bar, 'right_bar': right_bar
            }

        indicator = self.distance_indicators[index]
        left_x, left_y1, left_y2 = base_node.right, base_node.center_y - bar_height / 2, base_node.center_y + bar_height / 2
        indicator['left_bar'].points = [left_x + 2, left_y1, left_x + 2, left_y2]
        right_x, right_y1, right_y2 = control_node.x, control_node.center_y - bar_height / 2, control_node.center_y + bar_height / 2
        indicator['right_bar'].points = [right_x - 2, right_y1, right_x - 2, right_y2]
        indicator['dashed_line'].points = [base_node.center_x, base_node.center_y, control_node.center_x, control_node.center_y]

    def remove_distance_indicator(self, index):
        if index in self.distance_indicators:
            indicator = self.distance_indicators.pop(index)
            for key in ['dashed_line', 'left_bar', 'right_bar']:
                self.canvas.before.remove(indicator[key])

    def create_control_nodes(self):
        for node in self.nodes:
            self.remove_widget(node)
        self.nodes.clear()
        self.connections.clear()
        num_controls = 5
        remaining_height = self.height - self.vertical_start + 20
        vertical_spacing = remaining_height / (num_controls + 1)

        max_dist = self.width * 0.6

        for i in range(num_controls):
            x_pos = self.horizontal_start
            y_pos = self.vertical_start + (vertical_spacing * (i + 1))

            base_node = ControlNode(self, i, is_base=True, pos=(x_pos, y_pos))

            initial_ratio = self.slider_ratios[i]
            start_offset = 76
            control_x = x_pos + start_offset + (max_dist * initial_ratio)

            control_node = ControlNode(self, i, is_base=False, pos=(control_x, y_pos))

            connection = ControlConnection(base_node, control_node)
            self.nodes.append(base_node)
            self.control_nodes.append(control_node)
            self.connections.append(connection)
            self.add_widget(connection)
            self.add_widget(base_node)
            self.add_widget(control_node)
            self._update_event = Clock.schedule_interval(self.update, 1/60)

    def on_parent(self, instance, parent):
        if parent is None:
            if hasattr(self, '_update_event') and self._update_event:
                self._update_event.cancel()
                self._update_event = None

    def update_node_positions(self, *args):
        num_controls = len(self.nodes)
        if num_controls == 0: return
        vertical_spacing = self.height / (num_controls + 1)

        max_dist = self.width * 0.6

        for i, node in enumerate(self.nodes):
            node.default_x = self.horizontal_start - node.width / 2
            node.default_y = vertical_spacing * (i + 1) - node.height / 2
            if not node.dragging: node.pos = (node.default_x, node.default_y)

        for i, node in enumerate(self.control_nodes):
            base_node = self.nodes[i]

            current_ratio = self.slider_ratios[i]
            target_x = base_node.x + base_node.width + (max_dist * current_ratio)

            if not node.dragging:
                node.pos = (target_x, base_node.default_y)

    def create_multiple_nodes_effect(self, base_node, control_node):
        num_nodes = self.max_connections_per_node
        node_size = 80
        is_extended = control_node.x > base_node.x + base_node.width

        start_x = base_node.center_x
        start_y = base_node.center_y
        end_x = control_node.center_x
        end_y = control_node.center_y

        for i, rect in enumerate(self.static_node_visuals):
            if i < num_nodes and is_extended:
                progress = (i + 1) / (num_nodes + 1)
                node_x = start_x + (end_x - start_x) * progress - node_size / 2
                node_y = start_y + (end_y - start_y) * progress - node_size / 2
                rect.pos = (node_x, node_y)
                rect.size = (node_size, node_size)
            else:
                rect.size = (0, 0)

    def update_control_value(self, index):
        if index < len(self.control_nodes):
            control_node = self.control_nodes[index]
            base_node = self.nodes[index]
            max_distance = self.width * 0.6
            distance = control_node.x - (base_node.x + base_node.width)
            normalized_value = max(0, min(distance / max_distance, 1))

            self.slider_ratios[index] = normalized_value

            if index == 0:
                self.pending_packet_speed = 0 + normalized_value * 1000
            elif index == 1:
                self.visualizer.packet_life = 5 + normalized_value * 360
            elif index == 2:
                self.visualizer.node_speed_multiplier = 0.0 + normalized_value * 2.0
            elif index == 3:
                self.visualizer.max_connections_per_node = 1 + int(normalized_value * 5)
            elif index == 4:
                self.visualizer.max_connection_distance = 100 + normalized_value * 700

            for prop in ['packet_speed', 'packet_life', 'node_speed_multiplier',
                         'max_connection_distance', 'max_connections_per_node']:
                setattr(self, prop, getattr(self.visualizer, prop))


    def create_packet_effect(self, start_node, end_node):
        for packet_obj in self.packet_pool:
            if not packet_obj['in_use']:
                packet_obj['in_use'] = True
                packet_obj['color'].rgba = (1, 1, 1, 1)
                packet_obj['graphic'].pos = start_node.pos
                packet_obj['graphic'].size = (10, 10)

                speed = 0.125
                self.packets.append({
                    'start_node': start_node, 'end_node': end_node, 'progress': 0.0,
                    'graphic': packet_obj['graphic'],
                    'color': packet_obj['color'],
                    'pool_obj': packet_obj,
                    'speed': speed, 'fade': False, 'size': (10, 10)
                })
                return

    def create_fading_packet(self, start_node, end_node):
        if not self.packet_texture_large: return
        with self.canvas.before:
            packet_color = Color(1, 0, 0, 1)
            packet_graphic = Rectangle(
                texture=self.packet_texture_large, pos=start_node.pos, size=(12, 12)
            )
        self.packets.append({
            'start_node': start_node, 'end_node': end_node, 'progress': 0.0,
            'graphic': packet_graphic, 'color': packet_color, 'fade': True,
            'size': (12, 12)
        })

    def create_moving_node_effect(self, base_node, control_node, dt):
        self._moving_node_timer += dt

        while self._moving_node_timer >= self._moving_node_spawn_interval:
            self._moving_node_timer -= self._moving_node_spawn_interval

            if not self.moving_node_texture: continue

            for node_obj in self.moving_node_pool:
                if not node_obj.get('in_use'):
                    node_obj['in_use'] = True
                    node_size = 80

                    node_obj['color'].rgba = (1, 1, 1, 1)
                    node_obj['graphic'].pos = (base_node.x + (base_node.width - node_size) / 2,
                                             base_node.y + (base_node.height - node_size) / 2)
                    node_obj['graphic'].size = (node_size, node_size)

                    speed = 0.07 + (self.node_speed_multiplier / 16.0) * 0.3
                    self.packets.append({
                        'start_node': base_node, 'end_node': control_node, 'progress': 0.0,
                        'graphic': node_obj['graphic'],
                        'color': node_obj['color'],
                        'pool_obj': node_obj,
                        'speed': speed,
                        'size': (node_size, node_size)
                    })
                    break

        self._moving_node_spawn_interval = random.uniform(0.8, 3.0)

    def update(self, dt):
        if self.control_nodes:
            speed_control_node = self.control_nodes[0]
            if not speed_control_node.dragging and self.visualizer.packet_speed != self.pending_packet_speed:
                self.visualizer.update_tempo(self.pending_packet_speed)
                self.packet_speed = self.pending_packet_speed

        for i, (base_node, control_node) in enumerate(zip(self.nodes, self.control_nodes)):
            if i == 4:
                if control_node.active:
                    self.create_or_update_distance_indicator(i, base_node, control_node)
                else:
                    self.remove_distance_indicator(i)

            if i == 0:
                if random.random() < 0.008:
                    self.create_packet_effect(base_node, control_node)
            elif i == 1:
                if random.random() < 0.025:
                    self.create_fading_packet(base_node, control_node)
            elif i == 2:
                self.create_moving_node_effect(base_node, control_node, dt)
            elif i == 3:
                self.create_multiple_nodes_effect(base_node, control_node)

        for packet in self.packets[:]:
            speed_multiplier = 0.25 if packet.get('fade') else 3 * packet.get('speed', 1.5)
            packet['progress'] += dt * speed_multiplier

            if packet['progress'] >= 1.0:
                pool_obj = packet.get('pool_obj')
                if pool_obj:
                    pool_obj['graphic'].pos = (-100, -100)
                    pool_obj['color'].a = 0
                    pool_obj['in_use'] = False
                else:
                    if packet.get('color') in self.canvas.before.children:
                        self.canvas.before.remove(packet['color'])
                    if packet.get('graphic') in self.canvas.before.children:
                        self.canvas.before.remove(packet['graphic'])

                self.packets.remove(packet)
                continue

            start_x, start_y = packet['start_node'].center
            end_x, end_y = packet['end_node'].center
            size = packet['size']
            cx = start_x + (end_x - start_x) * packet['progress']
            cy = start_y + (end_y - start_y) * packet['progress']
            packet['graphic'].pos = (cx - size[0] / 2, cy - size[1] / 2)

            if packet.get('fade') and packet['color']:
                life_factor = self.packet_life / 10000
                fade_start = 0.4 + life_factor * 0.005
                progress = packet['progress']
                if progress > fade_start:
                    packet['color'].a = max(0.0, 0.7 - (progress - fade_start) / (1 - fade_start))


    def update_graphics(self, *args):
        if hasattr(self, 'fill_rect'):
            self.fill_rect.pos = (self.x - 2, self.y - 2)
            self.fill_rect.size = (self.width + 4, self.height + 4)
        if hasattr(self, 'border'):
            self.border.rectangle = (self.x-2, self.y-2, self.width+4, self.height+4)
