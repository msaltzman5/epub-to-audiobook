import sys
import os
import subprocess

def main():

    input_filepath = sys.argv[1]

    if os.path.exists(input_filepath):
        print("exists")
        txt_filepath = convert_pdf_to_text(input_filepath)
        if os.path.exists(txt_filepath):
            cleaned_txt_filepath = clean_characters(txt_filepath)
            if os.path.exists(cleaned_txt_filepath):
                print("file converted to txt")
                txt_to_speech(cleaned_txt_filepath)
            else:
                print("txt failed to clean")
        else:
            print("file failed to convert to txt D:")
    else:
        print("file path does not exist. try again :)")

def convert_pdf_to_text(filepath: str) -> str:

    # Check to see what operating system this is running on
    if sys.platform.__contains__("linux"):
        result = subprocess.run(
            [
                'packages/xpdf-tools-linux-4.06/bin64/pdftotext',
                '-marginb',
                '90',
                '-nopgbrk',
                f'{filepath}'
            ],
            capture_output=True,
            text=True
        )
    elif sys.platform.__contains__("win"):
        result = subprocess.run(
            [
                'packages/xpdf-tools-win-4.06/bin64/pdftotext',
                '-marginb',
                '90',
                '-nopgbrk',
                f'{filepath}'
            ],
            capture_output=True,
            text=True
        )
    else:
        print("unknown OS")
        return "uh oh"

    if result.returncode == 0:
        new_filepath = os.path.splitext(filepath)[0] + ".txt"
        return new_filepath
    else: 
        return "uh oh"

# TODO: fix this 
def clean_characters(filepath: str) -> str:

    def remove_c1_control_characters(text):
        """
        Remove C1 control characters (0x80-0x9F) from a string.
        These often appear due to incorrect encoding interpretation.
        """
        return ''.join(char for char in text if ord(char) not in range(0x80, 0xA0))


    with open(filepath, 'r', encoding='latin-1') as f:
        data = f.read()
    
    cleaned_data = remove_c1_control_characters(data)

    directory = os.path.splitext(filepath)[0]

    with open(f'{directory}_cleaned.txt', 'w') as f:
        f.write(cleaned_data)

    return f"{directory}_cleaned.txt"

def txt_to_speech(filepath: str) -> str:

    directory, file = os.path.split(filepath)
    new_file_name = file.replace("_cleaned.txt", ".mp3")

    print(filepath)
    print(f'{directory}/{new_file_name}')

    result = subprocess.run(
        [
            'edge-tts',
            '--voice',
            'en-US-AndrewNeural',
            '--file',
            f'{filepath}',
            '--write-media',
            f'{directory}/{new_file_name}'
        ],
        capture_output=True,
        text=True
    )

    print(result.stderr)

    # Test
    # result = subprocess.run(
    #     [
    #         'edge-tts',
    #         '--voice',
    #         'en-US-AndrewNeural',
    #         '--text',
    #         'Hi! I would be really suprised if this was working. Is this working?',
    #         '--write-media',
    #         'testing.mp3'
    #     ],
    #     capture_output=True,
    #     text=True
    # )

if __name__ == "__main__":
    main()