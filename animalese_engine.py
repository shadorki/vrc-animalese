import os
import random
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable
import soundfile as sf
from scipy import signal
import threading
import queue
import time

@dataclass
class SoundProfile:
    pitch_shift: float = 0.0
    pitch_variation: float = 0.2
    intonation: float = 0.0

class AnimaleseEngine:
    def __init__(self, assets_path: str, gender: str = "female", voice: str = "voice_1"):
        self.assets_path = assets_path
        self.gender = gender
        self.voice = voice
        self.sound_profile = SoundProfile()
        self.sample_rate = 44100
        self._audio_cache: dict[str, tuple[np.ndarray, int]] = {}
        self._audio_queue: queue.Queue = queue.Queue()
        self._playback_thread: Optional[threading.Thread] = None
        self._running = False
        self._current_source = None
        self._output_callback: Optional[Callable[[np.ndarray, int], None]] = None

    def set_output_callback(self, callback: Callable[[np.ndarray, int], None]):
        """Set callback for audio output (for virtual mic routing)"""
        self._output_callback = callback

    def set_voice(self, gender: str, voice: str):
        self.gender = gender
        self.voice = voice
        self._audio_cache.clear()

    def set_profile(self, pitch_shift: float = 0.0, pitch_variation: float = 0.2, intonation: float = 0.0):
        self.sound_profile = SoundProfile(pitch_shift, pitch_variation, intonation)

    def _get_audio_path(self, category: str, name: str) -> str:
        if category == "animalese":
            return os.path.join(self.assets_path, "audio", "animalese", self.gender, self.voice, f"{name}.wav")
        elif category == "sfx":
            return os.path.join(self.assets_path, "audio", "sfx", f"{name}.wav")
        elif category == "vocals":
            return os.path.join(self.assets_path, "audio", "vocals", self.gender, self.voice, f"{name}.wav")
        return ""

    def _load_audio(self, path: str) -> Optional[tuple[np.ndarray, int]]:
        if path in self._audio_cache:
            return self._audio_cache[path]

        if not os.path.exists(path):
            return None

        try:
            data, sr = sf.read(path)
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            self._audio_cache[path] = (data.astype(np.float32), sr)
            return self._audio_cache[path]
        except Exception as e:
            print(f"Error loading audio {path}: {e}")
            return None

    def _apply_pitch_shift(self, audio: np.ndarray, sr: int, semitones: float) -> np.ndarray:
        if abs(semitones) < 0.01:
            return audio

        factor = 2 ** (semitones / 12.0)
        new_length = int(len(audio) / factor)

        if new_length < 2:
            return audio

        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)

        return resampled.astype(np.float32)

    def _apply_volume(self, audio: np.ndarray, volume: float) -> np.ndarray:
        return (audio * volume * 0.95).astype(np.float32)

    def _process_audio(self, audio: np.ndarray, sr: int, volume: float,
                       rand_pitch: float, pitch: float, use_profile: bool) -> np.ndarray:
        profile_pitch = self.sound_profile.pitch_shift if use_profile else 0.0
        profile_variation = self.sound_profile.pitch_variation if use_profile else 0.0

        total_pitch = pitch + profile_pitch
        variation = (random.random() * 6 - 3) * (profile_variation + rand_pitch)
        total_pitch += variation

        processed = self._apply_pitch_shift(audio, sr, total_pitch)
        processed = self._apply_volume(processed, volume)

        return processed

    def play_sound(self, category: str, name: str, volume: float = 0.5,
                   rand_pitch: float = 0.0, pitch: float = 0.0, use_profile: bool = False) -> float:
        """Play a sound and return its duration in seconds."""
        path = self._get_audio_path(category, name)
        result = self._load_audio(path)

        if result is None:
            return 0.0

        audio, sr = result
        processed = self._process_audio(audio, sr, volume, rand_pitch, pitch, use_profile)

        if self._output_callback:
            self._output_callback(processed, sr)

        return len(processed) / sr

    def play_letter(self, letter: str, uppercase: bool = False) -> float:
        """Play a letter sound and return its duration in seconds."""
        if not letter.isalpha():
            return 0.0

        letter_lower = letter.lower()

        if uppercase:
            return self.play_sound("animalese", letter_lower, volume=0.7, rand_pitch=0.15, pitch=1.6, use_profile=True)
        else:
            return self.play_sound("animalese", letter_lower, volume=0.5, rand_pitch=0.0, pitch=0.0, use_profile=True)

    def play_special(self, key: str) -> float:
        """Play a special character sound and return its duration in seconds."""
        special_map = {
            "?": ("sfx", "question", 0.6),
            "!": ("sfx", "exclamation", 0.6),
            "~": ("sfx", "tilde", 0.6),
            "@": ("sfx", "at", 0.6),
            "#": ("sfx", "pound", 0.6),
            "$": ("sfx", "dollar", 0.6),
            "%": ("sfx", "percent", 0.6),
            "^": ("sfx", "caret", 0.6),
            "&": ("sfx", "ampersand", 0.6),
            "*": ("sfx", "asterisk", 0.6),
            "(": ("sfx", "parenthesis_open", 0.6),
            ")": ("sfx", "parenthesis_closed", 0.6),
            "[": ("sfx", "bracket_open", 0.6),
            "]": ("sfx", "bracket_closed", 0.6),
            "{": ("sfx", "brace_open", 0.6),
            "}": ("sfx", "brace_closed", 0.6),
            "/": ("sfx", "slash_forward", 0.6),
            "\\": ("sfx", "slash_back", 0.6),
            "\n": ("sfx", "enter", 0.2),
            "\t": ("sfx", "tab", 0.5),
            "\b": ("sfx", "backspace", 1.0),
        }

        if key in special_map:
            category, name, volume = special_map[key]
            return self.play_sound(category, name, volume=volume)
        elif key.isdigit():
            idx = int(key) - 1 if key != "0" else 9
            return self.play_sound("vocals", str(idx), volume=1.0)
        return 0.0

    def speak_text(self, text: str, delay_ms: int = 80, callback: Optional[Callable[[int], None]] = None):
        """Speak text character by character with animalese sounds.

        Args:
            text: The text to speak
            delay_ms: Delay between characters in milliseconds
            callback: Optional callback called with character index as each char is spoken
        """
        def _speak_thread():
            for i, char in enumerate(text):
                if char.isalpha():
                    self.play_letter(char, char.isupper())
                elif char in " \t\n":
                    pass
                else:
                    self.play_special(char)

                if callback:
                    callback(i)

                time.sleep(delay_ms / 1000.0)

        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
        return thread
