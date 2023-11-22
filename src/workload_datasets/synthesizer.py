from typing import List, Callable, Tuple
from .protocol import Workload, Visit, SimReq, OpenAIMessage
import uuid
import random


class SynthesizerDataset:
    def __init__(self, prompt_source: List[str]):
        self.prompt_source = prompt_source

    linearWorkloadGenerator = lambda t: (1000 * t) if t < 100 else None
    constantWorkloadGenerator = lambda t: 1000 if t < 100 else None
    exprWorkloadGenerator = lambda t: int(2 ** (t / 10) * 1000) if t < 100 else None

    def to_workload(
        self,
        workload_generator: Callable[[int], int | None],
        random_seed: int | None = None,
        **kwargs
    ) -> Workload:
        random.seed(random_seed)
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
                                    id=str(
                                        uuid.UUID(
                                            int=random.getrandbits(128), version=4
                                        )
                                    ),
                                    dep_id=None,
                                    messages_with_dep=[
                                        OpenAIMessage(
                                            role="user",
                                            content=random.sample(
                                                self.prompt_source, 1
                                            )[0],
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
        random.seed()
        return workload
