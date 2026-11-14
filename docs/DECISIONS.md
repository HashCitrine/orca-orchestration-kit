
## 2026-11-02: 작업별 후보 선택과 기존 route 호환

공급자별 고정 역할 대신 작업별 승인 후보 목록을 사용하고 조정자가 선택 이유를 기록한다. 기존 route와 명시 --profile 동작을 보존하고, 새 --select-profile만 승인 후보 사이에서 잔여량에 따라 대체할 수 있다. 새 경로는 공급자 간 effort를 품질 동등성 근거로 사용하지 않는다. 리뷰 대안은 구현과 다른 도구를 우선한다. unknown 사용량은 여유가 아니며 기존 정책대로 알려진 제한이 없으면 선택할 수 있다. Claude는 sonnet 하나로 한정하지 않고 CLI가 지원하는 sonnet·opus·fable 별칭을 각각 high 프로필(claude-sonnet/claude-opus/claude-fable)로 두어 simple 외 모든 작업 유형의 후보로 둔다. 각 조합은 CLI 지원 확인과 로컬 읽기 전용 검증 후 활성화하며 검증 근거는 컴퓨터 간 배포하지 않는다. 이 변경은 권한·인증·동시 작업자 수와 실행 중인 Dispatch를 바꾸지 않는다.

## 2026-11-02: Claude 모델별 후보, 계정별 Fable 가용성, 조정자 effort 선택

Claude 후보를 sonnet 하나에서 claude-sonnet/claude-opus/claude-fable로 확장한다. Fable은 계정·플랜에 따라 제공되지 않을 수 있으므로 프로필에 require_quota를 두고, 자동 경로에서는 Orca가 해당 한도 그룹을 보고할 때만 후보로 삼는다. 사용자의 명시 --profile은 이 제한을 받지 않는다. 조정자는 --select-profile에 --effort(low|medium|high, flag 방식만)를 붙여 작업별 effort를 고를 수 있으나, 검증 근거 키에 effort가 포함되므로 모델·effort 조합별 로컬 검증이 필요하다. 검증 경계와 high 초과 자동 선택 금지는 유지한다.

## 2026-11-02: Grok 모델 후보

Orca 작업자 id `grok`를 승인 후보에 추가한다. 프로필은 Orca 카탈로그 시드인 grok-4.5·grok-4.6·grok-4.7이며 기본 effort는 high, effort_mode는 flag다. 기본 route와 동시 작업자 상한은 유지한다. simple에는 grok-4.5만 두고 grok-4.6·grok-4.7은 implementation·test·design·debug·review 후보로 둔다. grok-4.5는 design 후보가 아니다. 사용량은 Orca `rateLimits.grok`가 보고한 창만 그룹 `grok`로 기록하고, null인 session으로 창을 만들지 않으며 이메일은 저장하지 않는다. 세 모델은 같은 그룹을 공유하므로 모델 교체를 한도 분리로 보지 않는다. `--effort` 자동 선택은 low·medium·high만 허용하고 xhigh는 제외한다. CLI에만 있는 모델 id는 기본 프로필에 넣지 않는다. 검증 근거는 컴퓨터 간 배포하지 않는다.

## 2026-11-02: AGY 멀티 모델(Gemini, Claude 5.5, GPT-OSS) 후보 확장 및 쿼터 분기

AGY(Antigravity)를 단일/역할형 프로필(`light`, `review`)에 국한하지 않고, AGY CLI가 지원하는 핵심 모델군을 개별 프로필(`gemini-flash`, `gemini-argon`, `agy-claude-sonnet`, `agy-claude-opus`, `agy-gpt-oss`)로 등록하여 작업별 후보에 전면 배치한다. 신규 프로필은 모두 `effort_mode: "flag"`를 채택하여 조정자가 `--effort low|medium|high`를 작업에 맞춰 지정할 수 있게 한다. Orca의 공식 rateLimits에서 보고되는 3대 쿼터 그룹(`Gemini Models`, `Gemini 4 Argon`, `Claude and GPT models`)을 각각 모델 프로필에 매핑하여, 특정 모델군 한도가 소진되더라도 다른 모델군으로 매끄럽게 대체하거나 독립 검토를 수행할 수 있도록 한다. 기존 `light`, `review` 프로필 및 기본 route는 하위 호환성을 위해 유지한다.

## 2026-11-14: OpenCode·Pi 작업자 지원

Orca 작업자 id `opencode`와 `pi`를 키트에서 선택할 수 있게 한다. 두 도구의 모델 ID와 가용 모델은 계정·설치마다 달라 기본 routing.json에 모델을 넣지 않고, 로컬 `profiles`와 `candidates`로 승인한다. OpenCode는 Orca worker-start가 effort를 지원하지 않으므로 `effort_mode: "none"`, `effort: "default"`만 허용하고 launch_args에 `--effort`를 넣지 않는다. Pi는 `effort_mode: "flag"`만 허용하며 Orca가 `--effort`를 Pi `--thinking`으로 전달한다. OpenCode의 `--model` 선택은 기존 작업 공간에서만 유효하다. 두 도구 모두 Orca의 자동 쿼터 집계 대상이 아니므로 usage unknown을 유지하고, 프로필의 `quota_groups`와 `usage set`으로만 수동 관찰한다. 스킬은 OpenCode `~/.config/opencode/skills`와 Pi `~/.pi/agent/skills`에도 설치하며 환경 변수 재정의를 허용한다. 검증은 setup 이후 성공한 Dispatch의 launch.effective가 실제 agent/model/effort와 일치할 때만 등록한다.

## 2026-11-14: OMP 작업자 지원

Orca 작업자 id `omp`를 키트에서 선택할 수 있게 한다. OMP는 모델 role/selector를 Orca에 그대로 전달하므로 `--model`은 `omp models`가 보고한 `provider/model` selector를 쓰고, 모델 ID에 effort를 내장하지 않는다. effort는 `effort_mode: "flag"`만 허용하며 Orca가 `--effort`를 OMP `--thinking`으로 전달한다. `embedded`와 `none` OMP 프로필은 설정 검증에서 거부한다. OMP 모델 ID와 가용 provider는 계정·설치마다 달라 기본 routing.json에 모델을 넣지 않고, 로컬 `profiles`와 `candidates`로 승인한다. 명시 `--agent omp` override는 기존 Pi와 같은 방식으로 effort를 low·medium·high 중 하나로 보정해 flag로 실행한다. 스킬은 OMP가 읽는 고정 사용자 경로 `~/.agents/skills`에 설치하며, OMP 로더가 XDG 계열 환경 변수를 따르지 않으므로 별도 재정의를 두지 않고 기존 `skill_roots` 설정으로만 바꾼다. OMP는 Orca의 자동 쿼터 집계 대상이 아니므로 usage unknown을 유지하고, 프로필의 `quota_groups`와 `usage set`으로만 수동 관찰한다.
