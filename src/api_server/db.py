import sqlite3
import os
from .protocols import TestConfig
from uuid import uuid4
from typing import List, Tuple
import time
import datetime

db_path = "tmp/api_server.db"

if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE test (id text, config text, status text, model text, start_timestamp text, nickname text)"
    )
    cursor.execute("CREATE TABLE error (id text, error_info text)")
    conn.commit()


def report_error(id: str, error_info: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO error VALUES (?, ?)", (id, error_info))
    cursor.execute("UPDATE test SET status=? WHERE id=?", ("error", id))
    conn.commit()


# return a list of (id, nickname, timestamp) from latest to oldest, timestamp is a string in format %Y-%m-%d %H:%M:%S
def get_id_list() -> List[str]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nickname, start_timestamp FROM test ORDER BY start_timestamp DESC"
    )
    return [
        (
            id,
            nickname,
            datetime.datetime.fromtimestamp(int(timestamp)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )
        for id, nickname, timestamp in cursor.fetchall()
    ]


def query_error_info(id: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT error_info FROM error WHERE id=?", (id,))
    error_info = cursor.fetchone()
    if error_info is None:
        return f"{id} has no error"
    return error_info[0]


def query_model(id: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT model FROM test WHERE id=?", (id,))
    model = cursor.fetchone()
    if model is None:
        return ""
    return model[0]


def query_config(id: str) -> TestConfig:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT config FROM test WHERE id=?", (id,))
    config = cursor.fetchone()
    if config is None:
        return None
    return TestConfig.model_validate_json(config[0])


def save_config(config: TestConfig) -> str:
    id = str(uuid4())
    model = config.model
    config_str = config.model_dump_json()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO test VALUES (?, ?, ?, ?, ?, ?)",
        (id, config_str, "init", model, str(int(time.time())), ""),
    )
    conn.commit()
    return id


def delete_test(id: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test WHERE id=?", (id,))
    conn.commit()


def set_nickname(id: str, nickname: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE test SET nickname=? WHERE id=?", (nickname, id))
    conn.commit()


def query_nickname(id: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname FROM test WHERE id=?", (id,))
    nickname = cursor.fetchone()
    if nickname is None:
        return f"Cannot find test {id}"
    return nickname[0]


def query_test_status(id: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM test WHERE id=?", (id,))
    status = cursor.fetchone()
    if status is None:
        return f"Cannot find test {id}"
    return status[0]


def set_status(id: str, st: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE test SET status=? WHERE id=?", (st, id))
    conn.commit()
    return "OK"


def set_test_to_pending(id: str) -> str:
    status = query_test_status(id)
    if status is None:
        return f"Cannot find test {id}"
    if status == "running":
        return f"Test {id} is already running"
    return set_status(id, "pending")


def get_all_pending_tests() -> List[Tuple[str, TestConfig]]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, config FROM test WHERE status=?", ("pending",))
    return [
        (id, TestConfig.model_validate_json(config_str))
        for id, config_str in cursor.fetchall()
    ]
