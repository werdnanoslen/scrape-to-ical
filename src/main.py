from my_calendar import MyCalendar
from scrapers.bbg import BBGScraper
from scrapers.bric import BRICScraper
from scrapers.barzakh import BarzakhScraper
from scrapers.bpl import BPLScraper
from scrapers.bfc import BFCScraper
from scrapers.red import RedScraper
from scrapers.jazz_generation import JazzGenerationScraper


def main() -> None:
    MyCalendar(BBGScraper()).write()
    MyCalendar(BRICScraper()).write()
    MyCalendar(BarzakhScraper()).write()
    MyCalendar(BPLScraper()).write()
    MyCalendar(BFCScraper()).write()
    MyCalendar(RedScraper()).write()
    MyCalendar(JazzGenerationScraper()).write()


if __name__ == '__main__':
    main()
