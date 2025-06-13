from my_calendar import MyCalendar
from scrapers.barzakh import BarzakhScraper
from scrapers.owl import OwlScraper


def main() -> None:
    MyCalendar(OwlScraper()).write()
    MyCalendar(BarzakhScraper()).write()


if __name__ == '__main__':
    main()
