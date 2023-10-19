from typing import List, Tuple, Any
from .protocol import Offset, Visit


def key_timestamp_to_offset(x: List[Tuple[float, Any]]) -> List[Tuple[Offset, Any]]:
    x.sort(key=lambda v: v[0])
    return [(t - x[0][0], v) for (t, v) in x]


def assert_visit_is_legal(visit: Visit):
    last_t = float("-inf")
    id_pool = [req.id for (_, req) in visit]

    for t, req in visit:
        assert t is None or t > last_t
        last_t = t
        assert req.dep_id is None or req.dep_id in id_pool
        for message in req.messages_with_dep:
            assert message.dep_id is None or message.dep_id in id_pool
            if message.dep_id is not None:
                assert message.dep_id != req.id
            assert message.content is not None or message.dep_id is not None


if __name__ == "__main__":
    from rich import print as rprint

    rprint(key_timestamp_to_offset([(2.5, 0.2), (1.2, 1), (3.10, 3)]))
