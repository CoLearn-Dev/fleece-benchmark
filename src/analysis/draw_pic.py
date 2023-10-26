from src.simulate.protocol import ReqResponse
from src.analysis.report import RequestLevelReport
from src.analysis.generate_report import generate_request_level_report
from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np


def RequestsStatus(req_ress: List[ReqResponse], path: str):
    plt.clf()
    start_timestamp = req_ress[0].start_timestamp
    end_timestamp = max([v.end_timestamp for v in req_ress])
    interval = 1
    x = np.arange(0, end_timestamp - start_timestamp, interval)
    issued_delta = np.zeros(len(x))
    success_delta = np.zeros(len(x))
    failed_delta = np.zeros(len(x))
    for r in req_ress:
        issued_delta[int((r.start_timestamp - start_timestamp) / interval)] += 1
        if r.error_info is not None:
            failed_delta[int((r.end_timestamp - start_timestamp) / interval)] += 1
        else:
            success_delta[int((r.end_timestamp - start_timestamp) / interval)] += 1

    def sumup(l):
        ret = []
        for i in l:
            if len(ret) == 0:
                ret.append(i)
            else:
                ret.append(ret[-1] + i)
        return np.array(ret)

    issued = sumup(issued_delta)
    success = sumup(success_delta)
    failed = sumup(failed_delta)
    reqs = {
        "failed": failed,
        "success": success,
        "processing": issued - success - failed,
    }
    _, ax = plt.subplots()
    ax.stackplot(
        x,
        reqs.values(),
        labels=reqs.keys(),
        alpha=0.95,
        colors=["#fc4f30", "#6d904f", "#008fd5"],
    )
    ax.legend(loc="upper left", reverse=True)
    ax.set_title("Request status over time")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("number of requests")
    plt.savefig(path)


def TokenPerSecond(report: RequestLevelReport, path: str):
    plt.clf()
    data: List[Tuple[float, int]] = report.token_timestamp
    start = data[0][0]
    end = data[-1][0]
    time_step = 1
    half_window_size = 7
    x = np.arange(0, end - start, time_step)
    y_ori = np.zeros(len(x))
    for t, n in data:
        y_ori[int((t - start) / time_step)] += n
    y = np.zeros(len(x))
    for i in range(len(y)):
        y[i] = sum(
            y_ori[max(0, i - half_window_size) : min(len(y_ori), i + half_window_size)]
        ) / (2 * half_window_size + 1)
    plt.plot(x, y)
    plt.xlabel("time (s)")
    plt.ylabel("number of tokens")
    plt.savefig(path)


if __name__ == "__main__":
    import pickle

    name = "single_request"
    loaded: List[ReqResponse] = sum(
        [v.responses for v in pickle.load(open(f"tmp/responses_{name}.pkl", "rb"))],
        [],
    )
    RequestsStatus(loaded, f"tmp/rs_{name}.png")
    TokenPerSecond(
        generate_request_level_report(loaded, "meta-llama/Llama-2-7b-chat-hf"),
        f"tmp/tps_{name}.png",
    )
