# Teuggahunter 프로젝트 요약

## 1. 프로젝트 개요
- **목표**: FastAPI 백엔드에서 Gmail로 수신된 항공권 특가 이메일을 자동 파싱, 구조화, Supabase DB에 저장. 향후 SNS 자동 업로드(외부 Make 등)까지 연동하는 시스템 구축.
- **주요 흐름**: Google Apps Script가 5분마다 라벨링된 새 메일을 FastAPI `/emails` 엔드포인트로 Webhook POST → FastAPI가 파싱/DB 저장(중복 방지, 특가 판별 등)

## 2. 전체 아키텍처/데이터 흐름
```
[Gmail] --(Apps Script Webhook)--> [FastAPI 서버] --(파싱/판별)--> [Supabase DB]
```
- (향후) [Supabase DB] → [Make 등 외부 서비스] → [SNS 업로드]

## 3. 주요 폴더/파일 설명
- `app/main.py` : FastAPI 엔트리포인트, Webhook 수신 및 서비스 연결, 로깅 설정
- `app/gmail/email_service.py` : 이메일 파싱, 특가 판별, 불필요 함수 제거됨
- `app/services/flight_service.py` : 이메일 데이터 처리, DB 저장, 파싱 로직 호출
- `app/db/supabase_client.py` : Supabase 연동 및 DB 관련 함수
- `requirements.txt` : Python 의존성 목록
- `COMMIT_LOG.md` : 커밋 상세 내역 및 변경 이력

## 4. 핵심 코드/로직 요약
- **Webhook 인증**: `x-webhook-secret` 헤더로 인증, config.py에서 관리
- **이메일 파싱**: Apps Script에서 받은 본문을 `parse_flight_blocks()`로 구조화
- **특가 판별**: 평균가/일반가/할인율 등 다양한 기준 적용, `is_special_deal` 필드로 구조화
- **DB 저장**: 중복 방지(hash_key), 신규 항공권만 저장
- **로깅**: 터미널+파일(app.log) 동시 기록, 주요 이벤트/에러 로깅

## 5. 운영/배포/CI-CD/문서화 규칙
- **커밋 메시지**: 한 줄 요약(타입: 내용), 상세 내역은 COMMIT_LOG.md에 기록
- **운영/배포**: Railway, Render, Fly.io 등 클라우드 서비스 추천, GitHub 연동 CI/CD 지원
- **테스트/운영**: 실제 DB/외부 서비스로 테스트 데이터가 넘어가지 않도록 주의(테스트 플래그, 환경 분리 등)
- **문서화**: ReadMe.md, COMMIT_LOG.md, PLAN.md 등으로 관리

## 6. 최근 커밋 요약
- refactor: 불필요한 코드 정리 및 feat: 로깅 시스템 추가
  - 사용하지 않는 함수/임포트 제거
  - main.py, email_service.py, flight_service.py에 로깅 추가
  - COMMIT_LOG.md, 코드 구조 정리

## 7. 기타/확장 계획
- Apps Script → Pub/Sub 방식 확장 가능성
- 외부 Make/SNS 연동, 운영 자동화, 모니터링(Sentry/UptimeRobot 등) 도입 가능
- PLAN.md에 향후 확장/운영/배포 계획 기록

---

> **이 파일은 ChatGPT 기반 요약 자동 생성본입니다. 민감 정보(비밀번호/시크릿 등)는 포함하지 않습니다.** 