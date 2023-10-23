from attrs import define
from typing import List


@define
class RequestLevelReport:
    request_num: int
    fail_rate: float

    TTLB: List[float]  # Time To Last Byte
    SLO: float  # Service Level Objective
    time_per_request: List[float]
    token_per_request: List[int]
    TPS: List[float]  # Tokens Per Second
    tokenizer_name: str


@define
class VisitLevelReport:
    visit_num: int
    fail_rate: float
    time_usage_per_visit: List[float]
    request_level_report: RequestLevelReport
