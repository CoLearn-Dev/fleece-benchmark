from attrs import define
from typing import List, Tuple
import numpy as np


@define
class RequestLevelReport:
    request_num: int
    fail_rate: float

    TTFT: List[float]  # Time To First Token (TTFT)
    latency: List[float] # Time cost from request to last response
    SLO: float  # Service Level Objective
    time_per_request: List[float]
    token_per_request: List[int]
    token_timestamp: List[Tuple[float, int]]
    TPOT: List[float]  # Time Per Output Token (avg for each request)
    Throughput: float
    tokenizer_name: str

    def show_as_dict(self):
        return {
            "request_num": self.request_num,
            "fail_rate": self.fail_rate,
            "TTFT": {
                "avg": np.mean(self.TTFT),
                "std": np.std(self.TTFT),
            },
            "SLO": self.SLO,
            "TPOT": {
                "avg": np.mean(self.TPOT),
                "std": np.std(self.TPOT),
            },
            "Throughput": self.Throughput,
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
