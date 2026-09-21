# Tasks: remove-background-image

## 1. Подготовка

- [x] 1.1 Создать change и артефакты (proposal, design, дельта спеки) — проверка: `openspec validate remove-background-image --strict` проходит

## 2. Реализация

- [x] 2.1 Упростить `create_business_card()` до vCard → QR, удалить константы `QR_X_POS`/`QR_Y_POS`/`QR_SIZE_RATIO` и PIL-импорт из `app.py` — проверка: в `app.py` нет упоминаний `white_page_square`, `QR_X_POS`, `from PIL`
- [x] 2.2 Удалить `static/white_page_square.png` — проверка: файл отсутствует, приложение работает
- [x] 2.3 Удалить `QR_X_POS`/`QR_Y_POS`/`QR_SIZE_RATIO` из `.env.example` — проверка: в файле нет этих переменных

## 3. Тесты и документация

- [x] 3.1 Обновить тест композиции: `test_business_card_matches_background_size` заменить на проверку квадратного изображения — проверка: `python -m pytest` зелёный (17 тестов)
- [x] 3.2 Обновить `readme.md` (убрать фон и настройки позиции из «Настройки» и описания возможностей) и `AGENTS.md` (структура static/, нюанс про QR_X_POS) — проверка: упоминаний `white_page_square`/`QR_X_POS` не осталось
- [x] 3.3 Обновить `VERSION` (2.0.0) и `CHANGELOG.md` с пометкой BREAKING — проверка: есть запись
- [x] 3.4 `openspec validate remove-background-image --strict` — проверка: валидация проходит

## 4. Ручная проверка

- [x] 4.1 Запустить приложение (`python app.py`), сгенерировать QR, отсканировать телефоном — проверка: чистый QR сканируется, контакт сохраняется, скачивание/печать работают
