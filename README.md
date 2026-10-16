# note

터미널에서 쓰는 개인용 빠른 메모 CLI. 서버나 계정 없이 로컬 마크다운 파일에만 저장합니다.

## 설치

```bash
# uv 사용 시
uv venv && uv pip install -e ".[dev]"

# uv 없이
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev]"
```

Python 3.11 이상이 필요합니다.

## 사용법

```bash
note add "회의 자료 준비 #work #급함"   # 메모 추가 (#태그 자동 인식)
note ls                              # 최근 7일 메모, 날짜별 표
note ls --days 30 --tag work         # 최근 30일 중 #work 메모만
note search 회의                     # 전체 검색, 일치 부분 강조
note show                            # 오늘 메모
note show 2026-10-16                 # 특정 날짜 메모
note edit                            # 오늘 파일을 $EDITOR로 열기
note edit 2026-10-16
note rm 2026-10-16 2                 # 해당 날짜 2번 메모 삭제 (확인 프롬프트)
note rm 2026-10-16 2 --yes           # 확인 없이 삭제
note tags                            # 태그별 사용 횟수
note --help                          # 전체 도움말
```

`rm`에 쓰는 번호는 `ls`/`show` 표의 `#` 열입니다.

## 저장 방식

- 위치: `~/.notes/` (환경변수 `NOTE_DIR`로 변경 가능)
- 날짜별 파일 하나: `YYYY-MM-DD.md` (UTF-8)
- 한 줄에 메모 하나:

```markdown
- [09:05] 회의 자료 준비 #work #급함
- [14:30] 아이디어: 메모 CLI 만들기 #idea
```

파일을 직접 열어 수정해도 됩니다. `- [HH:MM] ...` 형식이 아닌 줄(제목, 빈 줄, 자유 메모)은 무시되고, `rm`을 해도 그대로 남습니다.

`edit`은 `$EDITOR`를 사용하고, 설정되어 있지 않으면 Windows에서는 `notepad`, 그 외에서는 `vi`를 엽니다.

## 테스트

```bash
pytest
```

테스트는 `NOTE_DIR`을 임시 폴더로 지정하므로 실제 `~/.notes/`를 건드리지 않습니다.
