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
        alert('Не удалось обработать изображение');
    }
}