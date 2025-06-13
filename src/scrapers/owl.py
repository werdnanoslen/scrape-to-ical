from feedparser import parse
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper


class OwlScraper(AbstractScraper):
    NAME = "The Owl Music Parlor"
    URL = "https://theowl.nyc/feed/mfgigcal"

    @staticmethod
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

    def get_events(self) -> list[Event]:
        d = parse(self.URL)
        events = []
        for entry in d.entries:
            dtstart = OwlScraper.parse_datetime(
                str(entry['mfgigcal_event-date'] or ''),
                str(entry['mfgigcal_event-time'] or '00:00')
            )
            dtend = dtstart + timedelta(hours=2)
            event_time = entry.get('mfgigcal_event-time', '')
            content = entry.get('mfgigcal_content', '')
            link = entry.get('link', '')
            if event_time:
                matches = list(
                    re.finditer(
                        r'(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)',
                        str(event_time)
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
                    label = str(event_time[start:end]).strip()
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
                details = f'{link}\n{content}' if link else content
            event = Event()
            event.add('uid', entry.get('id') or entry.get('guidislink', ''))
            event.add('dtstamp', dtstart)
            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            event.add('summary', entry.get('title', ''))
            event.add('description', details)
            event.add('location', 'The Owl Music Parlor,  497 Rogers Ave. Brooklyn, NY 11225')  # noqa: E501
            events.append(event)
        return events
