import requests
import json

from typing import List, Dict
from .api_protocol import ResPiece
import logging

import aiohttp


async def streaming_inference(
    dialog: List[Dict[str, str]],
    **kwargs,
):
    try:
        if "stream" in kwargs:
            kwargs.pop("stream")
        url = "https://api.together.xyz/v1/chat/completions"
        payload = {
            "stop": ["</s>", "[/INST]"],
            "top_k": 50,
            "repetition_penalty": 1,
            "stream": True,
            "messages": dialog,
            **kwargs,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {kwargs['api_key']}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                async for chunk in response.content:
                    if chunk == b"\n":
                        continue
                    s = chunk.decode()[6:]
                    if s == "[DONE]\n":
                        break
                    try:
                        json.loads(s)
                    except:
                        print(s)
                    for choice in json.loads(s)["choices"]:
                        role, content = None, None
                        if "role" in choice["delta"]:
                            role = choice["delta"]["role"]
                        if "content" in choice["delta"]:
                            content = choice["delta"]["content"]
                        yield ResPiece(
                            index=choice["index"],
                            role=role,
                            content=content,
                            stop=choice.get("finish_reason", None),
                        )
    except Exception as e:
        yield e


def inference(
    dialog: List[Dict[str, str]],
    **kwargs,
) -> List[Dict[str, str]]:
    url = "https://api.together.xyz/v1/chat/completions"
    payload = {
        "stop": ["</s>", "[/INST]"],
        "top_k": 50,
        "repetition_penalty": 1,
        "stream": False,
        "messages": dialog,
        **kwargs,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {kwargs['api_key']}",
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.text


if __name__ == "__main__":
    import asyncio
    from rich.live import Live
    from rich.table import Table
    from rich import box

    conf = {
        "api_key": "",
        "model": "togethercomputer/llama-2-70b-chat",
        "max_tokens": 128,
    }

    # print(inference([{"role": "user", "content": "Can you tell me a joke?"}], **conf))
    # exit()
    n = 1 if "n" not in conf else conf["n"]

    def create_table(dlist):
        """Create a table with two columns, populated with data1 and data2."""
        table = Table(box=box.SIMPLE)
        for i in range(n):
            table.add_column(f"Stream {i}")
        table.add_row(*dlist)
        return table

    async def main():
        streaming = streaming_inference(
            dialog=[{"role": "user", "content": "Can you tell me a joke?"}], **conf
        )
        data_columns = [""] * n
        with Live(auto_refresh=True) as live:
            async for ctx in streaming:
                if isinstance(ctx, Exception):
                    raise ctx
                s = ""
                if ctx.role is not None:
                    s += "<" + ctx.role + ">: "
                if ctx.content is not None:
                    s += ctx.content
                if ctx.stop is not None:
                    s += " <" + ctx.stop + ">"
                data_columns[ctx.index] = data_columns[ctx.index] + s
                live.update(create_table(data_columns))

    asyncio.run(main())
