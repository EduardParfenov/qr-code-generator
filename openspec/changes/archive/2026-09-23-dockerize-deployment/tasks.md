# Задачи: переход на развертывание в Docker

## 1. Зависимости и логирование

- [x] 1.1 Добавить `gunicorn` (зафиксированная версия) в `requirements.txt`; проверка: `pip install -r requirements.txt` в свежем venv ставит gunicorn
- [x] 1.2 В `app.py` заменить логирование на stdout-only: удалить `RotatingFileHandler`, `os.makedirs("./logs", ...)` и импорт `logging.handlers`, оставить `logging.StreamHandler()` в `logging.basicConfig` (комментарии на русском); проверка: при локальном запуске `python app.py` записи о vCard выводятся в консоль, файлы `logs/` не создаются
- [x] 1.3 В `tests/test_app.py` заменить тест ротации (`test_log_handler_has_rotation`) на тест, что логи идут в stdout (StreamHandler + запись видна через caplog/capsys); проверка: `python -m pytest` — все тесты зелёные

## 2. Dockerfile, .dockerignore, compose

- [x] 2.1 Создать `Dockerfile` по каркасу из design.md (python:3.11-slim, `ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1`, `WORKDIR /app`, сначала `requirements.txt` + `pip install --no-cache-dir`, затем копирование `app.py`, `templates/`, `static/`, `EXPOSE 8000`, `CMD` с gunicorn и `${GUNICORN_WORKERS:-2}`); проверка: файл на месте, команды соответствуют design.md
- [x] 2.2 Создать `.dockerignore` (исключить `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `logs/`, `.env`, `input/`, `openspec/`, `.github/`, `.opencode/`); проверка: `docker build` не пересылает исключённые пути в контекст
- [x] 2.3 Создать `docker-compose.yml` по каркасу из design.md (`build: .`, `container_name: qr-app`, внешняя сеть `nginx-net` без публикации портов, `env_file: .env`, `restart: unless-stopped`, `logging` json-file 10m × 3); проверка: `docker compose config` выводит валидную конфигурацию без ошибок
- [x] 2.4 Собрать образ `docker compose build` (или `docker build -t qr-code-generator .`); проверка: сборка завершается без ошибок, в образе нет `.env`, `.venv/`, `input/` (`docker run --rm qr-code-generator ls -la /app`)

## 3. Проверка контейнера

- [x] 3.1 Создать сеть `docker network create nginx-net`, запустить `docker compose up -d`; проверка: из контейнера в той же сети `curl http://qr-app:8000/` возвращает HTTP 200 с формой, порт на хосте не опубликован (`curl http://127.0.0.1:8001/` недоступен)
- [x] 3.2 Сгенерировать QR-код через форму в контейнере (POST на `http://qr-app:8000/generate` из сети nginx-net); проверка: запись о vCard видна в `docker compose logs` (stdout), файлы `logs/` не создаются ни в контейнере, ни на хосте
- [x] 3.3 Перезапустить с `GUNICORN_WORKERS=4` (через `.env` или окружение); проверка: в `docker compose logs` видно 4 worker-процесса
- [x] 3.4 Запустить контейнер без переменных окружения; проверка: приложение отвечает и генерирует vCard с демо-значениями
- [x] 3.5 Проверить restart-политику: `docker compose restart` — контейнер поднимается, `docker compose logs` показывает накопленные логи

## 4. CI, документация и релиз

- [x] 4.1 В `.github/workflows/ci.yml` добавить шаг «Собрать Docker-образ» (`docker build .`) после шага тестов; проверка: push/PR прогоняет тесты, затем сборку, пайплайн зелёный
- [x] 4.2 Обновить `readme.md`: раздел «Запуск в Docker» (общая сеть `nginx-net`, compose up/build, `env_file`, `GUNICORN_WORKERS`, пример `conf.d/qr.conf` для nginx в контейнере с `proxy_pass` на имя контейнера, нюансы порядка запуска и reload nginx, пояснение про несколько проектов на сервере); раздел «Логирование» переписать: логи в stdout, как смотреть (`docker compose logs -f`, `--tail`, `--since`), где хранятся (json-file Docker), ротация 10 МБ × 3, выгрузка аудита; отметить, что `FLASK_HOST`/`FLASK_PORT` — только для локального запуска; проверка: по инструкции можно повторить задачи 3.1–3.2
- [x] 4.3 Обновить `AGENTS.md`: стек (+ gunicorn, Docker), раздел «Запуск и проверка» (Docker как production-способ), структура (+ `Dockerfile`, `.dockerignore`, `docker-compose.yml`), удалить упоминания `logs/` и ротации из «Структуры» и «Известных нюансов»; проверка: описание соответствует репозиторию
- [x] 4.4 Обновить `VERSION` (minor — новая возможность) и `CHANGELOG.md` (запись о переходе на Docker, включая breaking: файл `logs/info.log` больше не ведётся); проверка: версия в CHANGELOG совпадает с VERSION
- [x] 4.5 Прогнать `python -m pytest`; проверка: все тесты зелёные
- [x] 4.6 Ручная проверка: запустить приложение локально (`python app.py`), сгенерировать QR-код через форму, отсканировать камерой телефона — контакт корректно распознаётся
