# 커밋 히스토리

## feat: framework init
- FastAPI 프로젝트 기본 구조 설정
- 기본 엔드포인트 구현
- 환경 설정 파일 구성
- .gitignore 설정 (config.py 제외)

## feat: db init
- Supabase 클라이언트 설정
- 데이터베이스 연결 및 테이블 구조 정의
- RLS 정책 설정

## feat: mailing data init
- Gmail API 연동 및 이메일 파싱 기능 구현
- 항공권 정보 추출 로직 구현
- 직항 여부(direct) 필드 추가

## fix: timestamp unit consistency
- last_processed.json의 타임스탬프를 밀리초에서 초 단위로 변경
- Gmail API 쿼리와 저장 시 타임스탬프 단위 일관성 유지
- save_last_processed_time에서 Gmail API의 internalDate를 초 단위로 변환

## feat: special deal detection logic
- 특가 판별 로직 3단계 시스템 구현
  - 1순위: '여행자들은 일반적으로 ₩xxx의 가격으로 예약합니다' 패턴에서 평균 가격 추출 후 비교
  - 2순위: '대개 ₩xxx–₩yyy 사이입니다' 패턴에서 일반 가격 범위 추출 후 비교
  - 3순위: '% 할인' 표기가 있으면 특가로 판별
- is_special_deal 필드 추가: 각 항공권 정보에 특가 여부 포함
- 정규식 패턴 개선: Google Flights 링크 패턴을 더 정확하게 수정
- 특가 판별 기준 주석 추가로 로직 명확화
- SecretFlying 라벨 타임스탬프 추가 (last_processed.json)

## refactor: last_processed 코드 정리 및 Apps Script 연동 구조로 전환
- Google Apps Script 트리거 구현
  - 5분마다 트리거로 읽지 않고 별표되지 않은 이메일을 FastAPI로 전송
  - 이메일 실시간 수신은 Gmail API(Pub/Sub) 방안도 고려 중이며, 향후 해당 방식으로 변경 가능
- FastAPI는 받은 데이터만 파싱/DB 저장, last_processed 관련 코드/파일(메소드, json) 정리
- Webhook 인증을 위한 시크릿 토큰 적용
- Pub/Sub 등 서버 폴링 방식 도입 시 참고할 수 있도록 관련 메소드 주석 처리 및 PLAN.md에 설명 추가
- 아키텍처/운영 방식의 변화와 외부 시스템 연동에 대한 맥락을 명확히 기록

## refactor: 불필요한 코드 정리
- email_service.py에서 사용하지 않는 함수(extract_email_body, get_all_labels) 삭제
- flight_service.py에서 사용하지 않는 extract_email_body import 제거
- main.py에서 사용하지 않는 get_all_labels import 제거

## feat: 로깅 시스템 추가
- main.py에 logging 설정을 추가하여 터미널과 app.log 파일 모두에 로그가 남도록 개선
- email_service.py, flight_service.py에 주요 이벤트/에러 로그 추가
- 로그 파일(app.log) 미리 생성

## refactor: 라벨별 파싱 함수 분리 및 구조 리팩토링
- parse_flight_blocks 함수에서 라벨명(googleflights, secretflying 등)에 따라 각 서비스별 파싱 함수로 분기하도록 구조 변경
- 기존 구글 파싱 코드를 parse_google_flights 함수로 분리
- secretflying 등 신규 서비스용 빈 파싱 함수 추가 (확장성 고려)

## refactor: DB 저장 재시도 및 에러 처리/로깅 강화
- insert_flight 실패 시 최대 5회 재시도
- 성공/실패 항공권 분리 관리
- DB 저장 실패 시 에러 응답 및 상세 로깅 강화

## feat: DB 저장 성공 항공권만 Make Webhook으로 전송
- DB 저장 성공 항공권만 Make Webhook(헤더 포함)으로 한 번에 전송
- Make Webhook URI 및 API Key 헤더 적용

## refactor: save_and_notify, send_to_make 함수 분리 및 구조 리팩토링
- DB 저장/Make 전송 로직을 별도 함수로 분리
- process_email은 클라이언트에 필요한 정보만 반환하도록 개선