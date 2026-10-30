# 코드 출처와 외부 서비스

이 저장소는 HashCitrine의 개인 Orca 설정 작업으로 작성한 설치 도구, 스킬, 문서와 테스트를 포함하며 MIT 라이선스로 제공합니다.

`skills/orca-team/scripts/jev.py`는 저장소 최초 구성 시 사용자의 로컬 `jev-assist` 보조 실행기를 복사해 Windows 인증 처리 등을 수정한 코드입니다. Python 표준 라이브러리를 사용하는 자체 HTTP 클라이언트이며, TypeSafe가 배포하거나 인증한 공식 SDK라는 뜻은 아닙니다. 공식 TypeSafe API 주소를 호출합니다. 확인한 원본에는 별도 제3자 저작권·라이선스 헤더나 외부 SDK 번들이 없었습니다.

Orca, Claude, Codex, AGY, Jev와 각 모델은 해당 공급자의 제품·서비스입니다. 이 프로젝트의 MIT 라이선스는 해당 제품·서비스, 모델, API 이용 조건이나 상표에 대한 권리를 부여하지 않습니다. CLI와 모델은 사용자가 별도로 설치·인증하여 이용합니다.

GitHub Actions는 actions/checkout, actions/setup-python을 참조하며 소스 코드를 이 저장소에 포함하지 않습니다. 공식 문서와 명령 도움말은 동작 확인에 참고했고 공급자의 문서 전문을 배포하지 않습니다.
