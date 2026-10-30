# 처음 시작하기

목표는 **익숙한 에이전트 하나로 작은 읽기 작업을 성공시키는 것**입니다. 그 뒤 다른 도구와 모델을 추가하면 됩니다. 아래의 “일반 터미널”은 macOS Terminal, Linux 터미널 또는 Windows PowerShell을 뜻합니다.

## 1. 기본 도구와 로그인을 준비하세요

아래 공식 안내에서 운영체제에 맞는 설치 방법을 선택하세요. 설치 명령은 공급자 업데이트에 따라 달라질 수 있습니다.

| 도구 | 설치·로그인 안내 | 일반 터미널에서 확인 |
|---|---|---|
| Git | https://git-scm.com/downloads | `git --version` |
| Python 3.9+ | https://www.python.org/downloads/ | `python3 --version` / Windows: `py -3 --version` |
| Orca | https://www.onorca.dev/docs/install | `orca status --json` / Linux 기본: `orca-ide status --json` |
| Codex CLI | https://learn.chatgpt.com/docs/codex/cli | `codex --help`, `codex`를 실행하고 로그인 |
| Claude Code | https://code.claude.com/docs/en/quickstart | `claude --help`, `claude`를 실행하고 로그인 |
| AGY CLI | https://antigravity.google/docs/getting-started?tab=cli | `agy --help`, `agy`를 실행하고 로그인 |

**성공 기준:** 사용할 CLI가 실행되고 로그인 후 간단한 요청에 응답합니다. `--help` 성공만으로 로그인 완료를 판단하지 마세요. 모델 이용 가능 여부와 과금은 자신의 계정 조건을 확인하세요.

명령을 찾을 수 없다면 새 터미널을 열고 설치 위치가 PATH에 포함되어 있는지 확인합니다. macOS/Linux는 `command -v codex`처럼, PowerShell은 `Get-Command codex`처럼 확인할 수 있습니다. 설치 문제는 해당 도구의 공식 안내를 먼저 확인하세요.

Windows 네이티브와 WSL을 혼합하지 마세요. CLI·Python·인증·작업 폴더를 같은 실행 환경에 준비합니다. Orca 관리 환경에 `ORCA_CLI_COMMAND`가 제공되면 그 실행 파일을 사용합니다. Linux의 일반 터미널에서 `orca`는 다른 프로그램일 수 있으므로 기본적으로 `orca-ide`를 사용합니다.

## 2. Orca에서 프로젝트를 여세요

Orca 앱을 실행하고 **실제로 작업할 프로젝트 폴더**를 추가하세요. 키트 저장소는 스킬을 설치하는 장소이고, 작업 대상 프로젝트와 같을 필요는 없습니다.

공식 화면 안내: [Orca 설치](https://www.onorca.dev/docs/install)에서 연결되는 “Your first 3-agent session”을 참고하세요. 처음부터 작업자 세 명을 실행할 필요는 없습니다.

CLI로 등록하려면 일반 터미널에서 실제 프로젝트 경로로 바꿔 실행합니다.

```sh
orca repo add --path /absolute/path/to/your-project --json
```

Linux에서는 `orca`를 `orca-ide`로 바꾸고, Windows에서는 `--path "C:\work\your-project"`처럼 경로를 사용합니다. 프로젝트의 에이전트 탭에서 Claude·Codex·AGY 중 준비한 도구를 선택해 새 대화를 시작하세요. 앱 화면의 이름은 버전에 따라 달라질 수 있습니다.

**성공 기준:** Orca에서 대상 프로젝트와 해당 에이전트 대화가 보이고, Orca CLI 상태 조회가 연결 성공을 반환합니다. 외부의 일반 CLI 대화가 자동으로 Orca 조정자로 등록된다고 가정하지 마세요.

## 3. 키트를 설치하고 환경을 확인하세요

**일반 터미널 → 키트 저장소 디렉토리**에서 실행합니다.

```sh
git clone https://github.com/HashCitrine/orca-orchestration-kit.git
cd orca-orchestration-kit
python3 kit.py install
```

Windows PowerShell에서는 `python3` 대신 `py -3`를 사용하세요. 설치는 스킬 파일을 복사하며 외부 도구 설치나 로그인은 하지 않습니다.

| 처음 사용할 에이전트 | 진단 명령 | 첫 프로필 |
|---|---|---|
| Codex | `python3 kit.py setup --agent codex` | standard를 먼저 검증 |
| Claude | `python3 kit.py setup --agent claude` | 지원 모델·effort로 로컬 프로필 추가 후 검증 |
| AGY | `python3 kit.py setup --agent agy` | light를 먼저 검증 |

`setup`은 Git, Orca 연결, 선택한 CLI, 설치된 스킬과 프로필 상태를 알려주고 다음 단계와 복사할 요청문을 출력합니다. `--json`으로 기계 판독용 결과를 받을 수 있습니다. 외부 프로그램을 설치하거나 에이전트를 시작하지는 않지만, 나중에 실행 파일을 대조할 수 있도록 로컬 `setup-observation.json`을 기록합니다.

## 4. 첫 모델을 검증하고 작업을 시작하세요

**Orca 안의 대상 프로젝트에서 새 에이전트 대화**를 시작한 뒤, `setup`이 출력한 요청문을 붙여 넣으세요.

```mermaid
flowchart LR
    A[setup: 환경과 실행 파일 확인] --> B[에이전트: 작은 읽기 작업 실행]
    B --> C[Orca: 성공한 완료 보고]
    C --> D[verify-profile: 실제 설정 대조·등록]
    D --> E[조정자: 메시지 처리·작업자 회수]
    E --> F[첫 사용자 작업]
```

예를 들어 Codex에서는 다음처럼 요청합니다.

> “orca-team으로 standard 프로필을 검증해줘. setup 이후 읽기 전용 작업을 실행하고, 성공한 Dispatch를 verify-profile로 등록한 다음 작업자 회수까지 확인해줘.”

AGY는 같은 요청에서 `standard`를 `light`로 바꿉니다. Claude는 먼저 “현재 계정에서 지원하는 모델과 effort로 Claude용 로컬 프로필을 구성해줘. 기본 프로필과 작업 유형 연결은 임의로 바꾸지 말아줘”라고 요청하세요. 공급자 모델 ID를 모르는 상태에서 예시 이름을 추측해 넣지 않습니다.

조정자가 실행할 등록 명령은 다음과 같습니다. 직접 실행할 때도 **실제로 완료된 Dispatch ID**로 바꿔야 합니다.

```sh
python3 kit.py verify-profile --profile standard --dispatch <completed-dispatch-id>
```

설치된 스킬에서 호출할 때는 에이전트가 그 스킬의 `scripts/kit.py` 경로를 사용합니다. 이 명령은 Orca를 직접 조회해 성공 상태, 로컬 실행, 실제 도구·모델·effort, setup 당시 실행 파일과의 일치를 확인합니다. 오래된 작업이나 미확인 조합은 등록하지 않습니다.

**성공 기준:** 등록 결과가 `verified`이고 다음 명령이 해당 프로필에 `ready`를 반환합니다. 완료 메시지 처리와 작업자 회수는 조정자가 별도로 마칩니다.

```sh
python3 kit.py route --task-type implementation --profile standard
```

AGY·Claude는 `--profile`에 검증한 프로필 이름을 사용하세요. 일반 작업 유형 연결을 바꾸려면 로컬 `routes`를 명시적으로 수정합니다. 모델별로 유효한 검증이 필요하므로 하나를 검증했다고 모든 프로필이 준비되는 것은 아닙니다.

## 5. 설정과 문제 해결

로컬 설정: `~/.config/orca-orchestration-kit/config.json`. 저장소의 `config.example.json`을 참고하되 기존 설정은 덮어쓰지 마세요. [프로필 운영](ROUTING.md)에 옵션과 예제가 연결되어 있습니다.

| 상태·증상 | 다음 행동 |
|---|---|
| 명령을 찾을 수 없음 | 설치와 PATH를 확인하고 새 터미널을 여세요. |
| Orca 연결 실패 | 앱을 실행하고 같은 OS/WSL 환경의 CLI인지 확인하세요. |
| 스킬 미설치 | 키트 디렉토리에서 install 후 새 에이전트 대화를 여세요. |
| 프로필 없음 | 해당 도구에서 확인된 모델·effort로 로컬 프로필을 추가하세요. |
| route가 blocked | setup 후 작은 검증 작업을 실행하고 verify-profile을 사용하세요. |
| setup 기록이 작업보다 늦음 | 작업을 다시 수행하기 전 setup을 실행하세요. 이전 작업의 시간을 바꾸지 마세요. |
| 모델·effort 불일치 | 실제 launch 설정과 프로필을 확인하세요. 증거를 직접 수정하지 마세요. |
| 작업자가 응답하지 않음 | 조정자가 Orca 상태를 확인하게 하세요. 중복 실행하지 마세요. |
| 업데이트 충돌 | 사용자가 수정한 설치 파일을 보관·비교한 뒤 갱신하세요. |

### Claude 권한 모드

`python3 kit.py doctor`의 `claude_worker`가 `needs_claude_setup`이면 Orca에 설정된 권한 우회 모드의 최초 확인이 필요할 수 있습니다. 권한 우회를 사용하기로 결정한 경우에만 `python3 kit.py claude-setup`을 실행합니다. 이 명령은 Claude 설정을 백업한 뒤 최초 확인 설정을 추가합니다. 권한 우회를 원하지 않으면 Orca의 Claude 실행 설정을 원하는 모드로 바꾸세요. setup/install/update는 권한 설정을 자동 변경하지 않습니다.

### 업데이트·제거

키트 저장소에서 `git pull --ff-only` 후 `python3 kit.py update`를 실행하고 새 대화를 여세요. 제거는 `python3 kit.py uninstall`입니다. 로그인과 로컬 검증 기록은 삭제하지 않습니다. 다른 컴퓨터에서는 각 도구의 설치·로그인·검증을 다시 수행하며 키나 검증 파일을 복사하지 않습니다.

### Jev는 나중에 추가해도 됩니다

처음에는 Jev 없이 진행하세요. 필요해지면 [Jev 설정 안내](../skills/orca-team/references/jev.md)에 따라 별도로 인증합니다. API 호출 전 전송할 발췌를 알려주며, 실패 시 일반 도구로 계속 진행합니다.

## 선택 사항: 사용량에 맞춰 배정하기

첫 프로필 검증 이후 `python3 kit.py usage refresh --agent codex`와 `python3 kit.py usage show`로 현재 조회 상태를 확인하세요. 전환할 대안은 [사용량 안내](USAGE.md)에 따라 로컬 설정에 추가합니다. 다른 도구의 사용량을 모른다면 그대로 미확인으로 두세요.
