from book2audio.models import Page, TextBlock
from book2audio.pdf_clean import pdf_to_sections


def test_repeated_footer_does_not_survive():
    pages = []
    for i in range(1, 9):
        pages.append(Page(
            number=i,
            width=600,
            height=800,
            blocks=[
                TextBlock("A sentence that continues.", 80, 100, 520, 130, 0),
                TextBlock(str(i), 290, 755, 310, 770, 1),
            ],
        ))

    sections, diagnostics = pdf_to_sections(pages)
    all_text = "\n".join(
        p for s in sections for p in s.paragraphs
    )
    assert "\n1\n" not in f"\n{all_text}\n"
    assert diagnostics["removed_blocks"] >= 8
