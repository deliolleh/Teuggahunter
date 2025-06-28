from typing import Dict, Any, List
import json
from fastapi import HTTPException
import time

from app.gmail.email_service import get_gmail_service, extract_email_body, parse_flight_blocks
from app.db.supabase_client import filter_new_flights, insert_flight

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
        body = email_data['body']
        label = email_data['label']
        flight_blocks = parse_flight_blocks(body, label)
        print(f"Found {len(flight_blocks)} flight blocks")

        if not flight_blocks:
            return {
                "status": "warning",
                "message": f"No flight information found in email with label: {label}",
                "data": {
                    "parsed_flights": [],
                    "new_flights": []
                }
            }

        new_flights = filter_new_flights(flight_blocks)
        print(f"Found {len(new_flights)} new flights")

        if not new_flights:
            return {
                "status": "info",
                "message": f"All flights from email with label: {label} already exist in database",
                "data": {
                    "parsed_flights": flight_blocks,
                    "new_flights": []
                }
            }

        saved_flights = []
        for flight in new_flights:
            saved_flight = insert_flight(flight)
            if saved_flight:
                saved_flights.append(saved_flight)
        print(f"Saved {len(saved_flights)} flights to database")

        if not saved_flights:
            return {
                "status": "error",
                "message": f"Failed to save new flights to database for label: {label}",
                "data": {
                    "parsed_flights": flight_blocks,
                    "new_flights": []
                }
            }

        return {
            "status": "success",
            "message": f"Successfully saved {len(saved_flights)} new flights from email with label: {label}",
            "data": {
                "parsed_flights": flight_blocks,
                "new_flights": saved_flights
            }
        } 