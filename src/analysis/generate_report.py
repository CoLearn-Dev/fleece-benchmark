from ..simulate.protocol import VisitResponse, ReqResponse
from .report import VisitLevelReport, RequestLevelReport
from typing import List
import numpy as np
import bisect

def __get_tokens(s: str, tokenizer_name: str) -> int:
    if "llama" in tokenizer_name:
        return 1
    else:
        try:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        except Exception as e:
            print("load tokenizer failed, error info:", e)
            raise e
        return len(
            tokenizer(s, return_tensors="np")["input_ids"][0]
        )

def generate_request_level_report(
    ress: List[ReqResponse], tokenizer_name: str, **kwargs
) -> RequestLevelReport:
    success = [res for res in ress if res.error_info is None]
    TTLB = [res.loggings[0][0] - res.start_timestamp for res in success]
    start_on_time = [res.launch_latency == 0.0 for res in success]
    time_per_request = [res.end_timestamp - res.start_timestamp for res in success]
    token_per_request = []
    token_timestamp = []
    for c in ress:
        count = 0
        for pack in c.loggings:
            if not pack[1].content:
                continue
            num = __get_tokens(pack[1].content, tokenizer_name)
            count += num
            token_timestamp.append((pack[0], num))
        if c.error_info is None:
            token_per_request.append(count)
    token_timestamp.sort(key=lambda x: x[0])
    throughput_windows = kwargs.get("throughput_windows", 5)
    throughput_step = kwargs.get("throughput_step", 1)
    count_list = np.zeros(
        int((token_timestamp[-1][0] - token_timestamp[0][0]) / throughput_step) + 1
    )
    for t, c in token_timestamp:
        count_list[int((t - token_timestamp[0][0]) / throughput_step)] += c
    sample_list = np.zeros(len(count_list))
    for i in range(len(sample_list)):
        ty = token_timestamp[0][0] + i * throughput_step
        sample_list[i] = bisect.bisect_right(
            token_timestamp, ty + throughput_windows / 2, key=lambda x: x[0]
        ) - bisect.bisect_left(token_timestamp, ty - throughput_windows / 2, key=lambda x: x[0])
    sample_list = sample_list / throughput_windows
    TPOT: List[float] = []
    for ti, to in zip(time_per_request, token_per_request):
        if to == 0:
            TPOT.append(0)
        else:
            TPOT.append(ti / to)
    return RequestLevelReport(
        request_num=len(ress),
        fail_rate=1 - len(success) / len(ress),
        TTFT=TTLB,
        latency=[res.end_timestamp - res.start_timestamp for res in ress],
        SLO=len(start_on_time) / len(ress),
        time_per_request=time_per_request,
        token_per_request=token_per_request,
        token_timestamp=token_timestamp,
        TPOT=TPOT,
        Throughput=np.max(sample_list),
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
    import pickle
    from rich import print as rprint

    path = "tmp/responses_single_request.pkl"
    data: List[VisitResponse] = pickle.load(open(path, "rb"))
    rprint(
        generate_visit_level_report(
            data, "meta-llama/Llama-2-7b-chat-hf"
        ).show_as_dict()
    )
