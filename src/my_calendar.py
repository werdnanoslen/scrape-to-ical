from dataclasses import dataclass, field
from logging import getLogger, info, DEBUG, INFO
import re
from typing import List
from icalendar import Calendar, Event
from os import getenv
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from datetime import datetime


load_dotenv()
OUTPUT_ROOT = getenv('OUTPUT_ROOT')
LOG_LEVEL = getenv('LOG_LEVEL')
assert OUTPUT_ROOT
getLogger().setLevel(DEBUG if LOG_LEVEL == 'DEBUG' else INFO)


class AbstractCalendarSource(ABC):
    NAME: str
    URL: str

    @staticmethod
    @abstractmethod
    def parse_datetime(date_str: str, time_str: str) -> datetime:
        pass

    @abstractmethod
    def get_events(self) -> list[Event]:
        pass


@dataclass
class MyCalendar:
    scraper: AbstractCalendarSource
    events: List[Event] = field(default_factory=list)
    cal: Calendar | None = None
    cal_bytes: bytes | None = None

    def __post_init__(self):
        cal = Calendar()
        cal.add('X-WR-CALNAME', self.scraper.NAME)
        cal.add('X-WR-CALDESC', f'Events for {self.scraper.NAME}')
        cal.add('X-WR-RELCALID', self.scraper.NAME)
        cal.add('X-PUBLISHED-TTL', 'PT6H')
        cal.add('URL', f'https://raw.githubusercontent.com/werdnanoslen/scrape-to-ical/refs/heads/main/calendars/{self.scraper.NAME}.ics')  # noqa: E501
        cal.add('METHOD', 'PUBLISH')
        cal.add('VERSION', '2.0')
        cal.add('PRODID', 'andyhub.com')
        cal.add('CALSCALE', 'GREGORIAN')
        cal.add('X-MICROSOFT-CALSCALE', 'GREGORIAN')
        self.events = self.scraper.get_events()
        for e in self.events:
            cal.add_component(e)
        self.cal = cal
        self.cal_bytes = cal.to_ical(sorted=True)

    def write(self):
        if self.cal_bytes is None:
            raise ValueError("cal_bytes is None. Cannot write calendar file.")
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', self.scraper.NAME)
        filename = f'{OUTPUT_ROOT}/calendars/{safe_name}.ics'
        with open(filename, 'wb') as cf:
            cf.write(self.cal_bytes)
        info(f'Calendar generated, path={filename}')
