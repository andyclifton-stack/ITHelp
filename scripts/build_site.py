import html
import json
import os
import re
import shutil
import textwrap
import stat
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOME = "https://sites.google.com/claremontschool.co.uk/claremontschoolit/home"
SOURCE_PREFIX = "https://sites.google.com/claremontschool.co.uk/claremontschoolit"
SITE_PATH_PREFIX = "/claremontschool.co.uk/claremontschoolit"

CATEGORY_ORDER = [
    "Start Here",
    "Requests & Support",
    "Classlink",
    "Google Workspace",
    "Microsoft Teams",
    "iSAMS",
    "Printing",
    "Office Desk Phones",
    "Devices & Windows",
    "School Systems",
    "Security",
    "Room Help",
    "Files & Conversion",
    "Miscellaneous",
]

CATEGORY_LABELS = {
    "Google - Drive, Mail, Meet etc": "Google Workspace",
    "Conversion, general file problems": "Files & Conversion",
    "Senior Specific Room Help": "Room Help",
    "Prep Specific Room Help": "Room Help",
}

CATEGORY_ICONS = {
    "Start Here": "M4 5.5h16M4 12h10M4 18.5h16",
    "Requests & Support": "M4 5h16v10H7l-3 3V5ZM8 9h8M8 12h5",
    "Classlink": "M7 8h10M7 12h10M7 16h6M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z",
    "Google Workspace": "M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v11A2.5 2.5 0 0 1 17.5 20h-11A2.5 2.5 0 0 1 4 17.5v-11ZM8 8h8M8 12h8M8 16h5",
    "Microsoft Teams": "M8 7h8M8 12h8M8 17h5M5 4h14v16H5V4Z",
    "iSAMS": "M12 4v16M5 8h14M6 16h12M8 4h8a3 3 0 0 1 0 6H8V4Z",
    "Printing": "M7 8V4h10v4M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 14h10v6H7v-6Z",
    "Office Desk Phones": "M8 5h8v14H8V5ZM10 8h4M10 11h4M10 14h1M13 14h1M10 17h4",
    "Devices & Windows": "M4 5h16v10H4V5ZM8 19h8M10 15v4M14 15v4",
    "School Systems": "M4 7h16M6 7v13h12V7M8 4h8v3H8V4ZM8 11h3M13 11h3M8 15h3M13 15h3",
    "Security": "M12 3l7 3v5c0 4.5-3 7.5-7 10-4-2.5-7-5.5-7-10V6l7-3ZM9.5 12l1.7 1.7 3.8-4",
    "Room Help": "M4 20V8l8-4 8 4v12M8 20v-7h8v7M9 9h.01M15 9h.01",
    "Files & Conversion": "M6 3h8l4 4v14H6V3ZM13 3v5h5M9 13h6M9 17h4",
    "Miscellaneous": "M5 5h6v6H5V5ZM13 5h6v6h-6V5ZM5 13h6v6H5v-6ZM13 13h6v6h-6v-6Z",
}

CATEGORY_OVERRIDES = {
    "Student Password Reset Form": "Requests & Support",
    "Submitting a Support Ticket": "Requests & Support",
    "Tab Wrangler": "Devices & Windows",
    "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More": "Devices & Windows",
    "Opening multiple favourite tabs": "Devices & Windows",
    "How to use Chrome Remote Desktop": "Devices & Windows",
    "No sound and the speaker icon has a red cross through it": "Devices & Windows",
    "Chromebook shortcuts": "Devices & Windows",
    "Changing display settings on Chromebook and Windows": "Devices & Windows",
    "Activating Text to Speech - Chromebook + Windows": "Devices & Windows",
    "Exam Information": "School Systems",
    "Sign In App": "School Systems",
    "OneDrive": "School Systems",
    "Photography Sharepoint": "School Systems",
    "What is the WiFi password (SSID:Internet)": "Requests & Support",
    "Accident Forms": "School Systems",
}

CATEGORY_ACCENTS = [
    "navy",
    "blue",
    "sky",
    "orange",
]

SKIP_TITLES = {
    "Universal Printer",
    "YouTube to MP3",
    "Engage Client",
    "Multi-Factor Authentication",
    "Multi-Factor Authentication - Google",
    "Signing in",
    "Student Portal",
}

LOCAL_MEDIA = {
    "Log-in Page": [
        {"type": "image", "file": "log-in-page.png", "alt": "ClassLink login page."},
    ],
    "Customisation": [
        {"type": "image", "file": "customisation-customlinks.png", "alt": "ClassLink custom links."},
        {"type": "image", "file": "customisation-favorites.png", "alt": "ClassLink favourites."},
        {"type": "image", "file": "customisation-folders.png", "alt": "ClassLink folders."},
    ],
    "Gmail Customisation": [
        {"type": "image", "file": "gmail-customisation-1.jpg", "alt": "Gmail customisation step 1."},
        {"type": "image", "file": "gmail-customisation-2.jpg", "alt": "Gmail customisation step 2."},
        {"type": "image", "file": "gmail-customisation-3.jpg", "alt": "Gmail customisation step 3."},
    ],
    "Add/edit your Gmail signature": [
        {"type": "image", "file": "gmail-signature-1.png", "alt": "Gmail signature settings."},
        {"type": "image", "file": "gmail-signature-2.png", "alt": "Gmail signature editor."},
    ],
    "Remove conversation view in Gmail": [
        {"type": "image", "file": "conversation-view-1.png", "alt": "Gmail conversation view setting."},
        {"type": "image", "file": "conversation-view-2.png", "alt": "Gmail conversation view switched off."},
    ],
    "Persistant Meet link in Google Calendar": [
        {"type": "image", "file": "persistent-meet.png", "alt": "Persistent Google Meet link in Calendar."},
        {"type": "video", "file": "persistent-meet-link-google-calendar.mp4", "caption": "Persistent Meet link walkthrough."},
    ],
    "How to Log Into Google Drive": [
        {"type": "image", "file": "school-drive-1.png", "alt": "Google Drive sign-in step 1."},
        {"type": "image", "file": "school-drive-2.png", "alt": "Google Drive sign-in step 2."},
        {"type": "image", "file": "school-drive-3.png", "alt": "Google Drive sign-in step 3."},
    ],
    "Recording Google Meets/Classroom": [
        {"type": "video", "file": "recording-google-meet.mp4", "caption": "Recording a Google Meet walkthrough."},
    ],
    "Guardian Summaries on Google Classroom": [
        {"type": "image", "file": "guardian-summaries.png", "alt": "Guardian summaries setting in Google Classroom."},
        {"type": "video", "file": "guardian-summaries.mp4", "caption": "Guardian summaries walkthrough."},
    ],
    "Creating a new Google Calendar": [
        {"type": "image", "file": "new-google-calendar.png", "alt": "Create a new Google Calendar."},
    ],
    "Presentation Template": [
        {"type": "image", "file": "presentation-template-1.png", "alt": "Presentation template step 1."},
        {"type": "image", "file": "presentation-template-2.png", "alt": "Presentation template step 2."},
        {"type": "image", "file": "presentation-template-3.png", "alt": "Presentation template step 3."},
    ],
    "Creating Microsoft Teams": [
        {"type": "video", "file": "creating-microsoft-teams.mp4", "caption": "Creating a Microsoft Team walkthrough."},
    ],
    "Theatre Projector & Sound (Senior)": [
        {"type": "video", "file": "senior-theatre-audio.mp4", "caption": "Senior theatre projector and sound walkthrough."},
    ],
    "Prep Meeting Room": [
        {"type": "image", "file": "prep-meeting-room-1.png", "alt": "Prep meeting room setup step 1."},
        {"type": "image", "file": "prep-meeting-room-2.png", "alt": "Prep meeting room setup step 2."},
        {"type": "image", "file": "prep-meeting-room-3.png", "alt": "Prep meeting room setup step 3."},
        {"type": "image", "file": "prep-meeting-room-4.png", "alt": "Prep meeting room setup step 4."},
    ],
    "Converting a file format": [
        {"type": "video", "file": "converting-file-format.mp4", "caption": "Converting a file format walkthrough."},
    ],
    "Files in a ZIP folder won't open": [
        {"type": "video", "file": "extracting-zip-folder.mp4", "caption": "Extracting files from a ZIP folder walkthrough."},
    ],
    "How do I Spot Phishing Emails": [
        {"type": "image", "file": "phish-1.png", "alt": "Phishing email example 1."},
        {"type": "image", "file": "phish-2.png", "alt": "Phishing email example 2."},
        {"type": "image", "file": "phish-3.png", "alt": "Phishing email example 3."},
        {"type": "image", "file": "phish-4.png", "alt": "Phishing email example 4."},
    ],
    "Exam papers printing with grid lines": [
        {"type": "image", "file": "exam-papers.png", "alt": "Exam paper print settings."},
    ],
    "Papercut Hive": [
        {"type": "image", "file": "hive.png", "alt": "Papercut Hive printing screen."},
    ],
    "Forwarding Calls": [
        {"type": "image", "file": "forwarding-calls.png", "alt": "Desk phone forwarding buttons."},
    ],
    "iSAMS": [
        {"type": "image", "file": "wizard-bar-isams.png", "alt": "iSAMS wizard bar."},
    ],
    "How to take a register": [
        {"type": "image", "file": "isams-register.png", "alt": "iSAMS register screen."},
        {"type": "video", "file": "registration-eng.mp4", "caption": "Taking a register walkthrough."},
    ],
    "Rewards and Conduct": [
        {"type": "image", "file": "rewards-and-conduct-1.png", "alt": "Rewards and conduct step 1."},
        {"type": "image", "file": "rewards-and-conduct-2.png", "alt": "Rewards and conduct step 2."},
    ],
    "How To View a Timetable": [
        {"type": "image", "file": "timetable-1.png", "alt": "Timetable view step 1."},
        {"type": "image", "file": "timetable-2.png", "alt": "Timetable view step 2."},
    ],
    "Writing Reports": [
        {"type": "image", "file": "writing-reports-1.png", "alt": "Writing reports step 1."},
        {"type": "image", "file": "writing-reports-2.png", "alt": "Writing reports step 2."},
    ],
    "Searching up a Student": [
        {"type": "image", "file": "search-a-student-1.png", "alt": "Search for a student step 1."},
        {"type": "image", "file": "search-a-student-2.png", "alt": "Search for a student step 2."},
    ],
    "Emailing Correspondents": [
        {"type": "image", "file": "correspondence-1.png", "alt": "Email correspondents step 1."},
        {"type": "image", "file": "correspondence-2.png", "alt": "Email correspondents step 2."},
        {"type": "image", "file": "correspondence-3.png", "alt": "Email correspondents step 3."},
        {"type": "image", "file": "correspondence-4.png", "alt": "Email correspondents step 4."},
    ],
    "Creating a Group": [
        {"type": "image", "file": "group1.png", "alt": "Create an iSAMS group step 1."},
        {"type": "image", "file": "group2.png", "alt": "Create an iSAMS group step 2."},
        {"type": "image", "file": "group3.png", "alt": "Create an iSAMS group step 3."},
        {"type": "image", "file": "group4.png", "alt": "Create an iSAMS group step 4."},
    ],
    "Emailing Students": [
        {"type": "image", "file": "emailing-students-1.png", "alt": "Email students step 1."},
        {"type": "image", "file": "emailing-students-2.png", "alt": "Email students step 2."},
        {"type": "image", "file": "emailing-students-3.png", "alt": "Email students step 3."},
        {"type": "image", "file": "emailing-students-4.png", "alt": "Email students step 4."},
    ],
    "Attendance data for your form": [
        {"type": "image", "file": "attendance-data-1.png", "alt": "Attendance data step 1."},
        {"type": "image", "file": "attendance-data-2.png", "alt": "Attendance data step 2."},
    ],
    "Finding Pupil Information": [
        {"type": "image", "file": "pupil-information-1.png", "alt": "Find pupil information step 1."},
        {"type": "image", "file": "pupil-information-2.png", "alt": "Find pupil information step 2."},
    ],
    "OneDrive": [
        {"type": "image", "file": "onedrive-1.png", "alt": "OneDrive setup step 1."},
        {"type": "image", "file": "onedrive-2.png", "alt": "OneDrive setup step 2."},
    ],
}

CUSTOM_ARTICLES = [
    {
        "title": "Chromebook won't turn on",
        "category": "Devices & Windows",
        "summary": "A quick key combination that often wakes a Chromebook when the screen is blank or the device appears not to turn on.",
        "text": "If a student says their Chromebook won't turn on, hold Refresh, tap Power once, then let go of Refresh when the screen lights up.",
        "body": """
          <p>If a student says their Chromebook will not turn on, this quick reset often wakes the device straight away.</p>
          <figure class="media-frame help-illustration">
            <img src="../../assets/img/chromebook-refresh-power.svg" alt="Hold Refresh, tap Power once, then release Refresh when the Chromebook screen lights up.">
          </figure>
          <h3>Ask the student to try this</h3>
          <ol>
            <li>Hold down the <strong>Refresh</strong> key, which looks like a circular arrow.</li>
            <li>While still holding Refresh, tap the <strong>Power</strong> button once.</li>
            <li>Let go of Refresh when the screen lights up.</li>
          </ol>
          <p>If the Chromebook still does not respond, plug it into charge for a few minutes and submit a support ticket.</p>
        """.strip(),
        "media": [],
        "output": "articles/chromebook-wont-turn-on/index.html",
        "source_url": "",
        "custom": True,
    },
    {
        "title": "ClassLink page not appearing automatically",
        "category": "Classlink",
        "summary": "What to do if the usual ClassLink home page does not open automatically or Google shows the generic ClassLink login finder.",
        "text": "If the ClassLink home page is not appearing automatically, search for ISP on the ClassLink login finder and choose Staff and Students, or go directly to https://launchpad.classlink.com/ispschools.",
        "body": """
          <p>Some staff have reported that the usual ClassLink home page is not appearing automatically. If you search for ClassLink on Google, you may see the generic ClassLink page that asks you to find your login page.</p>
          <figure class="media-frame help-illustration">
            <img src="../../../assets/img/classlink-find-login-page.svg" alt="ClassLink find your login page screen.">
          </figure>
          <h3>Option 1: Search for ISP</h3>
          <ol>
            <li>On the ClassLink page, type <strong>ISP</strong> into the <strong>Find your login page</strong> box.</li>
            <li>Select <strong>Staff and Students</strong>.</li>
            <li>You should then see the ISP landing page. ISP means International Schools Partnership.</li>
            <li>Select <strong>Sign in with Microsoft</strong>.</li>
          </ol>
          <h3>Option 2: Go directly to our login page</h3>
          <p>Use this direct link to bypass the login finder: <a href="https://launchpad.classlink.com/ispschools">https://launchpad.classlink.com/ispschools</a></p>
          <p>If you still cannot access ClassLink after trying these steps, please let IT know as soon as possible.</p>
        """.strip(),
        "media": [],
        "output": "articles/classlink/classlink-page-not-appearing-automatically/index.html",
        "source_url": "",
        "custom": True,
    },
    {
        "title": "ClassLink using a personal Microsoft account",
        "category": "Classlink",
        "summary": "How to fix ClassLink opening with a personal Microsoft account instead of your school account.",
        "text": "If ClassLink defaults to a personal Microsoft account, sign out at myaccount.microsoft.com and make sure your school account is the active account before returning to ClassLink.",
        "body": """
          <p>If ClassLink is defaulting to your personal Microsoft account instead of your school account, it is usually because a personal account has previously been used on the device and kept signed in.</p>
          <figure class="media-frame help-illustration">
            <img src="../../../assets/img/microsoft-account-switch.svg" alt="Sign out of a personal Microsoft account and return to ClassLink with your school account.">
          </figure>
          <h3>Fix the account selection</h3>
          <ol>
            <li>Go to <a href="https://myaccount.microsoft.com/">https://myaccount.microsoft.com/</a>.</li>
            <li>Select your profile picture or initials in the top-right corner.</li>
            <li>Sign out of your personal Microsoft account.</li>
            <li>Make sure your school account is the only account signed in. Sign in with your school account if needed.</li>
            <li>Go back to ClassLink. It should now take you through using your school account.</li>
          </ol>
          <p>If ClassLink still chooses the wrong account, submit a support ticket and IT can help clear the browser sign-in state.</p>
        """.strip(),
        "media": [],
        "output": "articles/classlink/classlink-using-a-personal-microsoft-account/index.html",
        "source_url": "",
        "custom": True,
    }
]

CLEANUPS = {
    "Sevice Desk": "Service Desk",
    "soltutions": "solutions",
    "origional": "original",
    "wont": "won't",
    "Youtube": "YouTube",
    "google ": "Google ",
    "google.": "Google.",
    "google,": "Google,",
    " do i ": " do I ",
    "how do i": "how do I",
    "How do i": "How do I",
    "add/remote": "add/remove",
    "SEPERATE": "SEPARATE",
    "seperate": "separate",
    "incase": "in case",
    "re quently": "frequently",
    "requently": "frequently",
    "sceen": "screen",
    "CLick": "Click",
    "Playstore": "Play Store",
    "Appstore": "App Store",
    "onli ne": "online",
    "u se": "use",
}
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Claremont IT static migration/1.0"})


def slugify(value):
    value = html.unescape(value).strip().lower()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "page"


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    for old, new in CLEANUPS.items():
        value = value.replace(old, new)
    return value


def excerpt(value, limit=180):
    value = clean_text(value)
    if len(value) <= limit:
        return value
    clipped = value[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return clipped + "..."


def fetch(url):
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def full_source_url(href):
    if not href:
        return ""
    if href.startswith(SITE_PATH_PREFIX):
        return "https://sites.google.com" + href
    return urljoin(SOURCE_HOME, href)


def normalize_source_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.startswith(SITE_PATH_PREFIX):
        return "https://sites.google.com" + path
    return url.split("#", 1)[0].rstrip("/")


def page_output_path(source_url):
    path = urlparse(source_url).path
    rel = path.split("/claremontschoolit/", 1)[-1].strip("/")
    if rel == "home":
        return "index.html"
    return f"articles/{rel}/index.html"


def relative_link(from_file, to_file):
    return Path(to_file).relative_to(ROOT).as_posix() if Path(to_file).is_absolute() else to_file


def href_for(source_url, from_output):
    target = page_output_path(source_url)
    return Path(target).as_posix()


def asset_path_for(article, filename):
    article_dir = ROOT / Path(article["output"]).parent
    asset_path = ROOT / "assets" / "media" / filename
    return Path(os.path.relpath(asset_path, article_dir)).as_posix()


def local_media_figure(article, item):
    src = html.escape(asset_path_for(article, item["file"]))
    if item["type"] == "video":
        caption = html.escape(item.get("caption", "Video walkthrough."))
        return (
            '<figure class="media-frame">'
            f'<video controls preload="metadata" src="{src}"></video>'
            f"<figcaption>{caption}</figcaption>"
            "</figure>"
        )
    alt = html.escape(item.get("alt", article["title"]))
    return f'<figure class="media-frame"><img src="{src}" alt="{alt}"></figure>'


def apply_local_media(article):
    items = LOCAL_MEDIA.get(article["title"])
    if not items:
        return article
    article["body"] = re.sub(
        r'<figure class="media-frame"><img src="https?://[^"]+" alt="[^"]*"></figure>\n?',
        "",
        article["body"],
    )
    article["body"] = article["body"].replace(
        '<p class="resource-link">This page references an embedded video or file, but the Google Site did not expose a direct public media link during migration. Use the original source link below if needed.</p>',
        "",
    )
    media_html = "\n".join(local_media_figure(article, item) for item in items)
    article["body"] = article["body"].rstrip() + "\n" + media_html
    article["media"] = [
        item
        for item in article["media"]
        if item["type"] not in {"image", "unresolved embedded media"}
    ]
    return article


def build_nav():
    soup = BeautifulSoup(fetch(SOURCE_HOME), "lxml")
    items = []
    current_category = "Start Here"
    seen = set()
    for a in soup.find_all("a"):
        label = clean_text(a.get_text(" ", strip=True))
        href = a.get("href")
        if not label:
            continue
        source_category_labels = set(CATEGORY_ORDER) | set(CATEGORY_LABELS.keys()) | {"Senior Specific Room Help", "Prep Specific Room Help"}
        if href is None and label in source_category_labels:
            current_category = CATEGORY_LABELS.get(label, label)
            continue
        if not href or not href.startswith(SITE_PATH_PREFIX):
            continue
        if label == "Claremont School IT":
            continue
        if label in SKIP_TITLES:
            continue
        source_url = normalize_source_url(full_source_url(href))
        if source_url in seen:
            continue
        seen.add(source_url)
        category = CATEGORY_OVERRIDES.get(label, CATEGORY_LABELS.get(current_category, current_category))
        if label == "Home":
            category = "Start Here"
        items.append({"title": label, "source_url": source_url, "category": category})
    return items


def rewrite_href(href):
    if not href:
        return "#"
    href = href.replace("?utm_source=chatgpt.com", "").replace("&utm_source=chatgpt.com", "")
    if href.startswith("#"):
        return href
    full = normalize_source_url(full_source_url(href))
    if full.startswith(SOURCE_PREFIX):
        return "/" + href_for(full, "")
    return href


def render_inline(node):
    if isinstance(node, NavigableString):
        text = re.sub(r"\s+", " ", str(node))
        for old, new in CLEANUPS.items():
            text = text.replace(old, new)
        return html.escape(text)
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name == "a":
        text = "".join(render_inline(child) for child in node.children).strip()
        href = rewrite_href(node.get("href"))
        if not text:
            text = html.escape(href)
        return f' <a href="{html.escape(href)}">{text}</a> '
    if name in {"strong", "b"}:
        return f"<strong>{''.join(render_inline(child) for child in node.children)}</strong>"
    if name in {"em", "i"}:
        return f"<em>{''.join(render_inline(child) for child in node.children)}</em>"
    if name == "br":
        return "<br>"
    return "".join(render_inline(child) for child in node.children)


def render_list(tag):
    name = "ol" if tag.name == "ol" else "ul"
    items = []
    for li in tag.find_all("li", recursive=False):
        text = render_inline(li).strip()
        if text:
            items.append(f"<li>{text}</li>")
    return f"<{name}>" + "".join(items) + f"</{name}>" if items else ""


def should_skip_tag(tag):
    if tag.find_parent(["li", "p", "h1", "h2", "h3", "ul", "ol"]):
        return True
    text = clean_text(tag.get_text(" ", strip=True))
    return text in {"Report abuse", "Page details", "Page updated"}


def should_skip_migrated_content(text):
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in [
            "ai chatbot",
            "uses chatgpt",
            "chatgpt and local knowledgebase",
        ]
    )


def extract_article(item):
    soup = BeautifulSoup(fetch(item["source_url"]), "lxml")
    h1 = None
    for candidate in soup.find_all("h1"):
        text = clean_text(candidate.get_text(" ", strip=True))
        if text:
            h1 = candidate
            break
    title = clean_text(h1.get_text(" ", strip=True)) if h1 else item["title"]
    if item["title"] == "Home":
        title = "Welcome to Claremont School IT"

    parts = []
    plain = []
    media = []
    resource_media = []
    resource_headings = []
    if h1:
        for tag in h1.find_all_next(["h2", "h3", "p", "ul", "ol", "table", "img", "iframe", "video", "a"]):
            if should_skip_tag(tag):
                continue
            text = clean_text(tag.get_text(" ", strip=True))
            if text in {"Learn more"}:
                break
            if should_skip_migrated_content(text):
                continue
            if tag.name == "h2":
                parts.append(f"<h2>{html.escape(text)}</h2>")
                plain.append(text)
                if text.lower() in {"video", "embedded files", "embedded file"}:
                    resource_headings.append(text)
            elif tag.name == "h3":
                parts.append(f"<h3>{html.escape(text)}</h3>")
                plain.append(text)
                if text.lower() in {"video", "embedded files", "embedded file"}:
                    resource_headings.append(text)
            elif tag.name == "p":
                body = render_inline(tag).strip()
                if body:
                    parts.append(f"<p>{body}</p>")
                    plain.append(text)
            elif tag.name in {"ul", "ol"}:
                block = render_list(tag)
                if block:
                    parts.append(block)
                    plain.append(text)
            elif tag.name == "table":
                rows = []
                for tr in tag.find_all("tr"):
                    cells = [clean_text(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
                    if cells:
                        rows.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
                if rows:
                    parts.append('<div class="table-wrap"><table>' + "".join(rows) + "</table></div>")
                    plain.append(text)
            elif tag.name == "img":
                src = tag.get("src") or tag.get("data-src")
                alt = clean_text(tag.get("alt") or title)
                if src and src.startswith("http") and "gstatic.com" not in src and "google.com/images/icons/product" not in src:
                    parts.append(f'<figure class="media-frame"><img src="{html.escape(src)}" alt="{html.escape(alt)}"></figure>')
                    media.append({"type": "image", "url": src})
            elif tag.name in {"iframe", "video"}:
                src = tag.get("src")
                if src:
                    if "youtube.com/embed" in src:
                        parts.append(
                            '<figure class="media-frame video-embed">'
                            f'<iframe src="{html.escape(src)}" title="{html.escape(title)} video" allowfullscreen></iframe>'
                            "</figure>"
                        )
                    else:
                        parts.append(f'<p class="resource-link"><a href="{html.escape(src)}">Open embedded media</a></p>')
                    media.append({"type": tag.name, "url": src})
                    resource_media.append(src)
            elif tag.name == "a":
                href = tag.get("href")
                label = clean_text(tag.get_text(" ", strip=True))
                if href and ("googleusercontent" in href or "drive.google" in href):
                    link_text = label or "Open original embedded resource"
                    parts.append(f'<p class="resource-link"><a href="{html.escape(href)}">{html.escape(link_text)}</a></p>')
                    media.append({"type": "embedded resource", "url": href})
                    resource_media.append(href)

    if not parts:
        parts = ["<p>This page did not expose readable body content during migration. Please check the original Google Site source.</p>"]
        media.append({"type": "unresolved", "url": item["source_url"]})
    if resource_headings and not resource_media:
        parts.append('<p class="resource-link">This page references an embedded video or file, but the Google Site did not expose a direct public media link during migration. Use the original source link below if needed.</p>')
        media.append({"type": "unresolved embedded media", "url": item["source_url"]})
    summary = " ".join(plain)
    summary = clean_text(summary[:260])
    article = {
        **item,
        "title": title,
        "summary": summary,
        "body": "\n".join(parts),
        "text": clean_text(" ".join(plain)),
        "media": media,
        "output": page_output_path(item["source_url"]),
    }
    return apply_article_updates(article)


def replace_everywhere(article, old, new):
    for key in ["title", "summary", "body", "text"]:
        article[key] = article[key].replace(old, new)


def apply_article_updates(article):
    title = article["title"]

    if title == "How to create a team drive and how to add/remove people":
        article["title"] = "How to create a shared drive and add/remove people"
        replace_everywhere(article, "team drive", "shared drive")
        replace_everywhere(article, "Team Drive", "Shared drive")

    if title == "Submitting a Support Ticket":
        replace_everywhere(
            article,
            '<ol><li>Navigate to <a href="https://isp.onelogin.com/">https://isp.onelogin.com/</a>  <a href="https://launchpad.classlink.com/ispschools">https://launchpad.classlink.com/ispschools</a></li>',
            '<ol><li>Navigate to <a href="https://launchpad.classlink.com/ispschools">https://launchpad.classlink.com/ispschools</a></li>',
        )
        replace_everywhere(
            article,
            "Navigate to https://launchpad.classlink.com/ispschools Click on the Service Desk icon",
            "Navigate to https://launchpad.classlink.com/ispschools Click on the Service Desk icon",
        )

    if title == "Signing in":
        replace_everywhere(
            article,
            '<ol><li>Go to  <a href="https://isp.onelogin.com/">isp.onelogin.com</a></li><li>Select ISP: Everything</li><li>Click on iSAMS</li></ol>',
            '<ol><li>Open <a href="https://launchpad.classlink.com/ispschools">ClassLink</a>.</li><li>Sign in with your school account if prompted.</li><li>Click on iSAMS.</li></ol>',
        )
        replace_everywhere(article, "Sig ning in to iSAMS ( Mobile App )", "Signing in to iSAMS (mobile app)")
        replace_everywhere(article, "Click login with Onelogin", "Tap the school account sign-in option")
        replace_everywhere(article, "Use your onelogin details", "Sign in with your school account")

    if title == "Creating Microsoft Teams":
        replace_everywhere(
            article,
            "Log into ISP&#x27;s Onelogin page / Log in to the Microsoft Teams application with your school email (which will ask your for your onelogin)",
            "Sign in to the Microsoft Teams application with your school email address",
        )
        replace_everywhere(
            article,
            "Log into ISP's Onelogin page / Log in to the Microsoft Teams application with your school email (which will ask your for your onelogin)",
            "Sign in to the Microsoft Teams application with your school email address",
        )

    if title == "Photography Sharepoint":
        replace_everywhere(
            article,
            'Login to onelogin or go directly to  <a href="https://www.office.com/">https://www.office.com/</a>  and login',
            'Go to <a href="https://www.office.com/">office.com</a> and sign in with your school account',
        )
        replace_everywhere(
            article,
            "Accessing the Shortcut in OneDrive (online)",
            "Accessing the Shortcut in OneDrive (online)",
        )

    if title == "Exam Information":
        replace_everywhere(article, "Log into Google account via onelogin", "Log into the school Google account")
        replace_everywhere(
            article,
            "If it is not connected, connect to wifiStudent. Password: greenwood12",
            "If it is not connected, connect to the correct exam WiFi network or use one of the spare laptops",
        )
        replace_everywhere(article, "<p>wifiStudent password is greenwood12</p>\n", "")

    if title == "Google Drive is no longer showing in the file explorer":
        replace_everywhere(
            article,
            '<ol><li>For PC follow this link &gt;  <a href="https://dl.google.com/drive-file-stream/GoogleDriveFSSetup.exe">https://dl.Google.com/drive-file-stream/GoogleDriveFSSetup.exe</a></li><li>For Mac follow this link &gt;  <a href="https://dl.google.com/drive-file-stream/GoogleDrive.dmg">https://dl.Google.com/drive-file-stream/GoogleDrive.dmg</a></li><li>Follow the given instructions on the install packages</li><li>Submit a ticket to the  <a href="/articles/submitting-a-support-ticket/index.html">service desk</a>  if you have any issues</li></ol>',
            '<ol><li>Download Google Drive for desktop from <a href="https://support.google.com/drive/answer/10838124">Google Drive Help</a>.</li><li>Open the installer and follow the on-screen instructions.</li><li>Submit a ticket to the <a href="/articles/submitting-a-support-ticket/index.html">service desk</a> if you have any issues.</li></ol>',
        )

    if title == "Password Resetting":
        replace_everywhere(article, "Open embedded media", "Open the student password reset form")

    if title == "Phone Extensions":
        replace_everywhere(
            article,
            "https://drive.google.com/open?id=11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw",
            "https://docs.google.com/spreadsheets/d/11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw/edit?usp=sharing",
        )
        for item in article["media"]:
            if item["type"] == "embedded resource":
                item["url"] = "https://docs.google.com/spreadsheets/d/11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw/edit?usp=sharing"

    apply_local_media(article)
    article["summary"] = clean_text(BeautifulSoup(article["body"], "lxml").get_text(" ", strip=True)[:260])
    article["text"] = clean_text(BeautifulSoup(article["body"], "lxml").get_text(" ", strip=True))
    return article


def category_slug(category):
    return f"categories/{slugify(category)}/index.html"


def root_prefix(output_path):
    depth = len(Path(output_path).parts) - 1
    return "../" * depth


def page_shell(title, description, body, page="", output_path="index.html"):
    prefix = root_prefix(output_path)
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | Claremont School IT</title>
  <meta name="description" content="{html.escape(description[:155])}">
  <link rel="stylesheet" href="{prefix}assets/css/styles.css">
  <link rel="icon" href="{prefix}favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="{prefix}assets/img/favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{prefix}assets/img/favicon-180.png">
</head>
<body data-page="{html.escape(page)}">
  <a class="skip-link" href="#main">Skip to content</a>
  <div id="site-header"></div>
  <main id="main">
{body}
  </main>
  <div id="site-footer"></div>
  <script src="{prefix}assets/data/search-index.js"></script>
  <script src="{prefix}assets/js/site.js"></script>
</body>
</html>
"""
    return content.replace('href="/', f'href="{prefix}').replace('src="/', f'src="{prefix}')


def write(path, content):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def article_page(article):
    source_note = ""
    if article.get("source_url"):
        source_note = f"""
          <div class="source-note">
            <strong>Original source:</strong> <a href="{html.escape(article['source_url'])}">Google Site page</a>
          </div>"""
    body = f"""
    <section class="page-hero compact">
      <div class="container">
        <h1>{html.escape(article['title'])}</h1>
        <p class="page-meta">{html.escape(article['category'])}</p>
      </div>
    </section>
    <section class="section">
      <div class="container article-layout">
        <article class="article-content">
          {article['body']}
          {source_note}
        </article>
        <aside class="article-aside">
          <h2>Need more help?</h2>
          <p>For faults or requests, submit a ticket through the Service Desk so the IT team can track and respond properly.</p>
          <a class="button" href="/articles/submitting-a-support-ticket/index.html">Submit a support ticket</a>
        </aside>
      </div>
    </section>"""
    return page_shell(article["title"], article["summary"], body, "article", article["output"])


def home_page(articles, categories):
    quick_task_titles = [
        "Submitting a Support Ticket",
        "Student Password Reset Form",
        "Chromebook won't turn on",
        "How to Log Into Google Drive",
        "Papercut Hive",
        "Changing Toner",
        "Have you tried switching it off and on again?!",
        "No sound and the speaker icon has a red cross through it",
    ]
    by_title = {a["title"]: a for a in articles}
    quick_link_cards = []
    for title in quick_task_titles:
        article = by_title.get(title)
        if article:
            quick_link_cards.append(f"""<a class="quick-link" href="/{article['output']}">
              <strong>{html.escape(article['title'])}</strong>
              <span>{html.escape(excerpt(article['summary'], 115))}</span>
            </a>""")
    category_cards = []
    for category in categories:
        count = len([a for a in articles if a["category"] == category])
        if count:
            accent = CATEGORY_ACCENTS[len(category_cards) % len(CATEGORY_ACCENTS)]
            icon_path = CATEGORY_ICONS.get(category, CATEGORY_ICONS["Miscellaneous"])
            category_cards.append(f"""<a class="category-card" href="/{category_slug(category)}">
              <span class="category-icon {accent}" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path d="{html.escape(icon_path)}"></path>
                </svg>
              </span>
              <span class="category-count">{count} {'guide' if count == 1 else 'guides'}</span>
              <strong>{html.escape(category)}</strong>
            </a>""")
    total_articles = len(articles)
    body = f"""
    <section class="home-hero">
      <div class="container home-hero-inner">
        <div class="home-intro">
          <img class="hero-logo" src="/assets/img/claremont-logo-white.png" alt="Claremont School">
          <h1>Claremont School IT Help</h1>
          <p>Search practical staff guides, common fixes and classroom technology notes.</p>
        </div>
        <div class="search-panel" role="search">
          <label for="site-search">Search IT help</label>
          <input id="site-search" type="search" placeholder="Try password, Gmail, Teams or WiFi">
          <div id="search-results" class="search-results" aria-live="polite"></div>
        </div>
      </div>
    </section>
    <section class="support-strip">
      <div class="container">
        <div class="support-message">
          <strong>Need IT to act on something?</strong>
          <span>Technical faults and requests should still go through the Service Desk so they can be tracked and prioritised.</span>
          <a class="button" href="/articles/submitting-a-support-ticket/index.html">Service Desk guide</a>
        </div>
      </div>
    </section>
    <section class="section home-section">
      <div class="container">
        <div class="section-heading">
          <h2>Common Tasks</h2>
          <p>{total_articles} guides across {len(categories)} help areas.</p>
        </div>
        <div class="quick-link-grid">{''.join(quick_link_cards)}</div>
      </div>
    </section>
    <section class="section soft home-section">
      <div class="container">
        <div class="section-heading">
          <h2>Browse by Category</h2>
          <p>Choose the system or problem area you need.</p>
        </div>
        <div class="category-grid">{''.join(category_cards)}</div>
      </div>
    </section>
    <section class="section home-section">
      <div class="container two-col">
        <div>
          <h2>Contact IT Support</h2>
          <p>Use Google Chat for quick questions only. Faults and requests should go through the Service Desk so they can be tracked and prioritised.</p>
          <div class="button-row">
            <a class="button" href="/articles/submitting-a-support-ticket/index.html">Service Desk guide</a>
            <a class="button secondary" href="https://chat.google.com/">Open Google Chat</a>
          </div>
        </div>
        <aside class="callout blue">
          <p><strong>New content needed?</strong> Submit a ticket and the IT team can help directly, then add a guide here where it will help others too.</p>
        </aside>
      </div>
    </section>"""
    return page_shell("Home", "Searchable IT help for Claremont School staff.", body, "home", "index.html")


def category_page(category, articles):
    cards = "".join(
        f"""<article class="list-card">
          <h2><a href="/{a['output']}">{html.escape(a['title'])}</a></h2>
          <p>{html.escape(excerpt(a['summary'], 220))}</p>
        </article>"""
        for a in articles
    )
    body = f"""
    <section class="page-hero compact">
      <div class="container">
        <h1>{html.escape(category)}</h1>
        <p class="page-meta">{len(articles)} {'help guide' if len(articles) == 1 else 'help guides'} in this section.</p>
      </div>
    </section>
    <section class="section">
      <div class="container list-layout">
        {cards}
      </div>
    </section>"""
    return page_shell(category, f"{category} IT help guides.", body, slugify(category), category_slug(category))


def media_inventory(articles):
    rows = ["# Media and Embedded Resource Inventory", ""]
    unresolved = []
    for article in articles:
        if article["media"]:
            rows.append(f"## {article['title']}")
            if article.get("source_url"):
                rows.append(f"- Original page: {article['source_url']}")
            for item in article["media"]:
                rows.append(f"- {item['type']}: {item['url']}")
            rows.append("")
        elif article["title"] not in LOCAL_MEDIA and ("video" in article["text"].lower() or "recording" in article["title"].lower()):
            unresolved.append(article)
    if unresolved:
        rows.extend(["## Pages mentioning video with no resolved embed", ""])
        for article in unresolved:
            rows.append(f"- {article['title']}: {article['source_url']}")
    return "\n".join(rows).strip() + "\n"


def main():
    def clear_readonly(func, path, _exc):
        Path(path).chmod(stat.S_IWRITE)
        func(path)

    for folder in ["articles", "categories"]:
        shutil.rmtree(ROOT / folder, onexc=clear_readonly)
    nav = build_nav()
    articles = []
    for item in nav:
        if item["title"] == "Home":
            continue
        print(f"Fetching {item['title']}")
        articles.append(extract_article(item))
    articles.extend(CUSTOM_ARTICLES)

    category_order = [c for c in CATEGORY_ORDER if any(a["category"] == c for a in articles)]
    for article in articles:
        write(article["output"], article_page(article))
    for category in category_order:
        write(category_slug(category), category_page(category, [a for a in articles if a["category"] == category]))
    write("index.html", home_page(articles, category_order))

    search_index = [
        {
            "title": a["title"],
            "category": a["category"],
            "url": a["output"],
            "summary": a["summary"],
            "text": a["text"][:1600],
        }
        for a in articles
    ]
    write("assets/data/search-index.js", "window.IT_HELP_SEARCH_INDEX = " + json.dumps(search_index, ensure_ascii=False, indent=2) + ";\n")
    write("media-needed.md", media_inventory(articles))
    print(f"Generated {len(articles)} articles and {len(category_order)} category pages.")


if __name__ == "__main__":
    main()

