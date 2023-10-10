from typing import List, Tuple
from datasets import load_dataset
from .Interface import DatasetInterface
from ..InternalTyping import DataId, WorkLoadData, AnalysisData
from copy import deepcopy


class ArenaDataset(DatasetInterface):
    def __init__(self):
        raw_dataset = load_dataset("lmsys/chatbot_arena_conversations")
        self.dataset = {
            DataId(
                dataset_name="chatbot_arena",
                unique_id=raw_dataset["train"][i]["question_id"],
            ): raw_dataset["train"][i]
            for i in range(len(raw_dataset["train"]))
        }

    def convertToWorkloadFormat(
        self, load_real_multi_turn: bool = False
    ) -> List[WorkLoadData]:
        assert (
            load_real_multi_turn == False
        ), "arena dataset does not support load_real_multi_turn"
        workloads: List[WorkLoadData] = []
        for k, v in self.dataset.items():
            workloads.append(
                WorkLoadData(
                    index=k,
                    timestamp=v["tstamp"],
                    workload_body=[
                        c["content"] for c in v["conversation_a"] if c["role"] == "user"
                    ],
                )
            )
            assert len(workloads[-1].workload_body) == v["turn"]
        workloads.sort(key=lambda x: x.timestamp)
        return workloads

    def convertToAnalysisFormat(self) -> List[AnalysisData]:
        analysis: List[AnalysisData] = []
        for k, v in self.dataset.items():
            std_is_bad = False
            if v["winner"] == "tie":
                best_conv = v["conversation_a"]
            elif v["winner"] == "tie (bothbad)":
                best_conv = v["conversation_a"]
                std_is_bad = True
            else:
                best_conv = v["conversation_" + v["winner"][-1]]
            analysis.append(
                AnalysisData(
                    index=k,
                    history_ids=[k],
                    std_dialog=best_conv,
                    language=v["language"],
                    std_is_bad=std_is_bad,
                )
            )
        return analysis

    def getPrompts(self) -> List[str]:
        prompts = []
        for v in self.dataset.values():
            for c in v["conversation_a"]:
                if c["role"] == "user":
                    prompts.append(c["content"])
        return list(set(prompts))


if __name__ == "__main__":
    # used for testing
    ds = ArenaDataset()
    wl = ds.convertToWorkloadFormat()
    last = float("-inf")
    for w in wl:
        assert w.timestamp >= last
        last = w.timestamp
    ana = ds.convertToAnalysisFormat()
