from ..Datasets.workload import Visit, VisitCtx
from .response import Response
from typing import List, Dict, Any, Tuple
from ..API.openai import streaming_inference
from ..API.api_protocol import ResPiece
import time
import asyncio
import logging


async def sim_visit(visit: Visit, **kwargs) -> List[Response]:
    """
    Simulate a visit and return the responses.
    """
    ctx: VisitCtx = dict()
    responses: List[Response] = []
    last_finish = None
    HUMAN_INPUT_WPS = kwargs.pop("human_input_wps", 1.0)  # FIXME: set as a arg?
    for scheduled_offest, sim_req in visit:
        dialog = sim_req.messages(ctx)
        res_loggings: List[Tuple[float, ResPiece]] = []
        ret_str = None
        inference_conf = sim_req.shadow_params(**kwargs)
        assert (
            inference_conf["model"] is not None
        ), "<sim_visit>: model must be specified"
        if last_finish is not None:
            if scheduled_offest is not None:
                if last_finish + scheduled_offest - time.time() < 0:
                    logging.warning(f"Request {sim_req.id} cannot be executed in time.")
                else:
                    await asyncio.sleep(last_finish + scheduled_offest - time.time())
            else:
                await asyncio.sleep(
                    len(dialog[-1]["content"].split()) / HUMAN_INPUT_WPS
                )
        start_time = time.time()
        logging.debug(f"<{sim_req.id}>: start inference.")
        if sim_req.stream:
            async for res_piece in streaming_inference(dialog, **inference_conf):
                if isinstance(res_piece, Exception):
                    raise res_piece
                res_loggings.append((time.time(), res_piece))
            ret_str = "".join(
                [
                    p[1].content
                    for p in res_loggings
                    if p[1].content is not None and p[1].index == 0
                ]
            )
        else:
            raise NotImplementedError
        logging.debug(f"<{sim_req.id}>: finish inference.")
        last_finish = time.time()
        ctx[sim_req.id] = ret_str
        responses.append(
            Response(
                req_id=sim_req.id,
                start_timestamp=start_time,
                dialog=dialog + [{"role": "assitant", "content": ret_str}],
                loggings=res_loggings,
            )
        )
    return responses


if __name__ == "__main__":
    from ..Datasets.workload import Visit, VisitCtx
    from ..Datasets.arena import ArenaDataset

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    conf = {
        "api_base": "http://3.14.115.113:8000/v1",
        "api_key": "EMPTY",
        "model": "vicuna-7b-v1.3",
    }
    dataset = ArenaDataset()
    workloads = dataset.to_workload()
    for w in workloads:
        if len(w[1]) > 1:
            sample_visit = w[1]
            break
    responses = asyncio.run(sim_visit(sample_visit, **conf))
    from rich import print as rprint

    # rprint(sample_visit)
    # rprint(responses)
    for v, r in zip(sample_visit, responses):
        rprint([v, r])
