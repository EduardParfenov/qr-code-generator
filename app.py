from flask import Flask, render_template, request, send_file
import qrcode
import base64
import io
import vobject
import logging
from logging.handlers import RotatingFileHandler
import os
import re
from dotenv import load_dotenv


# Загружаем настройки из .env (если файла нет — работают значения по умолчанию)
load_dotenv()

app = Flask(__name__)

# Создаём папку для логов, если её нет (папка в .gitignore и отсутствует в свежем клоне)
os.makedirs("./logs", exist_ok=True)

# Настройка логирования
# force=True: применяем конфигурацию, даже если кто-то настроил логирование раньше (например, pytest)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler("./logs/info.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")],  # ротация: 1 МБ, 3 архивные копии
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


def generate_vcard(name, job_title, email, phone, ext_phone, mobile):
    """
    Генерирует vCard на основе информации пользователя
    """
    vcard = vobject.vCard()
    # Ф.И.О.
    vcard.add('fn').value = name
    # должность
    company_name = os.getenv("COMPANY_NAME", 'ООО "Рога и копыта"') # Название организации (задаётся в .env)
    vcard.add('title').value = f'{company_name}, {job_title}'
    # e-mail
    vcard.add('email').value = email
    # рабочий телефон
    work_tel = vcard.add('tel')
    work_tel.value = f"{phone}"
    work_tel.type_param = 'WORK'

    '''
    Если вам необходимо добавить рабочий телефон с добавлением добавочного в заметки контакта
    раскоментируйте код ниже.
    '''
    # work_tel = vcard.add('tel')
    # work_tel.value = phone
    # work_tel.type_param = 'WORK,VOICE'
    # vcard.add('note').value = f"Доб. номер {ext_phone}"

    '''
    Если добавочный телефон нужно отображать после рабочего номера, использейте код ниже
    '''
    # добавочный телефон (необязательный — добавляем только если заполнен)
    if ext_phone:
        ext_tel = vcard.add('tel')
        ext_tel.value = f"{ext_phone}"
        ext_tel.type_param = 'WORK'

    # мобильный телефон (необязательный — добавляем только если заполнен)
    if mobile:
        mobile_tel = vcard.add('tel')
        mobile_tel.value = mobile
        mobile_tel.type_param = 'CELL'
    # url
    vcard.add('url').value = os.getenv("COMPANY_SITE", 'roga-i-kopyta.com')  # Адрес сайта (задаётся в .env)
    # адрес
    adr = vcard.add('adr')
    adr.value = vobject.vcard.Address(
    street=os.getenv("COMPANY_ADDRESS_STREET", "ул. Рогов и копыт, 34"),  # Улица и номер дома
    city=os.getenv("COMPANY_ADDRESS_CITY", "Нью-Йорк"),  # Город
    region=os.getenv("COMPANY_ADDRESS_REGION", "Нью-Йорская область"),  # Область
    code=os.getenv("COMPANY_ADDRESS_CODE", "4444444"),  # Почтовый индекс
    country=os.getenv("COMPANY_ADDRESS_COUNTRY", "Россия"))
    adr.type_param = 'WORK'

    logging.info(f"Создана vCard: {vcard.serialize()}") # Запись в лог

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
    # Серверная валидация (HTML5-проверку на клиенте легко обойти)
    errors = validate_form(request.form)
    if errors:
        return render_template('index.html', error="; ".join(errors)), 400
    # Получаем данные из формы
    name = request.form.get('name', '').strip()
    job_title = request.form.get('job_title', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('work_phone', '').strip()
    ext_phone = request.form.get('ext_phone', '').strip()
    mobile = request.form.get('mobile', '').strip()
    # Генерируем QR-код
    card = create_business_card(name, job_title, email, phone, ext_phone, mobile)
    # Конвертируем в base64
    buffered = io.BytesIO()
    card.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    # Возвращаем HTML с изображением
    return render_template('index.html', card_image=img_str, name = name)

# Запуск
# По умолчанию — локально с debug; для сервера задайте FLASK_DEBUG=false и FLASK_HOST в .env
if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug, host=host, port=port)
