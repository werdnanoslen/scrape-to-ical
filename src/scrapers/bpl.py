from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper
from playwright.sync_api import sync_playwright
from dateutil import parser as dateutil_parser


class BPLScraper(AbstractScraper):
    NAME = "BPL"
    URL_TEMPLATE = "https://discover.bklynlibrary.org/?event=true&event=true&eventage=Adults&eventlocation=Central+Library%7C%7CCentral+Library%2C+Business+%26+Career+Center%7C%7CCentral+Library%2C+Info+Commons%7C%7CCrown+Heights+Library%7C%7CPacific+Library%7C%7CPark+Slope+Library%7C%7CBrooklyn+Heights+Library%7C%7CClinton+Hill+Library%7CLibrary+for+Arts+%26+Culture&pagination={page}"  # noqa: E501

    def get_events(self) -> list[Event]:
        events = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for i in range(1, 3):  # Adjust range as needed for more pages
                url = self.URL_TEMPLATE.format(page=i)
                page = browser.new_page()
                page.goto(url)
                page.wait_for_timeout(5000)
                content = page.content()
                strainer = SoupStrainer(
                    "div",
                    attrs={"class": "result-detail-text"}
                )
                soup = BeautifulSoup(content, "lxml", parse_only=strainer)
                for result in soup:
                    if not isinstance(result, Tag):
                        continue
                    event = self._parse_result(result)
                    if event:
                        events.append(event)
                soup.decompose()
            browser.close()
        return events

    def _parse_result(self, result) -> Event | None:
        if not isinstance(result, Tag):
            return None

        # Title
        title_divs = result.find_all("div", class_="result-title")
        title = title_divs[0].get_text(strip=True) if title_divs else "Event"
        if result.find_all("div", class_="event-canceled-msg"):
            title = f"CANCELLED: {title}"

        # Link
        link_tags = result.find_all("a")
        link = ""
        if link_tags:
            first_link = link_tags[0]
            if isinstance(first_link, Tag):
                link = first_link.get("href", "")

        # Date/Time/Location
        dtl_divs = result.find_all(
            "div",
            class_="event-date-location-container"
        )
        dtl = dtl_divs[0]
        if not isinstance(dtl, Tag):
            return None
        flex_divs = [div for div in dtl.find_all("div", class_="flex") if isinstance(div, Tag)]  # noqa: E501
        date_divs = [div for div in flex_divs[0].find_all("div") if isinstance(div, Tag)]  # noqa: E501
        time_divs = [div for div in flex_divs[1].find_all("div") if isinstance(div, Tag)]  # noqa: E501
        location_divs = [div for div in flex_divs[2].find_all("div") if isinstance(div, Tag)]  # noqa: E501
        date = date_divs[1].get_text(strip=True)
        time_range = time_divs[1].get_text(strip=True).split(' to ')
        location = location_divs[1].get_text(strip=True)
        start_time = self.make_time(date, time_range[0])
        end_time = self.make_time(date, time_range[1])

        # Summary/Description
        summary_div = result.find("div", class_="web-summary")
        summary = summary_div.get_text(strip=True) if summary_div else ""
        description = f"{summary}\n\n{link}"

        # Create event
        event = Event()
        event.add('summary', title)
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('location', location)
        event.add('description', description)
        return event

    @staticmethod
    def make_time(date: str, time: str):
        # Example: date = "Thursday, June 13, 2025", time = "6:30 PM"
        # Remove weekday from date
        date_part = ', '.join(date.split(', ')[1:])
        dt = dateutil_parser.parse(f"{date_part} {time} EST")
        # Convert to UTC
        return dt.astimezone(ZoneInfo("UTC"))
