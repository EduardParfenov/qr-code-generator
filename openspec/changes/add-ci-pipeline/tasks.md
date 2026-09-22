# Tasks: add-ci-pipeline

## 1. Конвейер

- [x] 1.1 Создать `.github/workflows/ci.yml`: job `test` на `ubuntu-latest`, триггеры push/PR на `main`, шаги checkout → setup-python (`.python-version`, cache pip) → install (requirements.txt + requirements-dev.txt) → `python -m pytest -v` — проверка: файл существует, YAML валиден (`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`)
- [x] 1.2 Обновить `VERSION` (2.2.1) и `CHANGELOG.md` — проверка: есть запись о CI
- [x] 1.3 Обновить `AGENTS.md` (проверка изменений — локальный pytest + CI на PR) — проверка: документ соответствует

## 2. Коммит и PR

- [ ] 2.1 Закоммитить в `fix-backlogs` и запушить — проверка: `git status` чист, ветка синхронизирована с origin
- [ ] 2.2 Создать PR `fix-backlogs` → `main` через `gh pr create` (заголовок/описание на русском: 8 релизов, закрытие backlog) — проверка: PR создан, ссылка выдана пользователю
- [ ] 2.3 Проконтролировать конвейер (`gh pr checks` / `gh run watch`) — проверка: job `test` завершился; при ошибках — лог и доклад пользователю, без самовольных фиксов

## 3. Слияние (после зелёного конвейера и подтверждения пользователя)

- [ ] 3.1 Влить PR в `main` (`gh pr merge`) — проверка: `main` содержит все релизы, PR закрыт
- [ ] 3.2 Обновить локальную `main` и вернуться на `fix-backlogs` — проверка: `git log --graph` показывает слияние

## 4. Ручная проверка

- [ ] 4.1 Локально `python -m pytest` зелёный, приложение запускается (`python app.py`) и генерирует QR — проверка: поведение не изменилось
