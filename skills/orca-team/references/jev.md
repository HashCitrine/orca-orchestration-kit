# Jev 보조 판단

scripts/jev.py는 공식 https://api.typesafe.ai/v1/systemone 만 사용한다. 모델 기본값은 jev-latest이며 요청 JSON의 model로 재정의할 수 있다.

작업 분류·후보 비교·완료 근거 평가처럼 좁은 질문에만 사용한다. 호출 전 한국어로 목적과 전송 발췌를 알리고 비밀/개인정보를 제거한다. 전체 저장소나 대량 처리에는 별도 승인이 필요하다.

`python scripts/jev.py status`로 인증 유무만 확인한다. POSIX는 기존 ~/.config/jev/credentials.json(0600, 현재 사용자 소유)을 사용한다. Windows는 TYPESAFE_API_KEY 환경변수를 사용자 환경에서 설정한다. 키를 채팅이나 명령 인자로 전달하지 않는다.

`python scripts/jev.py evaluate --input request.json`을 호출한다. 요청에는 state, questions, 선택적 model을 넣는다. 질문 설계 전 https://docs.typesafe.ai/api.md 와 primitives 문서를 읽는다. instructions에 판단과 맥락을 명시하고 Choice의 criteria에는 선택지를 정의한다. Noul은 yes 확률이며 별도 신뢰도가 아니다.

응답의 answers/model/usage와 확률·신뢰도를 보존한다. 임의 임계값으로 자동 실행하지 않는다. API/인증/형식 실패 시 재시도 루프 없이 원문과 일반 도구로 계속 진행한다. 모델 성능이나 권한은 Jev 판단 대상이 아니다.
