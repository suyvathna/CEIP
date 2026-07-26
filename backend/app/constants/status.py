from enum import Enum


class RecordStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"