from typing import List, Callable, Tuple
from .protocol import Workload, Visit, SimReq, OpenAIMessage
from uuid import uuid4
from random import sample


class SynthesizerDataset:
    def __init__(self, prompt_source: List[str]):
        self.prompt_source = prompt_source

    linearWorkloadGenerator = lambda t: (1000 * t) if t < 100 else None
    constantWorkloadGenerator = lambda t: 1000 if t < 100 else None
    exprWorkloadGenerator = lambda t: int(2 ** (t / 10) * 1000) if t < 100 else None

    def to_workload(
        self, workload_generator: Callable[[int], int | None], **kwargs
    ) -> Workload:
        cur = 0
        workload: List[Tuple[float, Visit]] = []
        while True:
            next_num = workload_generator(cur)
            if next_num is None:
                break
            new_num = next_num - len(workload)
            for _ in range(new_num):
                workload.append(
                    (
                        cur,
                        [
                            (
                                None,
                                SimReq(
                                    id=str(uuid4()),
                                    dep_id=None,
                                    messages_with_dep=[
                                        OpenAIMessage(
                                            role="user",
                                            content=sample(self.prompt_source, 1)[0],
                                            dep_id=None,
                                        )
                                    ],
                                    stream=True,
                                    model=None,
                                    n=1,
                                    temperature=kwargs.get("temperature", 1),
                                    top_p=kwargs.get("top_p", 1),
                                    max_tokens=kwargs.get("max_tokens", None),
                                ),
                            )
                        ],
                    )
                )
            cur += 1
        return workload
