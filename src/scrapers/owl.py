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
    def parse_datetime(date_str: str, time_str: str):
        # Returns a list of tuples: (dtstart, dtend, allday)
        range_pattern = r"([A-Za-z]+)\s+(\d+)-(\d+),\s*(\d{4})"
        range_match = re.match(range_pattern, date_str.strip())
        results = []
        if range_match:
            month = range_match.group(1)
            first_day = int(range_match.group(2))
            last_day = int(range_match.group(3))
            year = int(range_match.group(4))
            for day in range(first_day, last_day + 1):
                single_date_str = f"{month} {day}, {year}"
                date_fmt = "%b %d, %Y"
                try:
                    date_obj = datetime.strptime(
                        single_date_str.strip(),
                        date_fmt
                    )
                except Exception:
                    continue
                if not time_str.strip():
                    # All-day event
                    dtstart = date_obj.date()
                    dtend = (date_obj + timedelta(days=1)).date()
                    results.append((dtstart, dtend, True))
                else:
                    time_obj = OwlScraper._parse_time(time_str)
                    dt = datetime.combine(date_obj.date(), time_obj)
                    local_dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
                    dt_utc = local_dt.astimezone(ZoneInfo("UTC"))
                    dtend = dt_utc + timedelta(hours=2)
                    results.append((dt_utc, dtend, False))
            return results
        else:
            date_fmt = "%b %d, %Y"
            try:
                date_obj = datetime.strptime(date_str.strip(), date_fmt)
            except Exception:
                date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            if not time_str.strip():
                dtstart = date_obj.date()
                dtend = (date_obj + timedelta(days=1)).date()
                return [(dtstart, dtend, True)]
            else:
                time_obj = OwlScraper._parse_time(time_str)
                dt = datetime.combine(date_obj.date(), time_obj)
                local_dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
                dt_utc = local_dt.astimezone(ZoneInfo("UTC"))
                dtend = dt_utc + timedelta(hours=2)
                return [(dt_utc, dtend, False)]

    @staticmethod
    def _parse_time(time_str: str):
        m = re.search(r'(\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)', time_str)
        if m:
            time_part = m.group(1).strip()
            if not re.search(r'[ap]m', time_part, re.IGNORECASE):
                time_part += ' pm'
            try:
                return datetime.strptime(time_part, "%I:%M %p").time()
            except Exception:
                try:
                    return datetime.strptime(time_part, "%H:%M").time()
                except Exception:
                    return datetime.strptime("00:00", "%H:%M").time()
        else:
            return datetime.strptime("00:00", "%H:%M").time()

    def get_events(self) -> list[Event]:
        d = parse(self.URL)
        events = []
        for entry in d.entries:
            dtinfos = OwlScraper.parse_datetime(
                str(entry.get('mfgigcal_event-date', '') or ''),
                str(entry.get('mfgigcal_event-time', '') or '')
            )
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

            for dtstart, dtend, allday in dtinfos:
                event = Event()
                id = entry.get('id') or entry.get('guidislink', '')
                event.add('summary', entry.get('title', ''))
                event.add('description', details)
                event.add('location', 'The Owl Music Parlor, 497 Rogers Ave., Brooklyn, NY 11225')  # noqa: E501
                if allday:
                    event.add('uid', f"{id}-{dtstart.isoformat()}")
                    event.add('dtstart', dtstart)
                    event['dtstart'].params['VALUE'] = 'DATE'
                    event.add('dtend', dtend)
                    event['dtend'].params['VALUE'] = 'DATE'
                else:
                    event.add('uid', f"{id}-{dtstart}")
                    event.add('dtstamp', dtstart)
                    event.add('dtstart', dtstart)
                    event.add('dtend', dtend)
                events.append(event)
        return events
