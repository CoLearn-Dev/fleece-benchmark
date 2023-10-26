from .sim_visit import sim_visit
from ..datasets.protocol import Workload
from .protocol import VisitResponse
import asyncio
from typing import List, Tuple
import logging
import time


async def sim_workload_in_single_thread(
    workload: Workload, sim_start_time: float | None, **kwargs
) -> List[VisitResponse]:
    """
    Simulate a workload and return the responses.
    """
    TIME_TOLERANCE = kwargs.get("time_tolerance", 0.1)
    SKIP_IDLE_MIN: float | None = kwargs.pop("skip_idle_min", None)
    if sim_start_time is None:
        logging.info(
            "sim_start_time is not set for sim_workload_in_single_thread, simulating immediately."
        )
    elif sim_start_time - time.time() < TIME_TOLERANCE:
        logging.warning(
            f"sim_start_time is set to {sim_start_time}, but current time is {time.time()}, simluating run immediately."
        )
    else:
        logging.info(
            f"sim_start_time is set to {sim_start_time}, simulating after {sim_start_time - time.time()} seconds."
        )
        await asyncio.sleep(sim_start_time - time.time())
    logging.info("sim_workload_in_single_thread: start simulating.")

    tasks: List[Tuple[int, asyncio.Task]] = list()
    ress: List[Tuple[int, VisitResponse]] = list()

    TIME_STEP = kwargs.pop("time_step", min(0.1, TIME_TOLERANCE))
    CHECK_SIZE = kwargs.pop("check_size", 10)
    start_timestamp = time.time()
    next_index = 0
    total_visit_num = len(workload)
    skip_offset = 0
    finish_num = 0
    while True:
        # launch new tasks
        cur_offset = time.time() - start_timestamp + skip_offset
        logging.debug(f"current offset {cur_offset}")
        if next_index < total_visit_num:
            assert workload[next_index][0] is not None
            logging.debug(
                f"next visit {next_index} scheduled at {workload[next_index][0]}"
            )
            launch_imm = False
            if cur_offset - workload[next_index][0] > TIME_TOLERANCE:
                logging.warning(
                    f"visit {next_index} cannot be executed in time, late {cur_offset - workload[next_index][0]}."
                )
                launch_imm = True
            if abs(cur_offset - workload[next_index][0]) < TIME_TOLERANCE or launch_imm:
                logging.debug(f"launch visit {next_index}")
                tasks.append(
                    (
                        next_index,
                        asyncio.create_task(
                            sim_visit(workload[next_index][1], **kwargs)
                        ),
                    )
                )
                next_index += 1
                logging_next_time = (
                    workload[next_index][0] if next_index < total_visit_num else None
                )
                logging_after = (
                    (logging_next_time - cur_offset) if logging_next_time else None
                )
                logging.info(
                    f"launch visit {next_index - 1} finished. next visit {next_index} scheduled at {logging_next_time} after {logging_after}"
                )

        # recycle finished tasks & check if system is idle & check if all visits are done
        if len(tasks) > 0:
            to_pop = []
            not_finish = 0
            for i in range(len(tasks[:CHECK_SIZE])):
                if tasks[i][1].done():
                    finish_num += 1
                    logging.info(
                        f"visit <{tasks[i][0]}> done. Total {finish_num} visits done."
                    )
                    ress.append((tasks[i][0], tasks[i][1].result()))
                    to_pop.append(i)
                else:
                    not_finish += 1
            for i in to_pop[::-1]:
                tasks.pop(i)
            logging.debug(
                f"finished {len(to_pop)} tasks, {not_finish} tasks not finished."
            )
        else:
            next_time = (
                workload[next_index][0] if next_index < total_visit_num else None
            )
            if SKIP_IDLE_MIN and next_time:
                skip = max(0, next_time - cur_offset - 10 * TIME_STEP - SKIP_IDLE_MIN)
                if skip > 0:
                    skip_offset += skip
                    logging.info(
                        f"skip idle time {skip}, skip_offset now {skip_offset}"
                    )
            if next_index == total_visit_num:
                break

        if TIME_STEP != 0:
            await asyncio.sleep(TIME_STEP)

    # sort ress
    ress.sort(key=lambda x: x[0])
    return [r[1] for r in ress]


if __name__ == "__main__":
    from ..datasets.arena import ArenaDataset
    from ..datasets.oasst1 import Oasst1Dataset
    from ..setup_logger import setup_logger
    from rich import print as rprint

    setup_logger(level=logging.DEBUG)

    conf = {
        "api_base": "http://3.14.115.113:8000/v1",
        "api_key": "EMPTY",
        "model": "vicuna-7b-v1.3",
    }
    # dataset = ArenaDataset()
    dataset = Oasst1Dataset()
    workloads = dataset.to_workload()[:100]
    # offest = [0]+[w[0] for w in workloads]
    # offests_delta = [offest[i+1]-offest[i] for i in range(len(offest)-1)]
    # rprint(offests_delta)
    responses = asyncio.run(
        sim_workload_in_single_thread(workloads, None, skip_idle_min=0.5, **conf)
    )

    # rprint(sample_visit)
    # rprint(responses)
    result = [(w, r) for w, r in zip(workloads, responses)]
    rprint(result, file=open("tmp_100.log", "w"))
