from ..simulate.protocol import VisitResponse, ReqResponse
from typing import List
from attrs import asdict
import numpy as np
from ..analysis.generate_report import generate_request_level_report

if __name__ == "__main__":
    import pickle
    import json

    ids = [
        "073bf042-0ab0-4e27-88bf-ded93c560791",
        "cd5a98f4-cda1-44e4-b848-b077cc04850e",
        "00bbf906-b868-4a30-b311-d167d1f08b13",
    ]
    for id in ids:
        path = f"tmp/responses_{id}.pkl"
        data: List[VisitResponse] = pickle.load(open(path, "rb"))
        data = [asdict(v) for v in data]
        json.dump(data, open(f"tmp/responses_{id}.json", "w"))
        # responses: List[ReqResponse] = sum([v.responses for v in data], [])
        # report = generate_request_level_report(responses, 'llama')
        # pickle.dump(
        #     report,
        #     open(f"tmp/raw_report_{id}.pkl", "wb"),
        # )
