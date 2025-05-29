# Серверная часть: Анализ МРТ

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск сервера

```bash
uvicorn Server.main:app --reload
```

## Эндпоинт для анализа

- `POST /analyze/`
- Принимает файл изображения (JPG, PNG, DICOM)
- Возвращает результат анализа

Пример запроса можно сделать через Postman или curl:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" -F "file=@path_to_your_image.jpg"
``` 