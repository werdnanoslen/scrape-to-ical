import argparse
from my_calendar import MyCalendar
from scrapers.bbg import BBGScraper
from scrapers.bric import BRICScraper
from scrapers.barzakh import BarzakhScraper
from scrapers.bpl import BPLScraper
from scrapers.bfc import BFCScraper
from scrapers.red import RedScraper
from scrapers.jazz_generation import JazzGenerationScraper

SCRAPERS = {
    'bbg': BBGScraper,
    'bric': BRICScraper,
    'barzakh': BarzakhScraper,
    'bpl': BPLScraper,
    'bfc': BFCScraper,
    'red': RedScraper,
    'jazz_generation': JazzGenerationScraper,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('calendar', nargs='?', choices=SCRAPERS.keys(),
                        help='run only this calendar (default: all)')
    args = parser.parse_args()

    targets = [args.calendar] if args.calendar else SCRAPERS.keys()
    for name in targets:
        MyCalendar(SCRAPERS[name]()).write()


if __name__ == '__main__':
    main()
