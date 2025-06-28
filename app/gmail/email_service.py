import base64, quopri, re
from typing import Dict, Any, List
from datetime import datetime

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

def extract_email_body(payload: Dict[str, Any]) -> str:
    """
    이메일 페이로드에서 본문을 추출합니다.
    """
    if 'parts' in payload:
        parts = payload['parts']
        body = ''
        for part in parts:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body += base64.urlsafe_b64decode(part['body']['data']).decode()
                elif 'attachmentId' in part['body']:
                    continue
        return body
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode()
    return ''

def parse_flight_blocks(body: str, source: str) -> List[Dict[str, Any]]:
    """
    이메일 본문에서 항공권 정보 블록을 파싱합니다.
    여러 항로의 특가 정보도 처리할 수 있습니다.
    특가 판별 기준:
      1순위: '여행자들은 일반적으로 ₩xxx의 가격으로 예약합니다.'
      2순위: '대개 ₩xxx–₩yyy 사이입니다. 이보다 낮은 가격이 특가로 간주됩니다.'
    특가가 아닌 것은 '괜찮은 가격'으로 게시글을 적을 수 있도록 AI 한테 알려줘야 함.
    """
    date_pattern = r'(\d{1,2})월\s*(\d{1,2})일\s*\([^)]+\)\s*-\s*(\d{1,2})월\s*(\d{1,2})일\s*\([^)]+\)'
    price_pattern = r'(?:\d+%\s*할인\s*)?최저가:\s*₩([\d,]+)'
    airline_pattern = r'([^·\n]+)·\s*(?:직항|경유)\s*·\s*([A-Z]{3})[–-]([A-Z]{3})'
    link_pattern = r'https://www\.google\.com/travel/flights\?[\S"]+'

    # 특가 기준 추출
    avg_pattern = r'여행자들은 일반적으로\s*₩([\d,]+)의 가격으로 예약합니다'
    range_pattern = r'대개\s*₩([\d,]+)[–-]₩([\d,]+) 사이입니다'
    discount_pattern = r'(\d+)%\s*할인'  # 3순위: % 할인 표기

    avg_match = re.search(avg_pattern, body)
    range_match = re.search(range_pattern, body)
    discount_match = re.search(discount_pattern, body)  # 할인 표기 확인
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

    # 날짜 블록을 찾아서 각각 처리
    for date_match in re.finditer(date_pattern, body):
        depart_month, depart_day, return_month, return_day = map(int, date_match.groups())
        depart_year = current_year + 1 if depart_month < current_month else current_year
        return_year = current_year + 1 if return_month < current_month else current_year
        depart_date = f"{depart_year}-{depart_month:02d}-{depart_day:02d}"
        return_date = f"{return_year}-{return_month:02d}-{return_day:02d}"

        # 날짜 블록 이후의 텍스트에서 가격 패턴 찾기
        price_search = re.search(price_pattern, body[date_match.end():])
        if not price_search:
            continue
        price = int(price_search.group(1).replace(',', ''))
        price_start = date_match.end() + price_search.start()
        price_end = date_match.end() + price_search.end()

        # 가격 패턴 뒤의 텍스트에서 모든 항공사/경로 정보 찾기
        block_text = body[price_end: price_end + 500]  # 탐색 범위 확대
        airline_matches = list(re.finditer(airline_pattern, block_text))
        
        if not airline_matches:
            continue

        # 특가 여부 판별
        is_special_deal = False
        if special_price is not None and price < special_price:
            is_special_deal = True
        elif discount_match:  # 3순위: % 할인 표기 있으면 True
            is_special_deal = True

        # 각 항공사/경로 정보에 대해 처리
        for airline_match in airline_matches:
            airline = airline_match.group(1).strip()
            origin = airline_match.group(2)
            destination = airline_match.group(3)
            is_direct = '직항' in block_text[airline_match.start():airline_match.end()]

            # 해당 항공사/경로 정보 이후의 링크 찾기
            link_search = re.search(link_pattern, block_text[airline_match.end():])
            link = link_search.group(0) if link_search else None

            hash_input = f"{origin}{destination}{depart_date}{return_date}{airline}{price}"
            hash_key = base64.b64encode(hash_input.encode()).decode()

            results.append({
                "source": source,
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

    return results

def get_all_labels() -> List[str]:
    """
    Gmail 계정의 사용자가 만든 라벨만 반환합니다.
    """
    service = get_gmail_service()
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    
    # 사용자가 만든 라벨만 필터링 (labelListVisibility가 'labelShow'인 라벨)
    user_labels = [
        label['name'] for label in labels 
        if label.get('labelListVisibility') == 'labelShow'
    ]
    
    print(f"Found {len(user_labels)} user-created labels: {user_labels}")
    return user_labels 