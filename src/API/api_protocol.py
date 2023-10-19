from attrs import define


@define(kw_only=True)
class ResPiece:
    index: int
    role: str | None = None
    content: str | None = None
    stop: str | None = None
