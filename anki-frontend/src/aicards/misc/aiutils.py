import typing as t
import pydantic


class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


class AiRequest:
    pass
