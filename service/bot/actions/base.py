from abc import ABC, abstractmethod


class Action(ABC):
    name: str
    tool: dict

    @abstractmethod
    def build_prompt(self):
        ...

    @abstractmethod
    def parse(self, tool_input):
        ...

    @abstractmethod
    def fallback(self):
        ...
