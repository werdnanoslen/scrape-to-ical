import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper


class BRICScraper(AbstractScraper):
    NAME = "BRIC"
    URL = "https://bricartsmedia.org/wp-json/dod/v1/slot"

    def get_events(self) -> list[Event]:
        events = []
        # Calculate date_from as today minus 7 days
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        params = {
            "date_from": date_from,
            "per_page": 100
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # noqa: E501
        }
        resp = requests.get(self.URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            title = item.get("name", "BRIC Event")
            link = item.get("post_permalink", "")
            cost = item.get("cost", "")
            status = item.get("status", "")
            loc = item.get("primary_location")
            location = ""
            img_url = item.get("image_url", "")

            # Compose description
            description_parts = []
            if status and status.lower() != "active":
                description_parts.append(f"Status: {status}")
            if cost:
                description_parts.append(f"Cost: {cost}")
            if link:
                description_parts.append(link)
            if loc:
                location = loc.get("name", "")
                meta = loc.get("meta", {})
                if isinstance(meta, dict):
                    location_link = meta.get("location_link", "")
                elif isinstance(meta, list) and meta:
                    # If meta is a list, try the first element
                    meta_first = meta[0]
                    if isinstance(meta_first, dict):
                        location_link = meta_first.get("location_link", "")
                    else:
                        location_link = ""
                else:
                    location_link = ""
                loc_link = ""
                if isinstance(location_link, dict):
                    loc_link = location_link.get("url", "")
                elif isinstance(location_link, str):
                    loc_link = location_link
                if loc_link:
                    description_parts.append(loc_link)
            if img_url:
                description_parts.append(f"<img src=\"{img_url}\" alt=\"\" />")
            description = "\n".join(description_parts)

            # Date and time
            date_str = item.get("date")
            time_start = item.get("time_start")
            time_end = item.get("time_end")
            if not (date_str and time_start):
                continue
            format = "%Y-%m-%d %H:%M:%S"
            dtstart = datetime.strptime(f"{date_str} {time_start}", format)
            dtstart = dtstart.replace(tzinfo=ZoneInfo("America/New_York"))
            dtstart = dtstart.astimezone(ZoneInfo("UTC"))
            if time_end:
                dtend = datetime.strptime(f"{date_str} {time_end}", format)
                dtend = dtend.replace(tzinfo=ZoneInfo("America/New_York"))
                dtend = dtend.astimezone(ZoneInfo("UTC"))
            else:
                dtend = dtstart + timedelta(hours=2)

            # Create event
            event = Event()
            event.add('uid', f"{title}-{dtstart.isoformat()}")
            event.add('summary', title)
            event.add('dtstamp', dtstart)
            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            event.add('location', location)
            event.add('description', description)
            events.append(event)
        return events
