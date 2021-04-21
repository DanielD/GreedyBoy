from typing import Any, Dict

from github.GithubObject import CompletableGithubObject

class GitBlob(CompletableGithubObject):
    def __repr__(self) -> str: ...
    def _initAttributes(self) -> None: ...
    def _useAttributes(self, attributes: Dict[str, Any]) -> None: ...
    @property
    def content(self) -> str: ...
    @property
    def encoding(self) -> str: ...
    @property
    def sha(self) -> str: ...
    @property
    def size(self) -> int: ...
    @property
    def url(self) -> str: ...
