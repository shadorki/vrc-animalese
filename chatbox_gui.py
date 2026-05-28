import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum, auto

class VoiceGender(Enum):
    FEMALE = "female"
    MALE = "male"

class VoiceType(Enum):
    VOICE_1 = "voice_1"
    VOICE_2 = "voice_2"
    VOICE_3 = "voice_3"

@dataclass
class ChatboxSettings:
    gender: VoiceGender = VoiceGender.FEMALE
    voice: VoiceType = VoiceType.VOICE_1
    pitch_shift: float = 0.0
    pitch_variation: float = 0.2
    speech_rate: int = 115
    volume: float = 0.5
    auto_send: bool = True
    show_typing: bool = True

class ChatboxGui:
    def __init__(self, window_width: int = 500, window_height: int = 600, logo_path: Optional[str] = None):
        self.window_width = window_width
        self.window_height = window_height
        self.logo_path = logo_path
        self.settings = ChatboxSettings()

        self._on_send: Optional[Callable[[str], None]] = None
        self._on_settings_changed: Optional[Callable[[ChatboxSettings], None]] = None
        self._on_mic_toggle: Optional[Callable[[bool], None]] = None

        self._input_tag = None
        self._history_tag = None
        self._status_tag = None
        self._mic_button_tag = None
        self._mic_enabled = False
        self._speaking = False

    def set_on_send(self, callback: Callable[[str], None]):
        self._on_send = callback

    def set_on_settings_changed(self, callback: Callable[[ChatboxSettings], None]):
        self._on_settings_changed = callback

    def set_on_mic_toggle(self, callback: Callable[[bool], None]):
        self._on_mic_toggle = callback

    def _notify_settings_changed(self):
        if self._on_settings_changed:
            self._on_settings_changed(self.settings)

    def _handle_send(self, sender=None, app_data=None):
        if self._speaking:
            return

        text = dpg.get_value(self._input_tag)
        if not text.strip():
            return

        self._add_to_history(f"> {text}")
        dpg.set_value(self._input_tag, "")

        if self._on_send:
            self._on_send(text)

    def _handle_key_press(self, sender, app_data):
        if app_data == dpg.mvKey_Return:
            if not dpg.is_key_down(dpg.mvKey_LShift) and not dpg.is_key_down(dpg.mvKey_RShift):
                self._handle_send()

    def _handle_gender_change(self, sender, app_data):
        self.settings.gender = VoiceGender.FEMALE if app_data == "Female" else VoiceGender.MALE
        self._notify_settings_changed()

    def _handle_voice_change(self, sender, app_data):
        voice_map = {"Voice 1": VoiceType.VOICE_1, "Voice 2": VoiceType.VOICE_2, "Voice 3": VoiceType.VOICE_3}
        self.settings.voice = voice_map.get(app_data, VoiceType.VOICE_1)
        self._notify_settings_changed()

    def _handle_pitch_shift(self, sender, app_data):
        self.settings.pitch_shift = app_data
        self._notify_settings_changed()

    def _handle_pitch_variation(self, sender, app_data):
        self.settings.pitch_variation = app_data
        self._notify_settings_changed()

    def _handle_speech_rate(self, sender, app_data):
        self.settings.speech_rate = app_data
        self._notify_settings_changed()

    def _handle_volume(self, sender, app_data):
        self.settings.volume = app_data
        self._notify_settings_changed()

    def _handle_auto_send(self, sender, app_data):
        self.settings.auto_send = app_data
        self._notify_settings_changed()

    def _handle_show_typing(self, sender, app_data):
        self.settings.show_typing = app_data
        self._notify_settings_changed()

    def _handle_mic_toggle(self, sender=None, app_data=None):
        self._mic_enabled = not self._mic_enabled
        label = "Audio: ON" if self._mic_enabled else "Audio: OFF"
        dpg.configure_item(self._mic_button_tag, label=label)

        if self._on_mic_toggle:
            self._on_mic_toggle(self._mic_enabled)

    def _add_to_history(self, text: str):
        current = dpg.get_value(self._history_tag)
        new_text = text + "\n" + current if current else text
        lines = new_text.split("\n")[:100]
        dpg.set_value(self._history_tag, "\n".join(lines))

    def set_status(self, text: str):
        if self._status_tag:
            dpg.set_value(self._status_tag, text)

    def set_speaking(self, speaking: bool):
        self._speaking = speaking
        if speaking:
            self.set_status("Speaking...")
        else:
            self.set_status("Ready")

    def update_typing_indicator(self, char_index: int, total: int):
        progress = (char_index + 1) / total if total > 0 else 0
        self.set_status(f"Speaking... {int(progress * 100)}%")

    def _create_centered_image(self, tag: str, path: str):
        try:
            image_width, image_height, _, data = dpg.load_image(path)
        except Exception:
            return lambda: None

        with dpg.texture_registry():
            dpg.add_static_texture(width=image_width, height=image_height, default_value=data, tag=tag)

        spacer_width = (self.window_width - image_width) / 2
        with dpg.group(horizontal=True):
            spacer1 = dpg.add_spacer(width=int(spacer_width) - 25)
            dpg.add_image(tag)
            spacer2 = dpg.add_spacer(width=int(spacer_width))

        def resize_callback():
            current_width = dpg.get_viewport_width()
            new_spacer = (current_width - image_width) / 2
            dpg.configure_item(spacer1, width=int(new_spacer) - 25)
            dpg.configure_item(spacer2, width=int(new_spacer))

        return resize_callback

    def _create_voice_settings(self):
        with dpg.collapsing_header(label="Voice Settings", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text("Gender:")
                dpg.add_radio_button(
                    items=["Female", "Male"],
                    default_value="Female",
                    horizontal=True,
                    callback=self._handle_gender_change
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Voice:")
                dpg.add_combo(
                    items=["Voice 1", "Voice 2", "Voice 3"],
                    default_value="Voice 1",
                    width=150,
                    callback=self._handle_voice_change
                )

            dpg.add_slider_float(
                label="Pitch Shift",
                default_value=0.0,
                min_value=-12.0,
                max_value=12.0,
                width=-100,
                callback=self._handle_pitch_shift
            )

            dpg.add_slider_float(
                label="Pitch Variation",
                default_value=0.2,
                min_value=0.0,
                max_value=1.0,
                width=-100,
                callback=self._handle_pitch_variation
            )

            dpg.add_slider_int(
                label="Speech Rate (ms)",
                default_value=115,
                min_value=5,
                max_value=200,
                width=-100,
                callback=self._handle_speech_rate
            )

            dpg.add_slider_float(
                label="Volume",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                width=-100,
                callback=self._handle_volume
            )

    def _create_chatbox_settings(self):
        with dpg.collapsing_header(label="Chatbox Settings", default_open=True):
            dpg.add_checkbox(
                label="Auto-send to VRChat",
                default_value=True,
                callback=self._handle_auto_send
            )
            dpg.add_checkbox(
                label="Show typing indicator",
                default_value=True,
                callback=self._handle_show_typing
            )

    def _create_chat_area(self):
        dpg.add_text("Message History")
        self._history_tag = dpg.add_input_text(
            multiline=True,
            readonly=True,
            height=150,
            width=-1
        )

        dpg.add_spacer(height=10)
        dpg.add_text("Type your message:")
        self._input_tag = dpg.add_input_text(
            multiline=True,
            height=80,
            width=-1,
            hint="Press Enter to send, Shift+Enter for new line"
        )

        with dpg.handler_registry():
            dpg.add_key_press_handler(callback=self._handle_key_press)

        dpg.add_spacer(height=10)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Send", callback=self._handle_send, width=100)
            self._mic_button_tag = dpg.add_button(
                label="Audio: OFF",
                callback=self._handle_mic_toggle,
                width=100
            )

        dpg.add_spacer(height=10)
        self._status_tag = dpg.add_text("Ready", color=(150, 150, 150))

    def init(self):
        dpg.create_context()

        with dpg.window(tag="MAIN_WINDOW"):
            dpg.add_spacer(height=10)

            resize_callback = lambda: None
            if self.logo_path:
                resize_callback = self._create_centered_image("logo", self.logo_path)

            dpg.add_spacer(height=10)
            dpg.add_text("Animalese Chatbox for VRChat", color=(100, 200, 255))
            dpg.add_separator()
            dpg.add_spacer(height=10)

            self._create_chat_area()
            dpg.add_spacer(height=20)

            self._create_voice_settings()
            dpg.add_spacer(height=10)

            self._create_chatbox_settings()
            dpg.add_spacer(height=20)

            dpg.add_button(
                label="Created by Shadoki - Not affiliated with VRChat",
                width=-1,
                enabled=False
            )

        dpg.create_viewport(
            title="Animalese Chatbox",
            width=self.window_width,
            height=self.window_height
        )
        dpg.set_viewport_resize_callback(resize_callback)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("MAIN_WINDOW", True)

    def run(self):
        dpg.start_dearpygui()

    def cleanup(self):
        dpg.destroy_context()
