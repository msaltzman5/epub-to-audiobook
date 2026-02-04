# epub-to-audiobook

## Install
python
pip

## Activate environment
python -m venv .venv
source .venv/bin/activate
pip install edge-tts

## Usage
edge-tts --voice en-US-AndrewNeural --text "Hi! How are you?" --write-media test.mp3