from fastapi import FastAPI, Depends, Request, Header, HTTPException
from app.services.flight_service import FlightService
from app.config import WEBHOOK_SECRET
import logging

app = FastAPI()

logger = logging.getLogger("teuggahunter")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
else:
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_flight_service():
    return FlightService()

@app.get("/")
async def root():
    return {"message": "Welcome to Teuggahunter API"}

# @app.get("/emails")
# async def get_emails(flight_service: FlightService = Depends(get_flight_service)):
#     """
#     Gmail 계정의 모든 사용자 라벨에 대해 최신 이메일을 처리합니다.
#     """
#     # 사용자가 만든 라벨 가져오기
#     labels = get_all_labels()
#     
#     results = []
#     for label in labels:
#         try:
#             result = await flight_service.process_latest_email(label)
#             results.append(result)
#         except Exception as e:
#             print(f"Error processing label {label}: {str(e)}")
#             continue
#     
#     return {
#         "total_labels": len(labels),
#         "results": results
#     }

@app.post("/emails")
async def receive_email(request: Request, x_webhook_secret: str = Header(None)):
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = await request.json()
    flight_service = FlightService()
    result = await flight_service.process_email(data)
    return {"status": "ok", "result": result}