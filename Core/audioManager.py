from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget
import sounddevice as sd
import noisereduce as nr
from PyQt6 import uic
import numpy as np
import traceback
import pyaudio
import asyncio
import os


class AudioThread(QThread):
    audio_stream_signal = pyqtSignal(int)
    audio_stream_error = pyqtSignal(str)

    def __init__(
            self, max_reference_volume=0.5,
            engine="pyaudio",
            noise_reduction=True,
            sample_rate_noise_reduction=44100,
            parent=None
    ):
        super().__init__(parent)
        self.p = pyaudio.PyAudio()
        self.audio_stream = None
        self.selected_microphone_index = None
        self.max_reference_volume = max_reference_volume
        self.engine = engine
        self.noise_reduction = noise_reduction
        self.sample_rate_noise_reduction = sample_rate_noise_reduction

    def run(self):
        if self.engine == "pyaudio":
            self.run_pyaudio()
        else:
            self.run_sounddevice()

    def run_sounddevice(self):
        if self.selected_microphone_index is not None:
            try:
                device_info = sd.query_devices(self.selected_microphone_index)
                # print(device_info)
                supported_sample_rate = device_info['default_samplerate']

            except BaseException as e:
                self.handle_error(e)
                return

            try:
                with sd.InputStream(
                        channels=1, device=self.selected_microphone_index, callback=self.callback_sounddevice,
                        samplerate=supported_sample_rate
                ):
                    self.exec()
            except BaseException as e:
                self.stop_stream()
                self.handle_error(e)

    def run_pyaudio(self):
        if self.selected_microphone_index is not None:
            try:
                device_info = self.p.get_device_info_by_index(self.selected_microphone_index)
                supported_sample_rate = device_info['defaultSampleRate']
            except BaseException as e:
                self.handle_error(e)
                return

            try:
                self.audio_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=int(supported_sample_rate),
                    input=True,
                    input_device_index=self.selected_microphone_index,
                    frames_per_buffer=1024,
                    stream_callback=self.callback_pyaudio
                )
                self.audio_stream.start_stream()
            except BaseException as e:
                self.stop_stream()
                self.handle_error(e)

    def stop_stream(self):
        self.quit()

    def handle_error(self, error):
        print(f"An error occurred: {error}")
        self.audio_stream_error.emit(str(error))

    def set_microphone_index(self, index):
        self.selected_microphone_index = index

    def change_max_reference_volume(self, new_value):
        self.max_reference_volume = new_value

    def toggle_noise_reduction(self, value):
        self.noise_reduction = value

    def change_sample_rate_noise_reduction(self, new_value):
        self.sample_rate_noise_reduction = new_value

    def callback_sounddevice(self, indata, outdata, frames, time):
        if self.noise_reduction:
            reduced_noise = nr.reduce_noise(y=indata[:, 0], sr=self.sample_rate_noise_reduction)
        else:
            reduced_noise = indata
        volume = np.sqrt(np.mean(reduced_noise ** 2))
        normalized_volume = int((volume / self.max_reference_volume) * 100)
        normalized_volume = min(100, max(0, normalized_volume))
        self.audio_stream_signal.emit(normalized_volume)

    def callback_pyaudio(self, in_data, frame_count, time_info, status):
        if self.audio_stream is None:
            return

        if status:
            self.audio_stream.close()
            self.audio_stream = None
            self.audio_stream_error.emit(f"{status}")

        audio_data = np.frombuffer(in_data, dtype=np.int16)
        if self.noise_reduction:
            reduced_noise = nr.reduce_noise(y=audio_data, sr=self.sample_rate_noise_reduction)
        else:
            reduced_noise = audio_data
        rms_volume = abs(np.max(reduced_noise))
        volume = int((rms_volume / 32768) * 100)

        try:
            self.audio_stream_signal.emit(volume)
        except RuntimeError:
            pass

        return None, pyaudio.paContinue


class MicrophoneVolumeWidget(QWidget):
    activeAudio = pyqtSignal(int)
    settingsChanged = pyqtSignal()

    def __init__(
            self, exe_dir,
            max_reference_volume=0.5,
            noise_reduction=True,
            sample_rate_noise_reduction=44100,
            engine="pyaudio"
    ):
        super().__init__()
        uic.loadUi(os.path.join(exe_dir, f"UI", "audioMonitor.ui"), self)
        self.device_dict = {}
        self.previous_state = False
        self.active_audio_signal = -1
        self.max_reference_volume = max_reference_volume
        self.engine = engine
        self.noise_reduction = noise_reduction
        self.sample_rate_noise_reduction = sample_rate_noise_reduction
        self.obs_websocket = None
        
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.setInterval(500)

        self.volume.valueChanged.connect(self.settingsChanged.emit)
        self.volume_scream.valueChanged.connect(self.settingsChanged.emit)
        self.delay.valueChanged.connect(self.settingsChanged.emit)
        self.microphones.currentIndexChanged.connect(self.settingsChanged.emit)
        self.mute.clicked.connect(self.settingsChanged.emit)

        self.label.hide()
        self.loadStart()

    def change_audio_engine(self, engine):
        self.engine = engine
        self.audio_thread.engine = engine
        self.list_microphones()
        self.update_audio_stream(force=True)

    def change_max_reference_volume(self, new_value):
        self.max_reference_volume = new_value
        self.audio_thread.change_max_reference_volume(new_value)

    def toggle_noise_reduction(self, value):
        self.noise_reduction = value
        self.audio_thread.toggle_noise_reduction(value)

    def change_sample_rate_noise_reduction(self, new_value):
        self.sample_rate_noise_reduction = new_value
        self.audio_thread.change_sample_rate_noise_reduction(new_value)

    def load_settings(self, settings):
        self.volume.setValue(settings["volume threshold"])
        self.volume_scream.setValue(settings["scream threshold"])
        self.delay.setValue(settings["delay threshold"])
        self.microphones.setCurrentIndex(settings["microphone selection"])
        self.mute.setChecked(settings["microphone mute"])

        self.noise_reduction = settings.get("noise_reduction", True)
        self.sample_rate_noise_reduction = settings.get("sample_rate", 44100)

    def loadStart(self):
        self.list_microphones()
        self.last_microphone = None

        self.volume.valueChanged.connect(self.updateDelayView)

        self.mute.clicked.connect(self.update_audio_stream)
        self.microphones.currentIndexChanged.connect(self.update_audio_stream)

        self.audio_thread = AudioThread(
            engine=self.engine,
            noise_reduction=self.noise_reduction,
            sample_rate_noise_reduction=self.sample_rate_noise_reduction
        )
        self.audio_thread.audio_stream_signal.connect(self.update_volume)
        self.audio_thread.audio_stream_error.connect(self.error_handler)

        self.updateDelayView()
        self.update_audio_stream()

    def error_handler(self, error_message):
        print(f"Exception Type: {type(error_message).__name__}")
        print(f"Error in audio stream: {error_message}")
        print(f"Exception Message: {str(error_message)}")
        traceback.print_exc()
        self.label.setText(f"Este micrófono tiene problemas: {type(error_message).__name__} {error_message}")
        self.label.show()
        QTimer.singleShot(3000, self.update_audio_stream)

    def list_microphones(self):
        self.microphones.clear()
        if self.engine == "pyaudio":
            self.list_microphones_pyaudio()
        else:
            self.list_microphones_sounddevice()

    def list_microphones_pyaudio(self):
        excluded = ["jack", "speex", "upmix", "vdownmix"]
        p = pyaudio.PyAudio()
        num_devices = p.get_device_count()
        for i in range(num_devices):
            try:
                info = p.get_device_info_by_host_api_device_index(0, i)
                name = info.get('name')
                max_input_channels = info.get('maxInputChannels')
                if 24 > max_input_channels > 0 or name == "default":
                    if name not in excluded:
                        self.device_dict[name] = i
                        self.microphones.addItem(name)
                        if name == "default":
                            self.microphones.setCurrentText(name)
            except OSError as e:
                if e.errno != -9996:
                    print(f"Error when accessing device {i}: {str(e)}")
        p.terminate()

    def list_microphones_sounddevice(self):
        excluded = ["jack", "speex", "upmix", "vdownmix"]

        devices = sd.query_devices()

        # for device in devices:
        #     print()
        #     print(f"Device Name: {device['name']}")
        #     print(f"Input Channels: {device['max_input_channels']}")
        #     print(f"Output Channels: {device['max_output_channels']}")
        #     print(f"Default Sample Rate: {device['default_samplerate']} Hz")
        #     print(f"Default Input Latency: {device['default_low_input_latency']} seconds")
        #     print(f"Default Output Latency: {device['default_low_output_latency']} seconds")
        #     print(f"Supports Full Duplex: {device['default_full_duplex']}")

        if type(devices) is dict:
            devices = [devices]

        microphone_devices = [device for device in devices if device['max_input_channels'] > 0]

        for idx, mic in enumerate(microphone_devices):
            name = mic['name']
            index = mic['index']
            if name not in excluded:
                self.device_dict[name] = index
                self.microphones.addItem(f"{name}")
                if name == "default":
                    self.microphones.setCurrentText(name)

    def update_audio_stream(self, force=False):
        self.label.hide()
        selected_microphone_name = self.microphones.currentText()
        selected_microphone_index = self.device_dict.get(selected_microphone_name)
        if selected_microphone_index is not None:
            if self.mute.isChecked():
                if self.audio_thread.isRunning():
                    self.audio_thread.stop_stream()
            elif self.last_microphone != selected_microphone_index or force:
                if self.audio_thread.isRunning():
                    self.audio_thread.stop_stream()
                self.audio_thread.set_microphone_index(selected_microphone_index)
                self.audio_thread.start()
                self.last_microphone = selected_microphone_index

    def updateDelayView(self):
        self.progressBar_2.setMaximum(self.volume.value())
        self.delay.setMaximum(self.volume.value())

    def update_volume(self, volume):
        self.inactivity_timer.start()

        volume = volume if not self.mute.isChecked() else 0

        self.progressbar.setValue(volume)
        self.progressBar_2.setValue(self.progressBar_2.maximum() if volume > self.progressBar_2.maximum() else volume)

        if volume >= self.volume_scream.value():
            if not self.active_audio_signal == 2:
                self.active_audio_signal = 2
                self.activeAudio.emit(self.active_audio_signal)
        elif volume >= self.volume.value():
            if not self.active_audio_signal == 1:
                self.active_audio_signal = 1
                self.activeAudio.emit(self.active_audio_signal)
        elif volume <= self.delay.value():
            if not self.active_audio_signal == 0:
                self.active_audio_signal = 0
                self.activeAudio.emit(self.active_audio_signal)

    def check_inactivity(self):
        if not self.mute.isChecked():
            print("No audio data received for a while. Restarting the stream.")
            self.update_audio_stream(force=True)
