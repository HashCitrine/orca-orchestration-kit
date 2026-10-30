# Orca orchestration kit

Claude·agy·Codex 개인 공통 팀 운영 스킬. 시작한 에이전트가 조정하고 최대 2명의 작업자를 사용합니다. 모델을 고정하지 않습니다.

## 설치
Python 3.9+와 Orca 및 사용할 에이전트 CLI를 먼저 설치·로그인합니다. 이 저장소를 복사하거나 Git clone한 뒤:

```sh
python3 kit.py install
python3 kit.py doctor
```
Windows에서는 `py -3 kit.py install`과 `py -3 kit.py doctor`를 사용합니다. WSL에서는 WSL의 Python과 Orca 환경을 사용합니다.

새 에이전트 대화에서 “orca-team 스킬로 이 작업을 팀으로 처리해줘”라고 요청합니다. 명시 요청 없이 작업자를 자동 실행하지 않습니다. 스킬 설치 후 기존 대화에 즉시 반영된다고 가정하지 않습니다.

## Claude 작업자 준비
Orca 기본 설정은 Claude를 `--dangerously-skip-permissions`로 실행합니다. Claude 설정에 이 모드를 허용한 기록이 없으면 첫 실행 확인 화면에서 멈춰 작업자 readiness가 실패합니다. `python3 kit.py doctor`의 `claude_worker`가 상태를 알려줍니다.
- `ready`: 준비 완료.
- `needs_claude_setup`: `python3 kit.py claude-setup`을 실행합니다. Claude 설정 파일(`CLAUDE_CONFIG_DIR` 또는 `~/.claude/settings.json`)을 백업한 뒤 `skipDangerousModePermissionPrompt: true`만 추가하고 다른 키는 보존합니다. install/update/uninstall은 이 파일을 건드리지 않습니다. 되돌리려면 그 키를 삭제하거나 백업을 복원합니다.
- `unknown`: Orca 설정을 찾지 못했습니다. 작은 작업으로 먼저 확인합니다.

bypass를 원하지 않으면 Orca 설정의 에이전트 기본 인자에서 Claude 값을 `--permission-mode auto` 등으로 바꿉니다. kit은 Orca 앱 설정을 수정하지 않습니다. 이 경우 허용되지 않은 명령에서 작업자가 확인 대기로 멈출 수 있습니다.

## 업데이트·제거
패키지를 Git pull 또는 복사로 갱신한 뒤 `python3 kit.py update`를 실행합니다. `python3 kit.py uninstall`은 설치 당시 해시와 일치하는 관리 파일만 제거합니다. 사용자 수정과 추가 파일은 보존합니다. 충돌 시 파일을 별도로 보존·비교한 뒤 다시 실행합니다.

`config.example.json`을 `~/.config/orca-orchestration-kit/config.json`으로 복사해 필요한 항목만 변경합니다. executables/skill_roots/models/efforts의 키는 codex, claude, agy이며 executables는 orca도 지원합니다. 경로 재정의는 실행 파일 한 개의 경로이며 셸 명령이 아닙니다. max_workers는 1 또는 2입니다.

doctor는 경로와 CLI help의 지문을 캐시해 변경을 감지합니다. 모델 조회/실제 실행 가능 여부는 스킬의 실행 전 점검으로 확인합니다. doctor 성공만으로 인증이나 모델 가용성을 보장하지 않습니다.

Jev는 POSIX에서 `python3 skills/orca-team/scripts/jev.py configure`로 숨김 입력을 사용합니다. Windows는 TYPESAFE_API_KEY 환경변수를 사용합니다. 인증정보는 복사하거나 Git에 넣지 않습니다.

## 문서
- [계획](docs/PLAN.md)
- [진행](docs/PROGRESS.md)
- [검증](docs/VALIDATION.md)

실제 런타임과 모델은 컴퓨터마다 다를 수 있습니다. 원격 분배와 자동 업데이트는 포함하지 않습니다.

## 작업별 모델·effort 라우팅
`python3 kit.py route --task-type implementation`으로 실행 없이 선택 결과를 확인합니다. simple/implementation/test/design/debug/review를 지원하며 복잡한 작업에는 `--complexity complex`를 사용합니다. 조정자는 ready 결과의 launch_args만 새 Orca 작업자에 전달합니다.

[프로필·검증·상향 운영 안내](docs/ROUTING.md)를 참고하세요. 기존 기본 모델 상속은 비라우팅 실행에만 적용되며, orca-team 분배는 이제 검증된 프로필을 우선 사용합니다. 새 컴퓨터에서는 모델 검증 근거를 복사하지 않고 작은 작업부터 검증합니다.
