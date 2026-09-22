# Tasks: configurable-card-template-link

## 1. Подготовка

- [x] 1.1 Создать change и артефакты (proposal, design, дельта спеки) — проверка: `openspec validate configurable-card-template-link --strict` проходит

## 2. Реализация

- [x] 2.1 Добавить `card_template_url` в `inject_form_defaults()` в `app.py` — проверка: переменная читается из `CARD_TEMPLATE_URL` с дефолтом `""`
- [x] 2.2 В `index.html` заменить захардкоженный блок кнопки на `{% if card_template_url %}` с `href="{{ card_template_url }}"` — проверка: `localfile:server` в шаблоне отсутствует
- [x] 2.3 Добавить закомментированную `CARD_TEMPLATE_URL` в `.env.example` с пояснением — проверка: пример есть, по умолчанию выключена

## 3. Тесты и документация

- [x] 3.1 Тесты: без переменной кнопки нет (GET / и POST /generate); с `monkeypatch.setenv` кнопка есть и href корректный — проверка: `python -m pytest` зелёный
- [x] 3.2 Обновить `readme.md` («Настройка»: `CARD_TEMPLATE_URL`), `VERSION` (2.2.0), `CHANGELOG.md` — проверка: записи есть
- [x] 3.3 `openspec validate configurable-card-template-link --strict` — проверка: валидация проходит

## 4. Ручная проверка

- [x] 4.1 Запустить приложение: без `CARD_TEMPLATE_URL` кнопки нет; с заданной `CARD_TEMPLATE_URL` в `.env` кнопка появляется и ведёт на заданный адрес — проверка в браузере
