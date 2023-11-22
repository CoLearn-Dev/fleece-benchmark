import aioboto3
import json
from typing import List, Dict
from .api_protocol import ResPiece
import logging


async def streaming_inference(
    dialog: List[Dict[str, str]],
    **kwargs,
):
    try:
        drop_list = ["api_base", "n", "stream", "request_timeout"]
        for i in drop_list:
            if i in kwargs:
                kwargs.pop(i)
        model = kwargs.pop("model")
        aws_access_key_id, aws_secret_access_key = kwargs.pop("api_key").split("|")
        if "max_tokens" in kwargs:
            max_tokens = kwargs.pop("max_tokens")
            kwargs["max_gen_len"] = max_tokens
        body = json.dumps(
            {
                "prompt": dialog[-1]["content"],  # TODO
                **kwargs,
            }
        )
        region_name = (
            "us-west-2" if "region_name" not in kwargs else kwargs["region_name"]
        )
        async with aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        ).client(
            service_name="bedrock-runtime",
            region_name=region_name,
        ) as client:
            response = await client.invoke_model_with_response_stream(
                body=body, modelId=model
            )
            stream = response.get("body")
            if stream:
                async for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        res = json.loads(chunk.get("bytes").decode())
                        yield ResPiece(
                            index=0,
                            role="assistant",  # TODO
                            content=res["generation"],
                            stop=res["stop_reason"],
                        )
    except Exception as e:
        yield e


def inference(
    dialog: List[Dict[str, str]],
    **kwargs,
) -> List[Dict[str, str]]:
    raise NotImplementedError


if __name__ == "__main__":
    import asyncio
    from rich.live import Live
    from rich.table import Table
    from rich import box

    conf = {
        "api_key": "|",
        "model": "meta.llama2-13b-chat-v1",
        "n": 1,
        "max_tokens": 128,
    }

    def create_table(dlist):
        """Create a table with two columns, populated with data1 and data2."""
        table = Table(box=box.SIMPLE)
        for i in range(conf["n"]):
            table.add_column(f"Stream {i}")
        table.add_row(*dlist)
        return table

    async def main():
        streaming = streaming_inference(
            dialog=[{"role": "user", "content": "Can you tell me a joke?"}], **conf
        )
        data_columns = [""] * conf["n"]
        with Live(auto_refresh=True) as live:
            cur_role = None
            async for ctx in streaming:
                if isinstance(ctx, Exception):
                    raise ctx
                s = ""
                if ctx.role is not None and ctx.role != cur_role:
                    s += "<" + ctx.role + ">: "
                    cur_role = ctx.role
                if ctx.content is not None:
                    s += ctx.content
                if ctx.stop is not None:
                    s += " <" + ctx.stop + ">"
                # print(s.encode())
                data_columns[ctx.index] = data_columns[ctx.index] + s
                live.update(create_table(data_columns))

    asyncio.run(main())
