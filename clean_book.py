def main():

    def remove_c1_control_characters(text):
        """
        Remove C1 control characters (0x80-0x9F) from a string.
        These often appear due to incorrect encoding interpretation.
        """
        return ''.join(char for char in text if ord(char) not in range(0x80, 0xA0))

    with open('books/zen/zen.txt', 'r', encoding='latin-1') as f:
        data = f.read()
    
    cleaned_data = remove_c1_control_characters(data)

    with open('books/zen/zen_cleaned.txt', 'w') as f:
        f.write(cleaned_data)

    return 0

if __name__ == "__main__":
    main()