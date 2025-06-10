from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from icalendar import Calendar, Event
import re
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MyCalendarEvent:
    id: str
    title: str
    dtstart: datetime
    dtend: datetime
    details: str

    @staticmethod
    def to_my_calendar_events(entries: list[dict]):
        return [MyCalendarEvent.to_my_calendar_event(e) for e in entries]

    @staticmethod
    def to_my_calendar_event(entry: dict):
        def parse_datetime(date_str: str, time_str: str) -> datetime:
            # Example: date_str = 'Jun 5, 2025',
            # Example: time_str = '7:30 Doors 8:00 Music $15.00 suggested donation'  # noqa: E501
            date_fmt = "%b %d, %Y"
            try:
                date_obj = datetime.strptime(date_str.strip(), date_fmt)
            except Exception:
                date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            m = re.search(r'(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)', time_str)
            if m:
                time_part = m.group(1).strip()
                # If no am/pm specified, default to pm
                if not re.search(r'[ap]m', time_part, re.IGNORECASE):
                    time_part += ' pm'
                try:
                    time_obj = datetime.strptime(time_part, "%I:%M %p").time()
                except Exception:
                    try:
                        time_obj = datetime.strptime(time_part, "%H:%M").time()
                    except Exception:
                        time_obj = datetime.strptime("00:00", "%H:%M").time()
            else:
                time_obj = datetime.strptime("00:00", "%H:%M").time()
            dt = datetime.combine(date_obj.date(), time_obj)
            local_dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
            dt_utc = local_dt.astimezone(ZoneInfo("UTC"))
            return dt_utc

        dtstart = parse_datetime(
            entry.get('mfgigcal_event-date', ''),
            entry.get('mfgigcal_event-time', '00:00')
        )
        dtend = dtstart + timedelta(hours=2)
        event_time = entry.get('mfgigcal_event-time', '')
        content = entry.get('mfgigcal_content', '')
        link = entry.get('link', '')
        if event_time:
            matches = list(
                re.finditer(
                    r'(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)',
                    event_time
                )
            )
            formatted_time = ''
            for i, match in enumerate(matches):
                time = match.group(1).strip()
                start = match.end()
                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    end = len(event_time)
                label = event_time[start:end].strip()
                formatted_time += f"{time} {label}\n"
            formatted_time = formatted_time.strip()
            formatted_time = re.sub(
                r'(\$\d+(?:\.\d{2})?\s*[^\n]*)$',
                r'\n\1',
                formatted_time
            )
            details_parts = []
            if link:
                details_parts.append(link)
            if formatted_time:
                details_parts.append(formatted_time)
            if content:
                details_parts.append(content)
            details = "\n".join(details_parts)
        else:
            details = link + "\n" + content if link else content
        return MyCalendarEvent(
            id=entry.get('id') or entry.get('guidislink', ''),
            title=entry.get('title', ''),
            dtstart=dtstart,
            dtend=dtend,
            details=details
        )

    def to_event(self) -> Event:
        event = Event()
        event.add('uid', self.id)
        event.add('dtstamp', self.dtstart)
        event.add('dtstart', self.dtstart)
        event.add('dtend', self.dtend)
        event.add('summary', self.title)
        event.add('description', self.details)
        event.add('location', 'The Owl Music Parlor,  497 Rogers Ave. Brooklyn, NY 11225')  # noqa: E501
        return event


@dataclass()
class MyCalendar:
    name: str
    events: List[MyCalendarEvent]
    cal: Calendar | None = field(init=False)
    cal_bytes: bytes | None = field(init=False)

    def __post_init__(self):
        self.cal = None
        self.cal_bytes = None

    @staticmethod
    def to_my_calendar(name: str,
                       events: List[MyCalendarEvent]):
        return MyCalendar(
            name=name,
            events=events
        )

    def to_calendar(self) -> Calendar:
        if self.cal is None:
            cal = Calendar()
            cal.add('X-WR-CALNAME', self.name)
            cal.add('X-WR-CALDESC', f'Events for {self.name}')
            cal.add('X-WR-RELCALID', self.name)
            cal.add('X-PUBLISHED-TTL', 'PT6H')
            cal.add('URL', f'https://raw.githubusercontent.com/werdnanoslen/scrape-to-ical/refs/heads/main/calendars/{self.name}.ics')  # noqa: E501
            cal.add('METHOD', 'PUBLISH')
            cal.add('VERSION', '2.0')
            cal.add('PRODID', 'andyhub.com')
            cal.add('CALSCALE', 'GREGORIAN')
            cal.add('X-MICROSOFT-CALSCALE', 'GREGORIAN')
            for x in self.events:
                cal.add_component(x.to_event())
            self.cal = cal
        return self.cal

    def to_bytes(self) -> bytes:
        if self.cal_bytes is None:
            self.cal_bytes = self.to_calendar().to_ical(sorted=True)
        return self.cal_bytes
