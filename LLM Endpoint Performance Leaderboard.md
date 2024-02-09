# LLM Endpoint Performance Leaderboard

> Last update: 2024-02-09-08-49-37

## Key metrics

### Time To First Token (TTFT)

This metric represents the time for LLM to return the first token. This metric can influence the performance of some LLM applications with lots of user interactions, for example, chatbots.

> TTFT = time of the first token - time of the request sent out

### Time Per Output Token(TPOT)

This metric represents the speed of the endpoint to inference. For chatting applications, this metric will influence the user experience if this speed is slower than people's reading speed. For LLM-based applications, like knowledge databases or copilot, this metric will influence the end-to-end latency of their application. For example, if we choose the endpoint with a lower TPOT, the knowledge database may react to users' questions faster.

> TPOT = request_time_usage / output_token_num

### Total TPS

This metric represents the capacity of the endpoint to parallel requests. For chatting applications, the endpoint with a higher total TPS will allow the application to chat with more people at the same time. For LLM-based applications, this metric may be helpful to lower the end-to-end latency if some LLM-based operations can be processed parallel.

> Total TPS = sum(tps_per_requests)

## Config the workload used in the benchmarking

You can change the config in the `auto-testing.py` to modify the workload and some args.

```python
{
    "dataset_name": "synthesizer",
    "random_seed": 1234,
    "dataset_config": {
        "func": "lambda t: int(t / 0.1 + 1) if t < 120 else None",
        "prompt_source": "arena"
    },
    "kwargs": {
        "temperature": 0.7,
        "top_p": 1,
        "max_tokens": 1024,
        "skip_idle_min": 20,
        "time_step": 0.001,
        "request_timeout": 3600
    }
}
```

In our testing config, we send 10 requests to the endpoints for one second and we will keep sending requests for 2 minutes.

To learn more about our workload design, please refer to our blog post [here](https://medium.com/p/ba3cca28f246).

## Time To First Token (seconds)

The time for the LLM application to get the first response from the endpoint.

![TTFT](leaderboard_data/TTFT.png)

| Name | Mean | Min | Max | Median | p25 | p75 | p5 | p95 |
|:----:|:----:|:---:|:---:|:------:|:---:|:---:|:--:|:---:|
| **openai(gpt-3.5-turbo)** | **0.455** | **0.241** | **2.572** | **0.520** | **0.297** | **0.542** | **0.261** | **0.626** |
| openai(gpt-4) | 0.719 | 0.376 | 2.272 | 0.660 | 0.536 | 0.817 | 0.456 | 1.233 |
| anyscale | 1.118 | 0.352 | 2.757 | 1.065 | 0.788 | 1.384 | 0.545 | 1.892 |
| togetherai | 1.835 | 0.332 | 17.922 | 1.484 | 0.834 | 2.316 | 0.493 | 4.087 |
| aws(bedrock) | 2.873 | 0.654 | 20.465 | 1.916 | 1.224 | 3.249 | 1.080 | 9.104 |

## Time Per Output Token (ms)

The average time for the endpoint to output one token in a requests

![TPOT](leaderboard_data/TPOT.png)

| Name | Mean | Min | Max | Median | p25 | p75 | p5 | p95 |
|:----:|:----:|:---:|:---:|:------:|:---:|:---:|:--:|:---:|
| **openai(gpt-3.5-turbo)** | **0.026** | **0.012** | **0.550** | **0.016** | **0.014** | **0.023** | **0.014** | **0.060** |
| openai(gpt-4) | 0.088 | 0.044 | 1.071 | 0.067 | 0.061 | 0.087 | 0.052 | 0.156 |
| anyscale | 0.070 | 0.034 | 1.041 | 0.046 | 0.041 | 0.060 | 0.037 | 0.178 |
| togetherai | 0.077 | 0.028 | 0.965 | 0.065 | 0.055 | 0.080 | 0.039 | 0.151 |
| aws(bedrock) | 0.076 | 0.000 | 1.298 | 0.056 | 0.053 | 0.064 | 0.050 | 0.140 |

## Total TPS (Tokens per seconds)

The sum of all ongoing requests' TPS. In this part, we measure the peak TPS in the testing.

| Name | Peak TPS |
|:----:|:---:|
| openai(gpt-3.5-turbo) | 2728.8 |
| openai(gpt-4) | 1385.4 |
| anyscale | 854.8 |
| **togetherai** | **4344.4** |
| aws(bedrock) | 2533.6 |

## Feedback

* Please use the issue to report any bugs or suggestions.
* Please contact us if you want to add your endpoint to the leaderboard.
* You can also use our repo to run the testing by yourself.