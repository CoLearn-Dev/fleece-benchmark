from .Interface import DatasetInterface
from ..InternalTyping import WorkLoadData, AnalysisData, DataId, Hyperparameter
from typing import List, Callable, Dict
import random
from uuid import uuid4

MAX_WORKLOAD_SIM_LENGTH = 1000000

class Synthesizer(DatasetInterface):
    def convertToWorkloadFormat(self, prompt_source: List[str]) -> List[WorkLoadData]:
        self.prompt_source = prompt_source

    linearWorkloadGenerator = lambda t: (1000 * t) if t < 100 else None
    constantWorkloadGenerator = lambda t: 1000 if t < 100 else None
    exprWorkloadGenerator = lambda t: int(2 ** (t / 10) * 1000) if t < 100 else None

    def convertToWorkloadFormat(
        self,
        workload_generator: Callable[[int], int | None],
        load_real_multi_turn: bool = True,
        turn_distribution_generator: Callable[[], int] | None = None,
        hyperparameter_generator: Callable[[], Hyperparameter] | None = None,
    ) -> List[WorkLoadData]:
        if turn_distribution_generator != None:
            raise NotImplementedError(
                "turn_distribution_generator will be supported in the future"
            )       # TODO: support turn_distribution_generator
        turn_distribution_map = lambda: 1
        workloads: List[WorkLoadData] = []
        cur_time = 0
        while True:
            assert cur_time < MAX_WORKLOAD_SIM_LENGTH, "workload simulation is too long"
            workload_size = workload_generator(cur_time)
            if workload_size == None:
                break
            for _ in range(workload_size):
                turns = turn_distribution_map()
                assert turns == 1, "multi-turn workload generate is not supported yet"
                content = random.sample(self.prompt_source, 1)[0]
                body = {"role":"user","content":content} if load_real_multi_turn else content
                hyper = hyperparameter_generator() if hyperparameter_generator != None else None
                workloads.append(
                    WorkLoadData(
                        index=DataId(
                            dataset_name="synthesizer",
                            unique_id=str(uuid4()),
                        ),
                        timestamp=cur_time,
                        workload_body=[body],
                        hyperparameter=hyper,
                    )
                )
            cur_time += 1
        return workloads


    def convertToAnalysisFormat(self) -> List[AnalysisData]:
        raise Exception("Synthesizer is simply used for pressure test")
