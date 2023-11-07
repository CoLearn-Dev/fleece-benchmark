import requests
import time

if __name__ == "__main__":
    conf = {
        "url": "http://172.31.15.40:8000/v1",
        "key": "EMPTY",
        "model": "llama-2-7b-chat",
        "dataset_name": "synthesizer",
        "dataset_config": {
            "func": "lambda t: int(t / 10 + 1) if t < 60 else None",
            "prompt_source": "oasst1",
        },
        "kwargs": {
            "skip_idle_min": 20,
            "time_step": 0.001,
            "request_timeout": 3600,
        },
    }
    id = requests.post("http://localhost:8000/register_test", json=conf).text[1:-1]
    print(id)
    print(requests.get(f"http://localhost:8000/start_test/{id}").text)
    while True:
        status = requests.get(f"http://localhost:8000/test_status/{id}").text[1:-1]
        print("\r" + " " * 40, end="")
        print(f"\rstatus: {status}", end="")
        if status == "finish":
            print()
            break
        elif status == "error":
            exit()
        time.sleep(5)
    res = requests.get(f"http://localhost:8000/report/json/{id}")
    while res.status_code == 404:
        res = requests.get(f"http://localhost:8000/report/json/{id}")
    print(res.json())
    print(f"{id} finished.")
    print(
        f"you can see the report at \nhttp://localhost:8000/report/throughput/{id}\nhttp://localhost:8000/report/requests_status/{id}"
    )
