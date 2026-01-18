from bs4 import BeautifulSoup, Tag
from bs4.filter import SoupStrainer
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper
from playwright.sync_api import sync_playwright
import re


class BFCScraper(AbstractScraper):
    NAME = "Brooklyn Football Club"
    URLW = "https://www.brooklynfootballclub.com/women/schedule/"
    URLM = "https://www.brooklynfootballclub.com/men/schedule/"

    def get_events(self) -> list[Event]:
        def scrape_events(url):
            events = []
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                content = page.content()
                strainer = SoupStrainer(
                    "div",
                    attrs={"class": "entry-content"}
                )
                soup = BeautifulSoup(content, "lxml", parse_only=strainer)
                games = soup.find_all("div", class_=["HomeGame"])
                for result in games:
                    if not isinstance(result, Tag):
                        continue
                    if 'Upcoming' not in result['class']:
                        continue
                    vs = result.find_all('img')[1].get('alt').replace(' logo', '')
                    summary = 'BFC vs ' + vs
                    a_tag = result.find('a')
                    ticket = a_tag.get('href') if isinstance(a_tag, Tag) else 'No ticket link'

                    date_div = result.find(
                        'h5',
                        attrs={'id': 'saturday-august-31st'}
                    )
                    date = date_div.get_text().split(',')[1].strip()
                    now = datetime.now()
                    month = datetime.strptime(date.split()[0], "%B").month
                    year = now.year+1 if month < now.month else now.year
                    time_div = date_div.find_next_sibling('p')
                    time = time_div.get_text().split(' | ')[0].strip()
                    datetime_str = f"{date} {year} {time}"
                    # Remove trailing timezone abbreviation ('EDT')
                    datetime_str = re.sub(r'\s([A-Z]{2,4})$', '', datetime_str)
                    dt = datetime.strptime(datetime_str, "%B %d %Y %I:%M %p")
                    dt_local = dt.replace(tzinfo=ZoneInfo("America/New_York"))
                    dtstart = dt_local.astimezone(ZoneInfo("UTC"))
                    dtend = dtstart + timedelta(hours=2)

                    # Create the event
                    event = Event()
                    event.add('uid', now)
                    event.add('summary', summary)
                    event.add('dtstamp', dtstart)
                    event.add('dtstart', dtstart)
                    event.add('dtend', dtend)
                    event.add('description', ticket)
                    event.add('location', 'Maimonides Park, Brooklyn, NY')  # noqa: E501
                    events.append(event)
                browser.close()
            return events

        # Scrape both URLs and combine results
        all_events = scrape_events(self.URLW) + scrape_events(self.URLM)
        return all_events
