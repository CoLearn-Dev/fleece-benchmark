from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import datetime

from .protocols import TestConfig
from .db import save_config, set_test_to_pending, query_test_status, query_error_info, query_model, query_config, get_id_list
from ..simulate.log_to_db import cur_requests_status_of_task, past_packs_of_task

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register_test")
def register(config: TestConfig):
    return save_config(config)
    
@app.get("/start_test/{id}")
def start_test(id: str):
    return set_test_to_pending(id)

@app.get("/config/{id}")
def get_config(id: str):
    return query_config(id)

@app.post("/register_and_start_test")
def register_and_start(config: TestConfig):
    id = save_config(config)
    set_test_to_pending(id)
    return id

@app.get("/test_model/{id}")
def test_model(id: str):
    return query_model(id)

@app.get("/test_status/{id}")
def test_status(id: str):
    return query_test_status(id)

@app.get("/error_info/{id}")
def error_info(id: str):
    return query_error_info(id)

@app.get("/id_list")
def id_list():
    return get_id_list()

@app.get("/report/throughput/{id}")
def report_throughput(id: str):
    if not os.path.exists("tmp/tp_" + id + ".png"):
        raise HTTPException(status_code=404, detail="Report not found")
    else:
        file_like = open("tmp/tp_" + id + ".png", mode="rb")
        return StreamingResponse(file_like, media_type="image/png")
    
@app.get("/report/requests_status/{id}")
def report_requests_status(id: str):
    if not os.path.exists("tmp/rs_" + id + ".png"):
        raise HTTPException(status_code=404, detail="Report not found")
    else:
        file_like = open("tmp/rs_" + id + ".png", mode="rb")
        return StreamingResponse(file_like, media_type="image/png")
    
@app.get("/report/json/{id}")
def report_json(id: str):
    if not os.path.exists("tmp/report_" + id + ".json"):
        raise HTTPException(status_code=404, detail="Report not found")
    else:
        file_like = open("tmp/report_" + id + ".json", mode="r")
        return StreamingResponse(file_like, media_type="application/json")
    
@app.get("/trace/status/{id}")
def trace_status(id: str):
    return cur_requests_status_of_task(id)

@app.get("/trace/tps/{id}")
def trace_tps(id: str, model: str, sample_len: int = 5):
    packs = past_packs_of_task(id, past_time=sample_len)
    from ..analysis.generate_report import count_tokens_from_str
    try:
        tokens = sum([count_tokens_from_str(p, model) for p in packs])
        return {
            "tps": tokens / sample_len,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logging.warning(f"<trace_tps {id}>: tps failed: {str(e)}")
        return {
            "tps": 0,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
