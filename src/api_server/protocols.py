from pydantic import BaseModel
from typing import Tuple


class TestConfig(BaseModel):
    url: str
    model: str
    dataset_name: str
    endpoint_type: str
    key: str = "EMPTY"
    random_seed: int | None = None
    dataset_config: dict = {}
    workload_range: Tuple[int | None, int | None] = (None, None)
    kwargs: dict = {}

    def get_model_name(self):
        return self.model.split("/")[-1]
