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
