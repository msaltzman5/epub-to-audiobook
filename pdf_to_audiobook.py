import sys
import os
import subprocess
import edge_tts
import asyncio


def prompt_int(prompt: str, default: int = 0) -> int:
    value = input(f"{prompt} [{default}]: ").strip()
    return int(value) if value else default

def prompt_bool(prompt: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input(f"{prompt} ({suffix}): ").strip().lower()

    if not value:
        return default
    return value in ("y", "yes")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.pdf>")
        sys.exit(1)

    input_filepath = sys.argv[1]

    if not os.path.exists(input_filepath):
        print("File path does not exist. try again :)")
        sys.exit(1)

    print("\n=== Manual Margin Configuration ===\n")
    margins = {
        "top": prompt_int("Top margin", 0),
        "bottom": prompt_int("Bottom margin", 0),
        "left": prompt_int("Left margin", 0),
        "right": prompt_int("Right margin", 0),
    }

    include_page_breaks = prompt_bool("Include page breaks?", default=False)

    print("\nRunning conversion with settings:")
    for k, v in margins.items():
        print(f"  {k.capitalize():<6}: {v}")
    print(f"  Page breaks: {'ON' if include_page_breaks else 'OFF'}\n")

    txt_filepath = convert_pdf_to_text(
        filepath=input_filepath,
        margins=margins,
        include_page_breaks=include_page_breaks
    )

    if os.path.exists(txt_filepath):
        cleaned_txt_filepath = clean_characters(txt_filepath)
        if os.path.exists(cleaned_txt_filepath):
            print("✅ File converted to txt")
            txt_to_speech(cleaned_txt_filepath)
        else:
            print("❌ TXT failed to clean")
    else:
        print("❌ File failed to convert to txt")

def convert_pdf_to_text(filepath: str, margins: dict, include_page_breaks: bool) -> str:

    if "linux" in sys.platform:
        package_command = "packages/xpdf-tools-linux-4.06/bin64/pdftotext"
    elif "win" in sys.platform:
        package_command = "packages/xpdf-tools-win-4.06/bin64/pdftotext.exe"
    else:
        print("unknown OS")
        return "uh oh"

    command = [package_command]

    # ---- Margin loop ----
    margin_flags = {
        "top": "-margint",
        "bottom": "-marginb",
        "left": "-marginl",
        "right": "-marginr",
    }

    for side, value in margins.items():
        if value > 0:
            command.extend([margin_flags[side], str(value)])

    # ---- Page break handling ----
    if not include_page_breaks:
        command.append("-nopgbrk")

    command.append(filepath)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return os.path.splitext(filepath)[0] + ".txt"

    print(result.stderr)
    return "uh oh"

# TODO: fix this on windows
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

    async def generate_speech(input_file: str, output_file: str):
        with open(input_file, "r", encoding="utf-8") as file:
            text = file.read()
        voice = 'en-US-AndrewNeural'
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

    directory, file = os.path.split(filepath)
    new_file_name = file.replace("_cleaned.txt", ".mp3")
    new_file_path = f'{directory}/{new_file_name}'

    print(filepath)
    print(new_file_path)

    print(f"converting {filepath.replace("_cleaned.txt", ".pdf")} to audiobook!")

    asyncio.run(
        generate_speech(filepath, new_file_path)
    )

    print(f"audiobook ready to listen to at {new_file_path}!")

    # result = subprocess.run(
    #     [
    #         'edge-tts',
    #         '--voice',
    #         'en-US-AndrewNeural',
    #         '--file',
    #         f'{filepath}',
    #         '--write-media',
    #         f'{directory}/{new_file_name}'
    #     ],
    #     capture_output=True,
    #     text=True
    # )

    # print(result.stderr)

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