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

## Структура

```
qr-code-generator/
├── app.py                     # Весь backend: vCard + QR + Flask-роуты
├── static/                    # style.css, main.js, white_page_square.png (фон)
├── templates/                 # index.html (форма + предпросмотр)
├── logs/                      # info.log — создаётся в рантайме, в .gitignore
├── openspec/                  # OpenSpec: config.yaml, specs/, changes/
├── .opencode/                 # Скиллы и команды opsx-* для opencode
├── input/                     # ВСПОМОГАТЕЛЬНЫЕ ДАННЫЕ: не читать, не использовать, не коммитить
├── VERSION                    # Текущая версия проекта
├── CHANGELOG.md               # История изменений
└── backlog.md                 # Идеи и планируемые улучшения
```

## Запуск и проверка

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000 (debug=True)
```

Тесты:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Проверка изменений: сначала `python -m pytest`, затем при необходимости ручная —
запустить приложение, сгенерировать QR-код через форму, отсканировать камерой телефона.

## Конвенции

- Язык кода, комментариев и UI — **русский**.
- Коммит-сообщения — на русском (см. git log).
- Весь backend живёт в `app.py`; не раздувать архитектуру без необходимости.
- Папка `logs/` и файлы `*.log` не коммитятся.
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

- Данные компании (название, сайт, адрес) захардкожены в `generate_vcard()` — это осознанное решение, см. readme.
- Позиция QR на фоне — константы `QR_X_POS` / `QR_Y_POS` в начале `app.py`.
- В `app.py:117` есть безобидная «осиротевшая» строка `Flask` — не трогать без отдельной задачи.
- `debug=True` и `host="127.0.0.1"` — для локального запуска; при деплое менять осознанно.
