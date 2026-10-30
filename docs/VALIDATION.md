# 검증 결과

2026-10-30 / macOS / Orca 1.4.244

## 자동 테스트
`python3 -m unittest discover -s tests -v`: 4개 통과.
- macOS/Windows/Linux와 ORCA_CLI_COMMAND·개발 환경 선택.
- 공백·한글 임시 경로에서 설치, 반복 설치, 갱신, 제거.
- 사용자 변경 파일 및 추가 파일 보존, 소유하지 않은 파일 덮어쓰기 거부.
- 기능 캐시 재사용, 도구 지문·명시 모델 설정 변경과 CLI 부재 감지.

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

## 제한
- 각 도구의 새 대화에서 전역 스킬 자동 발견은 별도 확인이 필요하다. 작업자는 저장소의 스킬을 명시 경로로 읽었다.
- Claude의 정상 작업 수행, 세 에이전트 각각의 조정자 역할, blocking ask/reply 왕복은 미검증이다.
- Linux/Windows/WSL 실제 실행과 GitHub Actions는 아직 실행하지 않았다. CI 설정 제공은 성공 증거가 아니다.
- Jev 실제 HTTP 평가와 모델 삭제/옵션 변경에 따른 공급자 오류는 미검증이다. 기존 공식 실행기 및 실패 시 일반 도구 전환 지침을 제공한다.
- TypeSafe 공식 API 문서 웹 조회가 실패하여 기존 설치된 실행기를 재사용했다. 응답 계약을 새로 추측하지 않았다.
- max_workers와 재시도 방지는 에이전트 운영 지침이다. 별도 강제 스케줄러를 구현하지 않았다.
