from typing import List, Dict
import asyncio
from .InternalTyping import StreamingResult, SimluateConfig, WorkLoadData
from .API.openai import streaming_inference


def collect_streaming_data(dialog: List[Dict[str, str]]) -> List[StreamingResult]:
    """
    Collect streaming data from openai
    """

    async def streaming() -> List[StreamingResult]:
        data: List[StreamingResult] = [StreamingResult()]
        async for ctx in streaming_inference(dialog):
            data.append(StreamingResult(ctx))
        return data

    return asyncio.run(streaming())


def sim(
    workloads: List[WorkLoadData], config: SimluateConfig
) -> List[List[StreamingResult]]:
    raise NotImplementedError
