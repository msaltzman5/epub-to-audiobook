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
                # TODO: call edge-tss function on cleaned txt file
            else:
                print("txt failed to clean")
        else:
            print("file failed to convert to txt D:")
    else:
        print("file path does not exist. try again :)")

def convert_pdf_to_text(filepath: str) -> str:
    result = subprocess.run(
        [
            '/home/msaltzman/Downloads/xpdf-tools-linux-4.06/bin64/pdftotext',
            '-marginb',
            '90',
            '-nopgbrk',
            f'{filepath}'
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        new_filepath = os.path.splitext(filepath)[0] + ".txt"
        return new_filepath
    else: 
        return "uh oh"

    return result.returncode == 0

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

if __name__ == "__main__":
    main()