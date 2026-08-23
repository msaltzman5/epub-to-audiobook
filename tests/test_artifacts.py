from book2audio.artifacts import ArtifactDetector
from book2audio.models import Page, TextBlock


def make_pages(n=12):
    pages = []
    for i in range(1, n + 1):
        pages.append(Page(
            number=i,
            width=600,
            height=800,
            blocks=[
                TextBlock("The chapter text continues.", 80, 120, 520, 150, 0),
                TextBlock(str(i), 290, 755, 310, 770, 1),
            ],
        ))
    return pages


def test_sequential_page_numbers_removed():
    pages = make_pages()
    detector = ArtifactDetector(min_pages=5, min_frequency=0.45)
    removed = detector.detect(pages)

    assert len(removed) == 12
    assert all((i, 1) in removed for i in range(1, 13))
