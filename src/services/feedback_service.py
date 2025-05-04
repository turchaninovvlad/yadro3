from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.feedback import Feedback
from src.config.database.db_helper import db_helper
from sqlalchemy import text
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedbackService:
    async def create_feedback(self, feedback_data: Dict[str, Any], file_path: Optional[str] = None) -> Feedback:
        async with db_helper.get_db_session() as session:
            try:
                query = text("""
                    INSERT INTO feedback 
                    (feedback_type, full_name, email, phone, message, order_number, file_path, created_at)
                    VALUES 
                    (:feedback_type, :full_name, :email, :phone, :message, :order_number, :file_path, :created_at)
                    RETURNING *;
                """)
                
                logger.debug(f"Создание обращения с данными: {feedback_data}")
                
                # Добавляем текущую дату и время
                current_time = datetime.now()
                
                result = await session.execute(
                    query,
                    {
                        "feedback_type": feedback_data["feedback_type"],
                        "full_name": feedback_data["full_name"],
                        "email": feedback_data["email"],
                        "phone": feedback_data.get("phone"),
                        "message": feedback_data["message"],
                        "order_number": feedback_data.get("order_number"),
                        "file_path": file_path,
                        "created_at": current_time
                    }
                )
                
                await session.commit()
                feedback = result.fetchone()
                logger.info(f"Обращение успешно создано: {feedback}")
                return feedback
            except Exception as e:
                logger.error(f"Ошибка при выполнении SQL запроса: {str(e)}", exc_info=True)
                await session.rollback()
                raise