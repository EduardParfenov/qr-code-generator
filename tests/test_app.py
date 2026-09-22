"""
Тесты приложения qr-code-generator.

Запуск из корня проекта:
    pip install -r requirements-dev.txt
    python -m pytest
"""
import logging
from logging.handlers import RotatingFileHandler

import pytest
import vobject

from app import (
    app,
    generate_vcard,
    generate_qr_code,
    create_business_card,
    validate_form,
)

# Переменные окружения, влияющие на vCard
COMPANY_ENV_VARS = [
    "COMPANY_NAME",
    "COMPANY_SITE",
    "COMPANY_ADDRESS_STREET",
    "COMPANY_ADDRESS_CITY",
    "COMPANY_ADDRESS_REGION",
    "COMPANY_ADDRESS_CODE",
    "COMPANY_ADDRESS_COUNTRY",
]

# Демо-значения по умолчанию (как в app.py)
DEFAULT_COMPANY_NAME = 'ООО "Рога и копыта"'
DEFAULT_COMPANY_SITE = "roga-i-kopyta.com"

TEST_DATA = dict(
    name="Иванов Иван Иванович",
    job_title="Инженер",
    email="ivanov@test.ru",
    phone="+7(800)000-00-00",
    ext_phone="12-34",
    mobile="+7(900)111-22-33",
)


@pytest.fixture
def clean_company_env(monkeypatch):
    """Убирает COMPANY_* из окружения — тесты дефолтов не зависят от .env"""
    for var in COMPANY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


# --- generate_vcard ---

def test_vcard_contains_all_fields(clean_company_env):
    vcard = generate_vcard(**TEST_DATA)
    assert f"FN:{TEST_DATA['name']}" in vcard
    assert TEST_DATA["job_title"] in vcard
    assert f"EMAIL:{TEST_DATA['email']}" in vcard
    assert TEST_DATA["phone"] in vcard
    assert TEST_DATA["mobile"] in vcard
    assert "TYPE=WORK" in vcard
    assert "TYPE=CELL" in vcard
    assert "URL:" in vcard
    assert "ADR" in vcard


def test_vcard_is_valid(clean_company_env):
    """Сериализованная vCard парсится обратно без ошибок"""
    vcard = generate_vcard(**TEST_DATA)
    parsed = vobject.readOne(vcard)
    assert parsed.fn.value == TEST_DATA["name"]
    assert parsed.email.value == TEST_DATA["email"]


def test_vcard_uses_defaults_without_env(clean_company_env):
    vcard = generate_vcard(**TEST_DATA)
    assert DEFAULT_COMPANY_NAME in vcard
    assert DEFAULT_COMPANY_SITE in vcard


def test_vcard_reads_company_from_env(monkeypatch):
    monkeypatch.setenv("COMPANY_NAME", "ООО «Тестовая компания»")
    monkeypatch.setenv("COMPANY_SITE", "test-company.ru")
    vcard = generate_vcard(**TEST_DATA)
    assert "ООО «Тестовая компания»" in vcard
    assert "test-company.ru" in vcard


def test_vcard_with_empty_optional_phones(clean_company_env):
    """Пустые необязательные телефоны НЕ попадают в vCard"""
    data = {**TEST_DATA, "ext_phone": "", "mobile": ""}
    vcard = generate_vcard(**data)
    parsed = vobject.readOne(vcard)
    assert parsed.fn.value == TEST_DATA["name"]
    tel_lines = [l for l in vcard.splitlines() if l.startswith("TEL")]
    assert len(tel_lines) == 1  # только рабочий телефон
    assert "TYPE=CELL" not in vcard


def test_vcard_with_filled_mobile_only(clean_company_env):
    """Заполненный мобильный попадает в vCard, пустой добавочный — нет"""
    data = {**TEST_DATA, "ext_phone": ""}
    vcard = generate_vcard(**data)
    tel_lines = [l for l in vcard.splitlines() if l.startswith("TEL")]
    assert len(tel_lines) == 2  # рабочий + мобильный
    assert "TYPE=CELL" in vcard


# --- generate_qr_code ---

def test_qr_code_returns_square_image():
    # qrcode возвращает обёртку PilImage, делегирующую .size внутреннему PIL-объекту,
    # поэтому проверяем размер, а не конкретный класс
    vcard = generate_vcard(**TEST_DATA)
    qr_image = generate_qr_code(vcard)
    width, height = qr_image.size
    assert width == height
    assert width > 0


# --- create_business_card ---

def test_business_card_returns_square_image():
    """Чистый QR-код: квадратное изображение без композиции с фоном"""
    card = create_business_card(**TEST_DATA)
    width, height = card.size
    assert width == height
    assert width > 0


# --- Роуты Flask (smoke-тесты) ---

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_returns_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'name="name"' in response.get_data(as_text=True)
    assert 'name="work_phone"' in response.get_data(as_text=True)


def test_generate_returns_image_preview(client):
    response = client.post("/generate", data={
        "name": TEST_DATA["name"],
        "job_title": TEST_DATA["job_title"],
        "email": TEST_DATA["email"],
        "work_phone": TEST_DATA["phone"],
        "ext_phone": TEST_DATA["ext_phone"],
        "mobile": TEST_DATA["mobile"],
    })
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "data:image/png;base64," in html
    assert TEST_DATA["name"] in html


# --- Серверная валидация ---

FORM_DATA = {
    "name": TEST_DATA["name"],
    "job_title": TEST_DATA["job_title"],
    "email": TEST_DATA["email"],
    "work_phone": TEST_DATA["phone"],
    "ext_phone": TEST_DATA["ext_phone"],
    "mobile": TEST_DATA["mobile"],
}


def test_validate_form_valid_data():
    assert validate_form(FORM_DATA) == []


def test_validate_form_required_fields():
    errors = validate_form({})
    assert len(errors) == 4  # ФИО, должность, рабочий телефон, email


def test_validate_form_strips_whitespace():
    data = {**FORM_DATA, "name": "   "}
    assert any("Ф.И.О." in e for e in validate_form(data))


def test_validate_form_bad_email():
    for bad_email in ["не-почта", "a@", "@b.ru", "a@b"]:
        assert validate_form({**FORM_DATA, "email": bad_email}), bad_email


def test_generate_missing_required_field_returns_400(client):
    data = {k: v for k, v in FORM_DATA.items() if k != "name"}
    response = client.post("/generate", data=data)
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Ф.И.О." in html
    assert "data:image/png;base64," not in html


def test_generate_bad_email_returns_400(client):
    response = client.post("/generate", data={**FORM_DATA, "email": "не-почта"})
    assert response.status_code == 400
    assert "e-mail" in response.get_data(as_text=True)


def test_generate_lists_all_errors(client):
    response = client.post("/generate", data={**FORM_DATA, "name": "", "email": "криво"})
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Ф.И.О." in html
    assert "e-mail" in html


def test_generate_valid_with_empty_optional_fields(client):
    response = client.post("/generate", data={**FORM_DATA, "ext_phone": "", "mobile": ""})
    assert response.status_code == 200


# --- Кнопка «Шаблоны визиток» ---

def test_card_template_button_hidden_without_env(monkeypatch, client):
    """Без CARD_TEMPLATE_URL кнопка не отображается — ни на форме, ни в результате"""
    monkeypatch.delenv("CARD_TEMPLATE_URL", raising=False)
    assert "card-template-btn" not in client.get("/").get_data(as_text=True)
    response = client.post("/generate", data=FORM_DATA)
    assert "card-template-btn" not in response.get_data(as_text=True)


def test_card_template_button_shown_with_env(monkeypatch, client):
    """С заданной CARD_TEMPLATE_URL кнопка видна и ведёт на заданный адрес"""
    monkeypatch.setenv("CARD_TEMPLATE_URL", "https://example.com/templates")
    response = client.post("/generate", data=FORM_DATA)
    html = response.get_data(as_text=True)
    assert "card-template-btn" in html
    assert 'href="https://example.com/templates"' in html


# --- Логирование ---

def test_log_handler_has_rotation():
    """Лог ротируется по размеру (RotatingFileHandler), а не растёт бесконечно"""
    assert any(isinstance(h, RotatingFileHandler) for h in logging.getLogger().handlers)
