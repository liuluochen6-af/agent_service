import os

class StructPath:

    def __init__(self, base_path: str):
        self.base_path = base_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    def _full(self, path: str) -> str:
        return os.path.join(self.base_path, path)

    def read_path(self, path: str) -> str:
        return self._full(path)

    def write_path(self, path: str) -> str:
        return self._full(path)