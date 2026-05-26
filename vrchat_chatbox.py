from pythonosc import udp_client
from typing import Optional
import threading
import time

class VRChatChatbox:
    """Handles sending messages to VRChat's chatbox via OSC.

    VRChat OSC Chatbox API:
    - /chatbox/input s b n - Send text (s=text, b=send immediately, n=play notification sound)
    - /chatbox/typing b - Set typing indicator (b=is typing)
    """

    OSC_ADDRESS = "127.0.0.1"
    OSC_PORT = 9000

    CHATBOX_INPUT = "/chatbox/input"
    CHATBOX_TYPING = "/chatbox/typing"

    MAX_MESSAGE_LENGTH = 144

    def __init__(self, address: str = OSC_ADDRESS, port: int = OSC_PORT):
        self.address = address
        self.port = port
        self._client: Optional[udp_client.SimpleUDPClient] = None
        self._typing_thread: Optional[threading.Thread] = None
        self._stop_typing = threading.Event()

    def connect(self) -> bool:
        try:
            self._client = udp_client.SimpleUDPClient(self.address, self.port)
            return True
        except Exception as e:
            print(f"Failed to connect to VRChat OSC: {e}")
            return False

    def disconnect(self):
        self.set_typing(False)
        self._client = None

    def send_message(self, text: str, immediate: bool = True, sound: bool = False):
        """Send a message to the VRChat chatbox.

        Args:
            text: The message text (max 144 characters)
            immediate: If True, send immediately. If False, fill the chatbox input.
            sound: If True, play the notification sound.
        """
        if not self._client:
            if not self.connect():
                return

        text = text[:self.MAX_MESSAGE_LENGTH]

        try:
            self._client.send_message(self.CHATBOX_INPUT, [text, immediate, sound])
        except Exception as e:
            print(f"Failed to send chatbox message: {e}")

    def set_typing(self, is_typing: bool):
        """Set the typing indicator state."""
        self._stop_typing.set()

        if not self._client:
            if not self.connect():
                return

        try:
            self._client.send_message(self.CHATBOX_TYPING, is_typing)
        except Exception as e:
            print(f"Failed to set typing indicator: {e}")

    def send_typing_text(self, text: str, char_delay_ms: int = 80, callback=None):
        """Send text to chatbox character by character with typing indicator.

        This simulates typing by sending progressively longer portions of the text.

        Args:
            text: The full message to "type"
            char_delay_ms: Delay between characters in milliseconds
            callback: Optional callback(current_index, total_length) called per character
        """
        if not self._client:
            if not self.connect():
                return

        self._stop_typing.clear()

        def _typing_thread():
            self.set_typing(True)

            for i in range(len(text)):
                if self._stop_typing.is_set():
                    break

                partial = text[:i + 1]
                self.send_message(partial, immediate=True, sound=False)

                if callback:
                    callback(i, len(text))

                time.sleep(char_delay_ms / 1000.0)

            self.set_typing(False)

            if not self._stop_typing.is_set():
                self.send_message(text, immediate=True, sound=False)

        self._typing_thread = threading.Thread(target=_typing_thread, daemon=True)
        self._typing_thread.start()

    def stop_typing(self):
        """Stop the current typing animation."""
        self._stop_typing.set()
        self.set_typing(False)

    def clear(self):
        """Clear the chatbox by sending an empty message."""
        self.send_message("", immediate=True, sound=False)
