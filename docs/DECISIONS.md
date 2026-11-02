
## 2026-11-02: 작업별 후보 선택과 기존 route 호환

공급자별 고정 역할 대신 작업별 승인 후보 목록을 사용하고 조정자가 선택 이유를 기록한다. 기존 route와 명시 --profile 동작을 보존하고, 새 --select-profile만 승인 후보 사이에서 잔여량에 따라 대체할 수 있다. 새 경로는 공급자 간 effort를 품질 동등성 근거로 사용하지 않는다. 리뷰 대안은 구현과 다른 도구를 우선한다. unknown 사용량은 여유가 아니며 기존 정책대로 알려진 제한이 없으면 선택할 수 있다. Claude는 sonnet 하나로 한정하지 않고 CLI가 지원하는 sonnet·opus·fable 별칭을 각각 high 프로필(claude-sonnet/claude-opus/claude-fable)로 두어 simple 외 모든 작업 유형의 후보로 둔다. 각 조합은 CLI 지원 확인과 로컬 읽기 전용 검증 후 활성화하며 검증 근거는 컴퓨터 간 배포하지 않는다. 이 변경은 권한·인증·동시 작업자 수와 실행 중인 Dispatch를 바꾸지 않는다.

## 2026-11-02: Claude 모델별 후보, 계정별 Fable 가용성, 조정자 effort 선택

Claude 후보를 sonnet 하나에서 claude-sonnet/claude-opus/claude-fable로 확장한다. Fable은 계정·플랜에 따라 제공되지 않을 수 있으므로 프로필에 require_quota를 두고, 자동 경로에서는 Orca가 해당 한도 그룹을 보고할 때만 후보로 삼는다. 사용자의 명시 --profile은 이 제한을 받지 않는다. 조정자는 --select-profile에 --effort(low|medium|high, flag 방식만)를 붙여 작업별 effort를 고를 수 있으나, 검증 근거 키에 effort가 포함되므로 모델·effort 조합별 로컬 검증이 필요하다. 검증 경계와 high 초과 자동 선택 금지는 유지한다.
