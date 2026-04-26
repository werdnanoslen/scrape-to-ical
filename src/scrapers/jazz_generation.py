import requests
import html
from datetime import datetime, timezone
from icalendar import Event
from abstract_scraper import AbstractScraper

BASE_URL = "https://jazzgeneration.org"
COLLECTION_ID = "54badfc9e4b060f2e980c473"
API_URL = f"{BASE_URL}/api/open/GetItemsByMonth"


class JazzGenerationScraper(AbstractScraper):
    NAME = "Jazz Generation"
    URL = API_URL

    def get_events(self) -> list[Event]:
        month_str = datetime.now().strftime("%m-%Y")
        params = {
            "month": month_str,
            "collectionId": COLLECTION_ID,
        }
        resp = requests.get(self.URL, params=params)
        resp.raise_for_status()
        items = resp.json()

        events = []
        for item in items:
            title = html.unescape(item.get("title", "Jazz Generation")).strip()
            start_ms = item.get("startDate")
            end_ms = item.get("endDate")
            if not start_ms:
                continue

            dtstart = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
            dtend = (
                datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)
                if end_ms
                else dtstart.replace(hour=dtstart.hour + 2)
            )

            loc_data = item.get("location") or {}
            address_parts = [
                loc_data.get("addressTitle", ""),
                loc_data.get("addressLine1", ""),
                loc_data.get("addressLine2", ""),
            ]
            location = ", ".join(p for p in address_parts if p)

            full_url = item.get("fullUrl", "")
            event_url = f"{BASE_URL}{full_url}" if full_url else ""
            asset_url = item.get("assetUrl", "")

            description = event_url
            if asset_url:
                description += f'\n\n<img src="{asset_url}" alt="" />'
            id = item.get('id', '')

            event = Event()
            event.add("uid", f"jazz-generation-{id}-{start_ms}")
            event.add("summary", title)
            event.add("dtstamp", dtstart)
            event.add("dtstart", dtstart)
            event.add("dtend", dtend)
            event.add("location", location)
            event.add("description", description)
            events.append(event)

        return events
