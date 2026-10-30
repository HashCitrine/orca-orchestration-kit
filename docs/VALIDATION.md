# 검증 결과

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
`kit.py doctor`: orca/claude/codex/agy 실행 파일과 help 확인. 인증/모델 가용성 검증과는 구별한다.
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
