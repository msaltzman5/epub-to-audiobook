from doctr.io import DocumentFile
from doctr.models import ocr_predictor

# 1. Load the PDF
# doc = DocumentFile.from_pdf("books/zen/zen.pdf")
# doc = DocumentFile.from_pdf("books/test/s41598-025-14985-y.pdf")
# doc = DocumentFile.from_pdf("books/test/Malcolm Saltzman - Resume.pdf")
doc = DocumentFile.from_pdf("books/test/zen56.pdf")


# 2. Initialize the model (downloads pretrained weights automatically)
model = ocr_predictor(
  pretrained=True,
  resolve_blocks=True,   # Critical: enables paragraph detection
  # paragraph_break=0.1  # Optional: tune sensitivity (default=0.035)
  assume_straight_pages=True,
)

# 3. Run OCR
result = model(doc)

# Paragraphs are now constrained within detected layout regions
# for page in result.pages:
#     for block in page.blocks:
#         # Process block
#         print(block)
#         pass

# # Export full structure to JSON (includes bounding boxes and confidence scores)
json_output = result.export()

# Extract simple plain text
plain_text = "\n".join(
    word.value 
    for page in result.pages 
    for block in page.blocks 
    for line in block.lines 
    for word in line.words
)
print(plain_text)

# Displays a window with detected text boxes
# result.show()

# result.render()