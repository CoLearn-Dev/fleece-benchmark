import logging
import asyncio
import pickle
import threading
import json
import hashlib
from typing import List
from .db import get_all_pending_tests, set_status, report_error
from .protocols import TestConfig
from ..workload_datasets.arena import ArenaDataset
from ..workload_datasets.oasst1 import Oasst1Dataset
from ..workload_datasets.synthesizer import SynthesizerDataset

dataset_dict = {
    "arena": ArenaDataset,
    "oasst1": Oasst1Dataset,
    "synthesizer": SynthesizerDataset,
}
from ..simulate.sim_workload import sim_workload_in_single_thread
from ..analysis.generate_report import generate_request_level_report
from ..simulate.protocol import ReqResponse
from ..analysis.draw_pic import RequestsStatus, Throughput


def lambda_func_policy_check(f: str):
    import re

    pattern = r"^lambdat:int\(t/\d+(\.\d+)?\+\d+(\.\d+)?\)ift<\d+(\.\d+)?elseNone$"
    if not re.match(pattern, f.replace(" ", "")):
        raise Exception(f"lambda function {f} does not match pattern")


def run_with_config(id: str, config: TestConfig):
    try:
        if config.dataset_name == "synthesizer":
            source = dataset_dict[
                config.dataset_config.pop("prompt_source")
            ]().dialogs()
            dataset = dataset_dict[config.dataset_name](source)
            func = config.dataset_config.pop("func")
            lambda_func_policy_check(func)
            lambda_func = eval(func)
            workload = dataset.to_workload(
                workload_generator=lambda_func,
                random_seed=config.random_seed,
                **config.dataset_config,
            )
        else:
            dataset = dataset_dict[config.dataset_name]()
            workload = dataset.to_workload(**config.dataset_config)
            workload = workload[config.workload_range[0] : config.workload_range[1]]
        run_config = {
            "time_step": 0.01,
            "api_base": config.url,
            "api_key": config.key,
            "model": config.model,
            **config.kwargs,
        }
        hash_func = hashlib.md5()
        hash_func.update(pickle.dumps(workload))
        workload_hash = hash_func.hexdigest()
        logging.info(
            f"start {id}, size {len(workload)}, hash {workload_hash}, endpoint {config.endpoint_type}"
        )
        raw_result = asyncio.run(
            sim_workload_in_single_thread(
                workload, None, config.endpoint_type, id, **run_config
            )
        )
        pickle.dump(
            raw_result,
            open(f"tmp/responses_{id}.pkl", "wb"),
        )
        with open(f"tmp/workload_hash_{id}.txt", "w") as f:
            f.write(workload_hash)
        responses: List[ReqResponse] = sum([v.responses for v in raw_result], [])
        logging.info("start generate reports")
        report = generate_request_level_report(responses, config.get_model_name())
        pickle.dump(
            report,
            open(f"tmp/raw_report_{id}.pkl", "wb"),
        )
        with open(f"tmp/report_{id}.json", "w") as f:
            json.dump(report.show_as_dict(), f)
        RequestsStatus(responses, f"tmp/rs_{id}.png")
        Throughput(report, f"tmp/tp_{id}.png")
        set_status(id, "finish")
        logging.info(f"test {id} finished")
    except Exception as e:
        report_error(id, str(e))
        logging.error(f"Error when running test {id}: {e}")
        return "Error"
    return "OK"


if __name__ == "__main__":
    import time
    from ..setup_logger import setup_logger

    setup_logger(level=logging.INFO)
    logging.info("worker started")
    threads: List[threading.Thread] = []
    while True:
        pending_tests = get_all_pending_tests()
        if len(pending_tests) == 0:
            time.sleep(1)
            continue
        for id, config in pending_tests:
            logging.info(
                f"Found pending test {id}, endpoint: {config.url}, model: {config.model}"
            )
            # launch test in other thread
            set_status(id, "running")
            t = threading.Thread(target=run_with_config, args=(id, config))
            t.start()
            threads.append(t)
