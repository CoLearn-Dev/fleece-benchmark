import openai
from typing import Callable, List, Dict
from .api_protocol import ResPiece
import logging

logger = logging.getLogger("openai")
logger.setLevel(logging.WARNING)


def get_streaming_inference(
    endpoint_type: str,
) -> Callable:
    if endpoint_type == "openai":
        from .openai import streaming_inference

        return streaming_inference
    elif endpoint_type == "togetherai":
        from .togetherai import streaming_inference

        return streaming_inference
    elif endpoint_type == "aws":
        from .aws import streaming_inference

        return streaming_inference
    else:
        raise NotImplementedError


def get_inference(
    endpoint_type: str,
) -> Callable:
    if endpoint_type == "openai":
        from .openai import inference

        return inference
    elif endpoint_type == "togetherai":
        from .togetherai import inference

        return inference
    elif endpoint_type == "aws":
        from .aws import inference

        return inference
    else:
        raise NotImplementedError


if __name__ == "__main__":
    import asyncio
    from rich.live import Live
    from rich.table import Table
    from rich import box

    conf = {
        "api_key": "1d951da071cf06b3ce58ead7ae10f2cca564e10478223a47c7a64e4ed9039a8f",
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
        streaming = get_streaming_inference("togetherai")(
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
