from pydantic import BaseModel
from typing import Tuple

class TestConfig(BaseModel):
    url: str
    model: str
    dataset_name: str
    key: str = "EMPTY"
    dataset_config: dict = {}
    workload_range: Tuple[int|None,int|None] = (None, None)
    kwargs: dict = {}