from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import qrcode
import base64
import io
import vobject
import logging
import os


app = Flask(__name__)

# Создаём папку для логов, если её нет (папка в .gitignore и отсутствует в свежем клоне)
os.makedirs("./logs", exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("./logs/info.log", encoding="utf-8")]
    )


QR_X_POS = 0.055 # Позиция QR-code по горизонтали
QR_Y_POS = 0.055 # Позиция QR-code по вертикали


def generate_vcard(name, job_title, email, phone, ext_phone, mobile):
    """
    Генерирует vCard на основе информации пользователя
    """
    vcard = vobject.vCard()
    # Ф.И.О.
    vcard.add('fn').value = name
    # должность
    vcard.add('title').value = f'ООО "Рога и копыта", {job_title}' # Введите название вашей организации
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
    # добавочный телефон
    ext_tel = vcard.add('tel')
    ext_tel.value = f"{ext_phone}"
    ext_tel.type_param = 'WORK'

    # мобильный телефон
    mobile_tel = vcard.add('tel')
    mobile_tel.value = mobile
    mobile_tel.type_param = 'CELL'
    # url
    vcard.add('url').value = 'roga-i-kopyta.com'  # Укажите адрес сайта
    # адрес
    adr = vcard.add('adr')
    adr.value = vobject.vcard.Address(
    street="ул. Рогов и копыт, 34",  # Укажите наименование улицы и номер дома
    city="Нью-Йорк",  # Укажите город
    region="Нью-Йорская область",  # Укажите область
    code="4444444",  # Укажите почтовый индекс
    country="Россия")
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
    Генерирует сам QR-code
    - name, job_title, email, phone, ext_phone, mobile: контактная информация пользователя
    """
    template = Image.open('static/white_page_square.png')  # Фон на котором размещается QR-code

    # Сгенерировать и разместить QR-код
    width, height = template.size
    qr_size = int(height * 0.9)  # Размер QR-кода
    vcard_data = generate_vcard(name, job_title, email, phone, ext_phone, mobile)
    qr_image = generate_qr_code(vcard_data).resize((qr_size, qr_size))

    # Разместить QR-код на фоне
    qr_x = int(width * QR_X_POS)
    qr_y = int(height * QR_Y_POS)
    white_bg = Image.new('RGB', (qr_size + 20, qr_size + 20), 'white')
    template.paste(white_bg, (qr_x - 10, qr_y - 10))
    template.paste(qr_image, (qr_x, qr_y))
    return template


Flask
@app.route('/', methods=['GET'])
def index():
    """Отображает главную страницу"""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_card():
    """
    Обрабатывает отправку формы, генерирует и возвращает QR-code.
    Преобразует изображение в формат base64 для встраивания в HTML.
    """
    # Получаем данные из формы
    name = request.form['name']
    job_title = request.form['job_title']
    email = request.form['email']
    phone = request.form['work_phone']
    ext_phone = request.form['ext_phone']
    mobile = request.form['mobile']
    # Генерируем QR-код
    card = create_business_card(name, job_title, email, phone, ext_phone, mobile)
    # Конвертируем в base64
    buffered = io.BytesIO()
    card.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    # Возвращаем HTML с изображением
    return render_template('index.html', card_image=img_str, name = name)

# Запуск
# Для работы локально по IP, без сервера
if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000)  # Если размещаете на сервере поменяйте ip-адрес
