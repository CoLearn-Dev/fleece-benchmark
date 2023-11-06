from src.workload_datasets.arena import ArenaDataset
from src.workload_datasets.oasst1 import Oasst1Dataset
from src.workload_datasets.synthesizer import SynthesizerDataset
from src.simulate.sim_workload import sim_workload_in_single_thread
import logging
from src.setup_logger import setup_logger
import asyncio
import pickle
from typing import List
from src.analysis.generate_report import generate_request_level_report
from src.simulate.protocol import ReqResponse
from src.analysis.draw_pic import RequestsStatus, Throughput

if __name__ == "__main__":
    setup_logger(level=logging.INFO)

    from rich import print as rprint

    conf = {
        "api_base": "http://172.31.15.40:8000/v1",
        "api_key": "EMPTY",
        "model": "llama-2-7b-chat",
    }
    arena = ArenaDataset()
    arena_normal = arena.to_workload()[:100]
    arena_separate = arena.to_workload(separate_req_in_one_visit_with_interval=10)[:100]
    oasst = Oasst1Dataset()
    oasst_normal = oasst.to_workload()[:100]
    oasst_separate = oasst.to_workload(separate_req_in_one_visit=True)[:100]
    syn = SynthesizerDataset(oasst.dialogs())

    def workload_func(max_stage=6):
        stage = 1000
        reqs = [int(2**i) for i in range(10)]
        sum_reqs = [sum(reqs[:i]) for i in range(1, len(reqs) + 1)]

        def workload(t):
            if t < stage * max_stage:
                return sum_reqs[int(t / stage)]
            else:
                None

        return workload

    testcases = [
        (
            "line_5s_70b_oct27_large",
            syn.to_workload(
                workload_generator=lambda t: int(t / 5 + 1) if t < 900 else None
            ),
        ),
    ]
    for n, w in testcases:
        import os

        if os.path.exists(f"tmp/responses_{n}.pkl"):
            continue

        logging.info(f"start {n}, size {len(w)}")
        pickle.dump(
            asyncio.run(
                sim_workload_in_single_thread(
                    w, None, skip_idle_min=20, time_step=0.001, request_timeout = 3600, **conf
                )
            ),
            open(f"tmp/responses_{n}.pkl", "wb"),
        )

    responses: List[List[ReqResponse]] = [
        sum(
            [v.responses for v in pickle.load(open(f"tmp/responses_{n}.pkl", "rb"))], []
        )
        for n, _ in testcases
    ]
    logging.info("start generate reports")
    reports = [
        generate_request_level_report(responses[i], "meta-llama/Llama-2-7b-chat-hf")
        for i in range(len(testcases))
    ]
    reports_show_as_dict = [r.show_as_dict() for r in reports]
    rprint(reports_show_as_dict)
    for i in range(len(testcases)):
        RequestsStatus(responses[i], f"tmp/rs_{testcases[i][0]}.png")
        Throughput(reports[i], f"tmp/tp_{testcases[i][0]}.png")
