# 진행 현황

2026-10-30

| 단계 | 상태 | 근거 |
|---|---|---|
| 독립 저장소·Orca 등록 | 완료 | orca-orchestration-kit |
| 공통 스킬·Jev 실행기 | 완료 | 세 에이전트 개인 경로에 15개 관리 파일 설치 |
| 설치·갱신·제거·진단 | 완료 | 표준 라이브러리 Python CLI |
| 자동 검증 | 완료 | unittest 7개 통과 |
| AGY·Codex 작업자 검증 | 완료 | 실제 worker_done 성공, 회수 완료 |
| Claude 작업자 검증 | 완료 | claude-setup 후 run_434cabb4a423에서 worker_done 성공, 회수 완료 |
| Claude 조정자 검증 | 완료 | Claude Code 세션이 같은 Run을 생성·대기·회수 |
| AGY 조정자 역할 검증 | 미검증 | Codex·Claude 조정자만 검증 |
| Windows/Linux/WSL 실제 실행 | 미검증 | OS 선택 모의 테스트, CI 매트릭스 제공 |
| Jev 실제 API 호출 | 미검증 | 인증 존재 확인; 실제 평가 요청 없음 |

다음 작업: 다른 OS에서는 설치·doctor·테스트를 실행하고 결과를 VALIDATION.md에 추가한다.

변경 결정: Windows에서는 기존 POSIX 자격 증명 파일 구현을 억지로 재사용하지 않고 TYPESAFE_API_KEY를 사용한다. 모델 자동 목록 수집은 도구마다 지원이 달라 공통 CLI에 추측 구현하지 않고 스킬의 공식 도움말 기반 사전 점검으로 처리한다.

변경 결정(Claude): 사용자가 bypass 유지를 선택했다. kit은 Claude 설정을 명시 명령 `claude-setup`으로만 바꾸고 Orca 앱 설정은 읽기만 한다.

## 모델 라우팅 확장 (2026-10-30)
진행 중: 프로필별 agent/model/effort, 검증 근거, 한 번 상향 제한, 테스트 및 실제 검증.

## 모델·effort 라우팅 구현 결과 (2026-10-30)
완료: route JSON CLI, 4개 기본 프로필, 로컬 재정의, 검증된 조합만 자동 배정, effort 인코딩 구분, 한 번 상향·high 제한, 명시 선택 대체 금지. 기존 설정과 Claude readiness 기능 보존.

자동 테스트 12개 통과. 스킬 형식 검사 통과. 세 도구 설치 경로에 21개 관리 파일 갱신.
실제 검증 Run: run_9a76019419ed. light(ctx_d2e183bace44), standard(ctx_5907b11961a3), deep(ctx_9c2324619844), review(ctx_389d5ef9c02d) 모두 launch.effective 일치 및 worker_done succeeded 확인 후 회수.
로컬 model-evidence.json에 근거를 등록했으며 다른 컴퓨터로 동기화하지 않는다.

한계: 검증은 작은 읽기 작업이며 모델 성능·비용 비교가 아니다. Claude 전용 모델 프로필은 이번 기본 매핑에 포함하지 않았으며 로컬 profiles로 추가 후 검증할 수 있다. Jev는 기존 분류 보조 지침을 사용하며 이번에 API 평가를 호출하지 않았다. 상향 횟수의 이전 route JSON 및 Dispatch 종료 확인은 조정자가 관리한다. 임의 JSON 변조를 막는 별도 서버 스케줄러는 아니다. 모델 목록 자동 수집은 구현하지 않았으며 공식 CLI/로컬 캐시 조회와 실제 실행으로 확인한다. OS별 실제 실행 범위는 기존 기록을 따른다.

## 공개 전환 준비 (2026-10-30)

완료: 원본 이력 로컬 백업, 개인 경로의 과거 이력 일반화, 작성자 이메일 유지, MIT 및 코드 출처 안내 추가. 후속 실행 결과는 GitHub visibility와 CI에서 확인한다.

공개 전환 완료: GitHub API에서 visibility=public, private=false, license=MIT 확인. 공개 준비 커밋 71aac08의 CI 6개 작업(macOS/Linux/Windows, Python 3.9/3.13)이 모두 성공했다. 과거 커밋으로 연결되던 Actions 기록 4건은 삭제했다. 로컬 저장소 및 설치된 스킬도 정리된 이력으로 동기화했다.

개인 경로는 현재 main과 그 이력에서 제거했지만, GitHub가 참조되지 않는 옛 커밋 객체를 보관하는 동안에는 정확한 옛 SHA로 조회될 가능성이 있다. 서버 객체의 즉시 완전 삭제를 주장하지 않는다. 발견된 경로에는 인증정보가 포함되지 않았다.

## 초보자 시작 흐름 개선
진행 중: setup 진단, verify-profile 근거 등록, 세 도구별 시작 가이드와 README 재구성.

## Onboarding implementation completed (2026-10-30)

- Implemented setup and verify-profile, refreshed README, and added a getting-started guide for all three agents.
- 18 automated tests passed; skill validation and documentation link/JSON/code-fence checks passed.
- Real setup checks passed for Codex, Claude and AGY on macOS. Claude has no bundled model profile and receives configuration guidance.
- New Run run_3cc1edcbace3: Codex standard ctx_072b823518f8 and AGY light ctx_49dc417778ec succeeded. verify-profile registered live Orca evidence; repeated registration returned changed=false without extending completion time. Both workers were released.
- Installed skill copies were updated. New Claude model verification and other-OS agent execution remain untested in this change.
- setup writes only local observation metadata; it does not install external tools, log in, change permissions, or launch workers. Binary identity is checked using paths, size, timestamps and the pre-launch observation, not cryptographic attestation.
