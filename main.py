

def pix_to_image(pix):
    import numpy as np
    
    bytes = np.frombuffer(pix.samples, dtype=np.uint8)
    img = bytes.reshape(pix.height, pix.width, pix.n)
    return img

def main():
    import pytesseract
    import pymupdf
    import cv2
    # import os
    

    doc = pymupdf.open("books/zen/zen.pdf") # open a document

    pages = []

    print("converting pages to images")
    for i, page in enumerate(doc):
        pix = page.get_pixmap()
        pages.append(pix)


    for i, page in enumerate(pages):


        # page = doc[214].get_pixmap()
        image = pix_to_image(page)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("temp/gray.jpg", gray)

        blur = cv2.GaussianBlur(gray, (7,7), 0)
        # cv2.imwrite("temp/blur.jpg", blur)

        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        # cv2.imwrite("temp/threshhold.jpg", thresh)

        kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (25,10))
        # cv2.imwrite("temp/kernal.jpg", kernal)

        dilate = cv2.dilate(thresh, kernal, iterations=1)
        # cv2.imwrite("temp/dilate.jpg", dilate)

        contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0])
        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            if h > 20 and w > 20:
                cv2.rectangle(gray, (x,y), (x+w,y+h), (36,255,12), 2)
        # new_dir = f"temp/page_{i+1}"
        # if not os.path.exists(new_dir):
        #     os.makedirs(new_dir)
        cv2.imwrite(f"temp/page_{i+1}_bbox.jpg", gray)


    # PDF path
    # pdf_path = 'books/zen/zen.pdf'
    # pdf_path = 'books/test/test.epub'

    # print("Converting PDF to image")
    # pages = convert_from_path(pdf_path, 300)

    # Define the path to your image.
    # image_path = 'books/test/test.png'

    # Open the image.
    # image = Image.open(image_path)

    # extracted_text = []
    # config = '--psm 3 -l eng'
    # print("extracting text from image")
    # for page in pages:
    #     extracted_text.append(pytesseract.image_to_string(page, config=config))

    # # Print the extracted text.
    # print(extracted_text)

    # with open("output.txt", "w") as output_file:
    #     output_file.write(extracted_text)

if __name__ == "__main__":
    main()