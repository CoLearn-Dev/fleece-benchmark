from typing import List, Tuple
from .workload import Workload, Visit, SimReq, OpenAIMessage
from .utils import key_timestamp_to_offset
from datetime import datetime


class Oasst1Dataset:
    def __init__(self):
        from datasets import load_dataset

        raw = load_dataset("OpenAssistant/oasst1")
        merged_raw = list(raw["train"]) + list(raw["validation"])
        self.dicted_data = {
            v["message_id"]: {
                "timestamp": datetime.fromisoformat(v["created_date"]).timestamp(),
                **v,
            }
            for v in merged_raw
        }
        grouped_data = {}
        for v in self.dicted_data.values():
            grouped_data[v["message_tree_id"]] = [
                v,
                *grouped_data.get(v["message_tree_id"], []),
            ]
        self.grouped_data = grouped_data

    def to_workload(self, separate_ret_in_one_visit=False, **kargs) -> Workload:
        def get_prompter_id(cur_id):
            if cur_id == None:
                return None
            cur_req = self.dicted_data[cur_id]
            if cur_req["role"] == "prompter":
                return "oasst1-" + cur_id
            else:
                return get_prompter_id(cur_req["parent_id"])

        def parse_simreq(cur_id) -> SimReq:
            def get_messages(cur_id) -> List[OpenAIMessage]:
                if cur_id == None:
                    return []
                cur_req = self.dicted_data[cur_id]
                return get_messages(cur_req["parent_id"]) + [
                    OpenAIMessage(
                        role="user" if cur_req["role"] == "prompter" else "assistant",
                        content=cur_req["text"]
                        if cur_req["role"] == "prompter" or separate_ret_in_one_visit
                        else None,
                        dep_id=None
                        if cur_req["role"] == "prompter" or separate_ret_in_one_visit
                        else get_prompter_id(cur_req["parent_id"]),
                    )
                ]

            cur_req = self.dicted_data[cur_id]
            return SimReq(
                id=f"oasst1-{cur_id}",
                dep_id=get_prompter_id(cur_req["parent_id"])
                if not separate_ret_in_one_visit
                else None,
                messages_with_dep=get_messages(cur_id),
                stream=True,
                model=None,
                n=1,
                temperature=kargs.get("temperature", 1),
                top_p=kargs.get("top_p", 1),
                max_tokens=kargs.get("max_tokens", None),
            )

        if not separate_ret_in_one_visit:

            def get_visit_start_time(group):
                for v in group:
                    if v["parent_id"] == None:
                        return v["timestamp"]

            unordered_workloads = []
            for group in self.grouped_data.values():
                start_time = get_visit_start_time(group)
                unordered_workloads.append(
                    (
                        start_time,
                        sorted(
                            [
                                (
                                    v["timestamp"] - start_time,
                                    parse_simreq(v["message_id"]),
                                )
                                for v in group
                                if v["role"] == "prompter"
                            ],
                            key=lambda v: v[0],
                        ),
                    )
                )
            return key_timestamp_to_offset(unordered_workloads)
        else:
            return key_timestamp_to_offset(
                [
                    (v["timestamp"], [(None, parse_simreq(v["message_id"]))])
                    for v in self.dicted_data.values()
                    if v["role"] == "prompter"
                ]
            )


if __name__ == "__main__":
    from rich import print as rprint
    from .utils import assert_visit_is_legal

    ds = Oasst1Dataset()
    ds_workload = ds.to_workload()
    # rprint(ds.grouped_data['bebaaa50-9c9e-4fee-be15-1ff4d7efea8a'])
    rprint(ds_workload[1])
    for d in ds_workload:
        assert_visit_is_legal(d[1])
    ds_workload_sep = ds.to_workload(separate_ret_in_one_visit=True)
    rprint(ds_workload_sep[0])
    for d in ds_workload_sep:
        if len(d[1][0][1].messages_with_dep) > 1:
            rprint(d)
            break
    for d in ds_workload_sep:
        assert_visit_is_legal(d[1])
