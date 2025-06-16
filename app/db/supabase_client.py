from supabase import create_client
from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

def check_flight_exists(hash_key: str) -> bool:
    """
    주어진 hash_key를 가진 항공권 정보가 DB에 존재하는지 확인합니다.
    """
    response = supabase.table('airfare_stack').select('hash_key').eq('hash_key', hash_key).execute()
    return len(response.data) > 0

def insert_flight(flight_data: dict) -> dict:
    """
    새로운 항공권 정보를 DB에 저장합니다.
    """
    response = supabase.table('airfare_stack').insert(flight_data).execute()
    return response.data[0] if response.data else None

def filter_new_flights(flight_blocks: list) -> list:
    """
    새로운 항공권 정보만 필터링합니다.
    배치 처리 방식으로 DB 조회 횟수를 최소화합니다.
    """
    if not flight_blocks:
        return []

    # 모든 hash_key를 한 번에 조회
    hash_keys = [flight['hash_key'] for flight in flight_blocks]
    existing_flights = supabase.table('airfare_stack')\
        .select('hash_key')\
        .in_('hash_key', hash_keys)\
        .execute()
    
    # 이미 존재하는 hash_key 집합 생성
    existing_keys = {flight['hash_key'] for flight in existing_flights.data}
    
    # 새로운 항공권 정보만 필터링
    new_flights = [flight for flight in flight_blocks if flight['hash_key'] not in existing_keys]
    print(f"Found {len(new_flights)} new flights out of {len(flight_blocks)} total flights")
    
    return new_flights 