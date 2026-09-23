# Инструкция по развертыванию на сервере (для администратора)

Этот файл — пошаговая инструкция по развертыванию приложения в Docker на
сервере, где единый nginx (в контейнере) обслуживает несколько проектов.
Написана на примере qr-code-generator, но подходит для любого приложения,
оформленного по той же схеме. В конце — раздел «Адаптация под другие
приложения»: что и где поменять.

## Архитектура

```
клиент → nginx (контейнер, порты 80/443 — единственные открытые наружу)
            → общая Docker-сеть nginx-net
                → контейнер приложения (qr-app:8000, gunicorn)
```

Принципы схемы:

- Порты приложений **не публикуются на хост** — nginx обращается к ним
  по имени контейнера через общую сеть. До приложения нельзя достучаться
  в обход nginx.
- Логи приложения пишутся только в **stdout** — их собирает Docker
  (`docker logs` / `docker compose logs`), ротация настроена в compose.
- Настройки приложения передаются через `.env` (не вшит в образ, в git
  не коммитится).

## Пререквизиты

- Docker Engine и compose plugin (`docker version`, `docker compose version`).
- Nginx уже развёрнут как контейнер по той же схеме (свой каталог с
  `docker-compose.yml`, конфиги проектов в `conf.d/`, сеть `nginx-net`).
- Доменное имя, направленное на сервер (для `server_name`), и
  TLS-сертификаты, если нужен HTTPS.

## Шаг 1. Клонировать репозиторий

```bash
git clone <url-репозитория> /opt/qr-code-generator
cd /opt/qr-code-generator
```

## Шаг 2. Создать общую сеть (один раз на весь сервер)

```bash
docker network create nginx-net
```

Если сеть уже создана при развертывании nginx или другого проекта —
пропустите (ответ «already exists» — это нормально). Эту же сеть должны
использовать все проекты и контейнер nginx.

## Шаг 3. Настроить .env

```bash
cp .env.example .env
nano .env   # вписать данные компании (см. readme, раздел «Настройка»)
```

Заполнить: `COMPANY_NAME`, `COMPANY_SITE`, `COMPANY_ADDRESS_*`,
`FORM_EMAIL_DEFAULT`, `FORM_WORK_PHONE_DEFAULT`, при необходимости
`CARD_TEMPLATE_URL` и `GUNICORN_WORKERS` (по умолчанию 2).
Переменные `FLASK_*` в контейнере не используются.

## Шаг 4. Запустить приложение

```bash
docker compose up -d --build
```

Проверка:

```bash
docker ps                        # контейнер qr-app в статусе Up
docker compose logs --tail 20    # gunicorn запустился, workers поднялись
```

Важно: `docker ps` покажет `8000/tcp` **без** проброса на хост — так
задумано. `curl http://localhost:8000` с хоста работать НЕ будет.

## Шаг 5. Подключить к nginx

Добавить в `conf.d/` nginx-контейнера файл `qr.conf`:

```nginx
server {
    listen 443 ssl;
    server_name qr.example.com;              # <-- реальный домен

    ssl_certificate     /etc/nginx/ssl/qr.example.com.crt;   # <-- пути к сертификатам
    ssl_certificate_key /etc/nginx/ssl/qr.example.com.key;

    location / {
        proxy_pass http://qr-app:8000;       # <-- имя контейнера:порт приложения
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Перечитать конфиг nginx:

```bash
docker exec nginx nginx -t          # проверка синтаксиса
docker exec nginx nginx -s reload   # применить
```

**Порядок важен:** приложение (шаг 4) должно быть запущено ДО reload
nginx — nginx резолвит имя из `proxy_pass` при старте/перечитывании.
Если nginx упал с `host not found in upstream "qr-app"` — запустите
приложение и сделайте `docker restart nginx` (или reload).

## Шаг 6. Финальная проверка

```bash
curl -i https://qr.example.com/
# HTTP/2 200, в теле — HTML формы генератора
```

Открыть сайт в браузере, сгенерировать QR-код через форму, отсканировать
камерой телефона — контакт должен корректно распознаться.

## Эксплуатация

```bash
cd /opt/qr-code-generator

docker compose logs -f              # логи в реальном времени (здесь же аудит vCard)
docker compose logs --tail 100      # последние 100 строк
docker compose logs > audit.txt     # выгрузка логов в файл

docker compose restart              # перезапуск
docker compose up -d --build        # обновление: git pull + эта команда
docker compose down                 # остановка
```

Логи ротируются самим Docker (10 МБ × 3 файла, настроено в
`docker-compose.yml`), файлов логов внутри проекта нет.

## Диагностика

| Симптом | Причина и лечение |
|---|---|
| `host not found in upstream` у nginx | Приложение не запущено или не в той сети. Проверить: `docker ps`, `docker network inspect nginx-net` — в Containers должны быть и `nginx`, и `qr-app` |
| 502 Bad Gateway | Приложение упало или не отвечает: `docker compose logs` в каталоге приложения |
| 404 от nginx | Запрос пришёл на неверный `server_name`: проверить домен и `qr.conf` |
| `curl localhost:8000` не работает | Так задумано: порт не публикуется, доступ только через nginx |

## Адаптация под другие приложения

Схема повторяется для каждого нового проекта. Меняется следующее:

1. **`docker-compose.yml` проекта:**
   - `container_name: qr-app` → уникальное имя приложения (например,
     `app2`). Именно по нему nginx будет обращаться к контейнеру.
   - Порт в `CMD`/команде запуска приложения (у нас gunicorn на 8000)
     — может быть любым, лишь бы совпадал с портом в `proxy_pass`.
     Публиковать порт наружу (`ports:`) НЕ нужно.
   - `env_file`, `restart`, `logging`, `networks: nginx-net (external)` —
     без изменений.
2. **Файл в `conf.d/` nginx:** новый `<app>.conf` — меняются
   `server_name` (домен проекта) и `proxy_pass http://<имя-контейнера>:<порт>`.
3. **`.env` проекта** — переменные по `.env.example` конкретного проекта.
4. **`server_name`** у всех проектов разные — nginx различает проекты
   по доменному имени, а не по портам.

Не меняется никогда: общая сеть `nginx-net` (одна на сервер), принцип
«порты не публикуются», логирование в stdout, `restart: unless-stopped`,
ротация логов в compose.
