from attrs import define, asdict
import requests
import time
import json
import time
import numpy as np
from .keys import *


# Config fields:
test_api_server_url = "https://llm-benchmark-api.colearn.cloud:8000"

test_config = {
    "dataset_name": "synthesizer",
    "random_seed": 1234,
    "dataset_config": {
        "func": "lambda t: int(t / 0.1 + 1) if t < 120 else None",
        "prompt_source": "arena",
    },
    # "workload_range": [None, None],
    "kwargs": {
        "temperature": 0.7,
        "top_p": 1,
        "max_tokens": 1024,
        "skip_idle_min": 20,
        "time_step": 0.001,
        "request_timeout": 3600,
    },
}


@define
class EndpointConfig:
    url: str
    model: str
    endpoint_type: str
    key: str


openai_3_5 = EndpointConfig(
    url="https://api.openai.com/v1",
    model="gpt-3.5-turbo",
    endpoint_type="openai",
    key=openai_key,
)
openai_4 = EndpointConfig(
    url="https://api.openai.com/v1",
    model="gpt-4",
    endpoint_type="openai",
    key=openai_key,
)
anyscale = EndpointConfig(
    url="https://api.endpoints.anyscale.com/v1",
    model="meta-llama/Llama-2-70b-chat-hf",
    endpoint_type="openai",
    key=anyscale_key,
)
togetherai = EndpointConfig(
    url="https://api.togetherai.co/v1",
    model="togethercomputer/llama-2-70b-chat",
    endpoint_type="togetherai",
    key=togetherai_key,
)
aws = EndpointConfig(
    url="",
    model="meta.llama2-70b-chat-v1",
    endpoint_type="aws",
    key=aws_key,
)
endpoints = {
    "openai(gpt-3.5-turbo)": openai_3_5,
    "openai(gpt-4)": openai_4,
    "anyscale": anyscale,
    "togetherai": togetherai,
    "aws(bedrock)": aws,
}

# Test start
cur_time = time.strftime("%Y-%m-%d-%H-%M-%S")
print(f"current time: {cur_time}")
endpoint_configs = {k: {**asdict(v), **test_config} for k, v in endpoints.items()}
results = {}
hashs = []
for name, conf in endpoint_configs.items():
    res = requests.post(f"{test_api_server_url}/register_and_start_test", json=conf)
    assert res.status_code == 200
    id = res.text[1:-1]
    print(f"current test {name}, id: {id}")
    while True:
        status = requests.get(f"{test_api_server_url}/test_status/{id}").text[1:-1]
        print(f"\rcurrent status: {status}" + " " * 20, end="")
        if status == "finish":
            break
        elif status == "error":
            raise Exception(f"Test {id} failed")
        time.sleep(1)
    print(f"\rTest {id} finished" + " " * 20)
    workload_hash = requests.get(f"{test_api_server_url}/get/workload_hash/{id}").text[
        1:-1
    ]
    report_json = requests.get(f"{test_api_server_url}/report/json/{id}").json()
    results[name] = {
        "id": id,
        "workload_hash": workload_hash,
        "report": report_json,
    }
    hashs.append(workload_hash)

import os

os.system(f"mkdir tmp/leaderboard_{cur_time}")
with open(f"tmp/leaderboard_{cur_time}/result.json", "w") as f:
    json.dump(results, f)
assert len(set(hashs)) == 1, str(hashs)

# Load_data
# cur_time = "2024-02-09-08-49-37"
# results = json.load(open(f"tmp/leaderboard_{cur_time}/result.json", "r"))

import rich
from rich.table import Table

table = Table()
table.add_column("Endpoint")
table.add_column("Test ID")
table.add_column("report")
for name, res in results.items():
    table.add_row(name, res["id"], str(res["report"]))
rich.print(table)


import seaborn as sns
import matplotlib.pyplot as plt
from pandas import DataFrame


def get_metric(id):
    from ..analysis.report import RequestLevelReport
    import pickle

    report: RequestLevelReport = pickle.load(open(f"tmp/raw_report_{id}.pkl", "rb"))
    return report.TTFT, report.latency, report.TPOT, report.total_tps_list


ids = [res["id"] for res in results.values()]
names = list(results.keys())
metrics = [get_metric(id) for id in ids]
ori_data = []
for i in range(len(names)):
    ori_data.extend(
        [
            (metrics[i][0][j], metrics[i][1][j], metrics[i][2][j], names[i])
            for j in range(len(metrics[i][0]))
        ]
    )
assert len(metrics[0][0]) == len(
    metrics[0][1]
), f"{len(metrics[0][0])} != {len(metrics[0][1])}"
assert len(metrics[0][0]) == len(
    metrics[0][2]
), f"{len(metrics[0][0])} != {len(metrics[0][2])}"
df = DataFrame(ori_data, columns=["TTFT", "latency", "TPOT", "name"])
tps_data = []
for i in range(len(names)):
    tps_data.extend([(metrics[i][3][j], names[i]) for j in range(len(metrics[i][3]))])
tps_df = DataFrame(tps_data, columns=["total TPS", "name"])


def draw(col_name, source):
    sns.boxplot(
        source,
        x=col_name,
        y="name",
        hue="name",
        whis=[5, 95],
        width=0.6,
        palette="vlag",
        showfliers=False,
    )
    plt.savefig(f"leaderboard_data/{col_name}.png", bbox_inches = 'tight')
    plt.cla()


draw("TTFT", df)
draw("TPOT", df)


def get_table(name_list, data_list):
    cols = ["| Name | Mean | Min | Max | Median | p25 | p75 | p5 | p95 |"]
    cols.append("|:----:|:----:|:---:|:---:|:------:|:---:|:---:|:--:|:---:|")
    mediam_list = []
    values = []
    for i in range(len(data_list)):
        d = data_list[i]
        mean = np.mean(d)
        min = np.min(d)
        max = np.max(d)
        median = np.median(d)
        p25 = np.percentile(d, 25)
        p75 = np.percentile(d, 75)
        p5 = np.percentile(d, 5)
        p95 = np.percentile(d, 95)
        mediam_list.append(median)
        values.append([mean, min, max, median, p25, p75, p5, p95])
    best_index = np.argmin(mediam_list)
    for i in range(len(values)):
        if i == best_index:
            col_str = f'| **{name_list[i]}** | **{values[i][0]:.3f}** | **{values[i][1]:.3f}** | **{values[i][2]:.3f}** | **{values[i][3]:.3f}** | **{values[i][4]:.3f}** | **{values[i][5]:.3f}** | **{values[i][6]:.3f}** | **{values[i][7]:.3f}** |'
        else:
            col_str = f'| {name_list[i]} | {values[i][0]:.3f} | {values[i][1]:.3f} | {values[i][2]:.3f} | {values[i][3]:.3f} | {values[i][4]:.3f} | {values[i][5]:.3f} | {values[i][6]:.3f} | {values[i][7]:.3f} |'
        cols.append(col_str)
    return "\n".join(cols)


def get_max_table(name_list, data_list):
    cols = ["| Name | Peak TPS |"]
    cols.append("|:----:|:---:|")
    value_list = [np.max(d) for d in data_list]
    max_index = np.argmax(value_list)
    for i in range(len(value_list)):
        if i == max_index:
            cols.append(f"| **{name_list[i]}** | **{value_list[i]:.1f}** |")
        else:
            cols.append(f"| {name_list[i]} | {value_list[i]:.1f} |")
    return "\n".join(cols)


TTFT_table = get_table(names, [metrics[i][0] for i in range(len(names))])
TPOT_table = get_table(names, [metrics[i][2] for i in range(len(names))])
total_TPS_table = get_max_table(names, [metrics[i][3] for i in range(len(names))])
with open(f"leaderboard_data/TTFT_table.md", "w") as f:
    f.write(TTFT_table)
with open(f"leaderboard_data/TPOT_table.md", "w") as f:
    f.write(TPOT_table)
with open(f"leaderboard_data/total_TPS_table.md", "w") as f:
    f.write(total_TPS_table)

# Save results
import os

os.system(f"mkdir leaderboard_data/old_data/{cur_time}")
os.system(
    f"ls leaderboard_data/ | grep -v old_data | xargs -i cp -r leaderboard_data/{{}} leaderboard_data/old_data/{cur_time}/"
)

# render md
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("src/leaderboard"))
template = env.get_template("leaderboard_template.md")
data = {
    "last_update": cur_time,
    "run_config": json.dumps(test_config, indent=4),
    "TTFT_table": TTFT_table,
    "TPOT_table": TPOT_table,
    "Total_TPS_table": total_TPS_table,
}
rendered_md = template.render(data)
os.system('rm "LLM Endpoint Performance Leaderboard.md"')
with open("LLM Endpoint Performance Leaderboard.md", "w") as f:
    f.write(rendered_md)
