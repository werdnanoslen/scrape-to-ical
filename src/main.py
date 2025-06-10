import logging
import os
from dotenv import load_dotenv

from feedparser import parse

from my_calendar import MyCalendar, MyCalendarEvent

load_dotenv()
OUTPUT_ROOT = os.getenv('OUTPUT_ROOT')
LOG_LEVEL = os.getenv('LOG_LEVEL')

assert OUTPUT_ROOT

logging.getLogger().setLevel(logging.DEBUG if LOG_LEVEL == 'DEBUG'
                             else logging.INFO)


def main() -> None:
    url = 'https://theowl.nyc/feed/mfgigcal/'
    d = parse(url)
    title = d.channel.title  # type: ignore
    cal = MyCalendar.to_my_calendar(
        title,
        MyCalendarEvent.to_my_calendar_events(d.entries)  # type: ignore
    )
    calendar_path = f'{OUTPUT_ROOT}/calendars/{title}.ics'
    with open(calendar_path, 'wb') as cf:
        cf.write(cal.to_bytes())
    logging.info(f'Calendar generated, path={calendar_path}')


if __name__ == '__main__':
    main()
    # asyncio.run(fetch_data())
