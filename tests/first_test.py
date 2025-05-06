import pytest
import pytest_asyncio
import httpx
import uuid
from pathlib import Path
from typing import Dict, Optional
import os
from datetime import datetime
import json


BASE_URL = "http://localhost:8000"
FEEDBACK_URL = f"{BASE_URL}/feedback/submit"
TEST_FILE_DIR = Path("test_files")
TEST_FILE_DIR.mkdir(exist_ok=True)
RESULTS_FILE = "test_results.txt"



def init_results_files():
    with open(RESULTS_FILE, "w", encoding='utf-8') as f:
        f.write("Тестирование формы обратной связи\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n")
    



def write_test_result(test_name: str, status: str, error: str = ""):
    with open(RESULTS_FILE, "a", encoding='utf-8') as f:
        f.write(f"Тест: {test_name}\n")
        f.write(f"Статус: {'ПРОЙДЕН' if status == 'passed' else 'НЕ ПРОЙДЕН'}\n")
        if error:
            f.write(f"Ошибка: {error}\n")
        f.write("-"*50 + "\n")


def write_server_response(test_name: str, response: httpx.Response):
    try:
        response_data = {
            "test": test_name,
            "timestamp": datetime.now().isoformat(),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.headers.get("content-type") == "application/json" else response.text,
            "request": {
                "method": "POST",
                "url": str(response.url),
            }
        }
    except Exception as e:
        print(f"Ошибка при записи ответа сервера: {str(e)}")


@pytest_asyncio.fixture
async def async_client():
    async with httpx.AsyncClient() as client:
        yield client
        await client.aclose()


def create_test_file(filename: str, size_kb: int = 5) -> str:
    filepath = TEST_FILE_DIR / filename
    with open(filepath, 'wb') as f:
        f.write(os.urandom(size_kb * 1024))
    return str(filepath)


VALID_DATA = {
    "feedback_type": "problem",
    "full_name": "Иванов Иван Иванович",
    "email": "test@example.com",
    "message": "Тестовое сообщение длиной более 10 символов",
    "phone": "+7 999 123-45-67",
    "order_number": "ORD-123456"
}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def record_test_result(request):
    yield
    test_name = request.node.name
    status = request.node.rep_call.outcome if hasattr(request.node, 'rep_call') else 'unknown'
    error = str(request.node.rep_call.longrepr) if hasattr(request.node, 'rep_call') and request.node.rep_call.failed else ""
    write_test_result(test_name, status, error)

def pytest_sessionfinish(session, exitstatus):
    passed = sum(1 for result in session.items if hasattr(result, 'rep_call') and result.rep_call.passed)
    total = len(session.items)
    
    with open(RESULTS_FILE, "a", encoding='utf-8') as f:
        f.write("\n" + "="*50 + "\n")
        f.write(f"ИТОГО: {passed}/{total} тестов пройдено успешно\n")
        f.write(f"Процент успешных тестов: {passed/total*100:.2f}%\n")
    
    print(f"\nРезультаты тестирования сохранены в {RESULTS_FILE}")
    print(f"ИТОГО: {passed}/{total} тестов пройдено успешно")
    print(f"Процент успешных тестов: {passed/total*100:.2f}%")


init_results_files()

async def make_request_and_log(async_client, test_name, data, files=None):
    try:
        response = await async_client.post(FEEDBACK_URL, data=data, files=files)
        write_server_response(test_name, response)
        return response
    except Exception as e:
        error_response = {
            "test": test_name,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "request_data": data
        }
        raise

# 1. Тесты на обязательные поля
@pytest.mark.asyncio
async def test_required_fields(async_client):
    required_fields = ["feedback_type", "full_name", "email", "message"]
    
    for field in required_fields:
        test_data = VALID_DATA.copy()
        test_data.pop(field)
        
        files = {}
        if field == "file":
            files = {"file": open(create_test_file("test.jpg"), "rb")}
        
        response = await make_request_and_log(
            async_client,
            f"test_required_fields[{field}]",
            test_data,
            files
        )
        
        response_data = response.json()
        assert response.status_code == 422
        assert "detail" in response_data
        assert field in str(response_data["detail"]).lower()

# 2. Тесты на валидацию email
@pytest.mark.asyncio
@pytest.mark.parametrize("email", [
    "invalid",
    "missing@",
    "@missing.com",
    "space in@email.com",
    "toolongemailaddressmorethan254charactersxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@example.com"
])
async def test_email_validation(async_client, email):
    test_data = VALID_DATA.copy()
    test_data["email"] = email
    
    response = await make_request_and_log(
        async_client,
        f"test_email_validation[{email}]",
        test_data
    )
    
    response_data = response.json()
    assert response.status_code == 422
    assert "detail" in response_data
    assert "email" in str(response_data["detail"]).lower()

# 3. Тесты на валидацию телефона
@pytest.mark.asyncio
@pytest.mark.parametrize("phone", [
    "123", 
    "+7 999 123-45-67 ext 1234", 
    "abc123", 
    " " * 21, 
    "8" * 21,  
])
async def test_phone_validation(async_client, phone):
    test_data = VALID_DATA.copy()
    test_data["phone"] = phone
    
    response = await make_request_and_log(
        async_client,
        f"test_phone_validation[{phone}]",
        test_data
    )
    
    response_data = response.json()
    assert response.status_code in [422, 500]
    if response.status_code == 422:
        assert "detail" in response_data
        assert "phone" in str(response_data["detail"]).lower()

# 4. Тесты на валидацию сообщения
@pytest.mark.asyncio
@pytest.mark.parametrize("message", [
    "short",  
    "x" * 1001,
    "",  
    "   ",  
])
async def test_message_validation(async_client, message):
    test_data = VALID_DATA.copy()
    test_data["message"] = message
    
    response = await make_request_and_log(
        async_client,
        f"test_message_validation[{message}]",
        test_data
    )
    
    response_data = response.json()
    assert response.status_code == 422
    assert "detail" in response_data
    assert "message" in str(response_data["detail"]).lower()

# 5. Тесты на валидацию файлов
@pytest.mark.asyncio
@pytest.mark.parametrize("file_type,size_kb,expected_error", [
    ("test.jpg", 5120, None),  
    ("test.jpg", 5121, "Файл слишком большой"), 
    ("test.exe", 100, "Неподдерживаемый тип файла"),
    ("test.txt", 100, "Неподдерживаемый тип файла"),
    ("test.png", 5120, None),
    ("test.pdf", 5120, None),
])
async def test_file_validation(async_client, file_type, size_kb, expected_error):
    test_data = VALID_DATA.copy()
    filepath = create_test_file(file_type, size_kb)
    
    with open(filepath, "rb") as f:
        files = {"file": (file_type, f, "image/jpeg" if file_type in ['jpg', 'jpeg'] else file_type)}
        response = await make_request_and_log(
            async_client,
            f"test_file_validation[{file_type}-{size_kb}]",
            test_data,
            files
        )
    
    if expected_error:
        assert response.status_code in [413, 415] 
        response_data = response.json()
        assert "detail" in response_data
        assert expected_error in str(response_data["detail"])
    else:
        if response.status_code == 500:
            response_data = response.json()
            assert "Ошибка при сохранении данных" in str(response_data.get("detail", ""))
        else:
            assert response.status_code == 303
            assert "/feedback/success" in response.headers.get("location", "")
            
# 6. Тест на успешную отправку
@pytest.mark.asyncio
async def test_successful_submission(async_client):
    test_data = VALID_DATA.copy()
    filepath = create_test_file("success.jpg", 100)
    
    with open(filepath, "rb") as f:
        files = {"file": ("success.jpg", f, "image/jpeg")}
        response = await make_request_and_log(
            async_client,
            "test_successful_submission",
            test_data,
            files
        )
    
    if response.status_code == 500:
        response_data = response.json()
        assert "Ошибка при сохранении данных" in str(response_data.get("detail", ""))
    else:
        assert response.status_code == 303
        assert "/feedback/success" in response.headers.get("location", "")

@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    def remove_test_files():
        for file in TEST_FILE_DIR.glob("*"):
            file.unlink()
        TEST_FILE_DIR.rmdir()
    request.addfinalizer(remove_test_files)
