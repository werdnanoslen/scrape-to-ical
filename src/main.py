from my_calendar import MyCalendar
from scrapers.owl import OwlScraper
from scrapers.barzakh import BarzakhScraper


def main() -> None:
    MyCalendar(OwlScraper()).write()
    MyCalendar(BarzakhScraper()).write()


if __name__ == '__main__':
    main()
