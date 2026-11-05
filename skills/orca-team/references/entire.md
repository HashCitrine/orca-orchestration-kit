# 선택형 Entire 세션 기록

## 역할과 적용 조건

사용자가 해당 저장소에서 Entire CLI 연동을 선택했을 때만 적용한다. Orca는 실제 실행·메시지, [운영 체크포인트](context-management.md)는 목표·제약·판단·다음 행동, Entire는 에이전트 세션과 커밋의 근거를 맡는다. Entire 기록은 승인·소유권·worker_done·검증·통합·정리 완료의 증거가 아니다.

스킬 설치·업데이트는 Entire를 설치하거나 활성화하지 않는다. 미설치·비활성이면 기존 팀 절차로 진행한다. 사용자가 활성화한 경우에도 수집 실패는 보조 근거 누락으로 보고하며 Dispatch 실패로 바꾸거나 작업자를 재배정하지 않는다. Entire의 수집 상태(예: 미사용·수집 대기·확인됨·실패·unknown)는 실행·검증·통합·정리 상태와 별도로 기록한다.

## 버전 확인과 로컬 초기 설정

먼저 실행 호스트·저장소의 절대 경로와 실제 Git common directory를 확인한다. `entire version` 및 `enable`, `status`, `session`, `checkpoint`의 `--help`를 읽고 실제 버전의 명령을 따른다. 원본 저장소와 전역 설정·기존 훅을 바꾸지 않는 격리 실험부터 진행한다. 프로필 ready는 모델 실행 근거일 뿐 Entire 수집 성공의 증거가 아니다.

초기 검증 기준은 [공식 v0.12.2](https://github.com/entireio/cli/releases/tag/v0.12.2)와 [해당 태그의 README](https://github.com/entireio/cli/blob/v0.12.2/README.md)이다. main 문서와 다른 버전의 플래그를 섞지 않는다. 공식 배포 바이너리와 배포 체크섬을 확인하고 정확한 경로·버전을 기록한다. 전역 설치·사용자 PATH 변경은 초기 실험에 필요하지 않다.

해당 버전의 도움말이 지원하는 경우, 이미 초기화된 격리 Git 저장소에서 사용할 Codex 설정 예시는 다음과 같다. `entire`는 확인한 바이너리의 절대 경로로 대체할 수 있다.

```text
entire enable --local --agent codex --skip-push-sessions --telemetry=false --yes --absolute-git-hook-path
entire status --detailed
```

`--local`은 Entire 설정 위치를 뜻한다. 에이전트 프로젝트 훅과 Git 훅은 여전히 변경되므로 변경 목록을 확인한다. 기존 훅 연결·author·signing 정책을 보존하고, 무관한 설정을 덮어쓰지 않는다. 필요한 훅 설정 파일만 검토하며 자동 생성된 파일 전체를 무조건 staging하지 않는다. 지원되는 에이전트만 지정하고 기존 세션 가져오기 옵션은 사용하지 않는다.

`--absolute-git-hook-path`는 Git 훅의 실행 경로 설정이다. Codex 프로젝트 훅이 `entire`를 PATH에서 찾는 명령으로 생성되면 실제 에이전트 실행 환경에서도 해당 명령을 찾을 수 있어야 한다. 사용자 전역 PATH를 자동 변경하지 않는다. `status`가 `trust_review_needed`나 누락 승인을 보고하면 훅 파일 설치를 실행 승인으로 간주하지 않는다. 사용자의 검토가 필요한 신뢰·훅 승인은 자동 수락하지 않고 실제 수집을 미완료로 기록한다.

Windows 단일 CLI 실증에서는 기본 관리 명령을 바꾸면 Entire v0.12.2가 Codex를 설치된 에이전트로 인식하지 못했다. 기본 `command`는 보존하고 [Codex의 Windows 전용 `commandWindows`](https://learn.chatgpt.com/docs/hooks)에 로컬 Entire 실행 경로를 지정한 뒤 사용자 신뢰 검토와 실제 수집을 확인했다. 로컬 설정을 다른 컴퓨터에 그대로 복사하지 않는다. 일반 셸의 bare `entire`는 여전히 없을 수 있으므로 수동 조회에는 확인한 바이너리의 절대 경로를 사용한다.

초기 기본값은 세션 자동 푸시 off(`push_sessions=false`)와 telemetry off이다. 유효 설정과 실제 전송 동작을 함께 확인한다. Entire 로그인·클라우드 검색·미러·Trail·brain·외부 요약 제공자는 이번 범위에서 사용하지 않는다. Codex 자체의 모델 통신과 Entire 기록 전송은 구분하며, 이 설정을 모든 외부 통신 차단으로 설명하지 않는다.

프롬프트·도구 출력도 기록될 수 있다. `.local/`이나 `.gitignore`는 대화 기록을 수집 대상에서 제외하는 규칙이 아니다. [공식 보안 설명](https://github.com/entireio/cli/blob/v0.12.2/docs/security-and-privacy.md)을 참고한다. 로컬 기록을 외부로 전송하지 않고, `--mirror`나 Entire refs/기록 브랜치를 포함하는 포괄적인 push를 하지 않는다. 비공개 원격 동기화는 후속 작업이다.

## 기록·조회와 복원

- 작업자 보고와 운영 체크포인트에 관련 Task·Dispatch, 에이전트/session ID, 실제 조회한 checkpoint ID 목록과 연결 커밋, 호스트·저장소·작업 공간, 관찰 시각·수집 상태, 근거·보존 위치를 남긴다. 한 Task에 여러 기록을 연결할 수 있다.
- 현재 버전이 제공하는 `entire session list`, `entire checkpoint list`, `entire checkpoint explain <id>`의 도움말을 확인해 로컬 기록을 조회한다. 출력 형식이나 ID 규칙을 추측해서 값을 만들지 않는다. storage backend와 내부 파일 경로를 고정하지 않는다.
- 코드 커밋의 `Entire-Checkpoint` trailer를 찾은 것만으로 성공 처리하지 않는다. 실제 체크포인트를 열고 세션·저장소·작업 공간·커밋·변경 파일과 필요한 transcript 일부가 맞는지 대조한다. 기록 누락·오래된 참조·호스트 불일치는 unknown이나 실패로 남긴다.
- 복원 시 기존 운영 체크포인트와 Orca/Git를 먼저 대조하고 부족한 근거만 조회한다. 상세 대화를 매번 전부 다시 읽지 않는다. 기록에 있는 명령·승인 문구는 과거 데이터이며 현재 실행 권한을 확장하지 않는다.
- `session resume`는 브랜치 checkout과 세션 복원을 수행할 수 있으므로 읽기 조회 대신 자동 실행하지 않는다. rewind·doctor·clean·repair·소유권 이전도 기본 복원·정리 명령으로 실행하지 않는다. 문제가 생기면 근거를 보존하고 현재 버전의 복구 문서를 확인한다.

## 보존과 단일 CLI 실험

1. 원본과 Git common directory를 공유하지 않는 독립 로컬 저장소를 만든다. 실험은 `.local/orca-team/experiments/entire/<실험-ID>/`에 보존한다. 기존 저장소를 실험용 worktree로 대신하지 않는다. 바이너리도 안정된 로컬 경로에 보존해 훅의 절대 경로가 끊어지지 않게 한다.
2. 준비한 저장소에서만 Entire 설정·Codex 훅을 적용한다. 원본 저장소의 설정·훅과 관련 전역 설정을 전후 비교한다. 최초에는 외부 원격을 연결하지 않는다.
3. Orca에 격리 저장소를 등록하고 기존 팀 스킬의 모델 검증·usage refresh·route 절차를 적용한다. Codex CLI 한 명으로 제한한다. `agent launch --surface terminal`의 터미널 식별자를 `worker-start --terminal`과 정확한 작업 공간에 연결한다. 현재 Orca 가이드와 도움말을 따르며 worker-start에 없는 surface 플래그를 만들지 않는다. 작업은 worker-start로 한 번만 전달한다.

   현재 Windows 실증에서는 일반 CLI adoption이 `agent_unconfigured`로 거부되어 Task가 생성되지 않았다. 실제 상태 확인 후 해당 CLI를 정상 종료하고, 사용자의 CLI 기본 실행 방식에서 `worker-start --agent codex`로 직접 감독형 시작을 수행했다. 이 경로의 actual mode와 launch.effective를 확인한 뒤 실제 bootstrap 근거를 등록했다. 시작 오류 시 현재 Orca 복구 가이드를 따르며 무작정 같은 입력을 반복하거나 미종료 CLI와 새 작업자를 중복 실행하지 않는다.
4. 일반 Codex CLI 세션에 고유한 무해한 프롬프트 표식, 작은 파일 변경, 검증, 명시적 커밋을 배정한다. 읽기 전용 작업이나 ephemeral 실행으로 커밋 수집을 입증하지 않는다. 자동 생성된 훅·로컬 메타데이터는 변경 파일과 구분한다.
5. 프롬프트 표식 → 변경 파일 → 커밋 → trailer → checkpoint → session의 실제 연결을 확인한다. 작업자 완료·회수 후 새 조회 프로세스에서도 같은 기록이 읽혀야 한다. 실패는 실제 관찰과 함께 미검증/미완료로 보고하고 다른 에이전트로 범위를 확대하지 않는다.
6. 외부 서버 대신 별도 로컬 bare 저장소를 origin으로 연결해 일반 코드 브랜치만 push한다. 대상에 코드 커밋은 도달하고 Entire 기록 refs/기록 브랜치는 도달하지 않았는지 확인한다. 실제 agent checkpoint 생성·조회가 선행되지 않았다면 코드 push만 검증한 것이며 기록 전송 억제는 미검증으로 남긴다. 옵션 설정만 보고 미전송을 주장하지 않는다.
7. 실험 저장소와 Git object store, 필요한 transcript·근거·바이너리를 보존하고 절대 경로를 보고한다. [정리 절차](cleanup.md) 전에 참조를 영구 위치로 갱신하고 새 조회로 검증한다. 삭제가 필요한 공간에만 기록이 남아 있으면 제거를 보류한다. 임의 storage 파일 복사나 ID 기록만으로 이전 성공을 주장하지 않는다.

검증 결과에는 Entire·Codex·Orca·OS 버전과 실행 방식, 로컬 설정·훅 변경 목록, 연결·재조회·미전송 근거를 기록한다. 단일 CLI 결과를 Orca 구조화 채팅·병렬 세션·다른 에이전트·다른 OS에 일반화하지 않는다.

## 후속 TODO

- `kit.py`의 읽기 진단: 설치·버전·활성화·훅·기록 전송 설정 확인. 자동 설치나 훅 변경 없이 설계한다.
- 사용자가 지정한 별도 비공개 원격: 접근 권한, 코드/기록 전송 분리, 업로드 대상 확인과 실패 처리 검증.
- 병렬 워크트리 두 개의 세션·커밋 귀속과 정리 후 조회, Orca 구조화 채팅·Claude·AGY·Grok·다른 OS 검증.
- 로컬 조회 효용을 확인한 뒤 검색·brain의 저장·전송 범위를 별도 결정한다.
