from attrs import define
from ..Datasets.protocol import ReqId
from typing import List, Tuple, Dict
from ..API.api_protocol import ResPiece


@define
class Response:
    req_id: ReqId
    start_timestamp: float
    end_timestamp: float
    dialog: List[Dict[str, str]]
    loggings: List[Tuple[float, ResPiece]]


VisitResponse = List[Response]
