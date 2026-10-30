# 구현 계획
2026-10-30

독립 저장소에서 개인 공통 Orca 운영 스킬을 제공한다. 시작한 에이전트가 조정자이며 추가 작업자는 최대 2명이다. 명시 호출 때 실행하고 일반 작업에서는 추천만 한다.

1. 계획과 진행 기록 작성
2. 공통 스킬 및 모델 업데이트 대응 규칙
3. Python 3.9+ 설치·갱신·진단·제거 도구
4. 공식 Jev 실행기 및 컴퓨터별 인증
5. 충돌 보존·경로·모델 기본값 테스트
6. 현재 Mac 설치 및 실행 검증
7. Claude 작업자 권한 준비: doctor 감지와 명시 명령 `claude-setup`. Orca의 bypass 인자를 유지하고 Orca 앱 설정은 수정하지 않는다.

공통 정책과 로컬 설정을 분리하고 인증과 세션은 동기화하지 않는다. macOS/Linux/Windows/WSL을 대상으로 하되 실제 검증과 모의 검증을 구분한다. 원격 실행·예약·자동 병합·배포는 제외한다.

설정 우선순위: 현재 요청 > 로컬 재정의 > 공통 정책 > 도구 기본값. 모델을 기본으로 고정하지 않는다. 명시 모델이 없어지면 사용자 선택을 받는다.

## 모델 라우팅 확장 (2026-10-30)
진행 중: 프로필별 agent/model/effort, 검증 근거, 한 번 상향 제한, 테스트 및 실제 검증.

## 모델·effort 라우팅 구현 결과 (2026-10-30)
완료: route JSON CLI, 4개 기본 프로필, 로컬 재정의, 검증된 조합만 자동 배정, effort 인코딩 구분, 한 번 상향·high 제한, 명시 선택 대체 금지. 기존 설정과 Claude readiness 기능 보존.

자동 테스트 12개 통과. 스킬 형식 검사 통과. 세 도구 설치 경로에 21개 관리 파일 갱신.
실제 검증 Run: run_9a76019419ed. light(ctx_d2e183bace44), standard(ctx_5907b11961a3), deep(ctx_9c2324619844), review(ctx_389d5ef9c02d) 모두 launch.effective 일치 및 worker_done succeeded 확인 후 회수.
로컬 model-evidence.json에 근거를 등록했으며 다른 컴퓨터로 동기화하지 않는다.

한계: 검증은 작은 읽기 작업이며 모델 성능·비용 비교가 아니다. Claude 전용 모델 프로필은 이번 기본 매핑에 포함하지 않았으며 로컬 profiles로 추가 후 검증할 수 있다. Jev는 기존 분류 보조 지침을 사용하며 이번에 API 평가를 호출하지 않았다. 상향 횟수의 이전 route JSON 및 Dispatch 종료 확인은 조정자가 관리한다. 임의 JSON 변조를 막는 별도 서버 스케줄러는 아니다. 모델 목록 자동 수집은 구현하지 않았으며 공식 CLI/로컬 캐시 조회와 실제 실행으로 확인한다. OS별 실제 실행 범위는 기존 기록을 따른다.

## 초보자 시작 흐름 개선
진행 중: setup 진단, verify-profile 근거 등록, 세 도구별 시작 가이드와 README 재구성.

## Onboarding implementation completed (2026-10-30)

- Implemented setup and verify-profile, refreshed README, and added a getting-started guide for all three agents.
- 18 automated tests passed; skill validation and documentation link/JSON/code-fence checks passed.
- Real setup checks passed for Codex, Claude and AGY on macOS. Claude has no bundled model profile and receives configuration guidance.
- New Run run_3cc1edcbace3: Codex standard ctx_072b823518f8 and AGY light ctx_49dc417778ec succeeded. verify-profile registered live Orca evidence; repeated registration returned changed=false without extending completion time. Both workers were released.
- Installed skill copies were updated. New Claude model verification and other-OS agent execution remain untested in this change.
- setup writes only local observation metadata; it does not install external tools, log in, change permissions, or launch workers. Binary identity is checked using paths, size, timestamps and the pre-launch observation, not cryptographic attestation.

## Quota-aware routing
Completed: Codex read-only quota adapter, manual observations, reserve policy, tests and documentation.

## Quota-aware routing implementation (2026-10-30)

Implemented Codex read-only App Server quota refresh, manual observations, local account-scoped storage, five-minute expiry, reserve thresholds and quality-approved alternatives. Current real response supplied a weekly window; no five-hour window was inferred. No account identifiers or quota numbers are committed. Claude/AGY automatic collection remains unsupported. Cross-profile alternatives are opt-in configuration, not an inferred model performance ranking.

Quota validation: 25 automated tests and skill validation passed. Codex account/rateLimits/read succeeded without inference work; missing time windows were not inferred. Local alternatives were configured, and installed skill copies were updated. Claude/AGY quota automation and precise usage reservations remain outside this implementation.
