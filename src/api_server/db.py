import sqlite3
import os
from .protocols import TestConfig
from uuid import uuid4
from typing import List, Tuple

db_path = "tmp/api_server.db"

if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id text, config text, status text)")
    cursor.execute("CREATE TABLE error (id text, error_info text)")
    conn.commit()

def report_error(id: str, error_info: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO error VALUES (?, ?)", (id, error_info))
    cursor.execute("UPDATE test SET status=? WHERE id=?", ("error", id))
    conn.commit()

def save_config(config: TestConfig) -> str:
    id = str(uuid4())
    config_str = config.model_dump_json()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO test VALUES (?, ?, ?)", (id, config_str, "init"))
    conn.commit()
    return id

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
    if status[0] == "running":
        return f"Test {id} is already running"
    return set_status(id, "pending")

def get_all_pending_tests() -> List[Tuple[str, TestConfig]]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, config FROM test WHERE status=?", ("pending",))
    return [(id, TestConfig.model_validate_json(config_str)) for id, config_str in cursor.fetchall()]

