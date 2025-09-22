from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import analysis, companies, stocks

app = FastAPI(
    title="株式分析システム API",
    description="Stock Analysis System API",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの追加
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])

@app.get("/")
async def root():
    return {"message": "株式分析システム API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
