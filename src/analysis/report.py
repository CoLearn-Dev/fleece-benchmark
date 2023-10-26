from attrs import define
from typing import List, Tuple
import numpy as np


@define
class RequestLevelReport:
    request_num: int
    fail_rate: float

    TTLB: List[float]  # Time To Last Byte
    SLO: float  # Service Level Objective
    time_per_request: List[float]
    token_per_request: List[int]
    token_timestamp: List[Tuple[float, int]]
    TPS: List[float]  # Tokens Per Second
    tokenizer_name: str

    def show_as_dict(self):
        return {
            "request_num": self.request_num,
            "fail_rate": self.fail_rate,
            "TTLB": {
                "avg": np.mean(self.TTLB),
                "std": np.std(self.TTLB),
            },
            "SLO": self.SLO,
            "TPS": {
                "avg": np.mean(self.TPS),
                "std": np.std(self.TPS),
            },
        }

    def visualize(self):
        raise NotImplementedError


@define
class VisitLevelReport:
    visit_num: int
    fail_rate: float
    time_usage_per_visit: List[float]
    request_level_report: RequestLevelReport

    def show_as_dict(self):
        return {
            "visit_num": self.visit_num,
            "fail_rate": self.fail_rate,
            "request_level_report": self.request_level_report.show_as_dict(),
        }

    def visualize(self):
        raise NotImplementedError
