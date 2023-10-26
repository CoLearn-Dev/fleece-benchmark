from ..simulate.protocol import VisitResponse, ReqResponse
from .report import VisitLevelReport, RequestLevelReport
from typing import List, Tuple


def generate_request_level_report(
    ress: List[ReqResponse], tokenizer_name: str
) -> RequestLevelReport:
    success = [res for res in ress if res.error_info is None]
    TTLB = [res.loggings[0][0] - res.start_timestamp for res in success]
    start_on_time = [res.launch_latency == 0.0 for res in success]
    time_per_request = [res.end_timestamp - res.start_timestamp for res in success]
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    except Exception as e:
        print("load tokenizer failed, error info:", e)
        raise e
    token_per_request = []
    token_timestamp = []
    for c in success:
        count = 0
        for pack in c.loggings:
            if not pack[1].content:
                continue
            if "llama" in tokenizer_name:
                num = 1
            else:
                num = len(
                    tokenizer(pack[1].content, return_tensors="np")["input_ids"][0]
                )
            count += num
            token_timestamp.append((pack[0], num))
        token_per_request.append(count)
    token_timestamp.sort(key=lambda x: x[0])
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
        token_timestamp=token_timestamp,
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


def generate(
    ress: List[VisitResponse], tokenizer_name: str, report_level: str
) -> VisitLevelReport | RequestLevelReport:
    assert report_level in ["visit", "request"]
    if report_level == "visit":
        return generate_visit_level_report(ress, tokenizer_name)
    else:
        for res in ress:
            assert len(res.responses) == 1
        return generate_request_level_report(
            [v.responses[0] for v in ress], tokenizer_name
        )


if __name__ == "__main__":
    from ..Datasets.arena import ArenaDataset
    from ..Datasets.oasst1 import Oasst1Dataset
    from ..Datasets.synthesizer import SynthesizerDataset
    from ..simulate.sim_workload import sim_workload_in_single_thread
    import logging
    from ..setup_logger import setup_logger
    import asyncio
    import pickle

    setup_logger(level=logging.INFO)

    from rich import print as rprint

    conf = {
        "api_key": "sk-xx",
        "model": "gpt-3.5-turbo",
    }
    arena = ArenaDataset()
    arena_normal = arena.to_workload()[:100]
    arena_separate = arena.to_workload(separate_req_in_one_visit_with_interval=10)[:100]
    oasst = Oasst1Dataset()
    oasst_normal = oasst.to_workload()[:100]
    oasst_separate = oasst.to_workload(separate_ret_in_one_visit=True)[:100]
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
        ("cuntom_f", syn.to_workload(workload_generator=workload_func(max_stage=5))),
    ]
    for n, w in testcases:
        import os

        if os.path.exists(f"tmp/responses_{n}.pkl"):
            continue
        logging.info(f"start {n}")
        pickle.dump(
            asyncio.run(
                sim_workload_in_single_thread(
                    w, None, skip_idle_min=0.5, time_step=0.001, **conf
                )
            ),
            open(f"tmp/responses_{n}.pkl", "wb"),
        )

    responses: List[List[VisitResponse]] = [
        pickle.load(open(f"tmp/responses_{n}.pkl", "rb")) for n, _ in testcases
    ]
    levels = ["visit" if "normal" in n else "request" for n, _ in testcases]
    logging.info("start generate reports")
    reports = [
        generate(responses[i], "meta-llama/Llama-2-7b-chat-hf", levels[i])
        for i in range(len(testcases))
    ]
    reports_show_as_dict = [r.show_as_dict() for r in reports]
    rprint(reports_show_as_dict)
