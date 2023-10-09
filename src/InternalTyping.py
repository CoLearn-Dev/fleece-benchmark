from attrs import define
from typing import List, Dict


@define(kw_only=True)
class DataId:
    dataset_name: str
    unique_id: str

    def __hash__(self) -> int:
        return hash((self.dataset_name, self.unique_id))


@define
class WorkLoadData:
    """
    generate request rule:
    1. if workload_body is List[Dict[str, str]], just generate request with history_dialog
    2. if workload_body is List[str]
        - use the timestamp as the start time of the requests
        - genreate requests with next inputs after llm return the previous response(finally generate len(workload_body) requests)
        - each request wait for the fake user input time
    3. especially, if len(workload_body) == 1, these two rules are the same
    """

    index: DataId
    timestamp: float
    workload_body: List[Dict[str, str]] | List[str]
    n: int = 1
    temputure: float | None = None
    top_p: int | None = None
    max_tokens: int | None = None


@define
class AnalysisData:
    index: DataId
    history_ids: List[DataId]
    std_dialog: List[Dict[str, str]]
    language: str
    std_is_bad: bool = False
    std_response_timetable: List[float] | None = None
