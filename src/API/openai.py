import openai
from typing import List, Dict, Tuple
from ..InternalTyping import StreamingDelta, InferenceConfig, Hyperparameter
import attrs


async def streaming_inference(
    dialog: List[Dict[str, str]],
    config: InferenceConfig,
    hyperparameter: Hyperparameter,
) -> StreamingDelta | Exception:
    try:
        completion = openai.ChatCompletion.create(
            messages=dialog,
            stream=True,
            **attrs.asdict(config),
            **attrs.asdict(hyperparameter),
        )
        for chunk in completion:
            for choice in chunk.choices:
                role, content = None, None
                if "role" in choice.delta:
                    role = choice.delta["role"]
                if "content" in choice.delta:
                    content = choice.delta["content"]
                yield StreamingDelta(
                    index=choice.index,
                    role=role,
                    content=content,
                    stop=choice.finish_reason,
                )
    except Exception as e:
        yield e


if __name__ == "__main__":
    import asyncio
    from rich.live import Live
    from rich.table import Table
    from rich import box
    from ..secret import api_base, openai_key

    conf = InferenceConfig(
        api_base=api_base,
        api_key=openai_key,
        model="gpt-3.5-turbo",
    )
    hyper = Hyperparameter(
        n=2,
        temperature=0,
        top_p=0.3,
        max_tokens=128,
    )

    def create_table(dlist):
        """Create a table with two columns, populated with data1 and data2."""
        table = Table(box=box.SIMPLE)
        for i in range(hyper.n):
            table.add_column(f"Stream {i}")
        table.add_row(*dlist)
        return table

    async def main():
        streaming = streaming_inference(
            dialog=[{"role": "user", "content": "tell me a story?"}],
            config=conf,
            hyperparameter=hyper,
        )
        data_columns = [""] * hyper.n
        with Live(auto_refresh=True) as live:
            async for ctx in streaming:
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
