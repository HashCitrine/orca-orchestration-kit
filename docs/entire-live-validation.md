# Entire live capture validation

- 고유 표식: `ENTIRE-LIVE-20261105-ORCA-01`
- 환경: Entire `0.12.2`, Codex CLI `0.166.0`, Orca `1.4.248`.
- 조정자가 확인한 사전 준비: 로컬 보관, checkpoint push disabled, telemetry false 및 Codex 훅 사용자 검토 완료.
- native Codex 실행 경로로 setup 및 사용량 조회가 정상화되었으며, bootstrap `ctx_b7d8a53dc33b` 성공과 `standard` 프로필 등록이 완료되었다.

이 문서의 최초 커밋은 실제 Entire 세션 수집 연결을 검사하기 위한 것이다.
checkpoint 조회, 세션 종료 후 재조회, 전송 억제 및 CI는 조정자가 아직 확인해야 한다.
이 커밋만으로 실제 수집이나 후속 검증의 성공을 선언하지 않는다.
