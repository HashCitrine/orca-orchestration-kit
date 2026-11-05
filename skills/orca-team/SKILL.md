---
name: orca-team
description: Coordinate Claude, Codex, agy and Grok through Orca when the user requests team work or orchestration. For ordinary work, recommend orchestration when useful without launching it automatically.
---

# Orca 개인 공통 팀

사용자가 명시 요청했을 때만 작업자를 시작한다. 일반 요청은 병렬 구현 또는 독립 검토의 이점이 명확하면 추천만 한다. 시작한 에이전트가 조정자이며 작업자 수는 조정자를 제외한 동시 실행 인원이다. 완료한 작업자의 세션과 전용 임시 워크트리는 결과 보존 후 기본 정리한다. 보고는 한국어로 한다.

## 시작
- 처음 설치하거나 route가 blocked이면 scripts/kit.py setup --agent codex|claude|agy|grok를 실행한다. 검증 전 실행 파일 관찰 기록이 저장된다. setup은 작업자를 실행하지 않는다.
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
- 인원을 지정하지 않으면 2명을 출발점으로 삼아 독립 작업 수, 의존성, 수정 충돌, 자원 및 구독 여유에 따라 줄이거나 늘린다. 2명은 고정 상한이 아니다. 작은 작업은 직접 처리하며 인원을 채우려고 불필요한 작업을 만들지 않는다. 선택한 동시 인원과 이유를 사용자에게 설명한다.
- 로컬 max_workers가 미지정 또는 null이면 자동 모드이고, 양의 정수이면 동시 실행 상한이다. 기존 1·2 설정도 상한으로 유지한다. 현재 요청의 명시 인원은 로컬 설정보다 우선하며 요청 인원을 활용한다. 독립 작업 부족이나 실행 제약으로 충족할 수 없으면 이유와 실제 인원을 설명한다. 실행 환경의 제한을 우회하지 않는다.
- 작업 진행 중에도 의존성이 풀리거나 충돌·자원 상황이 달라지면 인원을 재평가한다. 인원 축소는 진행 중인 작업을 강제 종료하지 않고 새 배정을 줄여 반영한다. 조정자는 전체 Run의 동시 인원을 관리한다.
- 새 작업자 배정 직전에 scripts/kit.py usage refresh를 실행한다. Codex는 App Server, Claude·AGY·Grok는 Orca `account list`의 공식 집계로 갱신된다. 매 작업자 배정 전에 갱신한다. route 결과의 usage와 usage_reason을 사용자에게 설명한다.
- 잔여 20% 이하에서는 설정된 품질 적합 대안 중 다른 한도의 여유가 확인된 조합을 우선한다. 5% 이하에서는 새 배정을 보류한다. 미확인·오래된 정보는 여유 있다고 가정하지 않고 기존 정책을 유지한다.
- usage.alternatives는 작업별 품질 적합 프로필의 명시 목록이다. 새 대안을 모델 이름이나 effort만으로 동등하다고 추측해 추가하지 않는다. API 조회는 계정 변경 또는 실패 시 이전 계정 관찰을 재사용하지 않는다.
- 실행 중인 작업을 끊거나 조정자 모델을 바꾸지 않는다. 크레딧 구매·소비·계정 전환을 자동 수행하지 않는다. 계정·구독 사용량 데이터는 보조 판단 API에 보내지 않는다.
- 작은 작업은 직접 처리한다. 분배가 필요하면 `route --task-type <type> --candidates`로 작업별 승인 후보를 조회한다. Claude·Codex·AGY·Grok 중 작업 내용, 변경 범위, 검증 기준, 독립 검토 필요성과 확인된 구독 잔여량을 보고 매번 선택한다. 네 도구의 동시 사용·균등 배분이나 고정 역할은 강제하지 않는다. 기본 route는 바꾸지 않는다.
- Claude 후보는 모델별 프로필 claude-sonnet·claude-opus·claude-fable이다. 특정 모델 하나로 고정하지 않고 작업 성격과 각 한도 잔여량으로 고른다. effort는 `--select-profile ... --effort low|medium|high`로 작업에 맞게 고르되 `verified_efforts`에 있는 조합만 쓴다. fable은 현재 계정에 Fable 한도가 보고될 때만 자동 후보가 되므로 제외 사유를 사용자에게 설명한다. 미검증 조합은 setup·verify-profile(--effort 포함)로 먼저 검증한다.
- AGY 후보는 모델별 프로필 gemini-flash·gemini-argon·agy-claude-sonnet·agy-claude-opus·agy-gpt-oss이다. Gemini뿐만 아니라 Claude 5.5 및 GPT-OSS 120B까지 작업 성격과 3대 쿼터 그룹(Gemini Models, Gemini 4 Argon, Claude and GPT models) 잔여량에 따라 선택한다. 신규 프로필은 flag 방식으로 `--effort low|medium|high`를 지원하며 검증된 조합만 사용한다. 기존 light·review는 호환성을 유지한다.
- Grok 후보는 grok-4.5·grok-4.6·grok-4.7이다. 기본 effort는 high이고 flag 방식으로 `--effort low|medium|high`만 고른다. Orca 카탈로그의 xhigh는 자동 선택과 조정자 effort 선택에 넣지 않는다. 세 프로필은 Orca가 보고한 주간 창 하나인 quota group `grok`를 공유한다. session이 없으면 5시간 창을 만들지 않는다. simple에는 grok-4.5만 두고, grok-4.6·grok-4.7은 implementation·test·design·debug·review 후보이다. grok-4.5는 design 후보가 아니다. 모델만 바꿔 한도를 피한 것으로 보지 않는다. CLI에만 있는 모델은 기본 프로필에 넣지 않는다.
- 조정자 선택은 `route --task-type <type> --select-profile <name> --selection-reason "<작업에 맞는 이유>"`로 확정하고 ready의 launch_args만 사용한다. review에는 `--implementation-agent`를 전달해 다른 도구를 우선한다. 선택 이유와 usage_reason을 사용자에게 설명한다. 사용자의 명시 선택은 기존 --profile/--agent/--model/--effort로 처리하며 조정자 선택으로 바꾸지 않는다.
- 미검증·만료 후보와 보호 한도 후보를 실행하지 않는다. 사용량 unknown은 여유라는 뜻이 아니다. 도구 간 effort 값으로 품질 순위를 정하지 않는다. 지원 모델 별칭은 실제 모델 버전을 보장하지 않는다.
- 기존 단일 경로가 필요한 경우 분배 시 scripts/kit.py route --task-type simple|implementation|test|design|debug|review를 실행한다. 복잡하면 --complexity complex를 추가한다.
- route의 status=ready일 때만 launch_args를 Orca worker-start에 전달한다. blocked이면 해당 모델을 자동 배정하지 말고 검증 또는 명시 선택을 요청한다. 새 모델 이름을 추측하지 않는다.
- 현재 요청은 --profile/--agent/--model/--effort로 반영한다. 로컬 profiles/routes가 공통 정책보다 우선한다. 기존 models/efforts는 라우팅을 사용하지 않는 경우만 적용한다.
- 모델 검증/상향/대체 규칙은 references/routing.md를 읽는다. AGY는 ID 내장 effort를 사용하면 별도 --effort를 전달하지 않는다.
- 작업당 한 번만 quality 실패에 대해 high 이하로 상향한다. 먼저 기존 Dispatch의 확실한 settlement를 확인한다. 인증/네트워크/설치 실패는 모델 상향으로 해결하지 않는다.
- 모델이 달라지면 새 작업자를 시작한다. 실제 모델은 launch.effective 또는 공급자 응답으로 확인하고 미확인이면 그대로 기록한다.
- 같은 도구로 구현·검토를 수행하면 독립 도구 검토가 아님을 보고한다. 보조 판단 모델은 작업 분류 등을 보조하며 지원 여부와 모델 우열을 결정하지 않는다.

## 작업 수명
- Task마다 대상, 산출물, 제약, 수정 소유권, 검증 기준을 포함한다. references/task-template.md를 사용한다.
- `--worktree current`는 조정자 터미널이 속한 Orca 작업 공간이며 셸 cwd와 다를 수 있다. 시작 receipt의 worktree effect로 실제 위치를 확인하고 Task에 절대 경로를 적는다.
- 동시에 쓰는 작업은 별도 Orca 작업 공간으로 격리한다. Git이 없는 폴더에서는 쓰기 작업을 직렬화한다. 현재 미커밋 변경이 다른 작업 공간에 자동 전달된다고 가정하지 않는다.
- Run/Task/Dispatch, ask/reply, worker_done을 현재 가이드대로 사용한다. worker는 주입된 preamble의 정확한 ID/명령을 따른다. 작업자는 하위 작업자를 생성하지 않고 추가 분배가 필요하면 조정자에게 요청한다.
- 완료 주장과 실제 변경·테스트를 대조한다. 무응답은 실패가 아니다. 불확실하면 관찰하고, 확정된 종료/settlement에만 재시도·회수를 수행한다.
- 작업자는 결과·검증 근거·산출물의 절대 경로를 보고하고 worker_done 절차를 따른 뒤 턴을 종료한다. 자기 세션을 강제 종료하거나 자기 워크트리를 직접 삭제하지 않는다.
- 조정자는 완료 메시지를 현재 가이드대로 처리하고 필요한 ack를 수행한다. 결과 통합·보존 후 세션 회수와 이번 작업에서 만든 전용 임시 워크트리 정리를 마친다. 정리 전에 [완료 후 정리](references/cleanup.md)를 읽는다. 사용자 보존 요청이나 구체적인 후속 작업을 위한 재사용은 예외로 기록하고, 재사용이 끝나면 정리한다.
- 사용자에게 작업별 결과·근거·미해결 사항과 세션/워크트리 정리 결과를 보고한다. 정리 보류·실패는 대상과 이유를 명시하며, 완료 보고만으로 회수 성공을 주장하지 않는다.

## 보조 판단
필요할 때 [선택형 보조 판단](references/decision.md)을 읽는다. `scripts/decision.py status`로 기존 인증을 확인하고 현재 요청 > decision.provider 설정 > auto 순으로 선택한다. auto는 Jev 우선, OpenAI만 설정되어 있으면 GPT Decisions를 사용한다. 인증 존재는 API 접근 성공의 증거가 아니다. 둘 다 없거나 none이면 조정자가 판단한다.

호출 전 목적·선택 이유·전송할 최소 발췌와 자동 모드에서의 GPT 대체 가능성을 한국어로 알린다. auto에서 Jev 실패 시 설정된 GPT에 같은 발췌로 한 번 대체 호출하며, 명시 제공자는 자동 전환하지 않는다. 이후 실패하면 재시도 없이 조정자가 판단한다. 확률·점수는 보조 근거이며 권한, 지원 모델, 워커 실행이나 완료를 단독 결정하지 않는다.
