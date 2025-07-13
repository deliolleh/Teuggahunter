from typing import Dict, Any, List
import json
from fastapi import HTTPException
import time
import logging
import requests  # Make 전송용

from app.gmail.email_service import get_gmail_service, parse_flight_blocks
from app.db.supabase_client import filter_new_flights, insert_flight

logger = logging.getLogger("teuggahunter.flight_service")

def send_to_make(flights):
    MAKE_WEBHOOK_URL = "https://hook.us2.make.com/5lv6kg3kzeu2i1te8i5src3i8esw4x9t"
    headers = {"x-make-apikey": "G0GZ2G9mwxpMHyxPPG0a"}
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json=flights, headers=headers, timeout=5)
        logger.info(f"Make 전송 결과: {res.status_code}")
    except Exception as e:
        logger.error(f"Make 전송 실패: {e}")

def save_and_notify(new_flights, flight_blocks):
    saved_flights = []
    failed_flights = []
    for flight in new_flights:
        success = False
        for attempt in range(5):
            try:
                saved_flight = insert_flight(flight)
                if saved_flight:
                    saved_flights.append(saved_flight)
                    success = True
                    break
            except Exception as e:
                logger.error(f"DB 저장 실패 (시도 {attempt+1}/5): {e}", exc_info=True)
        if not success:
            failed_flights.append(flight)
    logger.info(f"DB 저장 완료: {len(saved_flights)}건, 실패: {len(failed_flights)}건")
    if saved_flights:
        send_to_make(saved_flights)
    return saved_flights, failed_flights

class FlightService:
    def __init__(self):
        self.gmail_service = get_gmail_service()
        self.last_processed_file = 'last_processed.json'
        # self.initialize_last_processed()

    # def initialize_last_processed(self):
    #     '''
    #     (삭제됨) 서비스 오픈 시점 기준으로 last_processed.json을 초기화합니다.
    #     '''
    #     pass

    # def get_last_processed_time(self, label: str) -> int:
    #     '''
    #     (주석처리) Gmail 실시간(Pub/Sub) 수신 구현 시 사용할 것을 제안
    #     라벨별 마지막 처리 시간을 파일에서 읽어옵니다.
    #     '''
    #     pass

    # def save_last_processed_time(self, label: str, timestamp: int):
    #     '''
    #     (주석처리) Gmail 실시간(Pub/Sub) 수신 구현 시 사용할 것을 제안
    #     라벨별 마지막 처리 시간을 파일에 저장합니다.
    #     '''
    #     pass

    async def process_email(self, email_data: dict) -> dict:
        logger.info(f"이메일 데이터 처리 시작: {email_data.get('subject', '')} (label: {email_data.get('label', '')})")
        body = email_data['body']
        label = email_data['label']
        try:
            flight_blocks = parse_flight_blocks(body, label)
            logger.info(f"파싱된 항공권 블록 수: {len(flight_blocks)}")
        except Exception as e:
            logger.error(f"항공권 파싱 실패: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"파싱 실패: {e}",
                "data": {
                    "parsed_flights": [],
                    "new_flights": []
                }
            }

        if not flight_blocks:
            logger.warning("파싱된 항공권 정보 없음")
            return {
                "status": "warning",
                "message": f"No flight information found in email with label: {label}",
                "data": {
                    "parsed_flights": [],
                    "new_flights": []
                }
            }

        new_flights = filter_new_flights(flight_blocks)
        logger.info(f"신규 항공권 저장 대상: {len(new_flights)}")

        # 저장 및 Make 전송
        saved_flights, failed_flights = save_and_notify(new_flights, flight_blocks)

        if not saved_flights:
            logger.error("DB 저장 실패: 신규 항공권 없음")
            return {
                "status": "error",
                "message": f"Failed to save new flights to database for label: {label}",
                "data": {
                    "parsed_flights": flight_blocks,
                    "new_flights": [],
                    "failed_flights": failed_flights
                }
            }

        return {
            "status": "success",
            "message": f"Successfully processed email. New: {len(saved_flights)}",
            "data": {
                "parsed_flights": flight_blocks,
                "new_flights": saved_flights
            }
        } 