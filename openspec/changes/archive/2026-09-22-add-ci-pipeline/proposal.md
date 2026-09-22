# Proposal: add-ci-pipeline

## Why

В проекте есть 21 автотест, но они запускаются только локально. Конвейер GitHub Actions будет прогонять тесты на каждый push в `main` и каждый pull request — регрессии станут видны до слияния. Первым испытанием конвейера станет PR `fix-backlogs` → `main` (8 релизов, v1.1.0–v2.2.0) — давно планируемое слияние после закрытия backlog.

## What Changes

- Создаётся `.github/workflows/ci.yml`: стандартный конвейер для Python-проекта — checkout, setup-python (версия из `.python-version`), кэш pip, установка зависимостей, запуск `pytest`.
- Триггеры: push в `main` и pull request в `main` (стандартная практика).
- Создаётся pull request `fix-backlogs` → `main` (через `gh`), конвейер запускается, результат контролируется; при ошибках — доклад пользователю.
- После зелёного конвейера PR вливается в `main` — это и есть давно откладываемое слияние `fix-backlogs`.

## Capabilities

### New Capabilities

_(пусто — поведение приложения не изменяется)_

### Modified Capabilities

_(пусто — поведение приложения не изменяется)_

Дельты спек отсутствуют намеренно: CI — tooling, spec-level поведение не меняется. В `.openspec.yaml` установлен `skip_specs: true`.

## Impact

- **Код приложения:** не затрагивается.
- **Новые файлы:** `.github/workflows/ci.yml`.
- **Изменённые файлы:** `VERSION` (2.2.1), `CHANGELOG.md`, `readme.md` (бейдж/упоминание CI — опционально), `AGENTS.md` (проверка через CI).
- **GitHub:** новый PR `fix-backlogs` → `main`; после мерджа `main` получает v2.2.0.
- **Версия:** 2.2.0 → 2.2.1 (tooling, patch).

## Не входит в объём (Non-goals)

- Линтеры (flake8/ruff/pylint), форматтеры, type-checking — отдельные улучшения при необходимости.
- Матрица версий Python (проект зафиксирован на 3.11, см. `.python-version`).
- Деплой/CD, публикация артефактов, релизные теги.
- Валидация OpenSpec в CI (требует установки openspec CLI — усложнение без явной пользы).
