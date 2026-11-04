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

import queue
import threading
from kivy.utils import platform

if platform != 'android':
    class AndroidMidi:
        def __init__(self, *args, **kwargs):
            print("WARNING: AndroidMidi is a dummy class on non-Android platforms.")
        def open_output(self): pass
        def open_input(self, cb): pass
        def send_message(self, msg): pass
        def close(self): pass
        def set_connection_mode(self, mode): pass
        def get_host_devices(self): return []
        def connect_to_device(self, info): pass
        def disconnect_device(self, dev_id): pass
        def get_connected_host_device_ids(self): return []

else:
    from jnius import autoclass, PythonJavaClass, java_method
    from kivy.logger import Logger
    from kivy.clock import Clock

    class MidiDeviceListener(PythonJavaClass):
        __javainterfaces__ = ['android/media/midi/MidiManager$OnDeviceOpenedListener']
        __javacontext__ = 'app'

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method('(Landroid/media/midi/MidiDevice;)V')
        def onDeviceOpened(self, device):
            if self.callback:
                self.callback(device)

    class MidiReceiverImpl(PythonJavaClass):
        __javainterfaces__ = ['com/yourcompany/midimesh/MidiReceiverWrapper$OnMidiDataListener']
        __javacontext__ = 'app'

        def __init__(self, event_queue):
            super().__init__()
            self.event_queue = event_queue

        @java_method('([BIIJ)V')
        def onMidiData(self, data, offset, count, timestamp):
            try:
                if count > 0:
                    status_byte = data[offset] & 0xFF
                    if status_byte == 0xFE or status_byte == 0xF8:
                        return

                msg = bytes(data[offset : offset + count])
                try:
                    self.event_queue.put((msg, timestamp), block=False)
                except queue.Full:
                    pass
            except Exception as e:
                Logger.error(f"AndroidMidi: Error parsing incoming payload: {e}")


    class MidiEventParser(threading.Thread):
        def __init__(self, event_queue, callback):
            super().__init__(daemon=True)
            self.event_queue = event_queue
            self.callback = callback
            self._stop_event = threading.Event()

        def run(self):
            while not self._stop_event.is_set():
                try:
                    msg, timestamp = self.event_queue.get(timeout=0.05)
                    self.callback(msg, timestamp)
                except queue.Empty:
                    continue
                except Exception as e:
                    Logger.error(f"MidiEventParser: {e}")

        def stop(self):
            self._stop_event.set()

    _android_loaded = False
    Context = None
    MidiManager = None
    Handler = None
    Looper = None
    PythonActivity = None
    DEVICE_TYPE_USB = None
    DEVICE_TYPE_USB_HOST = None

    try:
        Logger.info("AndroidMidi: Loading Android core classes...")
        Context = autoclass('android.content.Context')
        MidiManager = autoclass('android.media.midi.MidiManager')
        Handler = autoclass('android.os.Handler')
        Looper = autoclass('android.os.Looper')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        DEVICE_TYPE_USB = 1
        DEVICE_TYPE_USB_HOST = 4
        _android_loaded = True
        Logger.info("AndroidMidi: Core Android classes loaded successfully")
    except Exception as e:
        Logger.error(f"AndroidMidi: Could not load Android classes. Error: {e}")

    class AndroidMidi:
        def __init__(self):
            self.activity = None
            self.midi_manager = None
            self.midi_devices = {}
            self.midi_output_ports = {}
            self.midi_receivers = {}
            self.midi_input_ports = {}
            self.midi_input_callback = None
            self.device_listener = None
            self.main_looper = None
            self.main_handler = None
            self.connection_mode = 'client'

            self.midi_event_queue = queue.Queue(maxsize=128)
            self._parser_thread = None
            self._running = False
            self._fps_threshold = 30.0  # Drop non-critical events below this FPS

            if not _android_loaded:
                Logger.error("AndroidMidi: Cannot initialize. Android classes missing.")
                return

            try:
                self.activity = PythonActivity.mActivity
                self.midi_manager = self.activity.getSystemService(Context.MIDI_SERVICE)
                self.main_looper = Looper.getMainLooper()
                self.main_handler = Handler(self.main_looper)

                if not self.midi_manager:
                    Logger.error("AndroidMidi: MidiManager not available.")
            except Exception as e:
                Logger.error(f"AndroidMidi: Failed to init manager: {e}")
                self.midi_manager = None

        def _get_devices(self):
            if not self.midi_manager: return []
            try:
                return self.midi_manager.getDevices()
            except Exception:
                return []

        def get_host_devices(self):
            if not self.midi_manager:
                return []
            try:
                devices = self._get_devices()
                host_devices = []
                for dev_info in devices:
                    if dev_info.getOutputPortCount() > 0:
                        name = dev_info.getProperties().getString('name')
                        host_devices.append((name, dev_info))
                return host_devices
            except Exception as e:
                Logger.error(f"AndroidMidi: Error getting host devices: {e}")
                return []

        def get_connected_host_device_ids(self):
            return list(self.midi_devices.keys())

        def set_connection_mode(self, mode):
            if mode not in ('host', 'client'): return
            if self.connection_mode == mode: return
            Logger.info(f"AndroidMidi: Setting mode to '{mode}'.")
            self.connection_mode = mode
            Logger.info("AndroidMidi: Closing all connections to switch mode.")
            self.close_ports()
            if self.connection_mode == 'client':
                self.open_output()

        def open_input(self, callback):
            if not self.midi_manager:
                Logger.error("AndroidMidi: MidiManager not available.")
                return
            self.midi_input_callback = callback
            Logger.info("AndroidMidi: Scanning for devices to RECEIVE from...")

            devices = self._get_devices()
            if not devices:
                Logger.warning("AndroidMidi: No MIDI devices found.")
                return

            found = False
            for device_info in devices:
                if device_info.getOutputPortCount() > 0:
                    self.connect_to_device(device_info)
                    found = True
                    break

            if not found:
                Logger.warning("AndroidMidi: No compatible device found for input.")

        def open_output(self):
            if self.connection_mode != 'client': return
            Logger.info(f"AndroidMidi: Scanning for 'client' (PC) devices to SEND to...")
            devices = self._get_devices()
            if not devices:
                Logger.warning("AndroidMidi: No MIDI devices found on scan.")
                return

            found = False
            for device_info in devices:
                if device_info.getInputPortCount() > 0:
                    self.try_connect_client_device(device_info)
                    found = True
                    break

            if not found:
                Logger.warning("AndroidMidi: No matching 'client' output device found.")

        def try_connect_client_device(self, device_info):
            if device_info.getOutputPortCount() == 0: return False
            device_type = device_info.getType()
            device_name = device_info.getProperties().getString('name')
            if self.connection_mode == 'client' and device_type == DEVICE_TYPE_USB:
                Logger.info(f"AndroidMidi: Found CLIENT device: {device_name}")
                self.connect_to_device(device_info)
                return True
            return False

        def connect_to_device(self, device_info):
            device_id = device_info.getId()
            if device_id in self.midi_devices:
                Logger.info("AndroidMidi: Device already connected.")
                return
            device_name = device_info.getProperties().getString('name')
            Logger.info(f"AndroidMidi: Attempting to open: {device_name}")

            if not self.device_listener:
                self.device_listener = MidiDeviceListener(self.on_device_opened)

            try:
                self.midi_manager.openDevice(device_info, self.device_listener, self.main_handler)
            except Exception as e:
                Logger.error(f"AndroidMidi: Error opening device: {e}")

        def on_device_opened(self, device):
            if device is None:
                Logger.error("AndroidMidi: Could not open MIDI device (device is None).")
                return

            device_id = device.getInfo().getId()
            if device_id in self.midi_devices:
                Logger.warning("AndroidMidi: Device already connected. Closing new instance.")
                device.close()
                return

            device_name = device.getInfo().getProperties().getString('name')
            Logger.info(f"AndroidMidi: Opening ports for: {device_name}")

            recv_port = device.openOutputPort(0)
            if recv_port is not None and self.midi_input_callback:
                try:
                    python_listener = MidiReceiverImpl(self.midi_event_queue)
                    MidiReceiverWrapper = autoclass('com.yourcompany.midimesh.MidiReceiverWrapper')
                    java_receiver = MidiReceiverWrapper(python_listener)
                    recv_port.connect(java_receiver)
                    self.midi_receivers[device_id] = (python_listener, java_receiver)
                    self.midi_input_ports[device_id] = recv_port
                    if not self._running:
                        self._running = True
                        self._parser_thread = MidiEventParser(
                            self.midi_event_queue,
                            lambda msg, ts: Clock.schedule_once(
                                lambda dt, m=msg, t=ts: self.midi_input_callback(m, t), 0
                            )
                        )
                        self._parser_thread.start()

                    Logger.info(f"AndroidMidi: Receiver connected to {device_name}")
                except Exception as e:
                    Logger.error(f"AndroidMidi: Failed to connect receiver: {e}")
                    recv_port.close()
            elif recv_port is None:
                Logger.warning(f"AndroidMidi: Failed to open output port for {device_name}")

            send_port = device.openInputPort(0)
            if send_port is None:
                Logger.warning(f"AndroidMidi: Failed to open input port for {device_name}")
            else:
                self.midi_output_ports[device_id] = send_port
                Logger.info(f"AndroidMidi: Input port opened for {device_name}")

            self.midi_devices[device_id] = device
            Logger.info(f"AndroidMidi: Device connected successfully: {device_name} (ID: {device_id})")

        def disconnect_device(self, device_id):
            Logger.info(f"AndroidMidi: Request to disconnect device ID: {device_id}")
            try:
                if device_id in self.midi_receivers:
                    del self.midi_receivers[device_id]
                if device_id in self.midi_input_ports:
                    port = self.midi_input_ports[device_id]
                    try: port.close()
                    except: pass
                    del self.midi_input_ports[device_id]
                if device_id in self.midi_output_ports:
                    self.midi_output_ports[device_id].close()
                    del self.midi_output_ports[device_id]
                if device_id in self.midi_devices:
                    dev_name = self.midi_devices[device_id].getInfo().getProperties().getString('name')
                    self.midi_devices[device_id].close()
                    del self.midi_devices[device_id]
                    Logger.info(f"AndroidMidi: Host device disconnected: {dev_name}")
                else:
                    Logger.warning(f"AndroidMidi: Tried to disconnect unknown device ID: {device_id}")
            except Exception as e:
                Logger.error(f"AndroidMidi: Error during device disconnect: {e}")

        def send_message(self, msg):
            if not self.midi_output_ports:
                Logger.debug("AndroidMidi: No output ports available to send message.")
                return
            try:
                java_bytes = bytearray(msg)
                length = len(java_bytes)
                timestamp = 0
                for port in self.midi_output_ports.values():
                    port.send(java_bytes, 0, length, timestamp)
            except Exception as e:
                Logger.error(f"AndroidMidi: Error sending MIDI: {e}")

        def close_ports(self):
            Logger.info("AndroidMidi: Closing all MIDI ports and devices...")

            if self._parser_thread and self._running:
                self._parser_thread.stop()
                self._parser_thread = None
                self._running = False

            try:
                self.midi_receivers.clear()
                for port in self.midi_input_ports.values():
                    try: port.close()
                    except: pass
                for port in self.midi_output_ports.values():
                    try: port.close()
                    except: pass
                for device in self.midi_devices.values():
                    try: device.close()
                    except: pass
            except Exception as e:
                Logger.error(f"AndroidMidi: Error during port cleanup: {e}")
            finally:
                while not self.midi_event_queue.empty():
                    try: self.midi_event_queue.get_nowait()
                    except: break
                self.midi_devices.clear()
                self.midi_output_ports.clear()
                self.midi_input_ports.clear()
                self.midi_receivers.clear()
                self.midi_input_callback = None
                self.device_listener = None
                Logger.info("AndroidMidi: All ports and devices cleared.")

        def close(self):
            Logger.info("AndroidMidi: Closing all MIDI services.")
            self.close_ports()
            self.midi_manager = None




