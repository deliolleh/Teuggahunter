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
    flight_blocks에서 DB에 없는 새로운 항공권 정보만 필터링합니다.
    """
    new_flights = []
    for flight in flight_blocks:
        if not check_flight_exists(flight['hash_key']):
            new_flights.append(flight)
    return new_flights 