import openai
from typing import AsyncGenerator, List, Dict
from .api_protocol import ResPiece
import logging

logger = logging.getLogger("openai")
logger.setLevel(logging.WARNING)


async def streaming_inference(
    dialog: List[Dict[str, str]],
    **kwargs,
):
    try:
        if "stream" in kwargs:
            kwargs.pop("stream")
        completion = openai.ChatCompletion.acreate(
            messages=dialog,
            stream=True,
            **kwargs,
        )
        async for chunk in await completion:
            for choice in chunk.choices:
                role, content = None, None
                if "role" in choice.delta:
                    role = choice.delta["role"]
                if "content" in choice.delta:
                    content = choice.delta["content"]
                yield ResPiece(
                    index=choice.index,
                    role=role,
                    content=content,
                    stop=choice.finish_reason,
                )
    except Exception as e:
        yield e


def inference(
    dialog: List[Dict[str, str]],
    **kwargs,
) -> List[Dict[str, str]]:
    completion = openai.ChatCompletion.create(
        messages=dialog,
        **kwargs,
    )
    return [c["message"] for c in completion.choices]


if __name__ == "__main__":
    import asyncio
    from rich.live import Live
    from rich.table import Table
    from rich import box
    from ..secret import api_base, openai_key

    conf = {
        "api_base": "http://3.14.115.113:8000/v1",
        "api_key": "EMPTY",
        "model": "vicuna-7b-v1.3",
        "n": 2,
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
