## Context

См. proposal.md — Why. Бэклог содержит 11 пунктов из ревью проекта: документация, мёртвый код, обработка ошибок, тесты.

## Goals / Non-Goals

**Goals:**
- Привести документацию в соответствие с кодом.
- Удалить мёртвый код (CSS, HTML, JS, Python).
- Добавить обработку ошибок при генерации QR.
- Добавить JS-тесты для `formatPhone()`.

**Non-Goals:**
- Настроить HTTPS.
- Изменить логику vCard или QR.
- Проверить кодировку кириллицы (требует реального устройства).

## Decisions

**1. Обработка ошибок при генерации QR**
Добавить try/except вокруг `create_business_card()` в роуте `/generate`. При ошибке возвращать HTTP 500 с человекочитаемым сообщением в шаблоне.

**2. Инкапсуляция `showCopyTooltip`**
Переместить функцию внутрь `DOMContentLoaded` в `main.js`, чтобы не загрязнять глобальную область.

**3. JS-тесты для `formatPhone()`**
Создать `tests/test_format_phone.js` с простыми assert-тестами (без фреймворков, Node.js). Покрыть: нормализацию 8/7, скобки, дефисы, обрезку до 10 цифр.

**4. Удаление мёртвого кода**
- `app.py`: константы `MAX_FIELD_LENGTH`, `MAX_NAME_LENGTH`, `MAX_EMAIL_LENGTH`, функция `generate_qr_image`.
- `style.css`: `.file-input`, `.help-text`, `input[type="checkbox"]`.
- `index.html`: закомментированный `IIS_PROXY_TEST`, `enctype="multipart/form-data"`.

## Risks / Trade-offs

- **Риск:** Нет. Изменения минимальные, мёртвый код не используется.
- **JS-тесты:** Не интегрированы в CI (нет Node.js в GitHub Actions). Запускаются вручную: `node tests/test_format_phone.js`.
