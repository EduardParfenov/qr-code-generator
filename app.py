from flask import Flask, render_template, request, send_file
import qrcode
import base64
import io
import vobject
import logging
import os
import re
from dotenv import load_dotenv


# Загружаем настройки из .env (если файла нет — работают значения по умолчанию)
load_dotenv()

app = Flask(__name__)

# Настройка логирования: логи пишем только в stdout —
# в контейнере их собирает Docker (docker logs / docker compose logs),
# при локальном запуске они видны в консоли
# force=True: применяем конфигурацию, даже если кто-то настроил логирование раньше (например, pytest)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
    force=True
    )


@app.context_processor
def inject_form_defaults():
    """Предзаполненные значения полей формы (задаются в .env)"""
    return dict(
        email_default=os.getenv("FORM_EMAIL_DEFAULT", "@roga-i-kopyta.com"),
        phone_default=os.getenv("FORM_WORK_PHONE_DEFAULT", "+7(800)000-00-00"),
        card_template_url=os.getenv("CARD_TEMPLATE_URL", ""),  # если пусто — кнопка не показывается
    )


# Демо-значение сайта компании (задаётся в .env через COMPANY_SITE).
# Со схемой: поле URL в vCard должно содержать полный URI (RFC 2426)
DEFAULT_COMPANY_SITE = "https://roga-i-kopyta.com"

# Признак уже заданной схемы по RFC 3986: «схема://». Проверяется именно эта
# форма, а не наличие двоеточия: в «a.ru:8080» двоеточие отделяет порт, а не схему
URL_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def normalize_site_url(value):
    """
    Приводит адрес сайта к полному URI для поля URL в vCard.
    Схема, если она уже задана, сохраняется как есть (решение — за владельцем
    конфигурации); если схемы нет, добавляется https://.
    Пустое значение возвращается как есть: дописывать схему к пустой строке
    нельзя, поле URL должно остаться пустым.
    Ведущие «//» (протокол-относительная запись, сама по себе не URI) перед
    добавлением схемы убираются, иначе получилось бы «https:////».
    """
    if not value or URL_SCHEME_PATTERN.match(value):
        return value
    return "https://" + value.lstrip("/")


def generate_vcard(name, job_title, email, phone, ext_phone, mobile):
    """
    Генерирует vCard на основе информации пользователя
    """
    vcard = vobject.vCard()
    # Ф.И.О.
    fn = vcard.add('fn')
    fn.value = name
    fn.charset_param = 'UTF-8'
    # должность
    company_name = os.getenv("COMPANY_NAME", 'ООО "Рога и копыта"') # Название организации (задаётся в .env)
    title = vcard.add('title')
    title.value = f'{company_name}, {job_title}'
    title.charset_param = 'UTF-8'
    # e-mail
    email_field = vcard.add('email')
    email_field.value = email
    email_field.charset_param = 'UTF-8'

    # телефоны: рабочий и добавочный — WORK, мобильный — CELL.
    # CHARSET проставляется в единственном месте для всех трёх полей
    def add_tel(value, tel_type):
        if not value:
            return
        tel = vcard.add('tel')
        tel.value = value
        tel.type_param = tel_type
        tel.charset_param = 'UTF-8'

    add_tel(phone, 'WORK')

    '''
    Если вам необходимо добавить рабочий телефон с добавлением добавочного в заметки контакта
    раскоментируйте код ниже.
    '''
    # add_tel(phone, 'WORK')
    # vcard.add('note').value = f"Доб. номер {ext_phone}"

    '''
    Если добавочный телефон нужно отображать после рабочего номера, использейте код ниже
    '''
    # добавочный телефон (необязательный — добавляем только если заполнен)
    add_tel(ext_phone, 'WORK')
    # мобильный телефон (необязательный — добавляем только если заполнен)
    add_tel(mobile, 'CELL')
    # url
    url_field = vcard.add('url')
    # Адрес приводится к полному URI: без схемы в .env добавляется https://
    url_field.value = normalize_site_url(os.getenv("COMPANY_SITE", DEFAULT_COMPANY_SITE))
    url_field.charset_param = 'UTF-8'
    # адрес
    adr = vcard.add('adr')
    adr.value = vobject.vcard.Address(
    street=os.getenv("COMPANY_ADDRESS_STREET", "ул. Рогов и копыт, 34"),  # Улица и номер дома
    city=os.getenv("COMPANY_ADDRESS_CITY", "Нью-Йорк"),  # Город
    region=os.getenv("COMPANY_ADDRESS_REGION", "Нью-Йорская область"),  # Область
    code=os.getenv("COMPANY_ADDRESS_CODE", "4444444"),  # Почтовый индекс
    country=os.getenv("COMPANY_ADDRESS_COUNTRY", "Россия"))
    adr.type_param = 'WORK'
    adr.charset_param = 'UTF-8'

    # В лог пишется только имя контакта: e-mail, телефоны, должность и адрес
    # остаются в QR-коде, но в лог не попадают. Переводы строк заменяются
    # пробелом, иначе значение поля создало бы в логе отдельную запись
    contact_name = name.replace("\n", " ").replace("\r", " ")
    logging.info(f"v-card создана для контакта: {contact_name}")

    return vcard.serialize()


def generate_qr_code(vcard_data):
    """
    Генерирует QR-код, содержащий данные vCard
    Настраивает параметры QR-кода для сканирования
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard_data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def create_business_card(name, job_title, email, phone, ext_phone, mobile):
    """
    Генерирует QR-code с контактом пользователя
    - name, job_title, email, phone, ext_phone, mobile: контактная информация пользователя
    """
    vcard_data = generate_vcard(name, job_title, email, phone, ext_phone, mobile)
    return generate_qr_code(vcard_data)


@app.route('/', methods=['GET'])
def index():
    """Отображает главную страницу"""
    return render_template('index.html')


# Простой формат email: текст@текст.текст (без полной RFC-проверки)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Обязательные поля формы: имя поля -> название для сообщения об ошибке
REQUIRED_FIELDS = {
    "name": "Ф.И.О.",
    "job_title": "Должность",
    "work_phone": "Тел. рабочий",
}


def validate_form(form):
    """
    Проверяет данные формы на сервере.
    Возвращает список текстов ошибок (пустой список — данные валидны).
    """
    errors = []
    for field, label in REQUIRED_FIELDS.items():
        if not form.get(field, "").strip():
            errors.append(f'Заполните поле "{label}"')
    email = form.get("email", "").strip()
    if not email:
        errors.append('Заполните поле "e-mail"')
    elif not EMAIL_PATTERN.match(email):
        errors.append('Поле "e-mail" должно быть в формате текст@текст.текст')
    return errors


@app.route('/generate', methods=['POST'])
def generate_card():
    """
    Обрабатывает отправку формы, генерирует и возвращает QR-code.
    Преобразует изображение в формат base64 для встраивания в HTML.
    При ошибках валидации возвращает форму с сообщением (HTTP 400).
    """
    # Получаем данные из формы
    name = request.form.get('name', '').strip()
    job_title = request.form.get('job_title', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('work_phone', '').strip()
    ext_phone = request.form.get('ext_phone', '').strip()
    mobile = request.form.get('mobile', '').strip()
    # «Липкая форма»: введённые значения возвращаем в шаблон и при успехе, и при ошибке
    form_values = dict(name=name, job_title=job_title, email=email,
                       work_phone=phone, ext_phone=ext_phone, mobile=mobile)
    # Серверная валидация (HTML5-проверку на клиенте легко обойти)
    errors = validate_form(request.form)
    if errors:
        return render_template('index.html', error="; ".join(errors), **form_values), 400
    # Генерируем QR-код
    try:
        card = create_business_card(name, job_title, email, phone, ext_phone, mobile)
    except Exception as e:
        logging.error(f"Ошибка генерации QR-кода: {e}")
        return render_template('index.html', error="Не удалось сгенерировать QR-код. Попробуйте ещё раз.", **form_values), 500
    # Конвертируем в base64
    buffered = io.BytesIO()
    card.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    # Возвращаем HTML с изображением
    return render_template('index.html', card_image=img_str, **form_values)

# Запуск
# По умолчанию — локально с debug; для сервера задайте FLASK_DEBUG=false и FLASK_HOST в .env
if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug, host=host, port=port)
