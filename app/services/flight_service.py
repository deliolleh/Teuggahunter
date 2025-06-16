from typing import Dict, Any, List
from fastapi import HTTPException

from app.gmail.email_service import get_gmail_service, extract_email_body, parse_flight_blocks
from app.db.supabase_client import filter_new_flights, insert_flight

class FlightService:
    def __init__(self):
        self.gmail_service = get_gmail_service()

    async def process_latest_email(self, label: str) -> Dict[str, Any]:
        """
        라벨이 지정된 최신 이메일을 처리하고 항공권 정보를 추출/저장합니다.
        """
        print(f"\nProcessing label: {label}")
        
        # 이메일 가져오기
        query = f'label:{label}'
        results = self.gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=1
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No messages found for label: {label}")
            raise HTTPException(status_code=404, detail=f"No messages found with label: {label}")
        
        message = self.gmail_service.users().messages().get(
            userId='me',
            id=messages[0]['id'],
            format='full'
        ).execute()
        
        # 이메일 본문 파싱
        payload = message['payload']
        body = extract_email_body(payload)
        # print(f"Email body preview: {body[:200]}...")  # 본문 미리보기
        
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