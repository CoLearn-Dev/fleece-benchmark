import requests
import time

if __name__ == "__main__":
    conf = {
        "url": "http://xxx:8000/v1",
        "key": "EMPTY",
        "model": "llama-2-7b-chat",
        "dataset_name": "synthesizer",
        "dataset_config": {
            "func": "lambda t: int(t / 5 + 1) if t < 900 else None"
        },
        "kwargs": {
            "skip_idle_min": 20,
            "time_step": 0.001,
            "request_timeout": 3600,
        },
    }
    id = requests.post("http://localhost:8000/register_test", json=conf).text
    print(id)
    print(requests.get(f"http://localhost:8000/start_test/{id}").text)
    while True:
        status = requests.get(f"http://localhost:8000/test_status/{id}").text
        print(status)
        if status == "finish":
            break
        time.sleep(1)
    print(requests.get(f"http://localhost:8000/report/json/{id}").text)
    print(f"{id} finished.")
    
