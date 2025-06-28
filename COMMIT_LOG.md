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