from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
import os

from .protocols import TestConfig
from .db import save_config, set_test_to_pending, query_test_status

app = FastAPI()

@app.post("/register_test")
def register(config: TestConfig):
    return save_config(config)
    
@app.get("/start_test/{id}")
def start_test(id: str):
    return set_test_to_pending(id)

@app.get("/test_status/{id}")
def test_status(id: str):
    return query_test_status(id)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
