from datetime import date, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from note_cli import main, storage
from note_cli.main import app

runner = CliRunner()
TODAY = date.today().isoformat()


def invoke(*args: str, input: str | None = None):
    return runner.invoke(app, list(args), input=input)


def test_add_and_ls(note_dir: Path) -> None:
    result = invoke("add", "테스트 #idea")
    assert result.exit_code == 0, result.output
    assert "저장됨" in result.output
    assert "테스트 #idea" in (note_dir / f"{TODAY}.md").read_text(encoding="utf-8")

    result = invoke("ls")
    assert result.exit_code == 0
    assert TODAY in result.output
    assert "테스트 #idea" in result.output


def test_ls_tag_filter_and_empty() -> None:
    invoke("add", "a #x")
    invoke("add", "b #y")
    result = invoke("ls", "--tag", "x")
    assert "a #x" in result.output
    assert "b #y" not in result.output
    assert "메모가 없습니다" in invoke("ls", "--tag", "zzz").output


def test_ls_days_window() -> None:
    storage.add_note("오래된 메모", now=datetime(2000, 1, 1, 9, 0))
    assert "오래된" not in invoke("ls").output


def test_search_highlights() -> None:
    invoke("add", "테스트 메모")
    result = invoke("search", "테스트")
    assert result.exit_code == 0
    assert "1건" in result.output
    assert "테스트 메모" in result.output
    assert "일치하는 메모가 없습니다" in invoke("search", "nope").output


def test_show_today_and_missing() -> None:
    invoke("add", "오늘 메모")
    assert "오늘 메모" in invoke("show").output
    result = invoke("show", "2000-01-01")
    assert result.exit_code == 1
    assert "2000-01-01 메모가 없습니다" in result.output
    assert "Traceback" not in result.output


def test_show_bad_date() -> None:
    result = invoke("show", "어제")
    assert result.exit_code == 1
    assert "날짜 형식" in result.output


def test_rm_with_confirm() -> None:
    invoke("add", "first")
    invoke("add", "second")
    result = invoke("rm", TODAY, "1", input="n\n")
    assert "취소" in result.output
    assert len(storage.read_notes(date.today())) == 2

    result = invoke("rm", TODAY, "1", input="y\n")
    assert result.exit_code == 0
    assert [n.text for n in storage.read_notes(date.today())] == ["second"]


def test_rm_yes_and_missing() -> None:
    invoke("add", "only")
    assert invoke("rm", TODAY, "1", "--yes").exit_code == 0
    assert storage.read_notes(date.today()) == []
    result = invoke("rm", TODAY, "5", "--yes")
    assert result.exit_code == 1
    assert "메모가 없습니다" in result.output


def test_tags() -> None:
    assert "태그가 없습니다" in invoke("tags").output
    invoke("add", "#a #b")
    invoke("add", "#a")
    result = invoke("tags")
    assert "#a" in result.output and "2" in result.output


def test_edit_opens_editor(monkeypatch: pytest.MonkeyPatch, note_dir: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setenv("EDITOR", "myeditor --wait")
    monkeypatch.setattr(main.subprocess, "run", lambda cmd, check: calls.append(cmd))
    result = invoke("edit", "2026-10-16")
    assert result.exit_code == 0
    assert calls == [["myeditor", "--wait", str(note_dir / "2026-10-16.md")]]


def test_edit_missing_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDITOR", "definitely-not-an-editor-xyz")
    result = invoke("edit")
    assert result.exit_code == 1
    assert "에디터를 찾을 수 없습니다" in result.output
