# LLM Endpoint Performance Leaderboard

> Last update: {{last_update}}

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
{{run_config}}
```

In our testing config, we send 10 requests to the endpoints for one second and we will keep sending requests for 2 minutes.

To learn more about our workload design, please refer to our blog post [here](https://medium.com/p/ba3cca28f246).

## Time To First Token (seconds)

The time for the LLM application to get the first response from the endpoint.

![TTFT](leaderboard_data/TTFT.png)

{{TTFT_table}}

## Time Per Output Token (ms)

The average time for the endpoint to output one token in a requests

![TPOT](leaderboard_data/TPOT.png)

{{TPOT_table}}

## Total TPS (Tokens per seconds)

The sum of all ongoing requests' TPS. In this part, we measure the peak TPS in the testing.

{{Total_TPS_table}}

## Feedback

* Please use the issue to report any bugs or suggestions.
* Please contact us if you want to add your endpoint to the leaderboard.
* You can also use our repo to run the testing by yourself.
