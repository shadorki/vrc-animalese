import numpy as np
from typing import Optional
import threading

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

class VirtualMicrophone:
    """Outputs audio to an audio device.

    Can output to:
    - VB-Audio Virtual Cable (for routing to VRChat as mic input)
    - Default speakers (for local playback only)
    - Any other audio output device
    """

    def __init__(self):
        self._stream: Optional[sd.OutputStream] = None
        self._sample_rate = 44100
        self._channels = 1
        self._device: Optional[int] = None
        self._lock = threading.Lock()

    @staticmethod
    def is_available() -> bool:
        return SOUNDDEVICE_AVAILABLE

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio output devices."""
        if not SOUNDDEVICE_AVAILABLE:
            return []

        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_output_channels'] > 0:
                devices.append({
                    'id': i,
                    'name': dev['name'],
                    'channels': dev['max_output_channels'],
                    'sample_rate': dev['default_samplerate']
                })
        return devices

    @staticmethod
    def find_virtual_cable() -> Optional[int]:
        """Try to find VB-Audio Virtual Cable device."""
        if not SOUNDDEVICE_AVAILABLE:
            return None

        for i, dev in enumerate(sd.query_devices()):
            name_lower = dev['name'].lower()
            if dev['max_output_channels'] > 0:
                if 'cable input' in name_lower or 'vb-audio' in name_lower:
                    return i
        return None

    @staticmethod
    def get_default_device() -> Optional[int]:
        """Get the default output device."""
        if not SOUNDDEVICE_AVAILABLE:
            return None
        try:
            return sd.default.device[1]
        except Exception:
            return None

    def set_device(self, device_id: Optional[int] = None, prefer_virtual_cable: bool = True):
        """Set the output device.

        Args:
            device_id: Specific device ID, or None for auto-detect
            prefer_virtual_cable: If True and device_id is None, prefer VB-Cable over default
        """
        if device_id is not None:
            self._device = device_id
        elif prefer_virtual_cable:
            cable = self.find_virtual_cable()
            self._device = cable if cable is not None else self.get_default_device()
        else:
            self._device = self.get_default_device()

    def get_device_name(self) -> str:
        """Get the name of the current device."""
        if not SOUNDDEVICE_AVAILABLE or self._device is None:
            return "Default"
        try:
            return sd.query_devices(self._device)['name']
        except Exception:
            return "Unknown"

    def is_virtual_cable(self) -> bool:
        """Check if current device is a virtual cable."""
        name = self.get_device_name().lower()
        return 'cable input' in name or 'vb-audio' in name

    def start(self) -> bool:
        """Start the audio output stream."""
        if not SOUNDDEVICE_AVAILABLE:
            print("sounddevice not available. Install with: pip install sounddevice")
            return False

        with self._lock:
            if self._stream is not None:
                return True

            if self._device is None:
                self.set_device()

            try:
                self._stream = sd.OutputStream(
                    samplerate=self._sample_rate,
                    channels=self._channels,
                    dtype=np.float32,
                    device=self._device,
                    latency='low'
                )
                self._stream.start()
                device_name = self.get_device_name()
                is_cable = self.is_virtual_cable()
                print(f"Audio output: {device_name} {'(Virtual Cable)' if is_cable else '(Speakers)'}")
                return True
            except Exception as e:
                print(f"Failed to start audio stream: {e}")
                self._stream = None
                return False

    def stop(self):
        """Stop the audio output stream."""
        with self._lock:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                finally:
                    self._stream = None

    def write_audio(self, audio: np.ndarray, sample_rate: int, blocking: bool = True):
        """Write audio samples to the output device.

        Args:
            audio: Audio samples to play
            sample_rate: Sample rate of the audio
            blocking: If False, return immediately without waiting for audio to finish
        """
        if not SOUNDDEVICE_AVAILABLE:
            return

        if self._stream is None:
            if not self.start():
                return

        if sample_rate != self._sample_rate:
            ratio = self._sample_rate / sample_rate
            new_length = int(len(audio) * ratio)
            if new_length > 0:
                indices = np.linspace(0, len(audio) - 1, new_length)
                audio = np.interp(indices, np.arange(len(audio)), audio)

        audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

        if len(audio.shape) == 1:
            audio = audio.reshape(-1, 1)

        if not blocking:
            def _write():
                try:
                    with self._lock:
                        if self._stream:
                            self._stream.write(audio)
                except Exception as e:
                    print(f"Audio write error: {e}")
            threading.Thread(target=_write, daemon=True).start()
        else:
            try:
                with self._lock:
                    if self._stream:
                        self._stream.write(audio)
            except Exception as e:
                print(f"Audio write error: {e}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
