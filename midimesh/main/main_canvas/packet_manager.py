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
import math
import random
from kivy.clock import Clock

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
                    potential_targets = [c for c in connected_to_origin if c is not target_circle] or connected_to_origin
                    new_target = random.choice(potential_targets)
                    visualizer.create_packet(respawn_origin, new_target, current_time)

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
                    potential_new_targets = [c for c in connected if c is not start_circle] or connected
                    new_target = random.choice(potential_new_targets)
                    visualizer.create_packet(target_circle, new_target, current_time)

            connected_circles = visualizer.get_connected_circles(target_circle)
            if not connected_circles:
                if packet not in packets_to_remove:
                    packets_to_remove.append(packet) # Dead end.
                    visualizer.active_packet_count -= 1
                continue

            potential_targets = [c for c in connected_circles if c is not start_circle] or connected_circles
            next_target = random.choice(potential_targets)

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

            packet['start_circle'] = target_circle
            packet['target_circle'] = next_target
            packet['start_tick'] = visualizer.master_tick
            packet['journey_duration_in_ticks'] = max(dx, dy)
            packet['arrival_tick'] = visualizer.master_tick + packet['journey_duration_in_ticks']
            packet['progress'] = 0.0
            packet['total_distance'] = math.hypot(x2 - x1, y2 - y1) or 1e-3

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
