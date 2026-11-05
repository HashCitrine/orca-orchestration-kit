# Entire live capture validation

- 고유 표식: `ENTIRE-LIVE-20261105-ORCA-01`
- 환경: Entire `0.12.2`, Codex CLI `0.166.0`, Orca `1.4.248`.
- 조정자가 확인한 사전 준비: 로컬 보관, checkpoint push disabled, telemetry false 및 Codex 훅 사용자 검토 완료.
- native Codex 실행 경로로 setup 및 사용량 조회가 정상화되었으며, bootstrap `ctx_b7d8a53dc33b` 성공과 `standard` 프로필 등록이 완료되었다.

## 실제 관찰 결과

이 문서의 최초 커밋은 실제 세션 수집 연결을 검사하기 위해 작업자가 정상 Git 훅을 통해 생성했다. 아래 결과는 이후 조정자가 저장된 기록과 실제 Git 상태를 대조한 것이다.

| 검증 | 관찰 결과 |
|---|---|
| 코드 커밋 | `0c1d2a7fb430756630a5ba7bfc0ad1e340109cf4`; 변경 파일은 이 문서 하나 |
| Entire checkpoint | `01M6N3NQNYKXKDGTFBXQ7SPSAE`; 실제 커밋 trailer와 로컬 조회 일치 |
| 저장된 session | `01a1aa35-d873-71d2-9d04-454e6e8c2b3e`, Codex / gpt-6.1-sol |
| 귀속 | `test/entire-live-validation`, `files_touched`에 이 문서 하나; 저장된 transcript에 고유 표식과 대상 파일 확인 |
| 작업 완료 | bootstrap `ctx_b7d8a53dc33b`, 후속 `ctx_fc245ac5a175` 모두 succeeded |
| 작업자 회수 후 조회 | worker-show의 exited/released 및 release의 already_released 확인 후 새 Entire 프로세스로 동일 기록 재조회 성공 |
| 로컬 코드 푸시 | 실제 checkpoint가 존재하는 상태에서 origin의 pushurl을 해당 명령에만 로컬 bare 저장소로 지정; 코드 커밋 도달 확인 |
| 기록 전송 억제 | 대상 refs는 실증 코드 브랜치 하나이며 Entire checkpoint refs/기록 브랜치는 없음; 원본 Git config 해시 유지 |
| 호환성 수정 | 프로필 등록기가 `worker-show --full`을 요청하도록 수정; 실제 bootstrap 등록 성공 및 회귀 테스트 포함 전체 58개 통과 |

초기 CLI의 감독형 연결은 `agent_unconfigured`로 거부되어 Task가 생성되지 않았다. 해당 CLI의 정상 종료를 확인한 뒤 Orca의 감독형 시작 경로로 교체했다. Codex는 한 번에 한 작업자만 실행했으며, 성공한 후속 작업은 Dispatch 주소로 전달했다.

Git 훅은 절대 경로를 사용한다. Codex 훅은 Entire가 관리하는 기본 명령을 보존하고 Windows 전용 `commandWindows`에서 로컬 Entire 바이너리를 실행한다. 사용자가 최종 훅 정의를 검토·신뢰했으며 전역 PATH는 변경하지 않았다. Bare `entire`는 일반 셸 PATH에 없으므로 수동 조회에는 로컬 바이너리의 절대 경로를 사용한다.

## 보관과 적용 범위

체크포인트와 transcript, 원복용 백업 및 검사 결과는 로컬에만 보존한다. 로컬 근거 위치는 `.local/orca-team/experiments/entire/live-project-20261105/`이며 운영 체크포인트는 `.local/orca-team/runs/run_f688275c180e/checkpoint.md`이다. 원문 대화나 인증·capability 값은 이 문서에 복사하지 않았다.

성공한 로컬 Entire 활성화와 세션 전송 off 설정을 유지한다. GitHub에는 실증 코드 브랜치만 푸시하고 기록 refs의 부재를 별도로 확인한다. 해당 HEAD의 CI 결과는 GitHub Actions 실행으로 확인하며, 실증 브랜치를 main에 자동 병합하지 않는다.

이번 결과는 Windows의 단일 Orca Codex CLI 세션 수집·커밋 연결·회수 후 조회·전송 억제에 한정된다. 실제 컨텍스트 압축/세션 resume, 병렬 세션, 다른 에이전트·OS, 비공개 기록 원격 동기화와 brain은 검증하지 않았다.
