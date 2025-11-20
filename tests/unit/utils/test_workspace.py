from pathlib import Path
import tempfile

from pykis.utils.workspace import get_workspace_path, get_cache_path


def test_get_workspace_and_cache_paths_resolve(monkeypatch, tmp_path):
    # make a temporary fake home directory
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    # monkeypatch Path.home to return our fake home
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    ws = get_workspace_path()
    assert isinstance(ws, Path)
    expected_ws = (fake_home / ".pykis").resolve()
    assert ws == expected_ws
    # cache path should be a child "cache" under workspace
    cache = get_cache_path()
    assert isinstance(cache, Path)
    assert cache == (expected_ws / "cache").resolve()


def test_get_workspace_path_is_idempotent_and_absolute(monkeypatch, tmp_path):
    fake_home = tmp_path / "another_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    p1 = get_workspace_path()
    p2 = get_workspace_path()
    # both calls return the same resolved absolute Path
    assert p1 == p2
    assert p1.is_absolute()
    # the returned path ends with .pykis
    assert p1.name == ".pykis"
