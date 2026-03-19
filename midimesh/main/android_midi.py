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

from kivy.utils import platform

if platform != 'android':
    class AndroidMidi:
        def __init__(self, *args, **kwargs):
            print("WARNING: AndroidMidi is a dummy class on non-Android platforms.")

        def open_output(self): pass
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

    try:
        Logger.info("AndroidMidi: Loading Android core classes...")
        Context = autoclass('android.content.Context')
        MidiManager = autoclass('android.media.midi.MidiManager')
        Handler = autoclass('android.os.Handler')
        Looper = autoclass('android.os.Looper')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        MidiDevice = autoclass('android.media.midi.MidiDevice')
        MidiDeviceInfo = autoclass('android.media.midi.MidiDeviceInfo')
        MidiDeviceCallback = autoclass('android.media.midi.MidiManager$DeviceCallback')


        DEVICE_TYPE_USB = 1
        DEVICE_TYPE_USB_HOST = 4

        Logger.info("AndroidMidi: Core Android classes loaded successfully")

    except Exception as e:
        Logger.error(f"AndroidMidi: Could not load Android classes. Error: {e}")

        class AndroidMidi:
            def __init__(self, *args, **kwargs):
                Logger.error("AndroidMidi: Dummy class initialized due to class loading error.")
            def open_output(self): pass
            def send_message(self, msg): pass
            def close(self): pass
            def set_connection_mode(self, mode): pass
            def get_host_devices(self): return []
            def connect_to_device(self, info): pass
            def disconnect_device(self, dev_id): pass
            def get_connected_host_device_ids(self): return []

    else:
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

        class AndroidMidi:
            def __init__(self):
                self.activity = PythonActivity.mActivity
                self.midi_manager = self.activity.getSystemService(Context.MIDI_SERVICE)
                self.midi_devices = {}
                self.midi_receiver_ports = {}
                self.device_listener = None
                self.main_looper = Looper.getMainLooper()
                self.main_handler = Handler(self.main_looper)


                self.connection_mode = 'client'

                if not self.midi_manager:
                    Logger.error("AndroidMidi: MidiManager not available.")


            def _get_devices(self):
                if not self.midi_manager:
                    Logger.error("AndroidMidi: MidiManager not available.")
                    return []
                return self.midi_manager.getDevices()

            def set_connection_mode(self, mode):
                if mode not in ('host', 'client'):
                    Logger.error(f"AndroidMidi: Invalid connection mode '{mode}'.")
                    return

                if self.connection_mode == mode:
                    return

                Logger.info(f"AndroidMidi: Setting mode to '{mode}'.")
                self.connection_mode = mode

                Logger.info("AndroidMidi: Closing all connections to switch mode.")
                self.close_ports()

                if self.connection_mode == 'client':
                    self.open_output()

            def open_input(self, callback):
                Logger.info("AndroidMidi: MIDI input is not supported in this build.")
                pass

            def open_output(self):
                if self.connection_mode != 'client':
                    return

                Logger.info(f"AndroidMidi: Scanning for 'client' (PC) devices...")
                devices = self._get_devices()
                if not devices:
                    Logger.warning("AndroidMidi: No MIDI devices found on scan.")
                    return

                for device_info in devices:
                    if self.try_connect_client_device(device_info):
                        break
                else:
                    Logger.warning(f"AndroidMidi: No matching 'client' output device found.")

            def try_connect_client_device(self, device_info):
                if device_info.getInputPortCount() == 0:
                    return False

                device_type = device_info.getType()
                device_name = device_info.getProperties().getString('name')

                if self.connection_mode == 'client' and device_type == DEVICE_TYPE_USB:
                    Logger.info(f"AndroidMidi: Found CLIENT device: {device_name}")
                    self.connect_to_device(device_info)
                    return True

                return False

            def get_host_devices(self):
                if not self.midi_manager:
                    Logger.error("AndroidMidi: get_host_devices: MidiManager is missing.")
                    return []

                Logger.info("AndroidMidi: Scanning for HOST (OTG) devices...")
                all_devices = self._get_devices()

                if not all_devices:
                    Logger.warning("AndroidMidi: _get_devices() returned 0 devices.")
                    return []

                Logger.info(f"AndroidMidi: Found {len(all_devices)} total devices. Dumping info:")
                host_devices = []

                for device_info in all_devices:
                    try:
                        device_type = device_info.getType()
                        device_name = device_info.getProperties().getString('name')
                        input_ports = device_info.getInputPortCount()

                        output_ports = device_info.getOutputPortCount()

                        Logger.info(f"AndroidMidi: --> Device: '{device_name}', Type: {device_type}, Inputs: {input_ports}, Outputs: {output_ports}")

                        if input_ports > 0:
                            Logger.info(f"AndroidMidi:     '-- PASSED filter. Adding to list.")
                            host_devices.append((device_name, device_info))
                        else:
                            Logger.info(f"AndroidMDidi:     '-- FAILED filter (Inputs == 0). Skipping.")

                    except Exception as e:
                        Logger.error(f"AndroidMidi: Error inspecting device: {e}")

                if not host_devices:
                    Logger.warning("AndroidMidi: No devices passed the host filter.")

                return host_devices

            def connect_to_device(self, device_info):
                device_id = device_info.getId()
                if device_id in self.midi_devices:
                    Logger.info("AndroidMidi: Device already connected.")
                    return

                device_name = device_info.getProperties().getString('name')
                Logger.info(f"AndroidMidi: Attempting to open: {device_name}")

                if not self.device_listener:
                    self.device_listener = MidiDeviceListener(self.on_device_opened)

                self.midi_manager.openDevice(
                    device_info,
                    self.device_listener,
                    self.main_handler
                )

            def on_device_opened(self, device):
                if device is None:
                    Logger.error("AndroidMidi: Could not open MIDI device (device is None).")
                    return

                device_id = device.getInfo().getId()
                if device_id in self.midi_devices:
                    Logger.warning("AndroidMidi: A new device was opened, but we already have it. Closing new one.")
                    device.close()
                    return

                port = device.openInputPort(0)

                if port is None:
                    Logger.error("AndroidMidi: Failed to open the device's input port for sending.")
                    device.close()
                    return

                self.midi_devices[device_id] = device
                self.midi_receiver_ports[device_id] = port

                name = device.getInfo().getProperties().getString('name')
                Logger.info(f"AndroidMidi: Device connected successfully: {name} (ID: {device_id})")

            def disconnect_device(self, device_id):
                Logger.info(f"AndroidMidi: Request to disconnect device ID: {device_id}")
                try:
                    if device_id in self.midi_receiver_ports:
                        self.midi_receiver_ports[device_id].close()
                        del self.midi_receiver_ports[device_id]

                    if device_id in self.midi_devices:
                        dev_name = self.midi_devices[device_id].getInfo().getProperties().getString('name')
                        self.midi_devices[device_id].close()
                        del self.midi_devices[device_id]
                        Logger.info(f"AndroidMidi: Host device disconnected: {dev_name}")
                    else:
                        Logger.warning(f"AndroidMidi: Tried to disconnect unknown device ID: {device_id}")

                except Exception as e:
                    Logger.error(f"AndroidMidi: Error during device disconnect: {e}")

            def get_connected_host_device_ids(self):
                return list(self.midi_devices.keys())

            def send_message(self, msg):
                if not self.midi_receiver_ports:
                    return
                try:
                    java_bytes = bytearray(msg)
                    length = len(java_bytes)
                    timestamp = 0

                    for port in self.midi_receiver_ports.values():
                        port.send(java_bytes, 0, length, timestamp)

                except Exception as e:
                    Logger.error(f"AndroidMidi: Error sending MIDI: {e}")

            def close_ports(self):
                Logger.info("AndroidMidi: Closing all MIDI ports and devices...")
                try:
                    for port in self.midi_receiver_ports.values():
                        port.close()
                    for device in self.midi_devices.values():
                        device.close()
                except Exception as e:
                    Logger.error(f"AndroidMidi: Error during port cleanup: {e}")
                finally:
                    self.midi_devices.clear()
                    self.midi_receiver_ports.clear()
                    Logger.info("AndroidMidi: All ports and devices cleared.")

            def close(self):
                Logger.info("AndroidMidi: Closing all MIDI services.")
                self.close_ports()
                self.midi_manager = None
