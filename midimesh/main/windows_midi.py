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

import rtmidi
from kivy.logger import Logger

class MockProperties:
    def __init__(self, name):
        self._name = name

    def getString(self, key):
        if key == 'name':
            return self._name
        return ""

class MockMidiDevice:
    def __init__(self, port_index, port_name):
        self._id = port_index
        self._name = port_name
        self._props = MockProperties(port_name)

    def getId(self):
        return self._id

    def getProperties(self):
        return self._props

    def getType(self):
        return 1

    def getInputPortCount(self):
        return 1

    def getOutputPortCount(self):
        return 1

class WindowsMidi:
    def __init__(self):
        self.midi_out_interface = rtmidi.MidiOut()
        self.connected_devices = {}
        self.connection_mode = 'client'
        Logger.info("WindowsMidi: Initialized using rtmidi.")

    def open_output(self):
        pass

    def get_host_devices(self):
        Logger.info("WindowsMidi: Scanning for Windows MIDI devices...")
        ports = self.midi_out_interface.get_ports()

        device_list = []
        for index, name in enumerate(ports):
            dev = MockMidiDevice(index, name)
            device_list.append((name, dev))

        Logger.info(f"WindowsMidi: Found {len(device_list)} devices.")
        return device_list

    def connect_to_device(self, device_info):
        port_id = device_info.getId()
        name = device_info.getProperties().getString('name')

        if port_id in self.connected_devices:
            Logger.info(f"WindowsMidi: Already connected to {name}")
            return

        try:
            new_out = rtmidi.MidiOut()
            new_out.open_port(port_id)

            self.connected_devices[port_id] = new_out
            Logger.info(f"WindowsMidi: Connected to {name}")
        except Exception as e:
            Logger.error(f"WindowsMidi: Failed to connect to {name}: {e}")

    def disconnect_device(self, device_id):
        if device_id in self.connected_devices:
            self.connected_devices[device_id].close_port()
            del self.connected_devices[device_id]
            Logger.info(f"WindowsMidi: Disconnected device ID {device_id}")

    def send_message(self, msg):
        if not self.connected_devices:
            return

        for dev_id, midi_interface in self.connected_devices.items():
            try:
                midi_interface.send_message(msg)
            except Exception as e:
                Logger.error(f"WindowsMidi: Error sending to device {dev_id}: {e}")

    def close(self):
        for dev_id in list(self.connected_devices.keys()):
            self.disconnect_device(dev_id)
        del self.midi_out_interface

    def set_connection_mode(self, mode):
        self.connection_mode = mode

    def get_connected_host_device_ids(self):
        return list(self.connected_devices.keys())
