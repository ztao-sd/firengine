from dataclasses import dataclass, fields

from firengine.lib.fire_enum import EventType


@dataclass
class BaseEvent:
    timestamp: float
    event_type: EventType


@dataclass
class SubmitOrderEvent:
    pass