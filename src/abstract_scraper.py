from abc import ABC, abstractmethod
from icalendar import Event


class AbstractScraper(ABC):
    NAME: str
    URL: str

    @abstractmethod
    def get_events(self) -> list[Event]:
        pass
