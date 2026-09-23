# AGENTS.md

Контекст проекта для AI-агентов (opencode и др.).

## Что это за проект

Веб-приложение на Flask, генерирующее QR-код с контактом в формате vCard.
Пользователь заполняет форму (ФИО, должность, email, телефоны), приложение
создаёт vCard, кодирует её в QR-код и накладывает на фоновое изображение.
Результат показывается на странице, его можно скачать (PNG) или распечатать.

## Стек

- **Backend:** Python 3, Flask 3.0.2
- **Библиотеки:** `qrcode` (QR), `vobject` (vCard), `Pillow` (композиция изображения)
- **Frontend:** чистые HTML (Jinja2), CSS, JavaScript — без фреймворков и сборки
- **Тесты:** pytest (`tests/`, dev-зависимости в `requirements-dev.txt`)
- **Production-развертывание:** Docker + docker compose, gunicorn (WSGI), за nginx reverse proxy

## Структура

```
qr-code-generator/
├── app.py                     # Весь backend: vCard + QR + Flask-роуты
├── static/                    # style.css, main.js
├── templates/                 # index.html (форма + предпросмотр)
├── Dockerfile                 # Production-образ (python:3.11-slim + gunicorn, порт 8000)
├── docker-compose.yml         # Запуск контейнера: container_name qr-app, общая сеть nginx-net, env_file, restart, ротация логов
├── .dockerignore              # Исключения из образа (.env, .venv, logs/ и др.)
├── DEPLOY.md                  # Инструкция для админа: развертывание на сервере (+ адаптация под другие приложения)
├── openspec/                  # OpenSpec: config.yaml, specs/, changes/
├── .opencode/                 # Скиллы и команды opsx-* для opencode
├── input/                     # ВСПОМОГАТЕЛЬНЫЕ ДАННЫЕ: не читать, не использовать, не коммитить
├── VERSION                    # Текущая версия проекта
├── CHANGELOG.md               # История изменений
└── backlog.md                 # Идеи и планируемые улучшения
```

## Запуск и проверка

Локальная разработка:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000 (debug=True)
```

Production (Docker):

```bash
docker network create nginx-net  # один раз: общая сеть с nginx (reverse proxy)
docker compose up -d --build     # сборка и запуск (контейнер qr-app, порт на хост не публикуется)
docker compose logs -f           # логи (приложение пишет только в stdout)
docker compose down              # остановка
```

Тесты:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Проверка изменений: сначала `python -m pytest`, затем при необходимости ручная —
запустить приложение, сгенерировать QR-код через форму, отсканировать камерой телефона.
На GitHub работает CI (`.github/workflows/ci.yml`): на push в `main` и на каждый
pull request в `main` прогоняются тесты, затем собирается Docker-образ
(проверка, что Dockerfile не сломан; без публикации в registry).

## Конвенции

- Язык кода, комментариев и UI — **русский**.
- Коммит-сообщения — на русском (см. git log).
- Весь backend живёт в `app.py`; не раздувать архитектуру без необходимости.
- **Папка `input/` — служебная: не читать её содержимое, не использовать в коде, не коммитить.**

## Работа с изменениями: OpenSpec

В проекте используется spec-driven workflow через OpenSpec
(CLI `openspec`, конфиг `openspec/config.yaml`).

- Спецификации возможностей: `openspec/specs/<capability>/spec.md`
- Активные изменения: `openspec/changes/<change-name>/` (proposal.md, design.md, tasks.md, specs/)
- Архив завершённых: `openspec/changes/archive/`
- Команды opencode: `/opsx-explore`, `/opsx-propose`, `/opsx-apply`, `/opsx-archive`, `/opsx-update`, `/opsx-sync`

Правила:

1. Любое новое поведение/фича — сначала change proposal через OpenSpec, потом код.
2. Не создавать каталоги в `openspec/changes/` вручную — только `openspec new change "<name>"`.
3. После реализации изменение архивируется (`openspec archive`), дельты спеков синхронизируются в `openspec/specs/`.
4. При изменении версии обновлять `VERSION` и `CHANGELOG.md`.

## Известные нюансы кода

- Данные компании (название, сайт, адрес), значения полей формы и параметры запуска (`FLASK_DEBUG`/`FLASK_HOST`/`FLASK_PORT`) задаются в `.env` (см. readme, раздел «Настройка»).
- Логи пишутся только в stdout: в контейнере их собирает Docker (`docker compose logs`, ротация json-file 10 МБ × 3 в `docker-compose.yml`), при локальном запуске видны в консоли. Файл `logs/info.log` не ведётся.
- В Docker приложение запускает gunicorn (порт 8000, workers из `GUNICORN_WORKERS`, по умолчанию 2); переменные `FLASK_*` в контейнере не используются.
- Версия Python зафиксирована в `.python-version` (3.11.1).
