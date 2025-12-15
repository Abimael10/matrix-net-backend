from __future__ import annotations

import abc
import logging

from src.libs import b2

logger = logging.getLogger(__name__)


class AbstractFileStorage(abc.ABC):
    @abc.abstractmethod
    def upload(self, local_path: str, file_name: str) -> str:
        raise NotImplementedError


class B2FileStorage(AbstractFileStorage):
    def upload(self, local_path: str, file_name: str) -> str:
        return b2.b2_upload_file(local_file=local_path, file_name=file_name)


class FakeFileStorage(AbstractFileStorage):
    def __init__(self):
        self.uploads = []

    def upload(self, local_path: str, file_name: str) -> str:
        url = f"https://fake.local/{file_name}"
        self.uploads.append((local_path, file_name, url))
        return url
