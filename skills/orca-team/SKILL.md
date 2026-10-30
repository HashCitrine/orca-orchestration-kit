---
name: orca-team
description: Coordinate Claude, Codex and agy through Orca when the user requests team work or orchestration. For ordinary work, recommend orchestration when useful without launching it automatically.
---

# Orca 개인 공통 팀

사용자가 명시 요청했을 때만 작업자를 시작한다. 일반 요청은 병렬 구현 또는 독립 검토의 이점이 명확하면 추천만 한다. 시작한 에이전트가 조정자이며 추가 작업자는 기본 최대 2명이며 로컬 max_workers가 1이면 1명으로 제한한다. 보고는 한국어로 한다.

## 시작
- 이 스킬의 scripts/kit.py doctor를 현재 Python으로 실행한다. 설정은 ~/.config/orca-orchestration-kit/config.json이다. 현재 요청 > 로컬 설정 > 이 정책 > 도구 기본값 순으로 적용한다.
- ORCA_CLI_COMMAND, ORCA_DEV_REPO_ROOT, OS에 따라 실행 파일을 선택한다. Linux 비관리 터미널에서는 orca-ide를 사용한다. 실행 실패 시 다른 런타임으로 전환하지 않는다.
- 선택한 CLI의 `skills get orchestration`과 `skills get orca-cli`를 읽는다. 필요한 placement/recovery/coordinator 참고 자료는 해당 가이드에서 로드한다. 설치 시점의 문서를 실행 계약으로 고정하지 않는다.
- Orca 연결과 에이전트의 실제 실행 가능 여부를 확인한다. CLI 존재만으로 로그인 성공이나 모델 사용 가능을 주장하지 않는다.
- Claude 작업자 전에 doctor의 claude_worker를 본다. needs_claude_setup이면 띄우지 않고 사용자에게 `kit.py claude-setup` 실행을 안내한다. bypass 확인 화면을 터미널 입력으로 대신 수락하지 않는다. unknown이면 작은 작업으로 readiness를 먼저 확인한다.
- Claude가 조정자일 때 orca 명령에 권한 확인이 뜰 수 있다. 사용자 세션 설정의 문제이므로 조정자가 권한 설정을 임의로 바꾸지 않는다.

## 배분과 모델
- 작은 작업은 직접 수행한다. 역할은 작업 특성·가용 기능·검증 근거에 따라 정하고 모델별 성능 서열을 가정하지 않는다.
- CLI 이름 agy의 Orca 에이전트 ID는 antigravity다. claude/codex는 같은 ID다.
- 모델·effort는 기본 생략한다. 사용자 또는 로컬 설정의 명시 재정의만 전달한다. effort는 검증된 모델 지원과 Orca 계약이 있을 때만 쓴다.
- 모델 목록 기능은 현재 CLI help와 공식 문서로 확인한다. 지원하지 않으면 기본값을 사용하며 이름을 추측하지 않는다. 지정 모델이 사라지면 대안을 제시하고 선택을 받는다.
- 도구·설정 변경 후 doctor를 다시 실행한다. 인터페이스가 바뀌면 작은 작업으로 검증한다. 실행 오류 후에는 기존 Dispatch 상태부터 확인하고 새 작업자를 중복 실행하지 않는다.
- 실제 모델은 launch.requested가 아닌 launch.effective 또는 공급자 응답으로 확인한다. 알 수 없으면 '기본값 사용·실제 모델 미확인'으로 기록한다.

## 작업 수명
- Task마다 대상, 산출물, 제약, 수정 소유권, 검증 기준을 포함한다. references/task-template.md를 사용한다.
- `--worktree current`는 조정자 터미널이 속한 Orca 작업 공간이며 셸 cwd와 다를 수 있다. 시작 receipt의 worktree effect로 실제 위치를 확인하고 Task에 절대 경로를 적는다.
- 동시에 쓰는 작업은 별도 Orca 작업 공간으로 격리한다. Git이 없는 폴더에서는 쓰기 작업을 직렬화한다. 현재 미커밋 변경이 다른 작업 공간에 자동 전달된다고 가정하지 않는다.
- Run/Task/Dispatch, ask/reply, worker_done을 현재 가이드대로 사용한다. worker는 주입된 preamble의 정확한 ID/명령을 따른다. 하위 작업자 추가 생성은 하지 않아 전체 2명 한도를 유지한다.
- 완료 주장과 실제 변경·테스트를 대조한다. 무응답은 실패가 아니다. 불확실하면 관찰하고, 확정된 종료/settlement에만 재시도·회수를 수행한다.
- 완료마다 재사용/명시 보존/회수 중 하나를 결정하고 메시지를 처리한 뒤 ack한다. 조정자는 사용자에게 작업별 결과·근거·미해결 사항을 보고한다.

## Jev
필요할 때 references/jev.md를 읽는다. 판단은 보조 근거이며 권한이나 완료 여부를 단독 결정하지 않는다.
