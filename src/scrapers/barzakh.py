from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper
from playwright.sync_api import sync_playwright


class BarzakhScraper(AbstractScraper):
    NAME = "Barzakh Cafe"
    URL = "https://www.viewcy.com/o/barzakhcafe?tab=events"

    def get_events(self) -> list[Event]:
        events = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.URL)
            page.wait_for_timeout(5000)  # adjust as needed
            content = page.content()
            strainer = SoupStrainer(
                "div",
                attrs={'data-sentry-component': 'EventCard'}
            )
            soup = BeautifulSoup(content, "lxml", parse_only=strainer)
            for result in soup:
                if not isinstance(result, Tag):
                    continue
                title = result.find('h3')
                summary = title.get_text() if isinstance(title, Tag) else ''

                # datetime, looks like "Jun 13, 2025 • 8:00 PM EDT"
                datetime_div = result.find(
                    'div',
                    class_=lambda c: bool(c and 'styles_dates' in c)
                )
                if not isinstance(datetime_div, Tag):
                    continue
                date_str = ''
                time_str = ''
                text = datetime_div.get_text(strip=True)
                date_str, time_str = [p.strip() for p in text.split('•')]
                format = "%b %d, %Y %I:%M %p %Z"
                dt = datetime.strptime(f"{date_str} {time_str}", format)
                local_tz = ZoneInfo("America/New_York")
                dt_local = dt.replace(tzinfo=local_tz)
                dtstart = dt_local.astimezone(ZoneInfo("UTC"))
                dtend = dtstart + timedelta(hours=2)

                # details
                img = result.find('img')
                link = result.find('a', href=True)
                path = link.get('href') if isinstance(link, Tag) else None
                href = f'https://www.viewcy.com{path}'
                details = f"{href}\n{img}" if img else href

                # Create the event
                event = Event()
                event.add('uid', summary)
                event.add('summary', summary)
                event.add('dtstamp', dtstart)
                event.add('dtstart', dtstart)
                event.add('dtend', dtend)
                event.add('description', details)
                event.add('location', 'Barzakh Cafe, 147 Utica Ave, Brooklyn, NY 11213')  # noqa: E501
                events.append(event)
            browser.close()
        return events
