# Система обратной связи

Веб-приложение для обработки обратной связи с клиентами, реализованное на FastAPI. Позволяет пользователям отправлять обращения через интуитивную веб-форму с поддержкой файловых вложений.



## Основные возможности 

-  4 типа обращений: предложение, проблема, жалоба, другое
-  Загрузка файлов (JPG, PNG, PDF до 5MB)
-  Встроенная валидация данных (email, телефон, сообщение)
-  Автоматическое сохранение в SQLite базе
-  Логирование операций и обработка ошибок
-  Полноценное тестовое покрытие

## Структура проекта 
```
project
├── src                        
│ ├── config                   
│ │ └── database 
│ │     └── db_helper.py       # Менеджер сессий БД
│ ├── models                   
│ │   └── feedback.py          # Модель обратной связи
│ ├── routes                   
│ │   └── feedback.py          # Роуты формы
│ ├── services                 
│ │   └── feedback_service.py  # Сервис обработки
│ ├── static                   # CSS/JS, файлы
│ └── templates                # HTML шаблоны
├── tests                      
│   └── first_test.py          # Интеграционные тесты
└── main.py                    # Точка входа
```


## Установка и запуск для windows
Для установки надо:

1. Клонировать репозиторий

2. Создать виртуальную среду в проекте
```
python -m venv .venv 
```
3. Активировать её
```
.\.venv\Scripts\Activate.ps1
```

4. Установить зависимости
```
pip install -r requirements.txt 
```
5. Запустить main.py
```
python main.py
```

## Использование API 
Доступные эндпоинты:


  
  * GET	/feedback/	HTML форма обратной связи

  * POST	/feedback/submit	Отправка обращения

  * GET	/feedback/success	Страница успешной отправки

## Тестирование 

Запуск тестов:
```
 pytest tests/first_test.py -v
```

Тесты покрывают:

* Валидацию полей формы

* Обработку файлов

* Крайние случаи входных данных

* Ошибки базы данных

* Тестовая статистика

## Безопасность 
Реализованные меры защиты:

 * Экранирование HTML во всех полях ввода

 * Ограничение размера файлов (5MB)

 * Валидация MIME-типов файлов

 * Автоматическое удаление файлов при ошибках

 * Защита от SQL-инъекций через параметризованные запросы
