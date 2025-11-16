# Hackocats

Документирование сетей оператора связи

Зависимости:

- Python 3.13.0
- fastapi
- pydantic
- psycopg2
- uvicorn

## Предварительные требования

- Скачать и установить [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Убедитесь, что у вас установлена версия Python 3.13.0

## Установка и запуск

1. Установите зависимости проекта:

   ```bash
   pip install -r requirements.txt
   ```

2. Перейдите в директорию проекта:

   ```bash
   cd <путь к скачанной директории>
   ```

3. Запустите контейнеры (Docker Desktop должен быть включён):

   ```bash
   docker-compose up -d
   ```

4. Запустите сервер разработки:
   ```bash
   uvicorn server:app --reload
   ```

После запуска сервера карта будет доступна по адресу:  
http://localhost:8000
