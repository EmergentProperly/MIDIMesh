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

import math
import random
from kivy.graphics import Color, Line

def update_connections(visualizer):

    active_packets_per_connection = {}
    for packet in visualizer.packets:
        connection_id_forward = (id(packet['start_circle']), id(packet['target_circle']))
        connection_id_reverse = (id(packet['target_circle']), id(packet['start_circle']))

        active_packets_per_connection[connection_id_forward] = active_packets_per_connection.get(connection_id_forward, 0) + 1
        active_packets_per_connection[connection_id_reverse] = active_packets_per_connection.get(connection_id_reverse, 0) + 1

    active_connections = set()
    connections_to_remove = []

    for i, (circle1, circle2, connection_line) in enumerate(visualizer.connection_data[:]):
        if circle1 not in visualizer.circles or circle2 not in visualizer.circles:
            connections_to_remove.append(i)
            continue

        x1, y1 = circle1['pos'][0] + circle1['size']/2, circle1['pos'][1] + circle1['size']/2
        x2, y2 = circle2['pos'][0] + circle2['size']/2, circle2['pos'][1] + circle2['size']/2
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        dist_sq = (x2 - x1)**2 + (y2 - y1)**2
        connection_line.points = [x1, y1, x2, y2]

        connection_id = (id(circle1), id(circle2))
        reverse_connection_id = (id(circle2), id(circle1))
        has_active_packets = (active_packets_per_connection.get(connection_id, 0) > 0 or
                              active_packets_per_connection.get(reverse_connection_id, 0) > 0)

        if has_active_packets:
            active_connections.add(connection_id)
            connection_line.width = 1.5
            continue
        elif circle1.get('connection_mode') == 1 or circle2.get('connection_mode') == 1:
            active_connections.add(connection_id)
            continue
        elif dist_sq > visualizer.max_connection_distance**2:
            connections_to_remove.append(i)
        else:
            active_connections.add(connection_id)
            connection_line.width = 1.5
    for i in reversed(connections_to_remove):
        circle1, circle2, connection_line = visualizer.connection_data.pop(i)

        if connection_line in visualizer.canvas.before.children:
            visualizer.canvas.before.remove(connection_line)

        if connection_line in visualizer.all_connections:
            visualizer.all_connections.remove(connection_line)
        visualizer._line_colour_map.pop(connection_line, None)


    active_connection_pairs = set()
    for c1, c2, _ in visualizer.connection_data:
        pair_key = tuple(sorted((id(c1), id(c2))))
        active_connection_pairs.add(pair_key)

    # CPU friendly grid based on max connection length
    cell_size = visualizer.max_connection_distance
    grid = {}
    for circle in visualizer.circles:
        cx = circle['pos'][0] + circle['size'] / 2
        cy = circle['pos'][1] + circle['size'] / 2
        circle['center'] = (cx, cy)

        col = int(cx / cell_size)
        row = int(cy / cell_size)

        if (col, row) not in grid:
            grid[(col, row)] = []
        grid[(col, row)].append(circle)

    connection_counts = {id(c): 0 for c in visualizer.circles}
    for c1, c2, _ in visualizer.connection_data:
        connection_counts[id(c1)] += 1
        connection_counts[id(c2)] += 1

    max_connections = visualizer.max_connections_per_node
    max_dist_sq = visualizer.max_connection_distance**2
    _seen_pairs = set()

    for circle1 in visualizer.circles:
        if connection_counts[id(circle1)] >= max_connections:
            continue

        col = int(circle1['center'][0] / cell_size)
        row = int(circle1['center'][1] / cell_size)

        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                cell_key = (col + c_offset, row + r_offset)
                if cell_key not in grid:
                    continue

                for circle2 in grid[cell_key]:
                    if circle1 is circle2:
                        continue

                    pair_key = tuple(sorted((id(circle1), id(circle2))))
                    if pair_key in _seen_pairs:
                        continue
                    _seen_pairs.add(pair_key)

                    if connection_counts[id(circle2)] >= max_connections:
                        continue

                    x1, y1 = circle1['center']
                    x2, y2 = circle2['center']

                    dist_sq = (x2 - x1)**2 + (y2 - y1)**2

                    # Check squared distance first
                    if dist_sq < max_dist_sq:
                        if pair_key in active_connection_pairs:
                            continue

                        distance = math.sqrt(dist_sq)
                        probability = visualizer.calculate_connection_probability(distance, visualizer.max_connection_distance)

                        if distance < visualizer.max_connection_distance:
                            if pair_key in active_connection_pairs:
                                continue


                        probability = visualizer.calculate_connection_probability(distance, visualizer.max_connection_distance)
                        connection_bonus = 1.0 - (max(connection_counts[id(circle1)], connection_counts[id(circle2)]) / max_connections)
                        probability *= (1.0 + connection_bonus * 0.5)


                        if circle1['connection_mode'] == 1 or circle2['connection_mode'] == 1:
                            continue

                        if random.random() < probability * 0.05:

                            line_width = 1.5

                            connection_line = Line(points=[x1, y1, x2, y2], width=line_width)
                            visualizer.canvas.before.add(connection_line)


                            visualizer.connection_data.append((circle1, circle2, connection_line))

                            visualizer.all_connections.append(connection_line)
                            connection_counts[id(circle1)] += 1
                            connection_counts[id(circle2)] += 1

                            if connection_counts[id(circle1)] >= visualizer.max_connections_per_node:
                                break

    final_connection_pairs = set()
    for c1, c2, _ in visualizer.connection_data:
        final_connection_pairs.add(tuple(sorted((id(c1), id(c2)))))


    alive_packets = []
    packets_to_cleanup = []
    for pkt in visualizer.packets:

        pair_key = tuple(sorted((id(pkt['start_circle']), id(pkt['target_circle']))))
        if pair_key in final_connection_pairs:
            alive_packets.append(pkt)
        else:
            packets_to_cleanup.append(pkt)

    for packet in packets_to_cleanup:
        if packet.get('color_instruction') in visualizer.canvas.children:
            visualizer.canvas.remove(packet.get('color_instruction'))
        if packet.get('graphic') in visualizer.canvas.children:
            visualizer.canvas.remove(packet.get('graphic'))

    visualizer.packets = alive_packets
