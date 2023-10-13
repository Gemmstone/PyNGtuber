from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import numpy as np
import pyaudio


class AudioThread(QThread):
    audio_stream_signal = pyqtSignal(int)
    audio_stream_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_stream = None
        self.selected_microphone_index = None
        self.p = pyaudio.PyAudio()

    def run(self):
        if self.selected_microphone_index is not None:
            device_info = self.p.get_device_info_by_index(self.selected_microphone_index)
            supported_sample_rate = device_info['defaultSampleRate']

            if supported_sample_rate == 44100:
                sample_rate = 44100
            else:
                # Use a fallback sample rate that is supported
                sample_rate = 48000

            try:
                self.audio_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    input_device_index=self.selected_microphone_index,
                    frames_per_buffer=1024,
                    stream_callback=self.callback
                )
                self.audio_stream.start_stream()
            except BaseException as e:
                self.stop_stream()
                self.handle_error(e)

    def stop_stream(self):
        try:
            if self.audio_stream is not None:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
        except OSError as e:
            self.handle_error(e)

    def handle_error(self, error):
        print(f"An error occurred: {error}")

    def set_microphone_index(self, index):
        self.selected_microphone_index = index

    def callback(self, in_data, frame_count, time_info, status):
        if status:
            # self.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            self.audio_stream_error.emit(f"{status}")

        audio_data = np.frombuffer(in_data, dtype=np.int16)
        rms_volume = abs(np.max(audio_data))
        # Normalize the volume to fit in the range [0, 100]
        volume = int((rms_volume / 32768) * 100)

        # Emit the volume signal
        self.audio_stream_signal.emit(volume)

        # Return None and pyaudio.paContinue to keep the stream running
        return None, pyaudio.paContinue


class MicrophoneVolumeWidget(QWidget):
    activeAudio = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        uic.loadUi("UI/audioMonitor.ui", self)
        self.device_dict = {}
        self.previous_state = False
        self.active_audio_signal = -1
        self.label.hide()

        self.list_microphones()
        self.last_microphone = None

        self.volume.valueChanged.connect(self.updateDelayView)

        self.mute.clicked.connect(self.update_audio_stream)
        self.microphones.currentIndexChanged.connect(self.update_audio_stream)

        self.audio_thread = AudioThread()
        self.audio_thread.audio_stream_signal.connect(self.update_volume)
        self.audio_thread.audio_stream_error.connect(self.error_handler)

        self.updateDelayView()
        self.update_audio_stream()

    def error_handler(self, error_message):
        print(f"Error in audio stream: {error_message}")
        self.label.setText(f"Este micrófono tiene problemas: {error_message}")
        self.label.show()

    def list_microphones(self):
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
                        # print(i, name, max_input_channels)
                        self.device_dict[name] = i
                        self.microphones.addItem(name)
                        if name == "default":
                            self.microphones.setCurrentText(name)
                            # Your code for adding microphones and setting the current text goes here
            except OSError as e:
                if e.errno != -9996:
                    print(f"Error when accessing device {i}: {str(e)}")

        p.terminate()

    def update_audio_stream(self):
        self.label.hide()
        selected_microphone_name = self.microphones.currentText()
        selected_microphone_index = self.device_dict.get(selected_microphone_name)
        if selected_microphone_index is not None:
            if self.last_microphone != selected_microphone_index:
                if self.audio_thread.isRunning():
                    self.audio_thread.stop_stream()
                self.audio_thread.set_microphone_index(selected_microphone_index)
                self.audio_thread.start()
                self.last_microphone = selected_microphone_index
            elif self.mute.isChecked():
                if self.audio_thread.isRunning():
                    self.audio_thread.stop_stream()

    def updateDelayView(self):
        self.progressBar_2.setMaximum(self.volume.value())
        self.delay.setMaximum(self.volume.value())

    def update_volume(self, volume):
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