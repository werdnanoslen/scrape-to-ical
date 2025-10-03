from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper
from playwright.sync_api import sync_playwright
import re


class BBGScraper(AbstractScraper):
    NAME = "Brooklyn Botanic Garden"
    URL = "https://www.bbg.org/visit/calendar"

    def get_events(self) -> list[Event]:
        events = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.URL)
            page.wait_for_timeout(5000)  # Adjust as needed
            content = page.content()
            strainer = SoupStrainer("ul", attrs={
                "id": "event-calendar-regular"
            })
            soup = BeautifulSoup(content, "lxml", parse_only=strainer)

            current_date = None  # To track the date from the <h2> tag

            for element in soup.find_all(["h2", "li"]):
                if isinstance(element, Tag) and element.name == "h2":
                    # Extract the date from the <h2> tag
                    current_date = element.get_text(strip=True)
                    continue

                if isinstance(element, Tag)\
                   and element.name == "li" and current_date:

                    # Extract title
                    title_tag = element.find("h3")
                    title = title_tag.get_text(strip=True) if title_tag\
                        else "Untitled Event"

                    # Extract link
                    link_tag = element.find("a", href=True)
                    if isinstance(link_tag, Tag) and link_tag.get("href"):
                        link = f"https://www.bbg.org{link_tag.get('href')}"
                    else:
                        link = ""

                    # Extract time
                    date_tag = element.find("p", class_="event-date")
                    time_text = date_tag.get_text(strip=True) if date_tag\
                        else ""
                    time_str = time_text

                    # Extract description
                    description = f"{time_str}\n\n"
                    blurb_tag = element.find("p", class_="event-blurb")
                    description += blurb_tag.get_text(strip=True) if blurb_tag\
                        else ""
                    if link:
                        description += f"\n\nMore info:\n{link}"

                    # Extract image
                    img_tag = element.find("img")
                    if isinstance(img_tag, Tag) and img_tag.get("srcset"):
                        srcset = img_tag.get("srcset", "")
                        srcset_str = str(srcset)
                        img_url = srcset_str.split(" ")[0] if srcset_str\
                            else ""
                        alt = img_tag.get("alt", "")
                        description += f'\n\n<img src="{img_url}" alt="{alt}" />'  # noqa: E501

                    # Parse datetime
                    dtstart, dtend = self._parse_datetime(
                        current_date,
                        time_str
                    )

                    # Create event
                    event = Event()
                    event.add("uid", f"{title}-{dtstart}")
                    event.add("summary", title)
                    event.add("description", description)
                    event.add("location", "Brooklyn Botanic Garden, 990 Washington Ave, Brooklyn, NY 11225")  # noqa: E501
                    event.add("dtstart", dtstart)
                    event["dtstart"].params["VALUE"] = "DATE"
                    event.add("dtend", dtend)
                    event["dtend"].params["VALUE"] = "DATE"
                    events.append(event)

            browser.close()
        return events

    def _parse_datetime(self, date_str, time_str):
        if date_str == "Ongoing":
            # Handle "Ongoing" or date ranges like "July 2–October 26, 2025"
            # Extract the start and end date from the range
            match = re.match(
                r"([A-Za-z]+ \d+)[–-]([A-Za-z]+ \d+), (\d{4})",
                time_str
            )
            if match:
                # Use the start and end dates from the range
                start_month_day, end_month_day, year = match.group(1), match.group(2), match.group(3)  # noqa: E501
                dtstart = datetime.strptime(
                    f"{start_month_day}, {year}",
                    "%B %d, %Y"
                )
                dtend = datetime.strptime(
                    f"{end_month_day}, {year}",
                    "%B %d, %Y"
                ) + timedelta(days=1)
            else:
                # Fallback: just use today for both start and end
                dtstart = datetime.now()
                dtend = dtstart + timedelta(hours=2)
            dtstart = dtstart.replace(tzinfo=ZoneInfo("America/New_York")).astimezone(ZoneInfo("UTC"))  # noqa: E501
            dtend = dtend.replace(tzinfo=ZoneInfo("America/New_York")).astimezone(ZoneInfo("UTC"))  # noqa: E501
        else:
            # Parse the date and time strings into a datetime object
            dt = datetime.strptime(date_str, "%A, %B %d, %Y")
            dt_local = dt.replace(tzinfo=ZoneInfo("America/New_York"))
            dtstart = dt_local.astimezone(ZoneInfo("UTC"))
            dtend = dtstart + timedelta(hours=2)

        return dtstart, dtend
