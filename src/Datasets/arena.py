from typing import List, Tuple
from .protocol import Workload, Visit, SimReq, OpenAIMessage
from .utils import key_timestamp_to_offset


class ArenaDataset:
    def __init__(self):
        from datasets import load_dataset

        self.raw = load_dataset("lmsys/chatbot_arena_conversations")

    def to_workload(
        self, separate_req_in_one_visit_with_interval=None, **kargs
    ) -> Workload:
        def parse_simreq(d, i) -> SimReq:
            separate_req_in_one_visit = (
                separate_req_in_one_visit_with_interval is not None
            )
            # d["conversation_a"] follows the format
            #   [{"role": "user", "content": ...}, {...}, ...}
            return SimReq(
                id=f'arena-{d["question_id"]}-{i}',
                dep_id=f'arena-{d["question_id"]}-{i-1}'
                if i > 0 and not separate_req_in_one_visit
                else None,
                messages_with_dep=[
                    OpenAIMessage(
                        role=cc["role"],
                        content=cc["content"]
                        if cc["role"] == "user" or separate_req_in_one_visit
                        else None,
                        dep_id=None
                        if cc["role"] == "user" or separate_req_in_one_visit
                        else f'arena-{d["question_id"]}-{i-1}',
                    )
                    for cc in d["conversation_a"][: i * 2 + 1]
                ],
                stream=True,
                model=None,  # FIXME: load model info from arena?
                n=1,
                temperature=kargs.get("temperature", 1),
                top_p=kargs.get("top_p", 1),
                max_tokens=kargs.get("max_tokens", None),
            )

        if separate_req_in_one_visit_with_interval is None:

            def parse_visit(d) -> Visit:
                return [(None, parse_simreq(d, i)) for i in range(d["turn"])]

            return key_timestamp_to_offset(
                [(d["tstamp"], parse_visit(d)) for d in self.raw["train"]]
            )
        else:

            def parse_timestamped_visits(d) -> List[Tuple[float, Visit]]:
                return [
                    (
                        d["tstamp"] + separate_req_in_one_visit_with_interval * i,
                        [(None, parse_simreq(d, i))],
                    )
                    for i in range(d["turn"])
                ]

            return key_timestamp_to_offset(
                sum([parse_timestamped_visits(d) for d in self.raw["train"]], [])
            )

    def dialogs(self) -> List[str]:
        return sum(
            [
                [cc["content"] for cc in d["conversation_a"] if cc["role"] == "user"]
                for d in self.raw["train"]
            ],
            [],
        )


if __name__ == "__main__":
    from rich import print as rprint
    from .utils import assert_visit_is_legal

    ds = ArenaDataset()
    ds_workload = ds.to_workload()
    rprint(ds_workload[0])
    for d in ds_workload:
        if len(d[1]) > 1:
            rprint(d)
            break
    for d in ds_workload:
        assert_visit_is_legal(d[1])
    ds_workload_sep = ds.to_workload(separate_req_in_one_visit_with_interval=60)
    rprint(ds_workload_sep[0])
    for d in ds_workload_sep:
        if len(d[1][0][1].messages_with_dep) > 1:
            rprint(d)
            break
    for d in ds_workload_sep:
        assert_visit_is_legal(d[1])
