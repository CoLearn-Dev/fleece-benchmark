from attrs import define, field
import time
from typing import List, Dict


@define(kw_only=True)
class DataId:
    dataset_name: str
    unique_id: str

    def __hash__(self) -> int:
        return hash((self.dataset_name, self.unique_id))


@define(kw_only=True)
class Hyperparameter:
    n: int = 1
    temperature: float | None = None
    top_p: int | None = None
    max_tokens: int | None = None

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
    hyperparameter: Hyperparameter | None = None


@define
class AnalysisData:
    index: DataId
    history_ids: List[DataId]
    std_dialog: List[Dict[str, str]]
    language: str
    std_is_bad: bool = False
    std_response_timetable: List[float] | None = None


@define(kw_only=True)
class InferenceConfig:
    api_base: str
    api_key: str
    model: str


@define(kw_only=True)
class StreamingDelta:
    index: int
    role: str | None = None
    content: str | None = None
    stop: str | None = None


@define
class StreamingResult:
    ctx: StreamingDelta | Exception | None = None
    timestamp: float = field(factory=time.time)


@define(kw_only=True)
class SimluateConfig:
    inference_config: InferenceConfig
    fast_mode: bool = False  # if True, the simulation will skip the gap time when there are no pending requests
    HUMAN_TYPING_WPS: float = 1.0  # human typing speed: words per second
    default_hyperparameter: Hyperparameter = Hyperparameter()
    overwrite_hyperparameter: Hyperparameter | None = None
    stop_on_endpoint_overload: bool = False
    exit_on_benchmark_overload: bool = False
