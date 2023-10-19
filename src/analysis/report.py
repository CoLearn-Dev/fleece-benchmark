from attrs import define
from typing import List, Tuple
import numpy as np


@define
class Report:
    dataset_name: str
    endpoint_model_name: str
    time_usage: float
    request_num: int  # FIXME: add request_failed_num?
    time_usage_per_request: List[float]
    first_res_latency: List[float]

    def avg_latency(self):
        return np.mean(self.first_res_latency)

    def std_latency(self):
        return np.std(self.first_res_latency)

    def match_rate_for_latency(self, target_latency: float):
        return (
            np.sum(np.array(self.first_res_latency) <= target_latency)
            / self.request_num
        )

    token_per_request: List[int]

    def tps_per_request(self):
        [
            self.token_per_request[i] / self.time_usage_per_request[i]
            for i in range(self.request_num)
        ]

    def avg_tps(self):
        return np.mean(self.tps_per_request())

    def std_tps(self):
        return np.std(self.tps_per_request())

    def match_rate_for_tps(self, target_tps: float):
        return np.sum(np.array(self.tps_per_request) >= target_tps) / self.request_num

    visit_total_num: int
    visit_failed_num: int
