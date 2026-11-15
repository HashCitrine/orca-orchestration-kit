# 검증 결과

## Entire 선택형 연동 (2026-11-05, Windows)

- 스킬 지침·운영 체크포인트의 선택형 Entire 참조·작업자 보고·근거 보존 규칙을 추가했다. `kit.py`, 라우팅·설정 API는 변경하지 않았다. 네 에이전트의 설치·반복 갱신·사용자 수정 충돌 보존·제거 검증을 새 가이드에도 적용했다. 로컬 unittest 57개 및 Python 3.11 UTF-8 스킬 형식 검사, 로컬 문서 링크 37개 검사 통과. `kit.py update`로 관리 파일 52개를 갱신하고 네 설치본의 변경 지침이 원본과 일치함을 확인했다. 원본 저장소에 Entire는 활성화하지 않았다.
- 공식 Entire v0.12.2 windows/amd64 배포 ZIP의 SHA256 `d213ef9dd3329526a01be8ff44d5d2d07fc26dab2755e90618bf8ded692fade6`을 배포 checksums.txt와 대조했다. 바이너리의 enable/status/session/checkpoint 및 하위 조회 도움말을 확인했다. Codex CLI 0.166.0, Orca 1.4.248. 사용자 전역 PATH나 Codex 설정을 변경하지 않았다.
- `.local/orca-team/experiments/entire/20261105-single-cli-02/`의 독립 Git 저장소에서 `enable --local --agent codex --skip-push-sessions --telemetry=false --yes --absolute-git-hook-path`를 실행했다. 유효 설정은 push_sessions=false, telemetry=false, git-refs. 프로젝트 `.codex/hooks.json`, `.entire/.gitignore`·로컬 설정과 격리 저장소의 Git 훅이 생성됐다. 기존 prepare-commit-msg 훅의 백업 해시와 커밋 시 후속 실행을 확인했다. Git author/committer는 HashCitrine 계정을 명시했다.
- 별도 로컬 bare 저장소로 main 브랜치 코드 푸시 성공. 대상 refs는 refs/heads/main 하나였다. 그러나 실제 에이전트 체크포인트가 생성되지 않았으므로 이 결과는 코드 푸시만 검증하며 **세션 기록 전송 억제의 실증은 아니다**. 외부 원격에 실험 기록을 푸시하지 않았다. Entire 로그인·클라우드 기능·기존 세션 가져오기는 수행하지 않았다.
- 원본 Git config·훅, 관련 사용자 전역 Git/Codex/Claude/Gemini 설정과 원본의 Entire/Codex 훅 경로를 전후 비교했고 읽기 불가 항목 없이 동일했다. Entire의 사용자 캐시 접근은 승격 승인 후 수행했다. 첫 샌드박스 시도는 캐시 잠금 접근 경고가 있었으며, 이후 독립 실험을 승격 실행했다. 첫 시도의 기존 pre-commit 훅은 Entire가 설치하는 훅이 아니므로 이동을 기대한 실험 단언을 수정하고, prepare-commit-msg로 실제 연결을 검증했다. 두 저장소와 로컬 바이너리는 삭제하지 않고 보존했다.
- **실제 수집 실증 차단:** 현재 Windows의 `route --task-type implementation --profile standard`는 no verified compatible profile / missing, stale, or changed-runtime smoke-test evidence로 blocked, usage refresh는 unknown이었다. Entire status의 Codex 훅은 trust_review_needed와 7개 누락 승인을 보고한다. 설치된 Codex 훅은 PATH에서 entire를 찾으므로 실제 에이전트 환경의 명령 해석도 추가 확인이 필요하다. 제한을 우회하거나 승인을 자동 수락하지 않았으며 Orca 작업자 실행·실제 프롬프트 수집·세션 종료 후 재조회는 수행하지 않았다.
- 아스트라 독립 세션에서 미설치, trailer만 존재/조회 실패, 과거 승인, 삭제 전 근거 누락, 대화 수집과 gitignore, 훅 신뢰/PATH, 여러 세션·오래된 revision, 체크포인트 없는 푸시의 8개 시나리오를 읽기 전용 검토했다. 문서 반영을 막는 결함은 없었으며, 실제 기록 없는 푸시를 전송 억제 성공으로 판단하지 않는 문구와 수집 실패 시 세션 회수·저장소 제거를 분리하는 문구를 보강했다. 모의 검토를 실동작 검증으로 간주하지 않는다.
- 로컬 근거: 위 실험 디렉토리의 `evidence/summary.json`, 설정·도움말·훅·커밋·푸시·refs 관찰 결과. 원본과 별도 Git common directory임을 확인했다. 세션 기록과 실험 파일은 커밋 대상에서 제외한다. 1차 잔여, CLI 진단·비공개 원격·병렬·다른 에이전트/OS 검증은 [후속 계획](PLAN.md#entire-선택형-연동과-후속-todo)에 남겼다.

## 조정자 컨텍스트 체크포인트 (2026-11-05, Windows)

- Run별 로컬 체크포인트·복원 지침과 템플릿을 추가하고 작업자 보고·정리 지침에 연결했다. 실행 전 pending과 실행 후 실제 근거, 실행·검증·통합·정리 상태 분리, 승인·상향 이력 유실 처리, 새 세션의 읽기 전용 확인 범위를 명시했다. 새 CLI나 자동 세션 교체는 추가하지 않았다.
- `py -3 -m unittest discover -s tests -v`: 57개 통과. 새 설치 생명주기 테스트는 네 에이전트 경로에 참고문서가 복사되는지, 반복 갱신·사용자 수정 충돌 시 보존·제거와 별도 런타임 기록 보존을 확인한다.
- Python 3.11 UTF-8 모드의 skill-creator `quick_validate.py` 통과. 아스트라 독립 세션이 지침과 모의 Orca/Git 관찰로 8개 복원 시나리오를 검토했다. 배정 응답 유실, 검증 revision 불일치·임시 근거, 이미 반영된 통합, 회수 unknown·보존 요청, reply/ack 분리, 여러 호스트·Run, 새 세션, 손상 기록을 포함한다. 지적된 승인 범위·상향 이력 미확인 시 실행 보류 규칙을 반영했다.
- `py -3 -X utf8 kit.py update`: Windows 사용자 홈의 네 에이전트 경로에 48개 관리 파일 갱신. 샌드박스 밖 설치 경로 쓰기는 승격 승인 후 수행했으며 사용자 파일 충돌은 없었다.
- 복원 검토는 모의 관찰 기반의 읽기 전용 검증이다. 실제 장기 Run의 컨텍스트 압축·세션 재연결·워크트리 제거는 수행하지 않았다. 실제 실행과 메시지 수신은 현재 Orca 런타임 가이드에 의존한다.

## Jev·GPT 선택형 보조 판단 (2026-11-05, Windows)

- 공통 `decision.py` 실행기 추가. 로컬 인증 존재 확인, auto의 Jev 우선 선택, Jev 실패 후 설정된 OpenAI 1회 대체, 명시 제공자 전환 금지 및 none/인증 부재 시 조정자 판단을 검증했다. 기존 jev.py는 변경하지 않았다.
- Python 3.12 전체 55개 테스트 통과 후 설치된 공통 실행기 실행 테스트를 추가 검증했다. Python 3.9에서도 당시 새 테스트 10개 통과. 질문·선택지 식별자, 순서 있는 점수 기준 변환, HTTP 요청·리다이렉트 차단, 비밀 비출력, 거부·질문 누락·중복·잘못된 확률·인증 실패·시간 초과 처리 포함.
- `decision.py status`: 현재 프로세스의 Jev/OpenAI 인증 미감지, selected_provider=none. 실제 API 접근·과금·모델 판단 품질은 미검증이며 라이브 요청을 보내지 않았다. 모의 HTTP 응답과 공식 Decisions 요청·응답 명세를 기준으로 검증했다.
- 스킬 형식 검사와 `git diff --check` 통과. 전역 설치본과 사용자 인증·설정은 변경하지 않았다.

## 워커 수 자동 조절과 기본 정리 (2026-11-05, Windows)

- `py -3 -m unittest discover -s tests -v`: 45개 통과. max_workers 미지정/null/1/2/3/8 허용 및 0·음수·불리언·문자열·소수·배열·객체 거부 확인. 루트/설치용 스크립트 일치 검사 포함.
- `py -3.11 -X utf8 .../skill-creator/scripts/quick_validate.py skills/orca-team`: Skill is valid. 기본 Python 3.12에는 PyYAML이 없어 설치된 Python 3.11로 형식 검사 수행.
- `git diff --check`: 통과. 자동 인원 선택·사용자 지정·인원 축소 및 결과 통합 전 정리 금지·보존 요청·공유 공간·정리 실패 처리 지침 검토.
- 설치된 Orca의 orchestration/cleanup 가이드와 worker-release/worktree rm 도움말을 조회해 자동 세션 회수와 별도 워크트리 제거 절차 확인. 실제 워커 생성·회수·워크트리 삭제 검증과 전역 스킬 설치 갱신은 수행하지 않음. 에이전트 지침 변경이며 별도 스케줄러나 정리 프로세스를 추가하지 않음.

2026-10-30 / macOS / Orca 1.4.244

## 자동 테스트
`python3 -m unittest discover -s tests -v`: 7개 통과.
- macOS/Windows/Linux와 ORCA_CLI_COMMAND·개발 환경 선택.
- 공백·한글 임시 경로에서 설치, 반복 설치, 갱신, 제거.
- 사용자 변경 파일 및 추가 파일 보존, 소유하지 않은 파일 덮어쓰기 거부.
- 기능 캐시 재사용, 도구 지문·명시 모델 설정 변경과 CLI 부재 감지.
- Claude readiness(macOS/Linux 경로, bypass 유무, 설정 유무, Orca 설정 없음), claude-setup(키 보존, 백업 일치, 재실행 no-op, 잘못된 JSON 보존, 새 파일, CLAUDE_CONFIG_DIR), doctor 지문 반영.

`quick_validate.py skills/orca-team`: Skill is valid.
`kit.py install` 및 `update`: 15개 파일 설치·갱신.
`kit.py doctor`: orca/claude/codex/agy/grok/opencode/pi 실행 파일과 help 확인. 인증/모델 가용성 검증과는 구별한다.
Jev status: configured=true, credential_file. 키는 출력하지 않았다.

초기 테스트에서 macOS /var 임시 경로가 심볼릭 링크 보호에 걸렸다. 테스트 임시 루트를 resolve하여 시스템 경로 별칭을 정규화한 뒤 통과했다. 실제 설치 대상의 심볼릭 링크 보호는 유지했다.

## 실제 Orca 실행
Run: run_241e756ec53b
- AGY ctx_9221a7a59432: 정책 읽기 → worker_done succeeded → released.
- Codex ctx_85f3c69dc62a: 정책 읽기 → worker_done succeeded → released.
- Claude ctx_a5e4275a9a5e: agent_readiness 실패. 기존 Orca가 권한 우회 옵션으로 실행하여 최초 확인 화면에서 대기했다. No, exit로 거부했고 공식 복구 명령으로 released.
- 모델·effort를 전달하지 않았으며 실제 모델은 런타임 응답에서 null이므로 미확인으로 기록한다.

## Claude 작업자 재검증 (Claude Code 조정자)
- 원인: Orca `agentDefaultArgs.claude`=`--dangerously-skip-permissions`, Claude 설정에 `skipDangerousModePermissionPrompt` 없음.
- `kit.py doctor`: needs_claude_setup → `kit.py claude-setup`(기존 설정 백업, 키 1개 병합) → ready.
- Run run_434cabb4a423, Claude ctx_b982d5f887ec: worker-start state=ready·input_accepted → 정책 읽기 → worker_done succeeded → released. reclaimable 0.
- 조정자는 Claude Code(Opus 5.5) 세션. launch.effective 모델은 null이므로 작업자 실제 모델은 미확인.
- 관찰: `--worktree current`가 셸 cwd가 아닌 조정자 터미널의 Orca 작업 공간(<workspace>/example-project)으로 결정되었다. 작업자는 설치된 스킬 경로로 대신 읽었다. SKILL.md에 receipt 확인과 절대 경로 지침을 추가했다.

## 제한
- 각 도구의 새 대화에서 전역 스킬 자동 발견은 별도 확인이 필요하다. 작업자는 저장소의 스킬을 명시 경로로 읽었다.
- AGY 조정자 역할과 blocking ask/reply 왕복은 미검증이다.
- Linux/Windows/WSL 실제 실행과 GitHub Actions는 아직 실행하지 않았다. CI 설정 제공은 성공 증거가 아니다.
- Jev 실제 HTTP 평가와 모델 삭제/옵션 변경에 따른 공급자 오류는 미검증이다. 기존 공식 실행기 및 실패 시 일반 도구 전환 지침을 제공한다.
- TypeSafe 공식 API 문서 웹 조회가 실패하여 기존 설치된 실행기를 재사용했다. 응답 계약을 새로 추측하지 않았다.
- max_workers와 재시도 방지는 에이전트 운영 지침이다. 별도 강제 스케줄러를 구현하지 않았다.

## 모델·effort 라우팅 구현 결과 (2026-10-30)
완료: route JSON CLI, 4개 기본 프로필, 로컬 재정의, 검증된 조합만 자동 배정, effort 인코딩 구분, 한 번 상향·high 제한, 명시 선택 대체 금지. 기존 설정과 Claude readiness 기능 보존.

자동 테스트 12개 통과. 스킬 형식 검사 통과. 세 도구 설치 경로에 21개 관리 파일 갱신.
실제 검증 Run: run_9a76019419ed. light(ctx_d2e183bace44), standard(ctx_5907b11961a3), deep(ctx_9c2324619844), review(ctx_389d5ef9c02d) 모두 launch.effective 일치 및 worker_done succeeded 확인 후 회수.
로컬 model-evidence.json에 근거를 등록했으며 다른 컴퓨터로 동기화하지 않는다.

한계: 검증은 작은 읽기 작업이며 모델 성능·비용 비교가 아니다. Claude 전용 모델 프로필은 이번 기본 매핑에 포함하지 않았으며 로컬 profiles로 추가 후 검증할 수 있다. Jev는 기존 분류 보조 지침을 사용하며 이번에 API 평가를 호출하지 않았다. 상향 횟수의 이전 route JSON 및 Dispatch 종료 확인은 조정자가 관리한다. 임의 JSON 변조를 막는 별도 서버 스케줄러는 아니다. 모델 목록 자동 수집은 구현하지 않았으며 공식 CLI/로컬 캐시 조회와 실제 실행으로 확인한다. OS별 실제 실행 범위는 기존 기록을 따른다.

## 공개 준비 검토 (2026-10-30)

개인 작업 경로를 문서와 main의 과거 커밋에서 일반화했다. 커밋 작성자·커미터의 GitHub 계정 이름과 이메일은 소유자 선택에 따라 유지했다. 원본 이력은 비공개 로컬 백업으로 보관한다.

검토 당시 커밋 5개, 고유 파일 내용 32개 및 Actions 로그 4건에서 검사한 토큰·개인키 패턴이 발견되지 않았다. 이슈/PR/릴리스/Actions 아티팩트는 없었다. 패턴 검사는 모든 비밀정보 부재를 보장하지 않는다. MIT 라이선스와 코드 출처 문서를 추가했다. 공개 전 정리된 이력과 자동 테스트를 다시 확인한다.

공개 전환 완료: GitHub API에서 visibility=public, private=false, license=MIT 확인. 공개 준비 커밋 71aac08의 CI 6개 작업(macOS/Linux/Windows, Python 3.9/3.13)이 모두 성공했다. 과거 커밋으로 연결되던 Actions 기록 4건은 삭제했다. 로컬 저장소 및 설치된 스킬도 정리된 이력으로 동기화했다.

개인 경로는 현재 main과 그 이력에서 제거했지만, GitHub가 참조되지 않는 옛 커밋 객체를 보관하는 동안에는 정확한 옛 SHA로 조회될 가능성이 있다. 서버 객체의 즉시 완전 삭제를 주장하지 않는다. 발견된 경로에는 인증정보가 포함되지 않았다.

## Onboarding implementation completed (2026-10-30)

- Implemented setup and verify-profile, refreshed README, and added a getting-started guide for all three agents.
- 18 automated tests passed; skill validation and documentation link/JSON/code-fence checks passed.
- Real setup checks passed for Codex, Claude and AGY on macOS. Claude has no bundled model profile and receives configuration guidance.
- New Run run_3cc1edcbace3: Codex standard ctx_072b823518f8 and AGY light ctx_49dc417778ec succeeded. verify-profile registered live Orca evidence; repeated registration returned changed=false without extending completion time. Both workers were released.
- Installed skill copies were updated. New Claude model verification and other-OS agent execution remain untested in this change.
- setup writes only local observation metadata; it does not install external tools, log in, change permissions, or launch workers. Binary identity is checked using paths, size, timestamps and the pre-launch observation, not cryptographic attestation.

## Quota-aware routing implementation (2026-10-30)

Implemented Codex read-only App Server quota refresh, manual observations, local account-scoped storage, five-minute expiry, reserve thresholds and quality-approved alternatives. Current real response supplied a weekly window; no five-hour window was inferred. No account identifiers or quota numbers are committed. Claude/AGY automatic collection remains unsupported. Cross-profile alternatives are opt-in configuration, not an inferred model performance ranking.

Quota validation: 25 automated tests and skill validation passed. Codex account/rateLimits/read succeeded without inference work; missing time windows were not inferred. Local alternatives were configured, and installed skill copies were updated. Claude/AGY quota automation and precise usage reservations remain outside this implementation.

Claude/AGY quota validation: 28 automated tests passed (Orca payload conversion, ms timestamps, updatedAt freshness, AGY group minimum, Orca error isolation, AGY alternative selection). Real macOS run: `usage refresh` returned updated for codex, claude and agy; `usage show` reported light, standard, deep and review as normal with provider windows; `route --task-type review` included the AGY group windows. Quota numbers and account labels are not recorded here. Claude values require a claude.ai Pro/Max login; Team/Enterprise and other OSes are unverified.

## CANDIDATES-001 (2026-11-02, macOS / Python 3.9.6)

- `python3 -m unittest discover -s tests -q`: 35 tests, OK. 기존 28개 및 후보 조회 무변경, 설정·CLI 검증, Claude 검증 누락/만료/실행파일 변경, 정상/20%/5%/미확인 한도, 사용자 명시 선택 보존, 공급자 effort 비순위 처리, 독립 리뷰 대안 전환 7개 추가.
- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/orca-team`: Skill is valid. `git diff --check`: 성공.
- `kit.py setup --agent claude --json` 후 Run `run_2bb726775414`, Dispatch `ctx_2d02035c83eb`: routing.json만 읽는 작업 성공. launch.effective = claude / sonnet / high. 별칭의 구체적 버전은 프로필에 고정하거나 추측하지 않는다. 모델 품질 평가를 의미하지 않는다.
- `kit.py verify-profile --profile claude --dispatch ctx_2d02035c83eb`: verified. worker_done 메시지 처리·ack 및 worker-release 성공, reclaimable worker-list 빈 목록 확인.
- `kit.py usage refresh --json`: Codex·AGY updated, Claude unknown. 미확인 사용량을 여유로 취급하지 않았다. 인증·권한·계정 전환 없음.
- `kit.py update`: managed_files 24, removed_files 0. 세 에이전트 설치본의 모든 소스 파일 및 manifest 해시 일치 확인, 로컬 사용자 설정 보존.
- 설치본 `route --task-type review --candidates --implementation-agent codex` 및 `route --task-type design --select-profile claude --selection-reason ...`: Claude ready 및 선택 이유/실행 인자 확인. 후보 조회는 작업자 실행을 유발하지 않는다.

## CLAUDE-MODELS-001 (2026-11-02, macOS / Python 3.9.6)

- 변경: Claude 프로필을 claude-sonnet/claude-opus/claude-fable(각 high)로 분리하고 simple 외 모든 작업 후보에 포함. claude-fable은 require_quota로 계정에 Fable 한도가 보고될 때만 자동 후보. `--select-profile ... --effort`와 `verify-profile --effort`, 후보의 verified_efforts 추가.
- `python3 -m unittest discover -s tests`: 38 tests, OK. 모델별 후보·실행 인자, Fable 한도 미보고 시 자동 제외/명시 선택 허용/보고 시 ready, 조합 미검증 effort blocked·검증 후 ready, 잘못된 effort 거부 추가.
- `quick_validate.py skills/orca-team`: Skill is valid. `git diff --check`: 성공.
- `kit.py update`: managed_files 24, removed_files 0. 세 설치본과 저장소 skills/orca-team 일치 확인.
- 설치본 `usage refresh --agent claude` 후 `route --task-type design --candidates`: claude-sonnet ready(verified_efforts high, 기존 sonnet/high 근거 재사용), claude-opus는 검증 근거 없음으로 blocked, claude-fable은 검증 근거 없음 + `required quota not reported for this account: claude-fable`로 blocked. 현재 계정의 Orca 응답은 fableWeekly=null.
- 미실행: opus/fable 및 sonnet 외 effort 조합의 실제 읽기 전용 Dispatch 검증. 작업자 실행이 필요하므로 사용자 요청 시 진행한다.
- 추가 검증(2026-11-02): `setup --agent claude` 후 Run `run_273bb9f05d35`, Dispatch `ctx_6efaf931c338`: routing.json만 읽는 작업 성공, 저장소 변경 없음. launch.effective = claude / opus / high. `verify-profile --profile claude-opus --dispatch ctx_6efaf931c338`: verified. worker_done 처리·ack, worker-release 후 resource released 확인.
- 설치본 `route --candidates`(implementation/design/review): claude-sonnet·claude-opus ready(verified_efforts high). claude-fable은 현재 계정에 Fable 한도 미보고로 제외(미검증). `--select-profile claude-opus` 실행 인자 `--agent claude --model opus --effort high` 확인.

## OPENCODE-PI-001 (2026-11-14, macOS / Python 3.9.6)

- 변경: Orca 작업자 id `opencode`와 `pi`를 kit의 agent 목록, setup/doctor, 프로필 검증, 라우팅, 스킬 설치 경로, usage 처리에 추가. OpenCode는 `effort_mode: "none"` + `effort: "default"`만, Pi는 `effort_mode: "flag"`만 허용. 기본 routing.json에는 계정별 모델을 추측해 넣지 않았다.
- `TMPDIR=/private/tmp python3 -m unittest discover -s tests`: 63 tests, OK. 추가 테스트: 스킬 경로와 환경 변수 재정의, launch_args(`opencode`는 `--effort` 없음, `pi`는 `--effort` 포함), 후보/verified_efforts, 잘못된 effort_mode 거부, verify-profile의 OpenCode effort 없음/Pi effort 일치, usage unknown과 none-effort 대안 전환.
- 기본 TMPDIR(`/var/folders/...`)에서는 기존 `safe_path`가 `/var` 심볼릭 링크를 충돌로 판단해 `test_decision` 1건이 실패한다. 이는 이번 변경과 무관한 기존 환경 제약이며, `/private/tmp`에서는 전체 통과한다.
- `kit.py doctor --home <temp>`: orca/codex/claude/agy/grok/opencode/pi 모두 available, skill_roots에 `~/.config/opencode/skills`와 `~/.pi/agent/skills` 반영.
- `kit.py setup --agent opencode|pi --home <temp>`: 두 CLI와 Orca 연결 확인. 기본 프로필이 없으므로 로컬 profiles 추가 안내를 반환했고 작업자는 실행하지 않았다.
- `kit.py install --home <temp>`: managed_files 66, removed_files 0. 여섯 스킬 경로(Codex, Claude, AGY, Grok, OpenCode `~/.config/opencode/skills`, Pi `~/.pi/agent/skills`)에 `orca-team/SKILL.md` 설치 확인.
- 임시 config로 `route --candidates` 실행: opencode/pi 후보가 blocked(검증 근거 없음)로 표시되고 launch_args는 생성되지 않았다. OpenCode flag, Pi none 등 잘못된 조합은 설정 검증에서 거부됐다.
- 로컬 설치본 갱신: 기존 Codex/Claude/AGY/Grok 스킬 디렉터리를 백업한 뒤 `kit.py install`로 6개 경로를 다시 설치했다. 이후 원격의 추가 references까지 반영한 `kit.py update` 기준으로 manifest 78개 해시가 모두 일치하고, 모든 설치본의 `scripts/kit.py`·`usage.py`가 저장소와 같다. 기존 설치본에만 있던 `worker-show --full` 수정은 소스에도 반영해 보존했다.
- Orca 1.4.258의 `worker-start` 도움말과 앱의 agent catalog에서 `opencode`/`pi` id 및 Pi `--thinking`(effort), OpenCode 모델 선택 제약을 확인했다. 실제 OpenCode/Pi Dispatch 실행과 launch.effective 검증은 이번 변경에서 수행하지 않았다. 사용자 요청 시 `setup` 후 작은 읽기 전용 작업으로 검증한다.

## OMP-001 (2026-11-14, macOS / Python 3.9.6)

- 변경: Orca 작업자 id `omp`를 kit의 agent 목록, setup/doctor, 프로필 검증, 라우팅, 스킬 설치 경로, usage 처리에 추가. OMP 프로필은 `effort_mode: "flag"`만 허용하고 `--effort`가 OMP `--thinking`으로 전달된다. 기본 routing.json에는 계정별 모델을 추측해 넣지 않았다.
- `diff -q kit.py skills/orca-team/scripts/kit.py` 및 `diff -q usage.py skills/orca-team/scripts/usage.py`: 차이 없음.
- `TMPDIR=/private/tmp python3 -m unittest discover -s tests -v`: 65 tests, OK. 새 OMP 단언이 모두 실행됐다: `test_skill_roots`, `test_launch_and_candidates`, `test_verify_opencode_pi_and_omp_effort`, `test_setup_omp_has_no_default_profiles`, `test_refresh_extended_agents_is_unknown`. launch_args는 `--agent omp --model openai/gpt-5.4 --effort high`, 명시 override는 기본 `standard` 프로필 effort를 이어받아 `--effort medium`, effort 내장 `review` 기반에서도 `--agent omp`가 flag로 보정돼 `--effort high`였다.
- `orca agent-context --json`: `orchestration worker-start` 노트가 "OMP also takes its model roles and selectors ..., with --effort as its thinking level"을 보고한다. Orca 1.4.258.
- `kit.py doctor --home <temp>`: `tools.omp.available` true, `tools.omp.help_ok` true, `skill_roots.omp`가 `<temp>/.agents/skills`로 확인됐다. `XDG_CONFIG_HOME`·`CODEX_HOME`·`GROK_HOME`·`OPENCODE_CONFIG_DIR`·`PI_CODING_AGENT_DIR`를 제거한 환경에서도 OMP 경로는 변하지 않았다.
- `kit.py setup --agent omp --home <temp>`: CLI와 Orca 연결 확인, `프로필: {}`와 "기본 프로필이 없습니다" 다음 단계를 반환했고 요청문에 `omp`가 포함됐다. 작업자는 실행하지 않았다.
- `kit.py usage refresh --agent omp --home <temp>`: `"status":"unknown"`, `"agent":"omp"`, 사유 `automatic adapter unavailable; use manual input`.
- `kit.py install --home <temp>`: managed_files 91, removed_files 0. 일곱 스킬 경로(Codex, Claude, AGY, Grok, OpenCode `~/.config/opencode/skills`, Pi `~/.pi/agent/skills`, OMP `~/.agents/skills`) 모두에 `orca-team/SKILL.md`가 설치됐다. 첫 시도는 `/var` 심볼릭 링크를 포함한 `mktemp -d` 경로에서 `safe_path` 충돌로 실패했고, `/private/tmp` 기반 경로에서 통과했다. 이는 기존 환경 제약이며 변경과 무관하다.
- 로컬 설치본 갱신: `kit.py install`로 managed_files 91, removed_files 0, 사용자 파일 충돌 없음. `$HOME/.agents/skills/orca-team/SKILL.md`·`scripts/kit.py`가 저장소와 일치하고, `omp skill list --json`이 `orca-team`을 `"source":"agents:user"`로 보고한다.
- 당시 미실행: 실제 OMP Dispatch. 계정별 모델 선택과 bootstrap 검증이 필요해 이번 변경에서는 worker-start·verify-profile을 수행하지 않았고, OMP 프로필은 사용자 검증 전까지 blocked였다. 2026-11-15 OMP-LIVE-001에서 `omp-haiku`로 수행했다.

## OMP-LIVE-001 (2026-11-15, macOS / Python 3.9.6)

- 로컬 프로필: `omp-haiku` = agent `omp`, model `anthropic/claude-haiku-5-5`, effort `medium`, `effort_mode` `flag`. 계정별 모델 차이 때문에 `routing.json`과 후보(`candidates`)에는 넣지 않았고 저장소 파일은 변경하지 않았다.
- `kit.py setup --agent omp --json`: `profiles`가 `{"omp-haiku":"blocked"}`, `checks`가 python 3.9.6·git·orca_connected·agent_cli·skill_installed 모두 true. `setup-observation.json`의 `identities.omp`가 현재 실행 파일(`/Users/tmkim/.local/bin/omp`, size 224277648, mtime_ns 1794753191508426769)과 일치한다.
- 검증 전 `kit.py route --task-type implementation --profile omp-haiku --json`: `status` blocked, `rejected[0].reason`은 `missing, stale, or changed-runtime smoke-test evidence`였다. 이 상태에서 라우팅으로 작업자를 시작하지 않았다.
- 첫 Dispatch `ctx_e7a09b91c070`: worker_done succeeded, `worker-show`에서 `dispatch.status` completed·`worker.state` succeeded·`hostScope.kind` local이었고 `launch.effective`도 요청과 같았다. 그러나 `verify-profile`이 `작업 전 setup 기록과 현재 실행 파일이 일치해야 합니다`로 실패했다. setup 이후 OMP 실행 파일이 바뀐 것이 원인이었다(size 223369360 → 224277648, mtime_ns 1794584505794002030 → 1794753191508426769). evidence를 고치지 않고 `setup --agent omp`를 다시 실행한 뒤 새 Dispatch로 재검증했다.
- 두 번째 Dispatch `ctx_4a679fc9ba52`(task `task_4595d163b7e7`, run `run_7525dad8ba31`, terminal `term_32b21b0f-bb99-472d-b40c-8449090a54c2`): `check --wait`가 `worker_done`(`outcome` succeeded, subject `routes mapping reported`)을 받았고 `worker-show --full`에서 `dispatch.status` completed(completedAt 2026-11-15T14:33:46.108Z), `worker.state` succeeded, `hostScope` local/local이었다.
- `launch.effective`: `{"agent":"omp","model":"anthropic/claude-haiku-5-5","effort":"medium"}`로 요청과 정확히 같았다.
- `verify-profile --profile omp-haiku --dispatch ctx_4a679fc9ba52`: `status` verified, `changed` true, `verified_at` 2026-11-15T14:33:46.108000+00:00. evidence key는 `omp|anthropic/claude-haiku-5-5|medium|flag`이고 `dispatch_id`, `actual_model` `anthropic/claude-haiku-5-5`, `actual_effort` medium, `runtime_id` 8318e744-6f21-4290-9f62-e360b60da139, identity를 담는다.
- `worker-release`: 두 Dispatch 모두 `state` released, `processAction` closed_agent_terminal, `archive` transcript captured.
- 사후 `route --task-type implementation --profile omp-haiku --json`: `status` ready, `launch_args` `["--agent","omp","--model","anthropic/claude-haiku-5-5","--effort","medium"]`.
- 작업자는 안내한 `routing.json`만 읽었고 저장소 파일을 바꾸지 않았다(`git status --short` 비어 있음). 여섯 작업 유형의 `route --candidates`는 여전히 ready `grok-4.7` 하나·blocked 14개다.
- `TMPDIR=/private/tmp python3 -m unittest discover -s tests -v`: 65 tests, OK.
