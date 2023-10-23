from attrs import define
from ..Datasets.protocol import ReqId
from typing import List, Tuple, Dict
from ..API.api_protocol import ResPiece


@define
class ReqResponse:
    req_id: ReqId
    start_timestamp: float
    end_timestamp: float
    dialog: List[Dict[str, str]]
    loggings: List[Tuple[float, ResPiece]]
    launch_latency: float = 0.0


ReqResponseWithException = ReqResponse | Tuple[float, BaseException]


@define
class VisitResponse:
    start_timestamp: float
    end_timestamp: float
    responses: List[ReqResponseWithException]
    failed: bool = False
