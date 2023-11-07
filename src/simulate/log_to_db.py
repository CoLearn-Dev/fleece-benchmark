import redis
from typing import List, Dict, Any
import time
import datetime
import concurrent.futures

host = "localhost"
port = 6379
pool = redis.ConnectionPool(host=host, port=port)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=40)


def clear_db():
    r = redis.Redis(connection_pool=pool)
    r.flushdb()


def store_req_to_db(func):
    def wrapper(task_id: str, visit_index: int, request_id: str, *args, **kwargs):
        hash_name = f"{task_id}:{visit_index}:{request_id}"
        executor.submit(func, hash_name, *args, **kwargs)
        # func(hash_name, *args, **kwargs)

    return wrapper


def store_task_to_db(func):
    def wrapper(*args, **kwargs):
        executor.submit(func, *args, **kwargs)

    return wrapper


@store_task_to_db
def init_task(task_id: str, total_req_num: int, start_time: float):
    r = redis.Redis(connection_pool=pool)
    r.hset(
        f"{task_id}:info",
        mapping={
            "total_req_num": total_req_num,
            "start_timestamp": start_time,
            "end_timestamp": -1,
        },
    )


@store_task_to_db
def mark_finish_for_task(task_id: str, end_time: float):
    r = redis.Redis(connection_pool=pool)
    r.hset(f"{task_id}:info", "end_timestamp", end_time)


@store_req_to_db
def init_request(hash_name: str, start_time: float, launch_latency: float):
    r = redis.Redis(connection_pool=pool)
    r.hset(
        f"{hash_name}:info",
        mapping={
            "start_timestamp": start_time,
            "end_timestamp": -1,
            "launch_latency": launch_latency,
            "error_info": "",
        },
    )


@store_req_to_db
def mark_success_for_request(hash_name: str, end_time: float):
    r = redis.Redis(connection_pool=pool)
    r.hset(f"{hash_name}:info", "end_timestamp", end_time)


@store_req_to_db
def mark_error_for_request(hash_name: str, end_time: float, error_info: str):
    r = redis.Redis(connection_pool=pool)
    r.hset(
        f"{hash_name}:info",
        mapping={
            "end_timestamp": end_time,
            "error_info": error_info,
        },
    )


@store_req_to_db
def log_new_pack(hash_name: str, timestamp: float, pack: str):
    r = redis.Redis(connection_pool=pool)
    r.rpush(f"{hash_name}:loggings", f"{timestamp}:{pack}")


def past_packs_of_task(task_id: str, past_time: int = 5) -> List[str]:
    slice_start = time.time() - past_time
    # return pack in loggings whose timestamp is later than slice_start
    r = redis.Redis(connection_pool=pool)
    keys = r.keys(f"{task_id}:*:loggings")
    packs = []
    for key in keys:
        packs.extend(r.lrange(key, 0, -1))
    ret = []
    for pack in packs:
        pack = pack.decode()
        timestamp = float(pack.split(":")[0])
        if timestamp >= slice_start:
            ret.append(pack.split(":")[1])
    return ret


def cur_requests_status_of_task(task_id: str) -> List[Dict[str, Any]]:
    r = redis.Redis(connection_pool=pool)
    keys = r.keys(f"{task_id}:*:info")
    total = len(keys)
    finish = 0
    failed = 0
    for key in keys:
        info = r.hgetall(key)
        if info[b"error_info"] != b"":
            failed += 1
        if info[b"end_timestamp"] != b"-1":
            finish += 1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        {"timestamp": timestamp, "number": total, "status": "total"},
        {"timestamp": timestamp, "number": finish, "status": "finish"},
        {"timestamp": timestamp, "number": failed, "status": "failed"},
    ]


if __name__ == "__main__":
    init_request("test", 0, "id", 1, 2)
