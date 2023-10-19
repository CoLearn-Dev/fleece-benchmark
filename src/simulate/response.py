from attrs import define, field
import time
from ..Datasets.workload import ReqId
from typing import List, Tuple, Dict
from ..API.api_protocol import ResPiece


@define
class Response:
    req_id: ReqId
    start_timestamp: float
    dialog: List[Dict[str, str]]
    loggings: List[Tuple[float, ResPiece]]


VisitResponse = List[Response]
