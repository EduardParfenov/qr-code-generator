# Backlog

Идеи и планируемые улучшения. Каждый пункт перед реализацией оформляется
как change proposal через OpenSpec (`/opsx-propose`).

## Улучшения

- [ ] **Проверить кодировку кириллицы в vCard** — явный CHARSET=UTF-8 для совместимости со старыми телефонами.

## Техдолг

_(пусто)_

## Архивировано

- [x] **Вынести настройки компании из кода в конфиг** — реализовано в change `externalize-company-config` (v1.1.0): настройки компании, параметры QR и значения полей формы вынесены в `.env` + `.env.example`.
- [x] **Тесты** — реализовано в change `add-tests` (v1.1.1): 9 тестов на pytest (юнит-тесты функций + smoke-тесты роутов), запуск `python -m pytest`.
- [x] **Валидация ввода на сервере** — реализовано в change `add-server-validation` (v1.2.0): проверка обязательных полей и формата email, HTTP 400 с человекочитаемыми ошибками вместо 500.
- [x] **Валидация на клиенте** — реализовано в change `add-client-validation` (v1.3.0): маски телефонов `+7(XXX)XXX-XX-XX`, фильтр добавочного, проверка email до отправки без перезагрузки страницы.
- [x] **Убрать фоновое изображение** — реализовано в change `remove-background-image` (v2.0.0, BREAKING): чистый QR без композиции, удалены ассет и настройки `QR_X_POS`/`QR_Y_POS`/`QR_SIZE_RATIO`.
- [x] **Пустой добавочный номер, строка `Flask`, debug/host в `.env`, версия Python, ротация логов** — реализовано в change `housekeeping-fixes` (v2.1.0): пустые `TEL` не попадают в vCard, параметры запуска `FLASK_DEBUG`/`FLASK_HOST`/`FLASK_PORT` в `.env`, `.python-version` (3.11.1), ротация `logs/info.log` (1 МБ × 3), удалена мёртвая строка `Flask`.
- [x] **Кнопка «Шаблоны визиток»** — реализовано в change `configurable-card-template-link` (v2.2.0): адрес в `.env` (`CARD_TEMPLATE_URL`), без переменной кнопка скрыта; захардкоженная ссылка `localfile:...` удалена.
- [x] **Синхронизировать readme.md с кодом (раздел «Логирование»)** — реализовано в change `sync-readme-logging-section` (v2.5.0): текст приведён в соответствие с реальным поведением логирование.
- [x] **Fallback для кнопки «Копировать» без HTTPS** — реализовано в change `copy-button-fallback-tooltip` (v2.5.0): при недоступном Clipboard API показывается подсказка «Скопируйте через правый клик по изображению».
- [x] **Обновить readme.md (остальные разделы)** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): раздел «Формат номера телефона» приведён в соответствие с кодом, обновлена структура проекта.
- [x] **Убрать `enctype="multipart/form-data"` из формы** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): атрибут удалён, файлы не загружаются.
- [x] **Добавить тесты на маску телефона (JS)** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): создан `tests/test_format_phone.js` с 9 тестами для `formatPhone()`.
- [x] **Добавить обработку ошибок при генерации QR** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): try/except с человекочитаемым сообщением вместо HTTP 500.
- [x] **Удалить неиспользуемые константы** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): `MAX_FIELD_LENGTH`, `MAX_NAME_LENGTH`, `MAX_EMAIL_LENGTH` удалены из app.py.
- [x] **Обновить контекст в openspec/config.yaml** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): описание структуры приведено в соответствие с реальностью.
- [x] **Удалить мёртвый CSS** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): `.file-input`, `.help-text`, `input[type="checkbox"]` удалены из style.css.
- [x] **Удалить мёртвый HTML** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): закомментированный `IIS_PROXY_TEST` удалён из index.html.
- [x] **Удалить мёртвую функцию generate_qr_image** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): функция удалена из app.py.
- [x] **Инкапсулировать showCopyTooltip в main.js** — реализовано в change `backlog-improvements-and-techdebt` (v2.5.0): функция перемещена внутрь `DOMContentLoaded`.
