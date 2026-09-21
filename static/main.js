function copyImageFallback(base64Data) {
    try {
        // Создаем временную ссылку для скачивания
        const link = document.createElement('a');
        link.href = `data:image/png;base64,${base64Data}`;
        link.download = 'qr-code.png';

        // Показываем сообщение о скачивании
        if (confirm('Копирование недоступно. Скачать изображение?')) {
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось обработать изображения');
    }
}

// --- Клиентская валидация и маски ввода ---

// Формат email как на сервере: текст@текст.текст
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/**
 * Форматирует номер телефона в маску +7(XXX)XXX-XX-XX.
 * Извлекает цифры, ведущие 7/8 нормализует в код страны.
 */
function formatPhone(value) {
    // Сначала убираем собственный префикс маски (+7 или +7(),
    // иначе он попадёт в цифры номера при повторном форматировании
    let rest = value.replace(/^\+7\(?/, '');
    let digits = rest.replace(/\D/g, '');
    // Ведущие 7/8 — код страны, отбрасываем только если цифр 11 (код страны + номер);
    // иначе 800-е номера (+7(800)...) ломались бы
    if (digits.length === 11 && (digits.charAt(0) === '7' || digits.charAt(0) === '8')) {
        digits = digits.slice(1);
    }
    digits = digits.slice(0, 10);
    const p1 = digits.slice(0, 3);
    const p2 = digits.slice(3, 6);
    const p3 = digits.slice(6, 8);
    const p4 = digits.slice(8, 10);
    let result = '';
    if (p1) result = '+7(' + p1;
    // Скобку добавляем только когда набрана 4-я цифра,
    // иначе при удалении она восстанавливается и поле «застревает»
    if (p1.length === 3 && p2) result += ')';
    if (p2) result += p2;
    if (p3) result += '-' + p3;
    if (p4) result += '-' + p4;
    return result;
}

document.addEventListener('DOMContentLoaded', function () {
    // Маски телефонов
    ['work_phone', 'mobile'].forEach(function (id) {
        const input = document.getElementById(id);
        if (!input) return;
        // Нормализуем предзаполненное значение при загрузке
        if (input.value) input.value = formatPhone(input.value);
        input.addEventListener('input', function () {
            input.value = formatPhone(input.value);
        });
    });

    // Добавочный номер: только цифры и дефис
    const extPhone = document.getElementById('ext_phone');
    if (extPhone) {
        extPhone.addEventListener('input', function () {
            extPhone.value = extPhone.value.replace(/[^\d-]/g, '');
        });
    }

    // Проверка email до отправки
    const form = document.getElementById('businessCardForm');
    const emailInput = document.getElementById('email');
    const errorBlock = document.getElementById('js-error');
    if (form && emailInput && errorBlock) {
        form.addEventListener('submit', function (event) {
            if (!EMAIL_PATTERN.test(emailInput.value.trim())) {
                event.preventDefault();
                errorBlock.textContent = 'Поле "e-mail" должно быть в формате текст@текст.текст';
                errorBlock.style.display = 'block';
                emailInput.focus();
            } else {
                errorBlock.style.display = 'none';
            }
        });
    }
});