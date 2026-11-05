# 선택형 보조 판단

작업 분류·후보 비교·완료 근거 평가처럼 좁은 판단이 필요할 때만 사용한다. 기존 Jev와 OpenAI Decisions를 선택할 수 있다. 판단은 조정자의 보조 근거이며 별도 실행 권한이나 완료 증명이 아니다. 계정·구독 사용량은 전송하지 않고 일반 코드로 처리한다.

## 기존 설정 확인과 제공자 선택

`python scripts/decision.py status`는 API 호출 없이 기존 Jev 인증과 OPENAI_API_KEY 존재를 확인한다. configured는 인증 존재만 뜻하며 실제 접근 가능 여부는 미확인이다. 새 계정이나 키 설정을 강요하지 않는다. 키를 채팅·명령 인자·config.json에 넣지 않는다. Codex/ChatGPT 로그인 토큰을 API 키로 재사용하지 않는다.

키트의 `~/.config/orca-orchestration-kit/config.json`에 다음 항목을 선택적으로 추가한다.

```json
{"decision": {"provider": "auto"}}
```

- auto(미지정 기본값): Jev 인증이 있으면 Jev, 없고 OpenAI 인증이 있으면 OpenAI, 모두 없으면 조정자 판단.
- jev/openai: 해당 제공자만 사용. 인증·API 실패 시 자동 전환하지 않는다.
- none: 외부 판단 호출 없이 조정자가 판단.

현재 요청의 명시 제공자는 `--provider auto|jev|openai|none`으로 반영하며 설정보다 우선한다. status의 selected_provider와 선택 이유를 사용자에게 설명한다. Jev 인증 방식은 [Jev 안내](jev.md)를 따른다. OpenAI는 OPENAI_API_KEY 환경변수만 사용한다.

## 입력과 호출

호출 전 한국어로 목적과 전송할 최소 발췌를 알리고 비밀·개인정보를 제거한다. 질문과 선택지 설명도 전송 대상이다. 전체 저장소나 대량 처리는 기존처럼 별도 승인이 필요하다. auto에서 두 제공자가 설정되어 있으면 동일 발췌가 Jev 실패 후 OpenAI에 전송될 수 있음을 먼저 알린다. 실행기는 대체 전 stderr에 전환 사실을 알리고 본문이나 키는 로그에 남기지 않는다.

```sh
python scripts/decision.py evaluate --input request.json
python scripts/decision.py evaluate --provider openai --input request.json
```

`--input -`(기본값)는 표준 입력을 사용한다. `--home`은 격리된 테스트용 키트 설정 위치만 바꾸며 인증 위치는 바꾸지 않는다.

```json
{
  "state": "수정 범위가 작은 문서 오타 수정 요청",
  "questions": {
    "task_type": {
      "type": "choice",
      "instructions": "이 요청에 맞는 작업 유형을 고르세요.",
      "criteria": {"simple": "작은 수정", "implementation": "기능 구현"}
    }
  }
}
```

기존 Jev의 state(문자열/객체/배열)와 이름별 questions 입력을 사용한다. instructions는 문자열 또는 JSON이며, 객체·배열은 JSON 텍스트로 보존한다. choice의 criteria는 선택지 식별자별 설명, score는 낮은 단계부터 순서대로 2–10개 설명, noul은 참 여부 질문이다. score의 단계 라벨은 원래 0부터의 인덱스다. OpenAI는 choice/score/predicate로 변환하며 질문 이름·선택지 식별자를 유지한다. 지원 범위는 텍스트/JSON이며 이미지 입력은 이번 공통 실행기에 포함하지 않는다.

OpenAI는 공식 [Decisions API](https://developers.openai.com/api/docs/guides/decisions)의 `https://api.openai.com/v1/decisions`와 `gpt-6-luna`를 사용한다. Jev 기본값은 jev-latest다. 선택적 입력 model은 처음 선택한 제공자에만 적용하며 OpenAI의 미지원 모델은 거부한다. Jev 실패 후 GPT 대체 호출에는 Jev 모델명을 전달하지 않는다. 요청 형식은 [공식 API 명세](https://developers.openai.com/api/reference/resources/decisions/methods/create)를 기준으로 한다.

## 결과와 실패

성공 JSON은 status=succeeded, provider, 실제 응답 model, 질문 이름별 answers, usage, raw(제공자 원본 응답), attempts를 포함한다. OpenAI answers는 원래 type인 predicate/choice/score를 유지한다. 원본 확률·점수·confidence를 보존하며 별도 공통 신뢰도로 변환하지 않는다. predicate의 probability는 조건이 참일 확률, score는 단계 인덱스의 확률 가중 평균이다. Jev의 답 구조는 기존 그대로 유지한다.

auto에서 Jev 호출 실패 시 OpenAI 인증이 있으면 한 번 대체 호출한다. 같은 제공자 재시도는 하지 않는다. 명시 제공자는 전환하지 않는다. HTTP/인증/네트워크/형식 오류나 거부, 질문 누락은 정상 판단으로 쓰지 않는다. 외부 판단을 쓸 수 없으면 status=coordinator_required, provider=none, 실패 범주별 attempts를 반환하고 종료 코드는 1이다. none이나 인증 부재도 같은 상태로 조정자 판단을 요청한다. status 명령은 조회 성공 시 0이다.

조정자는 실패 및 대체 사실을 사용자에게 설명하고, 판단 API에 의존하지 않는 기존 기준으로 진행한다. 임의 확률 임계값으로 워커 실행·정리·권한 변경을 자동 수행하지 않는다. 기존 `jev.py`의 직접 명령과 동작은 변경하지 않는다.
