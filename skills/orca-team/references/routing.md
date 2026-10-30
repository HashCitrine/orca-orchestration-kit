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
