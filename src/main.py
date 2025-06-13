from my_calendar import MyCalendar
from scrapers.owl import OwlScraper
from scrapers.bric import BRICScraper
from scrapers.barzakh import BarzakhScraper
from scrapers.bpl import BPLScraper


def main() -> None:
    MyCalendar(OwlScraper()).write()
    MyCalendar(BRICScraper()).write()
    MyCalendar(BarzakhScraper()).write()
    MyCalendar(BPLScraper()).write()


if __name__ == '__main__':
    main()
