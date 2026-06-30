from abc import ABC, abstractmethod


class Action(ABC):
    name: str
    tool: dict
    system: str

    @abstractmethod
    def build_messages(self):
        ...

    @abstractmethod
    def parse(self, tool_input):
        ...
