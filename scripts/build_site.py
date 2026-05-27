import html
import json
import os
import re
import shutil
import textwrap
import stat
import sys
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
    "Previous Tab": "Devices & Windows",
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

SERVICE_DESK_URL = "https://servicedesk.ispschools.com"

RELATED_GUIDES = {
    "Have you tried switching it off and on again?!": [
        "Submitting a Support Ticket",
        "How to use Chrome Remote Desktop",
        "No sound and the speaker icon has a red cross through it",
    ],
    "Student Password Reset Form": [
        "Password Resetting",
        "What to do if a student needs IT help",
        "Submitting a Support Ticket",
    ],
    "What to do if a student needs IT help": [
        "Student Password Reset Form",
        "Chromebook won't turn on",
        "What is the WiFi password (Internet access)",
        "Submitting a Support Ticket",
    ],
    "Submitting a Support Ticket": [
        "What to do if a student needs IT help",
        "How to use Chrome Remote Desktop",
        "Have you tried switching it off and on again?!",
    ],
    "Log-in Page": [
        "ClassLink page not appearing automatically",
        "ClassLink using a personal Microsoft account",
        "Authenticator",
        "Customisation",
    ],
    "Authenticator": [
        "Log-in Page",
        "Google Account password and security",
        "ClassLink using a personal Microsoft account",
    ],
    "Customisation": [
        "Log-in Page",
        "ClassLink page not appearing automatically",
        "Opening multiple favourite tabs",
    ],
    "Password Resetting": [
        "Student Password Reset Form",
        "What to do if a student needs IT help",
        "Log-in Page",
    ],
    "ClassLink page not appearing automatically": [
        "Log-in Page",
        "ClassLink using a personal Microsoft account",
        "Customisation",
    ],
    "ClassLink using a personal Microsoft account": [
        "Log-in Page",
        "ClassLink page not appearing automatically",
        "Google Account password and security",
    ],
    "4 Tips on Staying Organised": [
        "How to Log Into Google Drive",
        "Google Drive is no longer showing in the file explorer",
        "I have overwritten a file in Google Drive",
    ],
    "Gmail Customisation": [
        "Remove conversation view in Gmail",
        "Add/edit your Gmail signature",
        "Gmail filters, labels, snooze and scheduling",
    ],
    "Add/edit your Gmail signature": [
        "Gmail Customisation",
        "Adding a Hyperlink to an Email",
        "Out of office in Gmail",
    ],
    "Adding a Hyperlink to an Email": [
        "Add/edit your Gmail signature",
        "Gmail Customisation",
        "How to search in Gmail",
    ],
    "Remove conversation view in Gmail": [
        "Gmail Customisation",
        "How to search in Gmail",
        "Gmail filters, labels, snooze and scheduling",
    ],
    "Out of office in Gmail": [
        "Add/edit your Gmail signature",
        "Gmail Customisation",
        "Create appointment schedules in Google Calendar",
    ],
    "Persistent Meet link in Google Calendar": [
        "Create appointment schedules in Google Calendar",
        "Creating a new Google Calendar",
        "Recording Google Meets/Classroom",
    ],
    "How to search in Gmail": [
        "How to create filters in Gmail",
        "Gmail filters, labels, snooze and scheduling",
        "Remove conversation view in Gmail",
    ],
    "How to create filters in Gmail": [
        "How to search in Gmail",
        "Gmail filters, labels, snooze and scheduling",
        "Gmail Customisation",
    ],
    "Create appointment schedules in Google Calendar": [
        "Creating a new Google Calendar",
        "Persistent Meet link in Google Calendar",
        "Out of office in Gmail",
    ],
    "How to Log Into Google Drive": [
        "Google Drive is no longer showing in the file explorer",
        "4 Tips on Staying Organised",
        "I have mistakenly deleted a file in Google Drive",
    ],
    "Google Drive is no longer showing in the file explorer": [
        "How to Log Into Google Drive",
        "OneDrive",
        "4 Tips on Staying Organised",
    ],
    "Recording Google Meets/Classroom": [
        "Persistent Meet link in Google Calendar",
        "Create appointment schedules in Google Calendar",
        "Recording a Meeting",
        "Sharing a Recorded Meeting",
    ],
    "I have mistakenly deleted a file in Google Drive": [
        "I have overwritten a file in Google Drive",
        "How to Log Into Google Drive",
        "4 Tips on Staying Organised",
    ],
    "How to create a shared drive and add/remove people": [
        "How to Log Into Google Drive",
        "4 Tips on Staying Organised",
        "Photography Sharepoint",
    ],
    "I have overwritten a file in Google Drive": [
        "I have mistakenly deleted a file in Google Drive",
        "4 Tips on Staying Organised",
        "How to Log Into Google Drive",
    ],
    "Guardian Summaries on Google Classroom": [
        "Recording Google Meets/Classroom",
        "Create appointment schedules in Google Calendar",
        "How to create a shared drive and add/remove people",
    ],
    "Creating a new Google Calendar": [
        "Create appointment schedules in Google Calendar",
        "Persistent Meet link in Google Calendar",
        "Out of office in Gmail",
    ],
    "Presentation Template": [
        "How to Log Into Google Drive",
        "4 Tips on Staying Organised",
        "Default Apps/Files",
    ],
    "Gmail filters, labels, snooze and scheduling": [
        "How to create filters in Gmail",
        "How to search in Gmail",
        "Remove conversation view in Gmail",
        "Gmail Customisation",
    ],
    "Creating Microsoft Teams": [
        "Create a Teams Meeting",
        "How to Admit Participants from the Waiting Room",
        "Recording a Meeting",
    ],
    "Create a Teams Meeting": [
        "Creating Microsoft Teams",
        "How to Admit Participants from the Waiting Room",
        "Recording a Meeting",
    ],
    "How to Admit Participants from the Waiting Room": [
        "Create a Teams Meeting",
        "Creating Microsoft Teams",
        "Recording a Meeting",
    ],
    "Recording a Meeting": [
        "Sharing a Recorded Meeting",
        "Create a Teams Meeting",
        "Recording Google Meets/Classroom",
    ],
    "Sharing a Recorded Meeting": [
        "Recording a Meeting",
        "Creating Microsoft Teams",
        "Create a Teams Meeting",
    ],
    "Theatre Projector & Sound (Senior)": [
        "Changing display settings",
        "No sound and the speaker icon has a red cross through it",
        "Prep Meeting Room",
    ],
    "Prep Meeting Room": [
        "Theatre Projector & Sound (Senior)",
        "Create a Teams Meeting",
        "No sound and the speaker icon has a red cross through it",
    ],
    "Converting a file format": [
        "Default Apps/Files",
        "Files in a ZIP folder won't open",
        "Zip and Unzip Files",
        "Exam papers printing with grid lines",
    ],
    "Files in a ZIP folder won't open": [
        "Zip and Unzip Files",
        "Default Apps/Files",
        "Converting a file format",
    ],
    "Zip and Unzip Files": [
        "Files in a ZIP folder won't open",
        "Converting a file format",
        "Default Apps/Files",
    ],
    "Default Apps/Files": [
        "Converting a file format",
        "Files in a ZIP folder won't open",
        "Exam papers printing with grid lines",
    ],
    "Google Account password and security": [
        "How do I Spot Phishing Emails",
        "Authenticator",
        "ClassLink using a personal Microsoft account",
    ],
    "How do I Spot Phishing Emails": [
        "Google Account password and security",
        "Authenticator",
        "Submitting a Support Ticket",
    ],
    "Exam papers printing with grid lines": [
        "Papercut Hive",
        "Converting a file format",
        "Default Apps/Files",
    ],
    "Papercut Hive": [
        "Changing Toner",
        "Exam papers printing with grid lines",
        "Submitting a Support Ticket",
    ],
    "Changing Toner": [
        "Papercut Hive",
        "Submitting a Support Ticket",
        "Exam papers printing with grid lines",
    ],
    "Phone Extensions": [
        "Forwarding Calls",
        "Office phone doesn't work - orange lights",
        "Submitting a Support Ticket",
    ],
    "Office phone doesn't work - orange lights": [
        "Phone Extensions",
        "Forwarding Calls",
        "Submitting a Support Ticket",
    ],
    "Forwarding Calls": [
        "Phone Extensions",
        "Office phone doesn't work - orange lights",
        "Submitting a Support Ticket",
    ],
    "Exam Information": [
        "Exam papers printing with grid lines",
        "Presentation Template",
        "Submitting a Support Ticket",
    ],
    "iSAMS": [
        "How to take a register",
        "Searching up a Student",
        "How To View a Timetable",
    ],
    "How to take a register": [
        "Attendance data for your form",
        "Searching up a Student",
        "How To View a Timetable",
    ],
    "Rewards and Conduct": [
        "Searching up a Student",
        "Finding Pupil Information",
        "How To View a Timetable",
    ],
    "How To View a Timetable": [
        "Searching up a Student",
        "Finding Pupil Information",
        "How to take a register",
    ],
    "Writing Reports": [
        "Finding Pupil Information",
        "Photo Report",
        "Searching up a Student",
    ],
    "Searching up a Student": [
        "Finding Pupil Information",
        "How To View a Timetable",
        "Emailing Correspondents",
    ],
    "Emailing Correspondents": [
        "Emailing Students",
        "Creating a Group",
        "Searching up a Student",
    ],
    "Creating a Group": [
        "Emailing Students",
        "Emailing Correspondents",
        "Searching up a Student",
    ],
    "Emailing Students": [
        "Creating a Group",
        "Emailing Correspondents",
        "Searching up a Student",
    ],
    "Attendance data for your form": [
        "How to take a register",
        "Extracting Data",
        "Creating a Group",
    ],
    "Finding Pupil Information": [
        "Searching up a Student",
        "Photo Report",
        "Writing Reports",
    ],
    "Photo Report": [
        "Finding Pupil Information",
        "Writing Reports",
        "Searching up a Student",
    ],
    "Extracting Data": [
        "Attendance data for your form",
        "Creating a Group",
        "Default Apps/Files",
    ],
    "Sign In App": [
        "Phone Extensions",
        "Submitting a Support Ticket",
        "Accident Forms",
    ],
    "OneDrive": [
        "Photography Sharepoint",
        "Google Drive is no longer showing in the file explorer",
        "4 Tips on Staying Organised",
    ],
    "Photography Sharepoint": [
        "OneDrive",
        "How to create a shared drive and add/remove people",
        "How to Log Into Google Drive",
    ],
    "What is the WiFi password (Internet access)": [
        "Submitting a Support Ticket",
        "What to do if a student needs IT help",
        "How to use Chrome Remote Desktop",
    ],
    "Opening multiple favourite tabs": [
        "Previous Tab",
        "Tab Wrangler",
        "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More",
        "Customisation",
    ],
    "Tab Wrangler": [
        "Previous Tab",
        "Opening multiple favourite tabs",
        "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More",
        "4 Tips on Staying Organised",
    ],
    "Previous Tab": [
        "Opening multiple favourite tabs",
        "Tab Wrangler",
        "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More",
        "4 Tips on Staying Organised",
    ],
    "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More": [
        "Previous Tab",
        "Opening multiple favourite tabs",
        "Tab Wrangler",
        "Activating Text to Speech - Chromebook & Windows",
    ],
    "How to use Chrome Remote Desktop": [
        "Submitting a Support Ticket",
        "Google Account password and security",
        "How do I Spot Phishing Emails",
    ],
    "No sound and the speaker icon has a red cross through it": [
        "Theatre Projector & Sound (Senior)",
        "Prep Meeting Room",
        "Submitting a Support Ticket",
    ],
    "Chromebook shortcuts": [
        "Chromebook won't turn on",
        "Changing display settings",
        "Activating Text to Speech - Chromebook & Windows",
    ],
    "Changing display settings": [
        "Theatre Projector & Sound (Senior)",
        "Chromebook shortcuts",
        "No sound and the speaker icon has a red cross through it",
    ],
    "Activating Text to Speech - Chromebook & Windows": [
        "Chromebook shortcuts",
        "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More",
        "Changing display settings",
    ],
    "Accident Forms": [
        "Sign In App",
        "Submitting a Support Ticket",
    ],
    "Chromebook won't turn on": [
        "What to do if a student needs IT help",
        "Chromebook shortcuts",
        "Submitting a Support Ticket",
    ],
}

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
    "Persistent Meet link in Google Calendar": [
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
        "title": "Previous Tab",
        "category": "Devices & Windows",
        "summary": "Use the Previous Tab Chrome extension to jump straight back to the tab you were using before, even when you have lots of tabs open.",
        "text": "Previous Tab is a Chrome extension that lets you press Ctrl+Q to switch back to the previously used tab. Chrome has built-in shortcuts for moving through tabs by position, but not for returning to the last active tab.",
        "body": """
          <figure class="media-frame help-illustration">
            <img src="../../assets/media/previous-tab.png" alt="Chrome browser with multiple school work tabs and a Ctrl+Q shortcut overlay.">
          </figure>
          <p>If you often move between several Chrome tabs while planning, teaching or checking school systems, the <strong>Previous Tab</strong> extension can make it much quicker to get back to the tab you were just using.</p>
          <p>Chrome already has useful keyboard shortcuts for moving between tabs, but these move by tab position. Previous Tab adds a shortcut for going back to the <em>previously used</em> tab instead.</p>

          <h3>Install Previous Tab</h3>
          <p>You can install it from the Chrome Web Store here: <a href="https://chromewebstore.google.com/detail/previous-tab/bjaniflnlhhofabpoamhnobeonjcjjpl?hl=en" target="_blank" rel="noopener noreferrer">Previous Tab Chrome extension</a>.</p>

          <h3>How to use it</h3>
          <ol>
            <li>Install the extension in Chrome.</li>
            <li>Press and hold <strong>Ctrl</strong>.</li>
            <li>Tap <strong>Q</strong>.</li>
          </ol>
          <p>Chrome will switch back to the tab you were using immediately before the current one. For example, if you were working on tab 3 and then moved to tab 9, pressing <strong>Ctrl+Q</strong> takes you straight back to tab 3.</p>

          <h3>Useful built-in Chrome tab shortcuts</h3>
          <ul>
            <li><strong>Ctrl+Tab</strong> moves to the next open tab.</li>
            <li><strong>Ctrl+Shift+Tab</strong> moves to the previous open tab.</li>
            <li><strong>Ctrl+1</strong> to <strong>Ctrl+8</strong> moves to a specific tab position.</li>
            <li><strong>Ctrl+9</strong> moves to the rightmost tab.</li>
          </ul>
          <p>Those shortcuts are still useful, but they do not jump to the tab you last used. That is the gap Previous Tab fills.</p>

          <h3>A quick note on lots of tabs</h3>
          <p>It is still worth closing tabs you no longer need, especially if Chrome starts to feel slow. In practice, lesson planning often means having registers, resources, email, calendars and documents open at the same time, so this shortcut can be a helpful way to stay oriented.</p>
        """.strip(),
        "media": [],
        "output": "articles/previous-tab/index.html",
        "source_url": "",
        "custom": True,
    },
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
    },
    {
        "title": "What to do if a student needs IT help",
        "category": "Requests & Support",
        "summary": "How form tutors and teachers can guide students to the student support site, collect useful details, handle password resets, and raise a support request when IT needs to help.",
        "text": "Direct students to the student support site first. Ask what they were trying to do, what happened instead, when it started, where it happens, and any exact error message. Staff can request student password resets. If the issue still needs IT, raise a support ticket with the student details and troubleshooting already tried.",
        "body": """
          <div class="student-site-callout">
            <div>
              <strong>Student support site</strong>
              <p>Students can use this site for practical guides on laptops, passwords, ClassLink, OneDrive, apps, safety and common fixes.</p>
            </div>
            <a class="button" href="https://help.claremontstudent.co.uk/" target="_blank" rel="noopener noreferrer">Open student support site</a>
          </div>
          <p>If a student asks you for help, please guide them to the student site first where appropriate. The aim is to help them try the right guide, gather useful information, and then involve IT if the problem cannot be resolved.</p>

          <h3>Suggested route for students</h3>
          <ol>
            <li>Ask the student to search the <a href="https://help.claremontstudent.co.uk/">student support site</a> for the issue.</li>
            <li>If the issue is about a forgotten password, use the <a href="/articles/student-password-reset-form/index.html">student password reset form</a>. The student guide is also available here: <a href="https://help.claremontstudent.co.uk/articles/what-to-do-if-you-forgot-your-password/index.html">What to do if you forgot your password</a>.</li>
            <li>For quick laptop issues, ask the student to restart the device if it is safe to do so, check power or WiFi, and note any error message.</li>
            <li>If they are still stuck, gather the details below and raise a support request.</li>
          </ol>

          <h3>Information to collect before raising a request</h3>
          <ul>
            <li>Student full name and form group.</li>
            <li>What the student was trying to do.</li>
            <li>What happened instead.</li>
            <li>When the problem started.</li>
            <li>Whether it happens at school, at home, or both.</li>
            <li>The device name, asset label, or room number if relevant.</li>
            <li>The exact error message or a screenshot, if one is available.</li>
            <li>Any checks already tried, such as restarting, checking WiFi, trying ClassLink again, or using the relevant student guide.</li>
          </ul>

          <h3>When to raise a support request</h3>
          <p>Raise a support request when the student has tried the relevant guidance and the issue still needs IT, or when the problem affects learning, access to school systems, hardware, safeguarding, or a wider group of students.</p>
          <p>Please include the details above in the request. IT will review the issue and get back to the form tutor or the member of staff who raised it.</p>
          <p><a class="button" href="/articles/submitting-a-support-ticket/index.html">How to submit a support ticket</a></p>
        """.strip(),
        "media": [],
        "output": "articles/student-it-help/index.html",
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


def has_visual_media(body):
    soup = BeautifulSoup(body, "lxml")
    return bool(soup.find(["img", "video", "iframe"]))


def has_reliable_visual_media(body):
    soup = BeautifulSoup(body, "lxml")
    if soup.find(["video", "iframe"]):
        return True
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "googleusercontent.com/sitesv/" not in src:
            return True
    return False


def wrap_svg_text(value, max_chars=28, max_lines=3):
    words = clean_text(value).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines or [value]


def generated_media_filename(article):
    return f"generated/{slugify(article['title'])}.svg"


def generated_media_svg(article):
    title_lines = wrap_svg_text(article["title"], 28, 3)
    helper_lines = wrap_svg_text("Use the steps on this page to complete the task.", 46, 2)
    category = html.escape(article["category"])
    title_tspans = "\n".join(
        f'<tspan x="96" y="{172 + index * 50}">{html.escape(line)}</tspan>'
        for index, line in enumerate(title_lines)
    )
    helper_start = 370 if len(title_lines) > 2 else 330
    helper_tspans = "\n".join(
        f'<tspan x="96" y="{helper_start + index * 32}">{html.escape(line)}</tspan>'
        for index, line in enumerate(helper_lines)
    )
    icon_label = html.escape(article["category"][:2].upper())
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(article['title'])}</title>
  <desc id="desc">Support guide illustration for {html.escape(article['title'])}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#071564"/>
      <stop offset="1" stop-color="#245b85"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#001044" flood-opacity="0.24"/>
    </filter>
  </defs>
  <rect width="1280" height="720" fill="#f4f7fb"/>
  <rect x="0" y="0" width="1280" height="720" fill="url(#bg)"/>
  <path d="M900 0c130 110 194 240 192 390-2 123-40 229-116 318h304V0H900Z" fill="#2d729a" opacity=".34"/>
  <rect x="64" y="64" width="1152" height="592" rx="22" fill="#fff" filter="url(#shadow)"/>
  <rect x="64" y="64" width="18" height="592" fill="#ff7a1a"/>
  <circle cx="1052" cy="210" r="104" fill="#eef7fb" stroke="#d5e4ee" stroke-width="3"/>
  <rect x="972" y="294" width="160" height="104" rx="14" fill="#f7fbfd" stroke="#d5e4ee" stroke-width="3"/>
  <path d="M1010 334h84M1010 362h56" stroke="#071564" stroke-width="12" stroke-linecap="round"/>
  <circle cx="1052" cy="210" r="52" fill="#071564"/>
  <text x="1052" y="226" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="700" fill="#fff">{icon_label}</text>
  <text x="96" y="104" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700" fill="#245b85">{category}</text>
  <text font-family="Georgia, 'Times New Roman', serif" font-size="46" font-weight="700" fill="#071564">{title_tspans}</text>
  <text font-family="Arial, Helvetica, sans-serif" font-size="24" fill="#43546a">{helper_tspans}</text>
  <g transform="translate(96 520)">
    <rect width="360" height="70" rx="10" fill="#f0f6fb" stroke="#d5e4ee"/>
    <circle cx="36" cy="35" r="15" fill="#ff7a1a"/>
    <path d="M29 35l5 6 11-14" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="68" y="43" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700" fill="#071564">Step-by-step staff guide</text>
  </g>
</svg>
"""


def ensure_generated_media(article):
    soup = BeautifulSoup(article["body"], "lxml")
    for figure in soup.select("figure.media-frame.help-illustration"):
        image = figure.find("img")
        if image and "assets/media/generated/" not in image.get("src", ""):
            return article
    article["body"] = re.sub(
        r'<figure class="media-frame help-illustration"><img[^>]+assets/media/generated/[^>]+></figure>\n?',
        "",
        article["body"],
    )
    article["body"] = re.sub(
        r'<figure class="media-frame"><img src="https?://[^"]*googleusercontent\.com/sitesv/[^"]+" alt="[^"]*"></figure>\n?',
        "",
        article["body"],
    )
    article["media"] = [
        item
        for item in article["media"]
        if not (item["type"] == "image" and "googleusercontent.com/sitesv/" in item["url"])
    ]
    filename = generated_media_filename(article)
    target = ROOT / "assets" / "media" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generated_media_svg(article), encoding="utf-8")
    article["body"] = (
        f'<figure class="media-frame help-illustration">'
        f'<img src="{html.escape(asset_path_for(article, filename))}" alt="{html.escape(article["title"])} support guide illustration.">'
        "</figure>\n"
        + article["body"].lstrip()
    )
    return article


def linkify_plain_urls(body):
    soup = BeautifulSoup(body, "lxml")
    pattern = re.compile(r"(?<![\"'=])(https?://[^\s<>()]+)")
    for text_node in list(soup.find_all(string=pattern)):
        if text_node.find_parent("a"):
            continue
        pieces = []
        last = 0
        text = str(text_node)
        for match in pattern.finditer(text):
            url = match.group(1).rstrip(".,;:")
            trailing = match.group(1)[len(url):]
            if match.start() > last:
                pieces.append(NavigableString(text[last:match.start()]))
            link = soup.new_tag("a", href=url)
            link.string = url
            pieces.append(link)
            if trailing:
                pieces.append(NavigableString(trailing))
            last = match.end()
        if last < len(text):
            pieces.append(NavigableString(text[last:]))
        for piece in reversed(pieces):
            text_node.insert_after(piece)
        text_node.extract()
    return "".join(str(child) for child in soup.body.contents) if soup.body else str(soup)


def apply_local_media(article):
    items = LOCAL_MEDIA.get(article["title"])
    if not items:
        return ensure_generated_media(article)
    soup = BeautifulSoup(article["body"], "lxml")
    local_files = {item["file"] for item in items}
    for figure in soup.select("figure.media-frame"):
        source = figure.find(["img", "video"])
        src = source.get("src", "") if source else ""
        if any(src.endswith(f"/{filename}") for filename in local_files):
            figure.decompose()
    article["body"] = "".join(str(child) for child in soup.body.contents) if soup.body else str(soup)
    article["body"] = re.sub(
        r'<figure class="media-frame"><img src="https?://[^"]+" alt="[^"]*"></figure>\n?',
        "",
        article["body"],
    )
    media_html = "\n".join(local_media_figure(article, item) for item in items)
    article["body"] = article["body"].rstrip() + "\n" + media_html
    article["media"] = [
        item
        for item in article["media"]
        if item["type"] not in {"image", "unresolved embedded media"}
    ]
    return ensure_generated_media(article)


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
            elif tag.name == "h3":
                parts.append(f"<h3>{html.escape(text)}</h3>")
                plain.append(text)
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
            elif tag.name == "a":
                href = tag.get("href")
                label = clean_text(tag.get_text(" ", strip=True))
                if href and ("googleusercontent" in href or "drive.google" in href):
                    link_text = label or "Open supporting resource"
                    parts.append(f'<p class="resource-link"><a href="{html.escape(href)}">{html.escape(link_text)}</a></p>')
                    media.append({"type": "embedded resource", "url": href})

    if not parts:
        parts = ["<p>Content for this guide is currently unavailable. Please submit a support ticket if you need help with this task.</p>"]
        media.append({"type": "unresolved", "url": item["source_url"]})
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

    if title == "Persistant Meet link in Google Calendar":
        replace_everywhere(article, "Persistant", "Persistent")

    if title == "Gmail Guide: Master Filters, Labels, Snooze, and Scheduling":
        article["title"] = "Gmail filters, labels, snooze and scheduling"
        article["body"] = """
<p>Use the steps below to organise email and control when messages return to your inbox or are sent.</p>
<h3>Create filters</h3>
<p>Filters apply actions automatically to incoming email based on criteria such as sender, keywords or subject.</p>
<ol><li>Click the search bar at the top of Gmail.</li><li>Enter an email address, keyword or other search criterion.</li><li>Click the search options icon, then choose "Create filter".</li><li>Select the actions to apply, such as "Skip the Inbox", "Apply the label" or "Mark as read".</li></ol>
<h3>Use labels</h3>
<ol><li>In the left-hand menu, click "Create new label".</li><li>Use filters if you want messages to be labelled automatically.</li><li>Click a label to see messages assigned to it.</li></ol>
<h3>Snooze an email</h3>
<ol><li>Hover over a message in your inbox.</li><li>Click the clock icon on the right-hand side.</li><li>Choose when the message should return to your inbox.</li></ol>
<h3>Schedule an email</h3>
<ol><li>Compose your message.</li><li>Click the dropdown arrow next to the "Send" button.</li><li>Select "Schedule send", then choose the date and time.</li></ol>
<p>Submit a support ticket if you need help configuring Gmail for your work.</p>
""".strip()

    if title == "Device Tips: Enable Dark Mode, Emoji Shortcuts, and More":
        article["body"] = """
<p>These settings and shortcuts cover common day-to-day tasks on Windows, Mac and Chromebook devices.</p>
<h3>Use dark mode</h3>
<ul><li>Windows: Go to Settings &gt; Personalisation &gt; Colours and select Dark.</li><li>Mac: Go to System Preferences &gt; General &gt; Appearance and select Dark.</li><li>Chromebook: Go to Settings &gt; Personalisation &gt; Set wallpaper &amp; style, then select Dark theme.</li></ul>
<h3>Enter emoji characters</h3>
<ul><li>Windows: Press Win + . (period).</li><li>Mac: Press Ctrl + Command + Space.</li><li>Chromebook: Right-click in a text field and select Emoji, or press Search + Shift + Space.</li></ul>
<h3>Arrange two windows side by side</h3>
<ul><li>Windows: Drag a window to the side of the screen or press Win + Left/Right Arrow.</li><li>Mac: Hover over the green button in the top-left of a window and choose Tile Window to Left/Right of Screen.</li><li>Chromebook: Drag the window to the side or press Alt + [ (left bracket) or Alt + ] (right bracket).</li></ul>
<h3>Use dictation</h3>
<ul><li>Windows: Press Win + H to enable dictation.</li><li>Mac: Go to System Preferences &gt; Keyboard &gt; Dictation to turn it on.</li><li>Chromebook: Go to Settings &gt; Accessibility, enable Dictation, and use the microphone icon in the status bar.</li></ul>
<h3>Search for files, apps or settings</h3>
<ul><li>Windows: Press Win + S to open the search bar.</li><li>Mac: Press Command + Space for Spotlight Search.</li><li>Chromebook: Press the Search key (or Launcher key) on your keyboard.</li></ul>
<h3>Adjust page zoom</h3>
<ul><li>Windows/Mac/Chromebook: Press Ctrl + Plus/Minus to zoom in or out.</li></ul>
<p>Submit a support ticket if you need help finding or enabling any of these settings.</p>
""".strip()

    if title == "Adding a Hyperlink to an Email":
        article["body"] = """
<p>Using descriptive link text can make an email easier to read than displaying a long web address.</p>
<h3>Add a hyperlink in Gmail</h3>
<ol><li>Compose a new email.</li><li>Press Ctrl + K to open the link window.</li><li>Enter the text that recipients should see.</li><li>Paste the URL into the web address field.</li><li>Click OK.</li></ol>
<p>To add a link to text you have already written, highlight the text and press Ctrl + K, then paste the URL.</p>
<h3>Add a hyperlink in Outlook</h3>
<ol><li>Compose a new email.</li><li>Press Ctrl + K, or select the Insert tab and choose Link.</li><li>Enter the text that recipients should see.</li><li>Paste the URL into the address field.</li><li>Click OK.</li></ol>
""".strip()

    if title == "Remove conversation view in Gmail":
        article["body"] = """
<p>Conversation view groups messages in the same email thread together. You can turn it off if you would prefer each message to appear separately in your inbox.</p>
<h3>Turn off conversation view in Gmail</h3>
<ol><li>In Gmail, click the gear icon and select "See all settings".</li><li>On the General tab, scroll down to the Conversation view section.</li><li>Select "Conversation view off".</li><li>Scroll to the bottom of the page and click "Save Changes".</li></ol>
<h3>Comparison of views</h3>
""".strip()

    if title == "Extracting Data":
        article["body"] = """
<p>Follow the steps below to export student data from iSAMS into a spreadsheet.</p>
<h3>Export student data</h3>
<ol><li>Open iSAMS.</li><li>Navigate to Student Manager.</li><li>Enter search criteria if required.</li><li>Select the students whose data you want to export.</li><li>Open the pink dropdown on the right-hand side and select "Export Wizard".</li><li>Select "Create a custom report", or select an existing report if appropriate.</li><li>Click Next.</li><li>Select the data fields you want to export and click Next.</li><li>Review the preview of the data to be exported and click Next.</li><li>Select .xlsx or .csv, depending on your requirements, and click Next.</li><li>Click the download link when the export is ready.</li><li>Open the file in Google Sheets or Microsoft Excel.</li></ol>
""".strip()

    if title == "Activating Text to Speech - Chromebook & Windows":
        article["body"] = """
<p>Text to speech can read selected content aloud on Chromebooks and Windows PCs. Use the steps below to enable it.</p>
<h3>Chromebook</h3>
<ol><li>Click the time in the bottom-right corner.</li><li>Click the Accessibility icon. If it is not displayed, contact IT.</li><li>Turn on "Select-to-speak".</li><li>Click the Select-to-speak icon in the bottom-right corner.</li><li>Click and drag over the text you want to hear.</li><li>Use the displayed controls to play, pause, skip or change speed.</li><li>Click the icon again to stop using the feature.</li></ol>
<h3>Windows</h3>
<ol><li>Open Narrator by pressing Ctrl + Windows + N, or open Settings &gt; Ease of Access &gt; Narrator.</li><li>Turn Narrator on.</li><li>Press Ctrl if you need to stop Narrator reading immediately.</li><li>Open the page containing the text you want read aloud.</li><li>Click the content or use the arrow keys to choose what Narrator reads.</li><li>Return to Narrator settings to turn it off when finished.</li></ol>
""".strip()

    if title == "Changing display settings":
        article["body"] = article["body"].replace("<h3>Video Example</h3>\n", "")
        article["body"] = article["body"].replace("displa y", "display")

    if title == "I have overwritten a file in Google Drive":
        article["body"] = article["body"].replace("<h3>Video Example</h3>\n<p>Restore Previous Version</p>", "")

    if title == "Papercut Hive":
        article["body"] = article["body"].replace(
            "<h3>Video Guide</h3>\n<p>Make sure Sync is on before following the video</p>",
            "<h3>Reference image</h3>\n<p>The image below shows the PaperCut Hive printing screen.</p>",
        )

    if title == "Create a Teams Meeting":
        replace_everywhere(article, "downlaod", "download")
        replace_everywhere(article, "apllication", "application")

    if title == "Google Account password and security":
        replace_everywhere(article, "reguarily", "regularly")

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
        replace_everywhere(article, "Open original embedded resource", "Open the extension directory")
        replace_everywhere(article, "Open supporting resource", "Open the extension directory")
        replace_everywhere(
            article,
            "https://drive.google.com/open?id=11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw",
            "https://docs.google.com/spreadsheets/d/11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw/edit?usp=sharing",
        )
        for item in article["media"]:
            if item["type"] == "embedded resource":
                item["url"] = "https://docs.google.com/spreadsheets/d/11HlvnGVHtu8QgzNGS97aYUz8LlHXKQwDr5M5q_j3vtw/edit?usp=sharing"

    apply_local_media(article)
    article["body"] = linkify_plain_urls(article["body"])
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
  <!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "0725fc87b5ad42108bdf952a0c799a2b"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
"""
    return content.replace('href="/', f'href="{prefix}').replace('src="/', f'src="{prefix}')


def write(path, content):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def related_articles_for(article, articles, limit=4):
    by_title = {item["title"]: item for item in articles}
    related = []
    seen = {article["title"]}

    for title in RELATED_GUIDES.get(article["title"], []):
        item = by_title.get(title)
        if item and item["title"] not in seen:
            related.append(item)
            seen.add(item["title"])

    if len(related) < limit:
        for item in articles:
            if item["category"] == article["category"] and item["title"] not in seen:
                related.append(item)
                seen.add(item["title"])
                if len(related) == limit:
                    break

    return related[:limit]


def related_guides_html(article, articles):
    related = related_articles_for(article, articles)
    if not related:
        return ""
    links = "".join(
        f'<li><a href="/{item["output"]}">{html.escape(item["title"])}</a></li>'
        for item in related
    )
    return f"""
          <h3>Related guides</h3>
          <ul>{links}</ul>"""


def article_page(article, articles):
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
        </article>
        <aside class="article-aside">
          <h2>Need more help?</h2>
          <p>For faults or requests, submit a ticket through the Service Desk so the IT team can track and respond properly.</p>
          <a class="button" href="{SERVICE_DESK_URL}">Submit a support ticket</a>
{related_guides_html(article, articles)}
        </aside>
      </div>
    </section>"""
    return page_shell(article["title"], article["summary"], body, "article", article["output"])


def home_page(articles, categories):
    quick_task_titles = [
        "What to do if a student needs IT help",
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


def articles_from_existing_site():
    index_path = ROOT / "assets" / "data" / "search-index.js"
    data = index_path.read_text(encoding="utf-8")
    match = re.search(r"=\s*(\[[\s\S]*\]);", data)
    if not match:
        raise RuntimeError("Could not read local search index.")

    articles = []
    for item in json.loads(match.group(1)):
        page_path = ROOT / item["url"]
        soup = BeautifulSoup(page_path.read_text(encoding="utf-8"), "lxml")
        content = soup.select_one(".article-content")
        if not content:
            continue
        article = {
            "title": item["title"],
            "category": item["category"],
            "summary": item["summary"],
            "text": item["text"],
            "body": content.decode_contents().strip(),
            "media": [],
            "source_url": "",
            "output": item["url"],
        }
        articles.append(apply_article_updates(article))
    return articles


def merge_custom_articles(articles, replace_existing=True):
    by_title = {article["title"]: index for index, article in enumerate(articles)}
    for custom_article in CUSTOM_ARTICLES:
        article = apply_article_updates(custom_article.copy())
        existing_index = by_title.get(article["title"])
        if existing_index is None:
            by_title[article["title"]] = len(articles)
            articles.append(article)
        elif replace_existing:
            articles[existing_index] = article
    return articles


def main():
    def clear_readonly(func, path, _exc):
        Path(path).chmod(stat.S_IWRITE)
        func(path)

    use_local = "--from-local" in sys.argv
    if use_local:
        articles = articles_from_existing_site()
        if len(articles) < 30:
            raise RuntimeError(f"Local site returned only {len(articles)} articles; aborting before clearing generated pages.")
    else:
        nav = build_nav()
        if len(nav) < 30:
            raise RuntimeError(f"Source navigation returned only {len(nav)} items; aborting before clearing generated pages.")

    for folder in ["articles", "categories"]:
        shutil.rmtree(ROOT / folder, onexc=clear_readonly)
    generated_media = ROOT / "assets" / "media" / "generated"
    if generated_media.exists() and not use_local:
        shutil.rmtree(generated_media, onexc=clear_readonly)
    if not use_local:
        articles = []
        for item in nav:
            if item["title"] == "Home":
                continue
            print(f"Fetching {item['title']}")
            articles.append(extract_article(item))
    merge_custom_articles(articles, replace_existing=not use_local)

    category_order = [c for c in CATEGORY_ORDER if any(a["category"] == c for a in articles)]
    for article in articles:
        write(article["output"], article_page(article, articles))
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
    print(f"Generated {len(articles)} articles and {len(category_order)} category pages.")


if __name__ == "__main__":
    main()

