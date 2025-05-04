from typing import Optional, Annotated  # Добавляем импорт Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import uuid
import re
import logging
from fastapi.responses import JSONResponse
from src.models.feedback import FeedbackCreate, FeedbackType
from src.services.feedback_service import FeedbackService
from src.config.database.db_helper import db_helper

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf"]

@router.get("/", response_class=HTMLResponse)
async def feedback_form(request: Request):
    return templates.TemplateResponse(
        "feedback_form.html",
        {
            "request": request,
            "feedback_types": [
                {"value": "suggestion", "label": "Предложение"},
                {"value": "problem", "label": "Проблема"},
                {"value": "complaint", "label": "Жалоба"},
                {"value": "other", "label": "Другое"},
            ],
            "example_data": {
                "full_name": "Иванов Иван Иванович",
                "email": "example@example.com",
                "phone": "+7 999 123-45-67",
                "order_number": "ORD-123456",
                "message": "Опишите вашу проблему или предложение здесь..."
            }
        }
    )

def validate_feedback_type(feedback_type: str) -> FeedbackType:
    """Проверка, что тип обращения допустимый"""
    try:
        return FeedbackType(feedback_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Недопустимый тип обращения. Допустимые значения: {', '.join([t.value for t in FeedbackType])}"
        )

async def validate_file(file: Optional[UploadFile]) -> Optional[str]:
    """Проверка и сохранение файла"""
    if not file or not file.filename:
        return None

    # Проверка типа файла по расширению (более надежно, чем content_type)
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['jpg', 'jpeg', 'png', 'pdf']:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Неподдерживаемый тип файла. Разрешены: JPG, PNG, PDF"
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE} байт"
        )

    upload_dir = Path("src/static/uploads")
    upload_dir.mkdir(exist_ok=True)
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"static/uploads/{file_name}"
    
    try:
        with open(Path("src") / file_path, "wb") as buffer:
            buffer.write(await file.read())
        return file_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )

@router.post("/submit")
async def submit_feedback(
    request: Request,
    feedback_type: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    phone: Optional[str] = Form(None),
    order_number: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    feedback_service: FeedbackService = Depends(),
):
    # Проверка типа обращения
    try:
        validated_type = validate_feedback_type(feedback_type)
    except HTTPException as e:
        logger.error(f"Ошибка валидации типа обращения: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

    # Валидация файла
    try:
        file_path = await validate_file(file)
    except HTTPException as e:
        logger.error(f"Ошибка валидации файла: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

    # Валидация данных через Pydantic
    try:
        feedback_data = FeedbackCreate(
            feedback_type=validated_type,
            full_name=full_name,
            email=email,
            phone=phone,
            message=message,
            order_number=order_number
        ).dict()
    except ValueError as e:
        logger.error(f"Ошибка валидации данных: {str(e)}")
        # Удаляем файл, если он был загружен до ошибки валидации
        if file_path:
            try:
                (Path("src") / file_path).unlink()
                logger.info(f"Удален файл {file_path} из-за ошибки валидации")
            except Exception as file_error:
                logger.error(f"Ошибка при удалении файла: {str(file_error)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)}
        )

    # Сохранение в базу
    try:
        feedback = await feedback_service.create_feedback(feedback_data, file_path)
        logger.info(f"Обращение успешно создано: ID {feedback.id}")
        # Исправляем возвращаемый ответ
        return RedirectResponse(url="/feedback/success", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Ошибка при сохранении в базу данных: {str(e)}", exc_info=True)
        # Удаляем файл, если он был загружен, но произошла ошибка БД
        if file_path:
            try:
                (Path("src") / file_path).unlink()
                logger.info(f"Удален файл {file_path} из-за ошибки базы данных")
            except Exception as file_error:
                logger.error(f"Ошибка при удалении файла: {str(file_error)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Произошла внутренняя ошибка сервера"}
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении в базу данных: {str(e)}", exc_info=True)
        # Удаляем файл, если он был загружен, но произошла ошибка БД
        if file_path:
            try:
                (Path("src") / file_path).unlink()
                logger.info(f"Удален файл {file_path} из-за ошибки базы данных")
            except Exception as file_error:
                logger.error(f"Ошибка при удалении файла: {str(file_error)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Произошла внутренняя ошибка сервера"}
        )

@router.get("/success", response_class=HTMLResponse)
async def feedback_success(request: Request):
    return templates.TemplateResponse("feedback_success.html", {"request": request})