import openai
from collections import namedtuple
from ..secret import api_base, openai_key
from typing import List, Dict

DeltaMessage = namedtuple("DeltaMessage", ["role", "content"])


async def streaming_inference(dialog: List[Dict[str, str]]):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            api_base=api_base,
            api_key=openai_key,
            messages=dialog,
            stream=True,
        )
        for chunk in completion:
            role, content = None, None
            if "role" in chunk.choices[0].delta:
                role = chunk.choices[0].delta["role"]
            if "content" in chunk.choices[0].delta:
                content = chunk.choices[0].delta["content"]
            yield DeltaMessage(role, content)
        yield None
    except Exception as e:
        yield e


if __name__ == "__main__":
    import asyncio

    async def main():
        role = None
        async for message in streaming_inference(
            dialog=[{"role": "user", "content": "hello"}]
        ):
            if message is None:
                break
            assert isinstance(message, DeltaMessage), f"{type(message)} {message}"
            if message.role != role and message.role is not None:
                print(f"\n{message.role}: ", end="", flush=True)
                role = message.role
            if message.content is not None:
                print(message.content, end="", flush=True)
        print("\n[DONE]")

    asyncio.run(main())
