import base64, quopri, re
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.config import (
    GMAIL_CLIENT_ID,
    GMAIL_CLIENT_SECRET,
    GMAIL_REFRESH_TOKEN,
)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logger = logging.getLogger("teuggahunter.email_service")

def get_gmail_service():
    """
    Gmail API 서비스를 초기화하고 반환합니다.
    """
    creds = Credentials(
        None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        scopes=SCOPES
    )
    
    return build('gmail', 'v1', credentials=creds)

def parse_flight_blocks(body: str, label: str) -> List[Dict[str, Any]]:
    label = label.lower()
    logger.info(f"[parse_flight_blocks] 파싱 시작 (label: {label})")
    if label == "googleflights":
        return parse_google_flights(body, label)
    elif label == "secretflying":
        return parse_secretflying(body, label)
    else:
        logger.warning(f"지원하지 않는 라벨: {label}")
        return []

def parse_google_flights(body: str, label: str) -> List[Dict[str, Any]]:
    date_pattern = r'(\d{1,2})월\s*(\d{1,2})일\s*\([^)]+\)\s*-\s*(\d{1,2})월\s*(\d{1,2})일\s*\([^)]+\)'
    price_pattern = r'(?:\d+%\s*할인\s*)?최저가:\s*₩([\d,]+)'
    airline_pattern = r'([^·\n]+)·\s*(?:직항|경유)\s*·\s*([A-Z]{3})[–-]([A-Z]{3})'
    link_pattern = r'https://www\.google\.com/travel/flights\?[\S"]+'

    avg_pattern = r'여행자들은 일반적으로\s*₩([\d,]+)의 가격으로 예약합니다'
    range_pattern = r'대개\s*₩([\d,]+)[–-]₩([\d,]+) 사이입니다'
    discount_pattern = r'(\d+)%\s*할인'

    avg_match = re.search(avg_pattern, body)
    range_match = re.search(range_pattern, body)
    discount_match = re.search(discount_pattern, body)
    special_price = None
    if avg_match:
        special_price = int(avg_match.group(1).replace(',', ''))
    elif range_match:
        special_price = int(range_match.group(1).replace(',', ''))

    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    results = []
    pos = 0

    for date_match in re.finditer(date_pattern, body):
        depart_month, depart_day, return_month, return_day = map(int, date_match.groups())
        depart_year = current_year + 1 if depart_month < current_month else current_year
        return_year = current_year + 1 if return_month < current_month else current_year
        depart_date = f"{depart_year}-{depart_month:02d}-{depart_day:02d}"
        return_date = f"{return_year}-{return_month:02d}-{return_day:02d}"

        price_search = re.search(price_pattern, body[date_match.end():])
        if not price_search:
            continue
        price = int(price_search.group(1).replace(',', ''))
        price_start = date_match.end() + price_search.start()
        price_end = date_match.end() + price_search.end()

        block_text = body[price_end: price_end + 500]
        airline_matches = list(re.finditer(airline_pattern, block_text))
        
        if not airline_matches:
            continue

        is_special_deal = False
        if special_price is not None and price < special_price:
            is_special_deal = True
        elif discount_match:
            is_special_deal = True

        for airline_match in airline_matches:
            airline = airline_match.group(1).strip()
            origin = airline_match.group(2)
            destination = airline_match.group(3)
            is_direct = '직항' in block_text[airline_match.start():airline_match.end()]

            link_search = re.search(link_pattern, block_text[airline_match.end():])
            link = link_search.group(0) if link_search else None

            hash_input = f"{origin}{destination}{depart_date}{return_date}{airline}{price}"
            hash_key = base64.b64encode(hash_input.encode()).decode()

            logger.debug(f"항공권: {airline} {origin}->{destination} {depart_date}~{return_date} {price}원 특가여부:{is_special_deal}")

            results.append({
                "source": label,
                "origin": origin,
                "destination": destination,
                "departure_date": depart_date,
                "arrival_date": return_date,
                "airline": airline,
                "price": price,
                "link": link,
                "hash_key": hash_key,
                "direct": is_direct,
                "is_special_deal": is_special_deal
            })

    logger.info(f"[parse_google_flights] 파싱 완료 - 총 {len(results)}건")
    return results

def parse_secretflying(body: str, label: str) -> List[Dict[str, Any]]:
    # TODO: SecretFlying 파싱 로직 구현 예정
    logger.info(f"[parse_secretflying] 파싱 시작 (label: {label})")
    return [] 