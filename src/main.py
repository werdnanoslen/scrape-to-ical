from my_calendar import MyCalendar
from owl import OwlCalendarSource


def main() -> None:
    MyCalendar(OwlCalendarSource()).write()


if __name__ == '__main__':
    main()
