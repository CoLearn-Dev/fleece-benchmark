from ..simulate.protocol import VisitResponse
from ..Datasets.protocol import Workload
from typing import List


def generate(workload: Workload, ress: List[VisitResponse | BaseException]):
    """
    Generate a report for the workload and the responses.
    """
    raise NotImplementedError
