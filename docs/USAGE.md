# 남은 사용량에 따라 작업 배정하기

사용량은 정확한 비용 예측이 아니라 **다음 작업자 배정의 여유 판단**에 사용합니다. 실행 중인 작업이나 조정자의 모델은 바꾸지 않습니다.

| 도구 | 이번 버전의 조회 |
|---|---|
| Codex | 공식 App Server account/read 및 account/rateLimits/read로 자동 조회 |
| Claude | Orca `account list --json`의 rateLimits로 자동 조회(5시간·주간). claude.ai Pro/Max 로그인에서만 값이 있음 |
| AGY | Orca `account list --json`의 rateLimits로 자동 조회(모델 그룹별 5시간·주간) |

Claude·AGY 값은 Orca가 작업자를 실행하는 활성 계정 기준으로 Orca가 주기적으로 갱신한 집계입니다. 기록 시각은 조회 시각이 아니라 Orca의 갱신 시각(updatedAt)이므로, Orca가 5분 넘게 갱신하지 못하면 미확인으로 처리됩니다. Orca가 상태 오류를 보고하면 해당 도구의 이전 관찰을 배정에 쓰지 않습니다. 수동 입력은 대체 수단으로 남아 있으며 같은 창의 유효한 자동 결과가 우선합니다.

```sh
python3 kit.py usage refresh              # codex, claude, agy 모두
python3 kit.py usage refresh --agent agy  # 하나만
python3 kit.py usage show
python3 kit.py usage show --json
python3 kit.py route --task-type design
```

조정자는 새 작업자 배정 직전에 refresh를 호출합니다. route는 최근 로컬 기록만 읽고 네트워크 호출을 하지 않습니다. 기본 5분이 지난 기록, 리셋 시각이 지난 기록은 미확인으로 처리합니다. 리셋 예정 시각이 지났다고 잔여량을 100%로 바꾸지 않습니다.

## 선택 기준

- 모든 관련 한도 잔여량이 20% 초과: 기존 프로필 유지.
- 하나라도 20% 이하: 품질 적합 대안 목록에서 여유가 확인된 별도 한도의 검증 프로필을 우선.
- 하나라도 5% 이하: 적절한 대안이 없으면 blocked. 새 작업자를 시작하지 않음.
- 미확인: 여유 있다고 추정하지 않고 기존 정책 유지. 이미 확인된 보호 구간은 다른 창이 미확인이어도 유지.

예를 들어 Codex 주간 잔여량이 10%이고 AGY의 해당 모델 한도가 충분하다면, design의 대안으로 review가 등록·검증되어 있을 때 그 프로필을 선택할 수 있습니다. AGY가 미확인이면 여유가 있다고 판단하지 않습니다. 같은 계정·그룹을 공유하면 모델 이름만 바꿔 한도를 피할 수 있다고 보지 않습니다.

## 대안 설정

기본은 **자동으로 다른 모델을 품질 동등하다고 가정하지 않는 것**입니다. 잔여량 경고와 5% 보호는 즉시 적용되지만, 자동 전환하려면 로컬 config.json의 usage.alternatives에 작업별로 허용할 프로필을 지정하세요. config.example.json은 시작점이며 자신의 작업 품질 요구에 맞게 선택합니다.

```json
{
  "usage": {
    "enabled": true,
    "ttl_seconds": 300,
    "conserve_percent": 20,
    "protect_percent": 5,
    "alternatives": {"design": ["review"], "review": ["deep"]}
  }
}
```

각 대안은 기존 모델 검증을 통과해야 합니다. 단순 작업 외에는 현재 구현이 같거나 높은 effort의 대안만 자동 허용하며 모델 간 품질 동등성을 증명하는 것은 아닙니다. 목록은 사용자가 품질 적합성을 정한 정책입니다. 더 낮은 effort나 다른 모델을 쓰려면 검증한 프로필을 준비하고 단순 작업의 대안으로 연결하세요. 알려진 한도를 공유하는 프로필끼리의 전환은 여유 확보로 인정하지 않습니다.

현재 요청으로 모델/프로필을 명시했다면 자동으로 바꾸지 않습니다. 사용량 때문에 보호된 경우 대안이나 리셋을 안내합니다. 크레딧 구매·리셋 크레딧 소비·로그인 계정 전환은 수행하지 않습니다.

## 수동 입력

계정 별칭에는 이메일 대신 본인만 알아볼 수 있는 비개인 식별자를 사용하세요. 해당 모델 한도 그룹의 이름과 프로필의 quota_groups를 일치시킵니다. 전체 계정에 적용되는 한도는 예약 그룹 account로 입력합니다. 모든 모델에 공통인 한도인지 확인되지 않았다면 account로 입력하지 마세요.

```sh
python3 kit.py usage set --agent agy --account personal-a --group model-pool-a --remaining 35 --window-minutes 300 --resets-at 1900000000
```

위 reset 값은 형식 예시입니다. 실제 화면의 리셋 시간을 Unix 초로 바꿔 입력하세요. 주간은 별도 관찰로 `--window-minutes 10080`을 입력합니다. 프로필 전체 정의에 `"quota_groups": ["model-pool-a"]`를 추가합니다. Codex 기본 그룹은 codex이며 다른 도구는 모델 그룹을 추측하지 않습니다.

수동 입력은 해당 도구의 활성 계정 별칭을 선택합니다. 같은 계정·그룹·기간의 최신 자동 조회가 있으면 유효한 자동 결과가 우선합니다. 자동 조회 실패 시 계정 변경 여부를 확인할 수 없으므로 이전 Codex 계정 관찰을 배정에 사용하지 않습니다. 새로운 수동 입력으로 다시 활성화할 수 있습니다.

## AGY 모델 그룹

AGY는 모델 그룹마다 한도가 따로 있습니다. 실제 그룹 이름은 `usage refresh` 결과에 표시됩니다(예: `Gemini Models`, `Claude and GPT models`, `Gemini 4 Argon`). kit은 모델 이름으로 그룹을 추측하지 않으므로 AGY 프로필에는 `quota_groups`를 지정해야 합니다. 기본 프로필은 다음과 같습니다.

| 프로필 | 모델 | quota_groups |
|---|---|---|
| light | gemini-3.8-flash-low | `Gemini Models` |
| review | gemini-4-argon-high | `Gemini Models`, `Gemini 4 Argon` |

Argon 한도는 플랜에 따라 별도이거나 Gemini 한도에 포함된다고 안내되므로, review는 두 그룹 중 낮은 잔여량을 사용합니다. AGY에서 Claude·GPT 계열 모델을 쓰는 프로필은 `Claude and GPT models`를 지정하세요. Claude 프로필의 기본 그룹은 `claude`이며, Orca가 Fable 주간 한도를 보고하면 `claude-fable` 그룹으로 기록됩니다.

## 데이터와 한계

usage.json은 로컬 설정 디렉토리에만 저장합니다. Codex 계정 식별자는 해시로, Claude·AGY는 Orca 활성 계정 라벨(예: `orca:system:host`)로 저장하고 이메일·토큰을 출력하거나 저장하지 않습니다. 수동 관찰도 다른 컴퓨터에 복사하지 마세요. 공급자가 보고한 실제 기간만 표시하며 5시간·주간 창이 모두 있다고 가정하지 않습니다.

한도 값은 실행 중에도 바뀔 수 있습니다. 두 번째 작업자 배정 전에도 갱신하지만 작업 비용 예약이나 한도 소진 방지를 보장하지 않습니다. low effort의 절약률이나 서로 다른 모델의 토큰 비용을 추정하지 않습니다. 사용량 계산은 일반 코드로 처리하고 계정·사용량을 Jev로 보내지 않습니다.
