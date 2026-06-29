import feedparser
import re
from datetime import datetime

USER_AGENT = (
    "Mozilla/5.0 (compatible; GitHubActions/1.0; "
    "+https://github.com/KimCookieYa/KimCookieYa)"
)


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


def create_blog_table(feed_url, max_posts=6):
    """RSS 피드에서 블로그 글을 가져와 3x2 테이블 형태의 마크다운 생성"""
    feed = feedparser.parse(feed_url, agent=USER_AGENT)
    entries = feed.entries[:max_posts]

    table = "| | | |\n"
    table += "|---|---|---|\n"

    for i in range(0, len(entries), 3):
        row_entries = entries[i : i + 3]
        row = "|"

        for entry in row_entries:
            thumbnail = get_thumbnail(entry)
            title = entry.title.replace("|", "")
            link = entry.link
            description = clean_html(entry.get("description", ""))[:50] + "..."
            pub_date = format_date(entry.get("published", ""))

            image_html = ""
            if thumbnail:
                image_html = (
                    f'<a href="{link}">'
                    f'<img src="{thumbnail}" width="300" height="200" alt="{title}"></a><br>'
                )

            # GitHub markdown tables require each cell on a single line
            cell = (
                f"{image_html}"
                f"<b><a href='{link}'>{title}</a></b><br>"
                f"{description}<br>"
                f"{pub_date}"
            )
            row += f" {cell} |"

        while len(row_entries) < 3:
            row += " |"
            row_entries.append(None)

        table += row + "\n"

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
