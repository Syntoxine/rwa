from enum import Enum

class EventType(Enum):
    # EJECT = "was ejected from"
    # EJECT_BANNED = "was ejected and banned"
    MOVE = "relocated from"
    FOUNDING = "was founded"
    FOUNDING_REFOUND = "was refounded"
    CTE = "ceased to"
    MEMBER_APPLY = "applied to"
    MEMBER_ADMIT = "was admitted"
    MEMBER_RESIGN = "resigned from"
    MEMBER_DELEGATE = "became WA"
    MEMBER_DELEGATE_SEIZED = "seized"
    MEMBER_DELEGATE_LOST = "lost WA"
    ENDO = "endorsed"
    ENDO_WITHDRAW = "withdrew its"

    @staticmethod
    def event_type_from_str(event_str: str):
        parts = event_str.split()
        for event_type in EventType:
            if " ".join(parts[1:]).startswith(event_type.value):
                return event_type
        raise ValueError(f"Unknown event type in string: {event_str}")
    
    def get_bucket(self) -> str:
        return self.name.lower().split('_')[0]


PARAMETER_POSITIONS: dict[EventType, tuple[int, ...]] = {
    # EventType.EJECT: (4, 6),
    # EventType.EJECT_BANNED: (6, 8),
    EventType.MOVE: (3, 5),
    EventType.FOUNDING: (4,),
    EventType.FOUNDING_REFOUND: (4,),
    EventType.CTE: (5,),
    EventType.MEMBER_APPLY: (),
    EventType.MEMBER_ADMIT: (),
    EventType.MEMBER_RESIGN: (),
    EventType.MEMBER_DELEGATE: (5,),
    EventType.MEMBER_DELEGATE_SEIZED: (5, 9),
    EventType.MEMBER_DELEGATE_LOST: (6,),
    EventType.ENDO: (2,),
    EventType.ENDO_WITHDRAW: (5,),
}


class NSEvent:
    def __init__(self, event_str: str):
        self.str = event_str
        parts = event_str.split()
        self.nation = parts[0][2:-2]
        self.event_type = EventType.event_type_from_str(event_str)
        self.parameters = [
            parts[i][2:-2] for i in PARAMETER_POSITIONS.get(self.event_type, ())
        ]

    def __repr__(self) -> str:
        return f"<NSEvent nation='{self.nation}' event_type={self.event_type}{f' parameters={self.parameters}' if self.parameters else ''}>"
    
    def __str__(self) -> str:
        parts = self.str.split()
        parts[0] = f"[{self.nation.title().replace('_', ' ')}](https://nationstates.net/nation={self.nation})"
        for i, param in zip(PARAMETER_POSITIONS.get(self.event_type, ()), self.parameters):
            parts[i] = f"[{param.title().replace('_', ' ')}](https://nationstates.net/nation={param})"
        return " ".join(parts)