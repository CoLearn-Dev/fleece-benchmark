from ..simulate.protocol import VisitResponse, ReqResponse, ReqResponseWithException
from .report import VisitLevelReport, RequestLevelReport
from typing import List, Tuple


def generate_request_level_report(
    ress: List[ReqResponseWithException], tokenizer_name: str
) -> RequestLevelReport:
    success = [res for res in ress if isinstance(res, ReqResponse)]
    TTLB = [res.loggings[0][0] - res.start_timestamp for res in success]
    start_on_time = [res.launch_latency == 0.0 for res in success]
    time_per_request = [res.end_timestamp - res.start_timestamp for res in success]
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    except Exception as e:
        print("load tokenizer failed, error info:", e)
        raise e
    token_per_request = [
        len(tokenizer(c.dialog[-1]["content"], return_tensors="np")["input_ids"][0])
        for c in success
    ]
    TPS: List[float] = []
    for ti, to in zip(time_per_request, token_per_request):
        if ti == 0:
            TPS.append(0)
        else:
            TPS.append(to / ti)
    return RequestLevelReport(
        request_num=len(ress),
        fail_rate=1 - len(success) / len(ress),
        TTLB=TTLB,
        SLO=len(start_on_time) / len(ress),
        time_per_request=time_per_request,
        token_per_request=token_per_request,
        TPS=TPS,
        tokenizer_name=tokenizer_name,
    )


def generate_visit_level_report(
    ress: List[VisitResponse], tokenizer_name: str
) -> VisitLevelReport:
    return VisitLevelReport(
        visit_num=len(ress),
        fail_rate=1 - len([res for res in ress if res.failed is False]) / len(ress),
        time_usage_per_visit=[res.end_timestamp - res.start_timestamp for res in ress],
        request_level_report=generate_request_level_report(
            sum([v.responses for v in ress], []),
            tokenizer_name,
        ),
    )

def generate(ress: List[VisitResponse], tokenizer_name: str, report_level: str) -> VisitLevelReport|RequestLevelReport:
    assert report_level in ["visit", "request"]
    if report_level == "visit":
        return generate_visit_level_report(ress, tokenizer_name)
    else:
        for res in ress:
            assert len(res.responses) == 1
        return generate_request_level_report([v.responses[0] for v in ress], tokenizer_name)

if __name__ == "__main__":
    from ..Datasets.arena import ArenaDataset
    from ..Datasets.oasst1 import Oasst1Dataset
    from ..simulate.sim_workload import sim_workload_in_single_thread
    import logging
    from ..setup_logger import setup_logger
    import asyncio
    import pickle

    
    setup_logger(level=logging.INFO)

    from rich import print as rprint

    conf = {
        "api_base": "http://3.14.115.113:8000/v1",
        "api_key": "EMPTY",
        "model": "vicuna-7b-v1.3",
    }
    arena = ArenaDataset()
    arena_normal = arena.to_workload()[:100]
    arena_separate = arena.to_workload(separate_req_in_one_visit_with_interval=10)[:100]
    oasst = Oasst1Dataset()
    oasst_normal = oasst.to_workload()[:100]
    oasst_separate = oasst.to_workload(separate_ret_in_one_visit=True)[:100]
    testcases = [
        ("arena_normal", arena_normal),
        ("arena_separate", arena_separate),
        # ("oasst_normal", oasst_normal),
        # ("oasst_separate", oasst_separate),
    ]
    for n, w in testcases:
        import os
        if os.path.exists(f"tmp/responses_{n}.pkl"):
            continue
        logging.info(f"start {n}")
        responses = asyncio.run(
            sim_workload_in_single_thread(w, None, skip_idle_min=0.3, **conf)
        )
        pickle.dump(responses, open(f"tmp/responses_{n}.pkl", "wb"))

    responses = [pickle.load(open(f"tmp/responses_{n}.pkl", "rb")) for n, _ in testcases]
    levels = ["visit" if "normal" in n else "request" for n, _ in testcases]
    reports = [generate(responses[i], "meta-llama/Llama-2-7b-chat-hf", levels[i]) for i in range(len(testcases))]
    reports_show_as_dict = [r.show_as_dict() for r in reports]
    rprint(reports_show_as_dict)
