from typing import List, Dict, Tuple
from attrs import define

Offset = float | None
NotNoneOffset = float
ReqId = str
VisitCtx = Dict[ReqId, str]


@define
class OpenAIMessage:
    role: str
    content: str | None
    dep_id: ReqId | None  # for content replacement with live interactions

    def render(self, ctx: VisitCtx):
        assert self.dep_id is None or self.dep_id in ctx
        return {
            "role": self.role,
            "content": self.content if self.dep_id is None else ctx.get(self.dep_id),
        }
        


@define
class SimReq:
    id: ReqId
    dep_id: ReqId|None  # this req needs to be executed after dep_id is finished
    # content
    messages_with_dep: List[OpenAIMessage]

    def messages(self, ctx: VisitCtx):
        return [m.render(ctx) for m in self.messages_with_dep]

    # config
    stream: bool
    model: str | None
    # param
    temperature: float
    top_p: float
    max_tokens: int
    n: int = 1  # response num

    def shadow_params(self, **kwargs):
        ret = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "n": self.n,
        }
        ret.update(kwargs)
        return ret


Visit = List[Tuple[Offset, SimReq]]
Workload = List[Tuple[NotNoneOffset, Visit]]
