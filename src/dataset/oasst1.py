from typing import List, Dict
from datasets import load_dataset
from .Interface import DatasetInterface
from ..InternalTyping import DataId, WorkLoadData, AnalysisData
from datetime import datetime


class Oasst1Dataset(DatasetInterface):
    def __init__(self):
        raw_dataset = load_dataset("OpenAssistant/oasst1")
        strandizer_time = lambda v: {
            "timestamp": datetime.fromisoformat(v["created_date"]).timestamp(),
            **v,
        }
        train_set = {
            raw_dataset["train"][i]["message_id"]: strandizer_time(
                raw_dataset["train"][i]
            )
            for i in range(len(raw_dataset["train"]))
        }
        validation_set = {
            raw_dataset["validation"][i]["message_id"]: strandizer_time(
                raw_dataset["validation"][i]
            )
            for i in range(len(raw_dataset["validation"]))
        }
        dialogs = dict()
        for k, v in {**train_set, **validation_set}.items():
            dialogs[v["message_tree_id"]] = {
                k: v,
                **dialogs.get(v["message_tree_id"], dict()),
            }
        self.dialogs = list(dialogs.values())

    def convertToWorkloadFormat(
        self, load_real_multi_turn: bool = True
    ) -> List[WorkLoadData]:
        workloads: List[WorkLoadData] = []
        for dialog in self.dialogs:
            loop_ids = dialog.keys()
            if not load_real_multi_turn:
                total_ids = set(dialog.keys())
                parent_ids = set([v["parent_id"] for v in dialog.values()])
                loop_ids = set(
                    [dialog[k]["parent_id"] for k in list(total_ids - parent_ids)]
                )
            loop_ids = list(loop_ids)
            for k in loop_ids:
                v = dialog[k]
                if v["role"] == "assistant":
                    continue

                def get_body(cur_id: str) -> List:
                    if cur_id == None:
                        return []
                    else:
                        cur = dialog[cur_id]
                        if load_real_multi_turn:
                            return get_body(cur["parent_id"]) + [
                                {
                                    "role": "user"
                                    if cur["role"] == "prompter"
                                    else "assistant",
                                    "content": cur["text"],
                                }
                            ]
                        else:
                            if cur["role"] == "assistant":
                                return get_body(cur["parent_id"])
                            else:
                                return get_body(cur["parent_id"]) + [cur["text"]]

                if load_real_multi_turn:
                    timestamp = v["timestamp"]
                else:

                    def get_ori_time(cur):
                        if cur["parent_id"] == None:
                            return cur["timestamp"]
                        else:
                            return get_ori_time(dialog[cur["parent_id"]])

                    timestamp = get_ori_time(v)

                workloads.append(
                    WorkLoadData(
                        index=DataId(dataset_name="oasst1", unique_id=k),
                        timestamp=timestamp,
                        workload_body=get_body(k),
                    )
                )
        workloads.sort(key=lambda x: x.timestamp)
        return workloads

    def convertToAnalysisFormat(self) -> List[AnalysisData]:
        analysis: List[AnalysisData] = []
        for dialog in self.dialogs:
            for k, v in dialog.items():
                if v["role"] == "prompter":
                    continue

                def get_dialog(cur_id: str) -> List[Dict[str, str]]:
                    if cur_id == None:
                        return []
                    else:
                        cur = dialog[cur_id]
                        return get_dialog(cur["parent_id"]) + [
                            {
                                "role": "user"
                                if cur["role"] == "prompter"
                                else "assistant",
                                "content": cur["text"],
                            }
                        ]

                def get_ids(cur_id: str) -> List[DataId]:
                    if cur_id == None:
                        return []
                    else:
                        return get_ids(dialog[cur_id]["parent_id"]) + [
                            DataId(dataset_name="oasst1", unique_id=cur_id)
                        ]

                analysis.append(
                    AnalysisData(
                        index=DataId(dataset_name="oasst1", unique_id=k),
                        history_ids=get_ids(k),
                        std_dialog=get_dialog(k),
                        language=v["lang"],
                    )
                )
        return analysis

    def getPrompts(self) -> List[str]:
        prompts = []
        for dialog in self.dialogs:
            for v in dialog.values():
                if v["role"] == "prompter":
                    prompts.append(v["text"])
        return list(set(prompts))


if __name__ == "__main__":
    # used for testing
    ds = Oasst1Dataset()
    wl = ds.convertToWorkloadFormat()

    pid = "f977683b-0406-46d5-ba5f-8125b54a5090"
    cid = "f29c1c38-af7b-465b-a21e-f08ef6462fc9"

    def select(l, id):
        for i in l:
            if i.index.unique_id == id:
                return i

    def select_ana(l, id):
        data_id = DataId(dataset_name="oasst1", unique_id=id)
        for i in l:
            if data_id in i.history_ids:
                return i

    from rich import print

    print(select(wl, pid))
    print(select(wl, cid))
    wl_fake = ds.convertToWorkloadFormat(load_real_multi_turn=False)
    print(select(wl_fake, cid))
    last = float("-inf")
    for w in wl:
        assert w.timestamp >= last
        last = w.timestamp
    ana = ds.convertToAnalysisFormat()
    print(select_ana(ana, cid))

    def check_workflow(l):
        assert len(l) == len(set([i.index for i in l]))

    check_workflow(wl)
    check_workflow(wl_fake)
