

def main():
    from PIL import Image
    import pytesseract
    import pymupdf

    doc = pymupdf.open("books/zen/zen.pdf") # open a document

    pages = []

    for i, page in enumerate(doc):
        pix = page.get_pixmap()

        pages.append(pix)
        # print(f"Page {i + 1}/{len(doc)}: {label}")



    # PDF path
    # pdf_path = 'books/zen/zen.pdf'
    # pdf_path = 'books/test/test.epub'

    # print("Converting PDF to image")
    # pages = convert_from_path(pdf_path, 300)

    # Define the path to your image.
    # image_path = 'books/test/test.png'

    # Open the image.
    # image = Image.open(image_path)

    extracted_text = []
    config = '--psm 3 -l eng'
    print("extracting text from image")
    for page in pages:
        extracted_text.append(pytesseract.image_to_string(page, config=config))

    # Print the extracted text.
    print(extracted_text)

    # Optional: Save the preprocessed image for review.
    # image.save('preprocessed_image.jpg')

    with open("output.txt", "w") as output_file:
        output_file.write(extracted_text)

if __name__ == "__main__":
    main()