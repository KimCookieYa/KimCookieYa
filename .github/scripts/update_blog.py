import feedparser
import re
from datetime import datetime

USER_AGENT = (
    "Mozilla/5.0 (compatible; GitHubActions/1.0; "
    "+https://github.com/KimCookieYa/KimCookieYa)"
)

CELL_WIDTH = 280
IMAGE_MAX_HEIGHT = 180
TITLE_MAX_LEN = 40
DESCRIPTION_MAX_LEN = 50


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def truncate(text, max_len):
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def clean_html(raw_html):
    """HTML 태그 제거하고 텍스트만 추출하는 함수"""
    cleantext = re.sub(r"<.*?>", "", raw_html)
    cleantext = re.sub(r"\s+", " ", cleantext)
    cleantext = cleantext.replace("|", "").replace('"', "'").replace("&nbsp;", " ")
    return cleantext.strip()


def get_thumbnail(entry):
    """RSS 엔트리에서 썸네일 이미지 URL을 추출하는 함수"""
    if hasattr(entry, "media_thumbnail"):
        return entry.media_thumbnail[0]["url"]

    if hasattr(entry, "enclosures") and entry.enclosures:
        for enclosure in entry.enclosures:
            if enclosure.get("type", "").startswith("image/"):
                return enclosure.get("url")

    if hasattr(entry, "description"):
        img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
        if img_match:
            return img_match.group(1)

    return None


def format_date(date_str):
    """RSS의 날짜를 YYYY.MM.DD 형식으로 변환하는 함수"""
    try:
        date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return date_obj.strftime("%Y.%m.%d")
    except ValueError:
        return date_str


def format_cell(entry):
    """단일 블로그 포스트 셀 HTML 생성"""
    thumbnail = get_thumbnail(entry)
    title = truncate(entry.title.replace("|", ""), TITLE_MAX_LEN)
    link = entry.link
    description = truncate(
        clean_html(entry.get("description", "")), DESCRIPTION_MAX_LEN
    )
    pub_date = format_date(entry.get("published", ""))
    safe_title = escape_html(title)

    if thumbnail:
        image_html = (
            f'<a href="{link}">'
            f'<img src="{thumbnail}" width="{CELL_WIDTH}" '
            f'style="max-width:100%;height:auto;object-fit:contain;'
            f'max-height:{IMAGE_MAX_HEIGHT}px;display:block;margin:0 auto;" '
            f'alt="{safe_title}"></a>'
        )
    else:
        image_html = f'<div style="height:{IMAGE_MAX_HEIGHT}px;"></div>'

    return (
        f'<td width="33%" valign="top" align="center" '
        f'style="width:33%;vertical-align:top;text-align:center;">'
        f'{image_html}<br>'
        f'<b><a href="{link}">{safe_title}</a></b><br>'
        f'<sub>{escape_html(description)}</sub><br>'
        f'<sub>{pub_date}</sub>'
        f"</td>"
    )


def create_blog_table(feed_url, max_posts=6):
    """RSS 피드에서 블로그 글을 가져와 3x2 HTML 테이블 생성"""
    feed = feedparser.parse(feed_url, agent=USER_AGENT)
    entries = feed.entries[:max_posts]

    table = '<table width="100%">\n'

    for i in range(0, len(entries), 3):
        row_entries = entries[i : i + 3]
        table += "<tr>\n"

        for entry in row_entries:
            table += format_cell(entry)

        for _ in range(3 - len(row_entries)):
            table += (
                f'<td width="33%" valign="bottom" '
                f'style="width:33%;vertical-align:bottom;">&nbsp;</td>\n'
            )

        table += "</tr>\n"

    table += "</table>\n"
    return table


def update_readme(readme_path, table_content):
    """README.md 파일의 마커 사이 내용을 새로운 테이블로 업데이트"""
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- BLOG-POST-LIST:START -->"
    end_marker = "<!-- BLOG-POST-LIST:END -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        new_content = (
            content[: start_idx + len(start_marker)]
            + "\n"
            + table_content
            + "\n"
            + content[end_idx:]
        )

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print("README.md updated successfully!")
    else:
        print("Could not find markers in README.md")


if __name__ == "__main__":
    RSS_FEED_URL = "https://insengnewbie.tistory.com/rss"
    README_PATH = "README.md"

    print("Fetching blog posts from RSS feed...")
    table = create_blog_table(RSS_FEED_URL, max_posts=6)

    print("Updating README.md...")
    update_readme(README_PATH, table)
