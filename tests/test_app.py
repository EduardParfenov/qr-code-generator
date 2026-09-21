"""
Тесты приложения qr-code-generator.

Запуск из корня проекта:
    pip install -r requirements-dev.txt
    python -m pytest
"""
import io

import pytest
import vobject
from PIL import Image

from app import (
    app,
    generate_vcard,
    generate_qr_code,
    create_business_card,
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
    """Необязательные телефоны могут быть пустыми — vCard всё равно формируется"""
    data = {**TEST_DATA, "ext_phone": "", "mobile": ""}
    vcard = generate_vcard(**data)
    parsed = vobject.readOne(vcard)
    assert parsed.fn.value == TEST_DATA["name"]


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

def test_business_card_matches_background_size():
    card = create_business_card(**TEST_DATA)
    with Image.open("static/white_page_square.png") as template:
        assert card.size == template.size


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
