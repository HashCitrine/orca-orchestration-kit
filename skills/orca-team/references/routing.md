# 작업별 모델과 effort

`python3 kit.py route --task-type implementation`은 실행하지 않고 JSON 선택 결과를 반환한다. status=ready일 때만 launch_args를 새 Orca worker-start에 전달한다. blocked이면 실행하지 않는다.

| 작업 | 프로필 | 초기 후보 | effort |
|---|---|---|---|
| simple | light | agy / gemini-3.8-flash-low | low (ID 내장) |
| implementation, test | standard | codex / gpt-6.1-sol | medium |
| design, debug 또는 complex | deep | codex / gpt-6-astra | high |
| review | review | agy / gemini-4-argon-high | high (ID 내장) |

이는 성능 벤치마크 순위가 아닌 초기 균형형 운영 정책이다. 구독 잔여량·요금은 추정하지 않는다. 모델은 새로 실행할 때 공급자에서 거부될 수 있다.

로컬 config.json의 profiles는 이름별 전체 프로필을 교체한다. routes는 작업 유형별 프로필을 재정의한다. 기존 models/efforts는 비라우팅 경로에서만 사용한다. 현재 요청의 --profile/--agent/--model/--effort가 가장 우선이며 명시 선택에는 자동 대체하지 않는다.

검증 근거는 로컬 model-evidence.json에 조합별로 보관한다. key는 agent|model|effort|effort_mode, 값은 verified_at(UTC ISO), identity(실행 파일 path/mtime_ns/size), dispatch_id, source, actual_model이다. 현재 컴퓨터에서 작은 작업의 accepted worker_done과 launch 영수증을 확인한 조정자만 등록한다. 7일 경과 또는 실행 파일 변경 시 재검증하며 다른 컴퓨터로 복사하지 않는다. 캐시·목록에 있다는 사실만으로 검증 근거를 만들지 않는다.

Jev는 유형/난이도 분류만 보조한다. 실패하면 조정자가 동일 기준으로 분류한다. 고정 모델 성능 순위를 추측하지 않는다.

상향: 이전 route JSON을 --prior로 전달하고 --failure quality --settled를 함께 사용한다. 실제 Dispatch 종료 확인은 조정자의 책임이다. 상향은 한 번만, high 이하 승인 프로필로 제한한다. 인증·네트워크·설치 실패는 상향하지 않는다. --prior 파일을 바꾸어 상향 제한을 회피하지 않는다.

리뷰는 --implementation-agent를 전달해 review_independence를 확인한다. false이면 독립 도구가 아님을 보고하고, 가능하면 다른 검증된 검토 프로필을 명시 선택한다. 모델 변경 시 기존 terminal 재사용을 하지 않는다.

## 검증 기록 등록

검증 전 `kit.py setup --agent <agent>`를 실행한다. 이후 조정자가 실행한 읽기 전용 작업이 성공하면 `kit.py verify-profile --profile <name> --dispatch <id>`를 사용한다. 검증 파일을 직접 작성하지 않는다. 완료 시각부터 7일을 계산하며 오래된 작업 재등록으로 연장하지 않는다. 실행 파일 관찰 기록이 누락되거나 작업 이후 변경되었으면 setup부터 새 검증을 수행한다. 완료 메시지 처리와 회수는 조정자의 책임이다.

### 로컬 설정 예제

아래는 기존 standard 프로필을 같은 조합으로 재정의하는 형식 예시다. 모델을 바꾸면 해당 조합을 다시 검증한다.

```json
{
  "max_workers": 1,
  "profiles": {
    "standard": {
      "agent": "codex",
      "model": "gpt-6.1-sol",
      "effort": "medium",
      "effort_mode": "flag",
      "upgrade": "deep"
    }
  },
  "routes": {"implementation": "standard"}
}
```

## 작업별 후보 선택 (2026-11-02)

고정 역할 대신 조정자가 승인 후보에서 작업 내용과 검증 기준에 맞춰 선택합니다. 기존 route 호출은 호환성을 유지합니다.

```sh
python3 kit.py route --task-type design --candidates
python3 kit.py route --task-type design --select-profile claude-opus --selection-reason "설계 대안을 구현 전에 검토"
python3 kit.py route --task-type review --candidates --implementation-agent codex
```

`--candidates`는 읽기 전용이며 작업자를 시작하거나 검증·사용량 기록을 갱신하지 않습니다. `verification_status`, `usage`, `excluded_reasons`, `review_independence`를 확인합니다. 구현 도구를 모르면 독립성은 null입니다. `candidates` 설정은 유형별 목록을 재정의하며 기존 routes의 기본 후보는 첫 항목으로 유지합니다. complex는 기존 deep 기본값을 유지합니다.

`--select-profile`은 승인 후보만 허용하며 선택 이유가 필수입니다. 사용자 명시 선택인 `--profile`과 달리 잔여량 부족 시 다른 승인 후보로 전환할 수 있습니다. 결과의 selected_profile/selection_reason과 실제 profile/usage_reason을 함께 보고합니다. 새 선택 경로는 공급자 간 effort를 품질 등급으로 비교하지 않습니다. 기존 단일 route의 사용량 대안 동작은 유지합니다. 선택·조회 모드는 명시 override 및 상향 옵션과 함께 쓸 수 없습니다.

배정 직전 usage refresh를 실행합니다. 잔여량 20% 이하는 별도 한도에 여유가 확인된 대안을 우선하고, 5% 이하는 대안이 없으면 blocked입니다. unknown은 여유로 취급하지 않으며, 알려진 제한이 없을 때 기존 정책대로 선택은 가능합니다. 독립 리뷰에서는 구현과 다른 도구를 우선하고 동일 도구 결과를 독립 검토로 보고하지 않습니다.

Claude 후보는 CLI 도움말에서 지원하는 별칭별 프로필 `claude-sonnet`(sonnet/high), `claude-opus`(opus/high), `claude-fable`(fable/high)입니다. simple을 제외한 모든 작업 유형의 승인 후보이며, 어느 모델을 쓸지는 조정자가 작업 내용과 잔여량을 보고 매번 선택합니다. `claude-fable`은 `claude`와 `claude-fable` 한도 그룹 중 낮은 잔여량을 사용합니다. Fable은 플랜·계정에 따라 제공되지 않을 수 있으므로 `require_quota: true`입니다. 자동 경로(route, `--candidates`, `--select-profile`)에서는 Orca가 현재 계정의 Fable 주간 한도(fableWeekly)를 보고할 때만 후보가 되며, 보고되지 않으면 `required quota not reported` 사유로 제외됩니다. 사용자가 `--profile claude-fable`로 명시하면 이 제한 없이 검증 근거만 확인합니다. 계정을 바꾸면 usage refresh 결과에 따라 자동으로 다시 판단됩니다. effort는 조정자가 `--select-profile <claude-*> --effort low|medium|high`로 작업에 맞게 고를 수 있습니다. 해당 모델·effort 조합이 검증되어 있어야 ready이며, `--candidates` 결과의 `verified_efforts`에 검증된 effort가 표시됩니다. 새 조합은 setup 후 그 effort로 작은 읽기 전용 작업을 실행하고 `verify-profile --profile <name> --effort <effort> --dispatch <id>`로 등록합니다. high 초과 effort는 자동 선택하지 않습니다. 조합마다 setup과 새 읽기 전용 Dispatch의 성공 후 verify-profile 등록 전에는 blocked입니다. 별칭을 특정 버전으로 추측하지 않으며 launch.effective 또는 공급자 응답으로 확인한 범위만 보고합니다. 모든 컴퓨터에서 로컬 검증이 필요합니다.
