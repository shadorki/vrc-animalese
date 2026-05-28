#!/usr/bin/env python3
"""Animalese Chatbox for VRChat

Sends text to VRChat's chatbox with animalese voice sounds routed to a virtual microphone.
"""

import os
import random
import sys
import threading
import time
from typing import Optional
from chatbox_gui import ChatboxGui, ChatboxSettings
from animalese_engine import AnimaleseEngine
from virtual_mic import VirtualMicrophone
from vrchat_chatbox import VRChatChatbox

class AnimaleseChatbox:
    def __init__(self):
        self.gui: Optional[ChatboxGui] = None
        self.engine: Optional[AnimaleseEngine] = None
        self.virtual_mic: Optional[VirtualMicrophone] = None
        self.chatbox: Optional[VRChatChatbox] = None

        self._speaking = False
        self._speak_thread: Optional[threading.Thread] = None
        self._mic_enabled = False

    def _get_assets_path(self) -> str:
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "animalese", "assets")

    def _on_settings_changed(self, settings: ChatboxSettings):
        if self.engine:
            self.engine.set_voice(settings.gender.value, settings.voice.value)
            self.engine.set_profile(
                pitch_shift=settings.pitch_shift,
                pitch_variation=settings.pitch_variation
            )

    def _on_mic_toggle(self, enabled: bool):
        self._mic_enabled = enabled
        if enabled:
            self.virtual_mic.set_device(None)
            if self.virtual_mic.start():
                device_name = self.virtual_mic.get_device_name()
                self.gui.set_status(f"Audio output: {device_name}")
            else:
                self.gui.set_status("Failed to start audio - install VB-Cable")
                self._mic_enabled = False
        else:
            self.virtual_mic.stop()
            self.gui.set_status("Audio output disabled")

    def _on_send(self, text: str):
        if self._speaking:
            return

        self._speaking = True
        self.gui.set_speaking(True)

        settings = self.gui.settings

        def _play_audio():
            for char in text:
                duration = 0.0
                if char.isalpha():
                    duration = self.engine.play_letter(char, char.isupper())
                elif char not in " \t\n":
                    duration = self.engine.play_special(char)
                if duration > 0:
                    time.sleep(duration * 0.5)

        def _send_text():
            total_chars = len(text)
            i = 0

            if settings.show_typing:
                self.chatbox.set_typing(True)

            while i < total_chars:
                chunk_size = random.randint(3, 5)
                i = min(i + chunk_size, total_chars)
                partial = text[:i]

                if settings.show_typing and settings.auto_send:
                    self.chatbox.send_message(partial, immediate=True, sound=False)

                self.gui.update_typing_indicator(i, total_chars)
                time.sleep(chunk_size * settings.speech_rate / 1000.0)

            if settings.show_typing:
                self.chatbox.set_typing(False)

            if settings.auto_send:
                self.chatbox.send_message(text, immediate=True, sound=False)

            self._speaking = False
            self.gui.set_speaking(False)

        threading.Thread(target=_play_audio, daemon=True).start()
        self._speak_thread = threading.Thread(target=_send_text, daemon=True)
        self._speak_thread.start()

    def _audio_callback(self, audio, sample_rate):
        if self._mic_enabled:
            self.virtual_mic.write_audio(audio, sample_rate, blocking=False)

    def init(self):
        assets_path = self._get_assets_path()

        if not os.path.exists(assets_path):
            print(f"Error: Assets not found at {assets_path}")
            print("Make sure the 'animalese' folder with assets is present.")
            sys.exit(1)

        self.engine = AnimaleseEngine(assets_path)
        self.virtual_mic = VirtualMicrophone()
        self.chatbox = VRChatChatbox()

        self.engine.set_output_callback(self._audio_callback)

        self.gui = ChatboxGui(
            window_width=500,
            window_height=700
        )
        self.gui.set_on_send(self._on_send)
        self.gui.set_on_settings_changed(self._on_settings_changed)
        self.gui.set_on_mic_toggle(self._on_mic_toggle)

        self.gui.init()

        if not self.chatbox.connect():
            self.gui.set_status("Warning: Could not connect to VRChat OSC")

        devices = VirtualMicrophone.list_devices()
        cable = VirtualMicrophone.find_virtual_cable()
        if cable is not None:
            self.gui.set_status("VB-Cable found - click 'Audio: OFF' to enable")
        elif devices:
            self.gui.set_status("VB-Cable not found - install from vb-audio.com/Cable")
        else:
            self.gui.set_status("No audio devices found - install sounddevice")

    def run(self):
        try:
            self.gui.run()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        if self.chatbox:
            self.chatbox.disconnect()
        if self.virtual_mic:
            self.virtual_mic.stop()
        if self.gui:
            self.gui.cleanup()

def main():
    app = AnimaleseChatbox()
    app.init()
    app.run()

if __name__ == "__main__":
    main()
