# Design: add-ci-pipeline

## Context

Проект: Python 3.11 (`.python-version`), зависимости `requirements.txt` + `requirements-dev.txt` (pytest), 21 тест в `tests/`, `conftest.py` в корне решает импорт `app`. Репозиторий на GitHub, CLI `gh` доступен. Ветка `fix-backlogs` опережает `main` на 8 релизов; слияние откладывалось до закрытия backlog — backlog закрыт. См. proposal.md — Why.

## Goals / Non-Goals

**Goals:**

- Конвейер запускает тесты на PR в `main` и push в `main`.
- Конфиг минимальный и идиоматичный — «как принято» для Python-проектов.
- PR `fix-backlogs` → `main` проходит проверку и вливается.

**Non-Goals:**

- Линт, матрица версий, CD, openspec-валидация в CI (см. proposal Non-goals).

## Decisions

1. **Один workflow `ci.yml`, один job `test` на `ubuntu-latest`.**
   Триггеры: `push` на `main` и `pull_request` на `main`. Шаги: `actions/checkout@v4` → `actions/setup-python@v5` → `pip install` → `pytest`. Это эталонный минимум для Python-проекта; усложнять нечего.
   _Альтернатива:_ матрица ОС/версий — отвергнута (Non-goals).

2. **Версия Python — из `.python-version`** (`python-version-file: ".python-version"` в setup-python).
   Единый источник правды: локальная разработка (pyenv) и CI читают один файл.
   _Альтернатива:_ хардкод `3.11` в ci.yml — отвергнута, рассинхрон при смене версии.

3. **Кэш pip** (`cache: "pip"` в setup-python) — стандартное ускорение, бесплатно.

4. **Установка обоих requirements** (`requirements.txt` + `requirements-dev.txt`) — тестам нужен и Flask, и pytest. Запуск: `python -m pytest -v`.

5. **PR и контроль через `gh`:** `gh pr create --base main --head fix-backlogs`, наблюдение `gh run watch` / `gh pr checks`. При падении — доклад пользователю с логом, фикс только после его решения (или новый change, если правка нетривиальна).
   Мердж (`gh pr merge`) — отдельный шаг после зелёного конвейера; это завершает плановое слияние `fix-backlogs` в `main`.

## Risks / Trade-offs

- [CI упадёт из-за окружения (например, tz/locale-зависимости тестов)] → Тесты изолированы (monkeypatch), зависимостей от окружения не выявлено; при падении — анализ лога и доклад.
- [Первый workflow-триггер на PR требует разрешения Actions в репозитории] → Обычно включено по умолчанию; если выключено — подскажем включить в Settings → Actions.
- [Мердж PR изменит `main` — это и есть цель] → Fast-forward не гарантирован (PR-мердж создаст merge commit, если политика репозитория иная — примем дефолтную).

## Migration Plan

1. Реализовать и закоммитить `ci.yml` в `fix-backlogs`, push.
2. Создать PR → конвейер запускается автоматически.
3. Зелёный конвейер → мердж → `main` = v2.2.0 (+ этот change в следующем коммите).
4. Откат конвейера: удалить `.github/workflows/ci.yml`; откат мерджа — `git revert` merge-коммита.
