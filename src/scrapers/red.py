import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Event
from abstract_scraper import AbstractScraper
from bs4 import BeautifulSoup
import feedparser


class RedScraper(AbstractScraper):
    NAME = "Red Calendar"
    URL = "https://cal.red/rss.xml"

    def get_events(self) -> list[Event]:
        feed = feedparser.parse(self.URL)
        events = []
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            guid = entry.get("guid", "")
            description_html = entry.get("description", "")
            # Parse description for location, cost, and start date
            soup = BeautifulSoup(description_html, "html.parser")
            description_text = soup.get_text(separator="\n")
            location = ""
            cost = ""
            dtstart = None
            for line in description_text.splitlines():
                if line.lower().startswith("location:"):
                    location = line.split(":", 1)[1].strip()
                elif line.lower().startswith("cost:"):
                    cost = line.split(":", 1)[1].strip()
                elif line.lower().startswith("start date:"):
                    # Example: Sun, Feb 15 14:00 ET
                    date_str = line.split(":", 1)[1].strip()
                    try:
                        dt = datetime.strptime(date_str, "%a, %b %d %H:%M ET")
                        # If the date string is missing a year, assume current year
                        if dt.year == 1900:
                            dt = dt.replace(year=datetime.now().year)
                        # Use year from guid if available
                        m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", guid)
                        if m:
                            dt = dt.replace(year=int(m.group(1)[:4]))
                        dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
                        dtstart = dt.astimezone(ZoneInfo("UTC"))
                    except Exception:
                        pass
            # Fallback: try to parse from guid
            if not dtstart:
                m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", guid)
                if m:
                    dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
                    dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
                    dtstart = dt.astimezone(ZoneInfo("UTC"))
            if not dtstart:
                continue
            dtend = dtstart + timedelta(hours=1)
            # Replace newlines in location with ', '
            if "\n" in location:
                location = ", ".join([l.strip() for l in location.split("\n") if l.strip()])
            desc_lines = []
            for line in description_text.splitlines():
                l = line.lower()
                # Exclude location and start date lines, and also exclude cost lines (will add cost separately)
                if not (l.startswith("location:") or l.startswith("start date:") or l.startswith("cost:")):
                    desc_lines.append(line)
            desc = (f"{link}\n" + "\n".join(desc_lines)).strip()
            if cost:
                desc += f"\nCost: {cost}"
            event = Event()
            event.add("uid", guid)
            event.add("summary", title)
            event.add("dtstamp", dtstart)
            event.add("dtstart", dtstart)
            event.add("dtend", dtend)
            event.add("location", location)
            event.add("description", desc)
            events.append(event)
        return events
