from API.openai import streaming_inference
from time import time
from InternalTyping import StreamingResult
from typing import List, Callable
import numpy as np


def cal_latency(res: List[StreamingResult]) -> float | Exception:
    """
    Calculate latency from streaming data
    """
    for r in res:
        if isinstance(r.ctx, Exception):
            return r
        if r.ctx.content != "" and r.ctx.content != None:
            return r.timestamp - res[0].timestamp


def cal_tps(res: List[StreamingResult], tokenizer_name: str) -> float | Exception:
    """
    Calculate tps from streaming data, currently support use the tokenizer from huggingface
    """
    # check the installation of transformers, if not, print the info to suggest the user to install it
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    except Exception as e:
        print("load tokenizer failed, error info:", e)
        raise e
    token_list = []
    stamp_list = []
    for r in res:
        if isinstance(r.ctx, Exception):
            return r
        if r.ctx.content != "" and r.ctx.content != None:
            token_list.append(
                len(tokenizer(r.ctx.content, return_tensors="np")["input_ids"][0])
            )
            stamp_list.append(r.timestamp)
    if len(token_list) == 0:
        return float("nan")
    total_tokens = np.sum(token_list)
    total_time = np.max(stamp_list) - np.min(stamp_list)
    return total_tokens / total_time


def cal_sli(
    ress: List[List[StreamingResult]],
    eval_func: Callable[[List[StreamingResult]], float | Exception],
    target_value: float,
) -> float:
    """
    Read the raw data from streaming data and calculate the SLI, return the reached percentage
    """
    values = []
    not_serviced = 0
    for res in ress:
        value = eval_func(res)
        if isinstance(value, Exception):
            not_serviced += 1
        else:
            values.append(value)
    return (
        (len([l for l in values if l > target_value]) + not_serviced)
        / len(values)
        * 100
    )


sli_latency = lambda res, target_latency: cal_sli(res, cal_latency, target_latency)
sli_tps = lambda res, target_tps: cal_sli(res, cal_tps, target_tps)
