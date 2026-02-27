# epub-to-audiobook

## Install
`python`  
`pip`  

## Activate environment
`python -m venv .venv`  
`source .venv/bin/activate` (or `.venv/Scripts/activate` on Windows)  
`pip install -r requirements.txt`  

## Usage
`python pdf_to_audiobook.py <directory_to_pdf>/<pdf_name>.pdf`

## Test edge-tts
`edge-tts --voice en-US-AndrewNeural --text "Hi! How are you?" --write-media test.mp3`

## pdf to text
1. Download Xpdf command line tools from https://www.xpdfreader.com/download.html  
2. Unzip download so you can execute the binaries  
3. `/home/msaltzman/Downloads/xpdf-tools-linux-4.06/bin64/pdftotext -marginb 90 -nopgbrk books/zen/zen.pdf`  
    a. pdftotext man: https://www.xpdfreader.com/pdftotext-man.html  
4. `python3 clean_book.py`  
    a. this should clean txt file
5. `edge-tts --voice en-US-AndrewNeural --file <books_directory>/<book_cleaned.pdf> --write-media test.mp3`
