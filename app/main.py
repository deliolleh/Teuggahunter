from fastapi import FastAPI, Depends
from app.services.flight_service import FlightService
from app.gmail.email_service import get_all_labels

app = FastAPI()

def get_flight_service():
    return FlightService()

@app.get("/")
async def root():
    return {"message": "Welcome to Teuggahunter API"}

@app.get("/emails")
async def get_emails(flight_service: FlightService = Depends(get_flight_service)):
    """
    Gmail 계정의 모든 사용자 라벨에 대해 최신 이메일을 처리합니다.
    """
    # 사용자가 만든 라벨 가져오기
    labels = get_all_labels()
    
    results = []
    for label in labels:
        try:
            result = await flight_service.process_latest_email(label)
            results.append(result)
        except Exception as e:
            print(f"Error processing label {label}: {str(e)}")
            continue
    
    return {
        "total_labels": len(labels),
        "results": results
    } 