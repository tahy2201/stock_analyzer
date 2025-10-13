import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analysis, candidates, companies, stocks
from shared.config.logging_config import setup_api_logging

# ログ設定
logger = setup_api_logging()

app = FastAPI(
    title="株式分析システム API",
    description="Stock Analysis System API",
    version="1.0.0"
)

# CORS設定 - 環境変数から許可するオリジンを取得
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの追加
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])

@app.get("/")
async def root():
    logger.info("APIルートエンドポイントへのアクセス")
    return {"message": "株式分析システム API"}

@app.get("/api/health")
async def health_check():
    logger.info("ヘルスチェックエンドポイントへのアクセス")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn

    # 環境変数から設定を取得
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    logger.info(f"APIサーバーを起動します: {host}:{port}")
    uvicorn.run(app, host=host, port=port)
