from typing import Optional

from bs4 import BeautifulSoup, Comment, NavigableString


def _clean_xml(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return str(soup)


def simplify_html(soup: BeautifulSoup, keep_attr: bool = False) -> str:
    # Remove scripts and styles
    for script in soup(["script", "style"]):
        script.decompose()

    # Remove all attributes
    if not keep_attr:
        for tag in soup.find_all(True):
            tag.attrs = {}

    # Remove empty tags recursively
    while True:
        removed = False
        for tag in soup.find_all():
            if not tag.get_text(strip=True):
                tag.decompose()
                removed = True
        if not removed:
            break

    # Remove href attributes from anchors
    for tag in soup.find_all("a"):
        if "href" in tag.attrs:
            del tag["href"]

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    def concat_text(text: str) -> str:
        text = "".join(text.split("\n"))
        text = "".join(text.split("\t"))
        text = "".join(text.split(" "))
        return text

    # Remove all tags that add no text beyond their single child
    for tag in soup.find_all():
        children = [child for child in tag.contents if not isinstance(child, NavigableString)]
        if len(children) == 1:
            tag_text = tag.get_text() or ""
            child_text = "".join([child.get_text() for child in tag.contents if not isinstance(child, NavigableString)])
            if concat_text(child_text) == concat_text(tag_text):
                tag.unwrap()

    # Remove empty lines from final string
    res = str(soup)
    lines = [line for line in res.split("\n") if line.strip()]
    res = "\n".join(lines)
    return res


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    simplified = simplify_html(soup)
    return _clean_xml(simplified)


