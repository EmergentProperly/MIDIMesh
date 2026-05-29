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

import time
import math
import random
from kivy.clock import Clock

def _resolve_next_target(current_node, previous_node, visualizer):
    connected = visualizer.get_connected_circles(current_node)
    if not connected:
        return None

    connected_sorted = sorted(connected, key=lambda c: (c['pos'][0], c['pos'][1]))
    total_connections = len(connected_sorted)

    locked_idx = current_node.get('locked_connection_index', 0)

    if locked_idx > 0 and current_node.get('connection_mode', 0) == 1:
        target_idx = (locked_idx - 1) % total_connections
        return connected_sorted[target_idx]
    else:
        potential = [c for c in connected_sorted if c is not previous_node]
        return random.choice(potential) if potential else connected_sorted[0]

def update_packets(visualizer, dt):
    packets_to_remove = []
    current_time = time.time()

    for packet in visualizer.packets[:]:
        if packet.get('is_fading'):
            packet['fade_timer'] += dt
            progress = packet['fade_timer'] / packet['fade_duration']
            if progress >= 1.0:
                if packet not in packets_to_remove:
                    packets_to_remove.append(packet)
                    visualizer.active_packet_count -= 1
            else:
                packet['color_instruction'].a = 1.0 - progress
            continue

        if current_time - packet['creation_time'] > visualizer.packet_life:
            if packet not in packets_to_remove:
                packets_to_remove.append(packet)
                visualizer.active_packet_count -= 1
            continue

        has_arrived = False
        progress = 0.0
        start_is_locked = packet['start_circle'].get('grid_locked', False)
        target_is_locked = packet['target_circle'].get('grid_locked', False)

        if start_is_locked and target_is_locked:
            if visualizer.master_tick >= packet['arrival_tick']:
                has_arrived = True
                progress = 1.0
            else:
                ticks_elapsed = visualizer.master_tick - packet['start_tick']
                total_progress_in_ticks = ticks_elapsed + visualizer.tick_progress
                if packet['journey_duration_in_ticks'] > 0:
                    progress = total_progress_in_ticks / packet['journey_duration_in_ticks']
        else:
            packet['progress'] += (packet['speed'] * dt) / max(packet['total_distance'], 1e-6)
            progress = packet['progress']
            if progress >= 1.0:
                has_arrived = True

        if has_arrived:
            target_circle = packet['target_circle']
            start_circle = packet['start_circle']

            _cx, _cy = visualizer.get_circle_center(target_circle)
            packet['graphic'].pos = (_cx - 10, _cy - 10)

            tc_a = target_circle.get('packet_state_a', False)
            tc_b = target_circle.get('packet_state_b', False)
            is_target_a_drop_node = tc_a and not tc_b

            sc_a = start_circle.get('packet_state_a', False)
            sc_b = start_circle.get('packet_state_b', False)
            preceding_was_not_respawn_node = not (sc_a and sc_b)

            is_last_packet = visualizer.active_packet_count == 1

            is_play_trigger_node = target_circle.get('play_trigger', False)

            lag = target_circle.get('lag_ticks', 0)
            if lag > 0:
                if 'trigger_tick' not in packet:
                    packet['trigger_tick'] = packet['arrival_tick'] + lag
                if visualizer.master_tick < packet['trigger_tick']:
                    continue

            if (is_play_trigger_node and visualizer.is_playing and is_last_packet and
                    is_target_a_drop_node and preceding_was_not_respawn_node):
                visualizer.trigger_all_play_nodes()

                if packet not in packets_to_remove:
                    packets_to_remove.append(packet)
                    visualizer.active_packet_count -= 1
                continue

            respawn_origin = packet.get('respawn_origin_circle')
            if respawn_origin and is_target_a_drop_node:
                connected_to_origin = visualizer.get_connected_circles(respawn_origin)
                if connected_to_origin:
                    # UPDATED: Use deterministic/locked routing
                    new_target = _resolve_next_target(respawn_origin, target_circle, visualizer)
                    if new_target:
                        visualizer.create_packet(respawn_origin, new_target, current_time)

            notes_to_play = target_circle.get('merged_notes')
            if notes_to_play:
                strum_delay_ms = target_circle.get('strum_delay_ms', 0)
                strum_delay_sec = strum_delay_ms / 1000.0

                if strum_delay_sec <= 0:
                    for note, vel, ch in notes_to_play:
                        visualizer.send_midi_note(note, vel, channel=ch)

                    if target_circle['duration'] > 0:
                        for note, vel, ch in notes_to_play:
                            Clock.schedule_once(
                                lambda dt, n=note, ch=ch:
                                visualizer.send_midi_note(n, 0, True, ch),
                                target_circle['duration']
                            )
                else:
                    for i, (note, vel, ch) in enumerate(notes_to_play):
                        delay_time = i * strum_delay_sec
                        Clock.schedule_once(
                            lambda dt, n=note, v=vel, c=ch:
                            visualizer.send_midi_note(n, v, channel=c),
                            delay_time
                        )
                        if target_circle['duration'] > 0:
                            off_delay_time = delay_time + target_circle['duration']
                            Clock.schedule_once(
                                lambda dt, n=note, c=ch:
                                visualizer.send_midi_note(n, 0, True, c),
                                off_delay_time
                            )

                visualizer.flash_circle(target_circle)
            else:
                visualizer.send_midi_note(target_circle['note'], target_circle['velocity'],
                                          channel=target_circle.get('midi_channel'))
                if target_circle['duration'] > 0:
                    Clock.schedule_once(
                        lambda dt, n=target_circle['note'], ch=target_circle.get('midi_channel'):
                        visualizer.send_midi_note(n, 0, True, ch),
                        target_circle['duration']
                    )
                visualizer.flash_circle(target_circle)

            if is_target_a_drop_node:
                if packet not in packets_to_remove:
                    packets_to_remove.append(packet)
                    visualizer.active_packet_count -= 1
                continue

            if 'respawn_origin_circle' in packet:
                del packet['respawn_origin_circle']

            if not tc_a and tc_b:
                connected = visualizer.get_connected_circles(target_circle)
                if connected:
                    # UPDATED: Use deterministic/locked routing
                    new_target = _resolve_next_target(target_circle, start_circle, visualizer)
                    if new_target:
                        visualizer.create_packet(target_circle, new_target, current_time)

            connected_circles = visualizer.get_connected_circles(target_circle)
            if not connected_circles:
                if packet not in packets_to_remove:
                    packets_to_remove.append(packet) # Dead end.
                    visualizer.active_packet_count -= 1
                continue

            # UPDATED: Use deterministic/locked routing instead of random.choice
            next_target = _resolve_next_target(target_circle, start_circle, visualizer)

            if tc_a and tc_b:
                nt_a = next_target.get('packet_state_a', False)
                nt_b = next_target.get('packet_state_b', False)
                if nt_a and not nt_b:
                    packet['respawn_origin_circle'] = target_circle

            x1, y1 = visualizer.get_circle_center(target_circle)
            x2, y2 = visualizer.get_circle_center(next_target)
            grid_size = visualizer.grid.grid_size
            target_grid_x = int(round(x1 / grid_size))
            target_grid_y = int(round(y1 / grid_size))
            next_grid_x = int(round(x2 / grid_size))
            next_grid_y = int(round(y2 / grid_size))
            dx = abs(next_grid_x - target_grid_x)
            dy = abs(next_grid_y - target_grid_y)

            journey_duration = max(dx, dy)

            visualizer.create_packet(target_circle, next_target, current_time, journey_duration_override=journey_duration)

            if packet not in packets_to_remove:
                packets_to_remove.append(packet)
                visualizer.active_packet_count -= 1

        else:
            x1, y1 = visualizer.get_circle_center(packet['start_circle'])
            x2, y2 = visualizer.get_circle_center(packet['target_circle'])
            packet_x = x1 + (x2 - x1) * progress
            packet_y = y1 + (y2 - y1) * progress
            packet['graphic'].pos = (packet_x - 10, packet_y - 10)

    for packet in packets_to_remove:
        if packet in visualizer.packets:
            visualizer.packets.remove(packet)
            if packet.get('graphic'):
                if packet.get('color_instruction') in visualizer.canvas.children:
                    visualizer.canvas.remove(packet.get('color_instruction'))
                if packet.get('graphic') in visualizer.canvas.children:
                    visualizer.canvas.remove(packet.get('graphic'))

    if not visualizer._hard_reset_running and len(visualizer.packets) >= visualizer.max_packets:
        visualizer._trigger_hard_reset()
