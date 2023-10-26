from typing import List, Tuple, Any
from .protocol import Offset, Visit, NotNoneOffset


def key_timestamp_to_offset(
    x: List[Tuple[float, Any]]
) -> List[Tuple[NotNoneOffset, Any]]:
    x.sort(key=lambda v: v[0])
    return [(t - x[0][0], v) for (t, v) in x]


def assert_visit_is_legal(visit: Visit):
    last_t = float("-inf")
    id_pool = [req.id for (_, req) in visit]

    for t, req in visit:
        if t is not None:
            assert t > last_t
            last_t = t
        assert req.dep_id is None or req.dep_id in id_pool
        for message in req.messages_with_dep:
            assert message.dep_id is None or message.dep_id in id_pool
            if message.dep_id is not None:
                assert message.dep_id != req.id
            assert message.content is not None or message.dep_id is not None


def cache(enable=True, root_dir="tmp/"):
    """
    Cache the return value of a **method function** in disk using pickle.
    The first argument of the function must be `self`.
    If the file does not exist, call the function and store the return value in the file named `{class_name}_{func_name}_{args}_{kwargs}` in `root_dir`.
    if `enable` is False, the function will not be cached.
    Raise error if the `root_dir` does not exist.
    """
    import pickle
    import os
    import functools

    if not enable:
        return lambda f: f

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not os.path.exists(root_dir) and root_dir != "":
                raise FileNotFoundError(f"Cache root dir {root_dir} does not exist.")
            cache_path = os.path.join(
                root_dir,
                f"{args[0].__class__.__name__}_{f.__name__}_{args[1:]}_{kwargs}",
            )
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as fi:
                    return pickle.load(fi)
            else:
                ret = f(*args, **kwargs)
                with open(cache_path, "wb") as fi:
                    pickle.dump(ret, fi)
                return ret

        return wrapper

    return decorator


if __name__ == "__main__":
    from rich import print as rprint

    rprint(key_timestamp_to_offset([(2.5, 0.2), (1.2, 1), (3.10, 3)]))
