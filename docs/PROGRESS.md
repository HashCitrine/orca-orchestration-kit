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
