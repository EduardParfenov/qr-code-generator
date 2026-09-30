"""
Тесты приложения qr-code-generator.

Запуск из корня проекта:
    pip install -r requirements-dev.txt
    python -m pytest
"""
import logging

import pytest
import qrcode
import qrcode.util
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
    assert f"FN;CHARSET=UTF-8:{TEST_DATA['name']}" in vcard
    assert TEST_DATA["job_title"] in vcard
    assert f"EMAIL;CHARSET=UTF-8:{TEST_DATA['email']}" in vcard
    assert TEST_DATA["phone"] in vcard
    assert TEST_DATA["mobile"] in vcard
    assert "TYPE=WORK" in vcard
    assert "TYPE=CELL" in vcard
    assert "URL;CHARSET=UTF-8:" in vcard
    assert "ADR" in vcard
    assert "CHARSET=UTF-8" in vcard


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


# --- Кодировка кириллицы: CHARSET на всех полях и цепочка vCard -> QR ---

# Поля vCard, которые несут текст: каждая такая строка обязана объявлять CHARSET
TEXT_FIELDS = ("FN", "TITLE", "ADR", "EMAIL", "URL", "TEL")


def content_lines(vcard):
    """
    Строки содержимого vCard без продолжений переноса.

    Перенос длинной строки в vCard 3.0 — это CRLF и один пробел в начале
    следующей строки, поэтому продолжение начинается с пробела и не является
    новым полем: его собственный CHARSET не нужен и не проверяется.
    """
    return [
        line for line in vcard.splitlines()
        if not line.startswith((" ", "\t")) and ":" in line
        and not line.startswith(("BEGIN", "END", "VERSION"))
    ]


def test_charset_on_every_text_field_without_cyrillic(clean_company_env):
    """
    CHARSET=UTF-8 объявлен на каждом текстовом поле даже когда значение
    состоит только из латиницы и цифр: набор параметров не должен зависеть
    от того, вписал ли пользователь кириллицу.
    """
    data = dict(TEST_DATA, name="Ivanov Ivan", job_title="Engineer", mobile="+79001112233")
    vcard = generate_vcard(**data)
    checked = set()
    for line in content_lines(vcard):
        field = line.split(":", 1)[0].split(";", 1)[0]
        if field in TEXT_FIELDS:
            assert "CHARSET=UTF-8" in line.split(":", 1)[0], f"нет CHARSET в строке: {line}"
            checked.add(field)
    assert checked == set(TEXT_FIELDS), f"не проверены поля: {set(TEXT_FIELDS) - checked}"


def test_charset_on_optional_phones_with_cyrillic(clean_company_env):
    """Добавочный и мобильный с кириллицей тоже объявляют CHARSET"""
    data = {**TEST_DATA, "ext_phone": "доб. 12-34", "mobile": "+7(900)111-22-33 доб"}
    vcard = generate_vcard(**data)
    tel_lines = [line for line in content_lines(vcard) if line.startswith("TEL")]
    assert len(tel_lines) == 3  # рабочий + добавочный + мобильный
    for line in tel_lines:
        assert "CHARSET=UTF-8" in line.split(":", 1)[0], f"нет CHARSET в строке: {line}"


CYRILLIC_DATA = dict(
    name="Иванов Иван Иванович",
    job_title="Ведущий инженер",
    email="ivanov@рога.рф",
    phone="+7(800)000-00-00",
    ext_phone="доб. 12",
    mobile="+7(900)111-22-33",
)


def test_cyrillic_survives_round_trip(monkeypatch):
    """Кириллица в каждом поле читается обратно парсером в исходном виде"""
    monkeypatch.setenv("COMPANY_SITE", "рога-и-копыта.рф")
    monkeypatch.setenv("COMPANY_ADDRESS_STREET", "ул. Рогов и Копыт")
    parsed = vobject.readOne(generate_vcard(**CYRILLIC_DATA))
    assert parsed.fn.value == CYRILLIC_DATA["name"]
    assert parsed.email.value == CYRILLIC_DATA["email"]
    assert parsed.url.value == "рога-и-копыта.рф"
    tels = [t.value for t in parsed.contents["tel"]]
    assert CYRILLIC_DATA["phone"] in tels
    assert CYRILLIC_DATA["ext_phone"] in tels
    assert CYRILLIC_DATA["mobile"] in tels
    assert CYRILLIC_DATA["job_title"] in parsed.title.value
    assert "Рогов и Копыт" in parsed.adr.value.street


def test_qr_encodes_exact_utf8_bytes_of_vcard(clean_company_env):
    """
    В QR-код уходят те же UTF-8-байты, что и в сериализованной vCard:
    кириллица не переводится в другой алфавит и не теряется.

    Здесь намеренно обращаемся к внутреннему состоянию qrcode — иначе
    убедиться в побайтовом совпадении нечем.
    """
    vcard = generate_vcard(**CYRILLIC_DATA)
    expected = vcard.encode("utf-8")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(expected)
    qr.make(fit=True)
    assert qr.data_list[0].mode == qrcode.util.MODE_8BIT_BYTE
    assert bytes(qr.data_list[0].data) == expected


def unfold(vcard):
    """Склеивает переносы строк vCard 3.0 обратно в исходные строки"""
    lines = []
    for line in vcard.splitlines():
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def test_long_cyrillic_value_folds_without_splitting_characters(monkeypatch):
    """
    Длинное кириллическое значение переносится по границам многобайтовых
    символов и обратно собирается без потерь.

    Предел формата задан в октетах, а не в символах: кириллица занимает два
    байта, поэтому длина считается в len(line.encode("utf-8")).
    """
    long_name = "АО " + "Гипростроительный трест " * 4 + " имени академика Сеченова"
    monkeypatch.setenv("COMPANY_NAME", long_name)
    vcard = generate_vcard(**CYRILLIC_DATA)
    assert max(len(l.encode("utf-8")) for l in vcard.splitlines()) <= 75
    unfolded = unfold(vcard)
    title_lines = [l for l in unfolded if l.startswith("TITLE")]
    assert len(title_lines) == 1
    assert long_name in title_lines[0]
    assert "CHARSET=UTF-8" in title_lines[0].split(":", 1)[0]
    # перенос не разорвал ни одного многобайтового символа
    assert long_name in vobject.readOne(vcard).title.value


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


# --- Липкая форма (введённые значения остаются в полях после отправки) ---

def test_generate_preserves_form_values(client):
    """Успешный POST: все шесть полей возвращаются в HTML с введёнными значениями"""
    response = client.post("/generate", data=FORM_DATA)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for value in FORM_DATA.values():
        assert f'value="{value}"' in html


def test_generate_user_values_override_defaults(client):
    """Введённые email и рабочий телефон приоритетнее значений по умолчанию"""
    data = {**FORM_DATA, "email": "user@example.org", "work_phone": "+7(999)123-45-67"}
    response = client.post("/generate", data=data)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'value="user@example.org"' in html
    assert 'value="+7(999)123-45-67"' in html


def test_generate_error_preserves_form_values(client):
    """Ошибка валидации: поля показывают введённые значения, включая невалидный email"""
    data = {**FORM_DATA, "email": "не-почта"}
    response = client.post("/generate", data=data)
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    for value in data.values():
        assert f'value="{value}"' in html


def test_index_shows_defaults_and_empty_fields(monkeypatch, client):
    """GET /: email и рабочий телефон — дефолты, остальные поля пусты"""
    monkeypatch.delenv("FORM_EMAIL_DEFAULT", raising=False)
    monkeypatch.delenv("FORM_WORK_PHONE_DEFAULT", raising=False)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'value="@roga-i-kopyta.com"' in html
    assert 'value="+7(800)000-00-00"' in html
    for field in ["name", "job_title", "ext_phone", "mobile"]:
        assert f'name="{field}" value=""' in html


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

def test_log_handler_writes_to_stdout():
    """Логи выводятся в stdout (StreamHandler) — в контейнере их собирает Docker"""
    assert any(type(h) is logging.StreamHandler for h in logging.getLogger().handlers)


def test_vcard_logged_to_stdout(client, caplog):
    """Созданная vCard записывается в лог уровня INFO (виден через docker logs)"""
    with caplog.at_level(logging.INFO):
        response = client.post("/generate", data=FORM_DATA)
    assert response.status_code == 200
    assert any("Создана vCard" in record.message for record in caplog.records)
