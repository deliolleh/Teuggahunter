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
        self.initialize_last_processed()

    def initialize_last_processed(self):
        """
        서비스 오픈 시점 기준으로 last_processed.json을 초기화합니다.
        타임스탬프는 초 단위로 저장됩니다.
        """
        now = int(time.time())  # 초 단위 타임스탬프
        try:
            with open(self.last_processed_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        
        # 모든 라벨에 대해 현재 시각을 저장 (초 단위)
        for label in ['GoogleFlights', 'SecretFlying']:  # 필요한 라벨 추가
            if label not in data:
                data[label] = now
        
        with open(self.last_processed_file, 'w') as f:
            json.dump(data, f)
        print(f"Initialized last_processed.json with timestamp: {now}")

    def get_last_processed_time(self, label: str) -> int:
        """
        라벨별 마지막 처리 시간을 파일에서 읽어옵니다.
        타임스탬프는 초 단위입니다.
        """
        try:
            with open(self.last_processed_file, 'r') as f:
                data = json.load(f)
                return data.get(label, 0)
        except FileNotFoundError:
            return 0

    def save_last_processed_time(self, label: str, timestamp: int):
        """
        라벨별 마지막 처리 시간을 파일에 저장합니다.
        Gmail API의 internalDate(밀리초)를 초 단위로 변환하여 저장합니다.
        """
        try:
            with open(self.last_processed_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        
        # 밀리초를 초로 변환
        timestamp_seconds = timestamp // 1000
        data[label] = timestamp_seconds
        with open(self.last_processed_file, 'w') as f:
            json.dump(data, f)

    async def process_latest_email(self, label: str) -> Dict[str, Any]:
        """
        라벨이 지정된 최신 이메일을 처리하고 항공권 정보를 추출/저장합니다.
        """
        print(f"\nProcessing label: {label}")
        
        # 마지막 처리 시간 이후의 이메일만 가져오기
        last_processed = self.get_last_processed_time(label)
        query = f'label:{label}'
        if last_processed:
            # 밀리초를 초로 변환
            last_processed_seconds = last_processed // 1000
            query += f' after:{last_processed_seconds}'
        
        results = self.gmail_service.users().messages().list(
            userId='me',
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No new messages found for label: {label}")
            return {
                "status": "info",
                "message": f"No new messages found with label: {label}",
                "data": {
                    "parsed_flights": [],
                    "new_flights": []
                }
            }
        
        # 가장 최근 이메일의 시간 저장 (밀리초 단위 유지)
        latest_message = self.gmail_service.users().messages().get(
            userId='me',
            id=messages[0]['id'],
            format='full'
        ).execute()
        self.save_last_processed_time(label, int(latest_message['internalDate']))
        
        # 이메일 본문 파싱
        payload = latest_message['payload']
        body = extract_email_body(payload)
        
        # 항공권 정보 파싱
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
        
        # 새로운 항공권 정보만 필터링
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
        
        # 새로운 항공권 정보를 DB에 저장
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