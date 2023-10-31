from attrs import define
from ..workload_datasets.protocol import ReqId
from typing import List, Tuple, Dict, Optional
from ..API.api_protocol import ResPiece


@define
class ReqResponse:
    req_id: ReqId
    start_timestamp: float
    end_timestamp: float
    dialog: List[Dict[str, str]] = []
    loggings: List[Tuple[float, ResPiece]] = []
    launch_latency: float = 0.0
    error_info: Optional[Tuple[str, str]] = None  # (error message, traceback)


@define
class VisitResponse:
    start_timestamp: float
    end_timestamp: float
    responses: List[ReqResponse]
    failed: bool = False
