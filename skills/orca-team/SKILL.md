---
name: orca-team
description: Coordinate Claude, Codex and agy through Orca when the user requests team work or orchestration. For ordinary work, recommend orchestration when useful without launching it automatically.
---

# Orca 개인 공통 팀

사용자가 명시 요청했을 때만 작업자를 시작한다. 일반 요청은 병렬 구현 또는 독립 검토의 이점이 명확하면 추천만 한다. 시작한 에이전트가 조정자이며 추가 작업자는 기본 최대 2명이며 로컬 max_workers가 1이면 1명으로 제한한다. 보고는 한국어로 한다.

## 시작
- 처음 설치하거나 route가 blocked이면 scripts/kit.py setup --agent codex|claude|agy를 실행한다. 검증 전 실행 파일 관찰 기록이 저장된다. setup은 작업자를 실행하지 않는다.
- 새 모델 검증은 setup 이후 작은 읽기 전용 Task로 실행한다. 이 bootstrap 작업만 검증 전 프로필의 명시 모델을 사용할 수 있다. 일반 사용자 작업에 이 예외를 적용하지 않는다.
- 성공한 Dispatch에 scripts/kit.py verify-profile --profile <name> --dispatch <id>를 실행한다. 검증 JSON을 직접 작성하지 않는다. 누락 정보나 불일치가 있으면 새로운 검증으로 해결하고 실제 모델을 추측하지 않는다.
- 등록 후에도 완료 메시지 처리·ack·회수는 조정자의 책임이다. setup과 verify-profile은 실행·회수·권한 변경을 하지 않는다.
- 이 스킬의 scripts/kit.py doctor를 현재 Python으로 실행한다. 설정은 ~/.config/orca-orchestration-kit/config.json이다. 현재 요청 > 로컬 설정 > 이 정책 > 도구 기본값 순으로 적용한다.
- ORCA_CLI_COMMAND, ORCA_DEV_REPO_ROOT, OS에 따라 실행 파일을 선택한다. Linux 비관리 터미널에서는 orca-ide를 사용한다. 실행 실패 시 다른 런타임으로 전환하지 않는다.
- 선택한 CLI의 `skills get orchestration`과 `skills get orca-cli`를 읽는다. 필요한 placement/recovery/coordinator 참고 자료는 해당 가이드에서 로드한다. 설치 시점의 문서를 실행 계약으로 고정하지 않는다.
- Orca 연결과 에이전트의 실제 실행 가능 여부를 확인한다. CLI 존재만으로 로그인 성공이나 모델 사용 가능을 주장하지 않는다.
- Claude 작업자 전에 doctor의 claude_worker를 본다. needs_claude_setup이면 띄우지 않고 사용자에게 `kit.py claude-setup` 실행을 안내한다. bypass 확인 화면을 터미널 입력으로 대신 수락하지 않는다. unknown이면 작은 작업으로 readiness를 먼저 확인한다.
- Claude가 조정자일 때 orca 명령에 권한 확인이 뜰 수 있다. 사용자 세션 설정의 문제이므로 조정자가 권한 설정을 임의로 바꾸지 않는다.

## 배분과 모델
- 새 작업자 배정 직전에 scripts/kit.py usage refresh --agent codex를 실행한다. 두 번째 작업자 배정 전에도 갱신한다. route 결과의 usage와 usage_reason을 사용자에게 설명한다.
- 잔여 20% 이하에서는 설정된 품질 적합 대안 중 다른 한도의 여유가 확인된 조합을 우선한다. 5% 이하에서는 새 배정을 보류한다. 미확인·오래된 정보는 여유 있다고 가정하지 않고 기존 정책을 유지한다.
- usage.alternatives는 작업별 품질 적합 프로필의 명시 목록이다. 새 대안을 모델 이름이나 effort만으로 동등하다고 추측해 추가하지 않는다. API 조회는 계정 변경 또는 실패 시 이전 계정 관찰을 재사용하지 않는다.
- 실행 중인 작업을 끊거나 조정자 모델을 바꾸지 않는다. 크레딧 구매·소비·계정 전환을 자동 수행하지 않는다. 사용량 데이터는 Jev에 보내지 않는다.
- 작은 작업은 직접 처리한다. 분배 시 scripts/kit.py route --task-type simple|implementation|test|design|debug|review를 실행한다. 복잡하면 --complexity complex를 추가한다.
- route의 status=ready일 때만 launch_args를 Orca worker-start에 전달한다. blocked이면 해당 모델을 자동 배정하지 말고 검증 또는 명시 선택을 요청한다. 새 모델 이름을 추측하지 않는다.
- 현재 요청은 --profile/--agent/--model/--effort로 반영한다. 로컬 profiles/routes가 공통 정책보다 우선한다. 기존 models/efforts는 라우팅을 사용하지 않는 경우만 적용한다.
- 모델 검증/상향/대체 규칙은 references/routing.md를 읽는다. AGY는 ID 내장 effort를 사용하면 별도 --effort를 전달하지 않는다.
- 작업당 한 번만 quality 실패에 대해 high 이하로 상향한다. 먼저 기존 Dispatch의 확실한 settlement를 확인한다. 인증/네트워크/설치 실패는 모델 상향으로 해결하지 않는다.
- 모델이 달라지면 새 작업자를 시작한다. 실제 모델은 launch.effective 또는 공급자 응답으로 확인하고 미확인이면 그대로 기록한다.
- 같은 도구로 구현·검토를 수행하면 독립 도구 검토가 아님을 보고한다. Jev는 분류만 보조하며 지원 여부와 모델 우열을 결정하지 않는다.

## 작업 수명
- Task마다 대상, 산출물, 제약, 수정 소유권, 검증 기준을 포함한다. references/task-template.md를 사용한다.
- `--worktree current`는 조정자 터미널이 속한 Orca 작업 공간이며 셸 cwd와 다를 수 있다. 시작 receipt의 worktree effect로 실제 위치를 확인하고 Task에 절대 경로를 적는다.
- 동시에 쓰는 작업은 별도 Orca 작업 공간으로 격리한다. Git이 없는 폴더에서는 쓰기 작업을 직렬화한다. 현재 미커밋 변경이 다른 작업 공간에 자동 전달된다고 가정하지 않는다.
- Run/Task/Dispatch, ask/reply, worker_done을 현재 가이드대로 사용한다. worker는 주입된 preamble의 정확한 ID/명령을 따른다. 하위 작업자 추가 생성은 하지 않아 전체 2명 한도를 유지한다.
- 완료 주장과 실제 변경·테스트를 대조한다. 무응답은 실패가 아니다. 불확실하면 관찰하고, 확정된 종료/settlement에만 재시도·회수를 수행한다.
- 완료마다 재사용/명시 보존/회수 중 하나를 결정하고 메시지를 처리한 뒤 ack한다. 조정자는 사용자에게 작업별 결과·근거·미해결 사항을 보고한다.

## Jev
필요할 때 references/jev.md를 읽는다. 판단은 보조 근거이며 권한이나 완료 여부를 단독 결정하지 않는다.
