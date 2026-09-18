# Tasks: bootstrap-project

## 1. Инфраструктурные файлы

- [x] 1.1 Создать `AGENTS.md` — проверка: файл существует, содержит стек, структуру, конвенции и предупреждение про `input/`
- [x] 1.2 Создать `VERSION` со значением `1.0.0` — проверка: `cat VERSION` выводит `1.0.0`
- [x] 1.3 Создать `CHANGELOG.md` с записью 1.0.0 — проверка: файл существует, есть раздел `[1.0.0]`
- [x] 1.4 Создать `backlog.md` с идеями улучшений — проверка: файл существует, пункты оформлены чекбоксами
- [x] 1.5 Добавить `input/` в `.gitignore` — проверка: `git status` не показывает `input/`

## 2. Настройка OpenSpec

- [x] 2.1 Заполнить `context` в `openspec/config.yaml` — проверка: `openspec instructions proposal --change bootstrap-project --json` возвращает контекст проекта
- [x] 2.2 Добавить `rules` и `operations` в `openspec/config.yaml` — проверка: CLI не выводит предупреждений о формате rules

## 3. Спецификации

- [x] 3.1 Написать `proposal.md` — проверка: есть разделы Why, What Changes, Capabilities (3 новые), Impact, Non-goals
- [x] 3.2 Написать `design.md` — проверка: есть разделы Context, Goals/Non-Goals, Decisions (4 решения), Risks, Migration Plan
- [x] 3.3 Написать `specs/vcard-generation/spec.md` — проверка: Purpose + 2 требования со сценариями WHEN/THEN
- [x] 3.4 Написать `specs/qr-code-generation/spec.md` — проверка: Purpose + 2 требования со сценариями WHEN/THEN
- [x] 3.5 Написать `specs/web-interface/spec.md` — проверка: Purpose + 3 требования со сценариями WHEN/THEN
- [x] 3.6 Прогнать `openspec validate bootstrap-project --strict` — проверка: валидация проходит без ошибок

## 4. Исправление: запуск без папки logs/

- [x] 4.1 Добавить `os.makedirs("./logs", exist_ok=True)` перед настройкой логирования в `app.py` — проверка: при отсутствующей папке `logs/` `python app.py` стартует без `FileNotFoundError`
- [x] 4.2 Зафиксировать требование «Автоматическое создание директории логов» в `specs/vcard-generation/spec.md` — проверка: `openspec validate bootstrap-project --strict` проходит

## 5. Ручная проверка

- [x] 5.1 Запустить приложение (`python app.py`), сгенерировать QR-код через форму и отсканировать камерой телефона — проверка: приложение работает, контакт сохраняется (проверено пользователем в браузере)
- [x] 5.2 Заархивировать change (`openspec archive bootstrap-project`) — проверка: спеки появились в `openspec/specs/`, change в `openspec/changes/archive/`
