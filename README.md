# epub-to-audiobook

## Install
`python`  
`pip`  

## Activate environment
`python -m venv .venv`  
`source .venv/bin/activate`  
`pip install edge-tts`  

## Usage
`edge-tts --voice en-US-AndrewNeural --text "Hi! How are you?" --write-media test.mp3`

## pdf to text
1. Download Xpdf command line required  
2. Unzip download so you can execute the binaries  
3. `/home/msaltzman/Downloads/xpdf-tools-linux-4.06/bin64/pdftotext <books_directory>/<book>.pdf`  
    a. pdftotext man: https://www.xpdfreader.com/pdftotext-man.html  
4. `python3 main.py`  
    a. this should clean txt file
5. `edge-tts --voice en-US-AndrewNeural --file <books_directory>/<book_cleaned.pdf> --write-media test.mp3`
