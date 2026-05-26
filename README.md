# Animalese Chatbox for VRChat

A VRChat chatbox that speaks your messages using Animal Crossing-style animalese sounds, routed through a virtual audio cable so others can hear you!

> **Disclaimer:** This application is not affiliated with VRChat or Nintendo. Use at your own risk.

## Features

- Type messages that get sent to VRChat's chatbox via OSC
- Each character plays an animalese sound (like Animal Crossing villagers)
- Virtual microphone output - others in VRChat can hear your animalese voice
- Customizable voice settings (gender, pitch, speed, variation)
- Typing indicator support

## Requirements

- Windows 10/11
- Python 3.10+
- [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) (free)

## Installation

1. Install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) - it's a small driver (~1MB), no background app needed

2. Clone the repository:
   ```shell
   git clone https://github.com/shadorki/vrc-owo-suit.git
   cd vrc-owo-suit
   ```

3. Install dependencies:
   ```shell
   pip install -r requirements.txt
   ```

4. Run the chatbox:
   ```shell
   python chatbox_main.py
   ```

## VRChat Setup

1. In VRChat, enable OSC: Action Menu > Options > OSC > Enabled
2. In the app, click "Audio: OFF" to enable audio output (it will auto-detect VB-Cable)
3. In VRChat audio settings, select **CABLE Output** as your microphone input

## Usage

1. Type your message in the text box
2. Press Enter to send (Shift+Enter for new line)
3. The app "speaks" each character with animalese sounds
4. The message appears in VRChat's chatbox as it's being spoken
5. Others hear your animalese voice through the virtual cable

## Settings

### Voice Settings

| Setting | Description |
|---------|-------------|
| Gender | Female or Male voice |
| Voice | Different voice variations (Voice 1, 2, 3) |
| Pitch Shift | Raise or lower the overall pitch (-12 to +12 semitones) |
| Pitch Variation | Random pitch variation per character (0.0 - 1.0) |
| Speech Rate | Milliseconds between each character (lower = faster) |
| Volume | Output volume |

### Chatbox Settings

| Setting | Description |
|---------|-------------|
| Auto-send to VRChat | Automatically send text to VRChat's chatbox |
| Show typing indicator | Update the chatbox character-by-character as it speaks |

## Troubleshooting

**"VB-Cable not found"**: Make sure you've installed VB-Audio Virtual Cable and restarted your computer.

**No sound in VRChat**: Make sure you selected "CABLE Output" (not "CABLE Input") as your microphone in VRChat.

**OSC not working**: Delete the OSC folder at `%AppData%\..\LocalLow\VRChat\VRChat\OSC` and restart VRChat to regenerate it.

## Audio Assets

The animalese audio samples are from the [animalese-typing](https://github.com/joshxviii/animalese-typing) Chrome extension by Joshua Sherry.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
