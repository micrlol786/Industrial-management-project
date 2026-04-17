

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Product:
    """
    Represents one finished-goods unit flowing through the manufacturing process.

    Attributes:
        unit_id        : sequential identifier
        arrival_time   : simulation time when unit entered the line [min]
        departure_time : simulation time when unit left the last WS [min]
        route          : ordered list of WS ids visited
        wait_times     : wait time at each workstation [min]
        process_times  : actual processing time at each workstation [min]
    """
    unit_id: int
    arrival_time: float = 0.0
    departure_time: Optional[float] = None

    route: List[int] = field(default_factory=list)
    wait_times: List[float] = field(default_factory=list)
    process_times: List[float] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    #  Derived metrics                                                     #
    # ------------------------------------------------------------------ #

    @property
    def lead_time(self) -> Optional[float]:
        """Total time from entering to leaving the line [min]."""
        if self.departure_time is None:
            return None
        return round(self.departure_time - self.arrival_time, 3)

    @property
    def total_wait(self) -> float:
        return round(sum(self.wait_times), 3)

    @property
    def total_processing(self) -> float:
        return round(sum(self.process_times), 3)

    @property
    def value_added_ratio(self) -> float:
        """Processing time / lead time — lean efficiency measure."""
        lt = self.lead_time
        if lt is None or lt == 0:
            return 0.0
        return round(self.total_processing / lt, 4)

    def record_step(self, ws_id: int, wait: float, processing: float) -> None:
        self.route.append(ws_id)
        self.wait_times.append(wait)
        self.process_times.append(processing)

    def complete(self, departure_time: float) -> None:
        self.departure_time = departure_time

    def to_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "arrival_time": self.arrival_time,
            "departure_time": self.departure_time,
            "lead_time": self.lead_time,
            "total_wait": self.total_wait,
            "total_processing": self.total_processing,
            "value_added_ratio": self.value_added_ratio,
            "route": self.route,
        }
