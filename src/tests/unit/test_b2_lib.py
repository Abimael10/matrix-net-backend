from types import SimpleNamespace

import pytest

from src.libs import b2


class DummyBucket:
    def __init__(self):
        self.uploads = []

    def upload_local_file(self, local_file: str, file_name: str):
        self.uploads.append((local_file, file_name))
        return SimpleNamespace(id_="file-id-123")


class DummyApi:
    def __init__(self, info=None):
        self.info = info
        self.authorized = False
        self.bucket = DummyBucket()

    def authorize_account(self, realm, key_id, application_key):
        self.authorized = True
        self.auth_args = (realm, key_id, application_key)

    def get_bucket_by_name(self, name):
        self.bucket_name = name
        return self.bucket

    def get_download_url_for_fileid(self, fileid):
        return f"https://download/{fileid}"


@pytest.mark.no_db
def test_b2_helpers_use_cached_api(monkeypatch):
    dummy_api = DummyApi()

    # reset caches between tests
    b2.b2_api.cache_clear()
    b2.b2_get_bucket.cache_clear()

    dummy_module = SimpleNamespace(
        InMemoryAccountInfo=lambda: object(),
        B2Api=lambda info: dummy_api,
    )
    monkeypatch.setattr(b2, "b2", dummy_module)

    url = b2.b2_upload_file("/tmp/local.txt", "remote.txt")

    assert dummy_api.authorized is True
    assert dummy_api.bucket.uploads == [("/tmp/local.txt", "remote.txt")]
    assert url == "https://download/file-id-123"

    # Second call should reuse cached API object
    url2 = b2.b2_upload_file("/tmp/another.txt", "second.txt")
    assert dummy_api.bucket.uploads[-1] == ("/tmp/another.txt", "second.txt")
    assert url2.endswith("file-id-123")
