from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from src.routes.feedback import router as feedback_router
from src.config.database.init_db import init_models

app = FastAPI()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Роутинг
app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])

@app.on_event("startup")
async def on_startup():
    await init_models()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)