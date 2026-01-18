from my_calendar import MyCalendar
from scrapers.bbg import BBGScraper
from scrapers.owl import OwlScraper
from scrapers.bric import BRICScraper
from scrapers.barzakh import BarzakhScraper
from scrapers.bpl import BPLScraper
from scrapers.bfc import BFCScraper


def main() -> None:
    MyCalendar(BBGScraper()).write()
    MyCalendar(OwlScraper()).write()
    MyCalendar(BRICScraper()).write()
    MyCalendar(BarzakhScraper()).write()
    MyCalendar(BPLScraper()).write()
    MyCalendar(BFCScraper()).write()


if __name__ == '__main__':
    main()
