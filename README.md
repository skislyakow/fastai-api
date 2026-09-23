# fastai-api
AI site generator

## Локальная установка

Инструкции по развёртыванию и настройке окружения смотрите в [CONTRIBUTING.md](CONTRIBUTING.md).

## Настройка переменных окружения

Скопируйте шаблон `example.env` в файл `.env` и заполните значения:

```shell
$ cp example.env .env
```

Файл `.env` хранит переменные окружения и **не должен попадать в git** — он уже
добавлен в `.gitignore`. Файл `example.env` — шаблон без реальных значений и
секретов, поэтому он безопасен для хранения в репозитории.

### Переменные

Приложение считывает и валидирует настройки через Pydantic Settings: при
отсутствии переменной используется значение по умолчанию, при невалидном
значении запуск завершается с ошибкой `ValidationError`.

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `DEEPSEEK__API_KEY` | да | — | API-ключ DeepSeek |
| `DEEPSEEK__MAX_CONNECTIONS` | нет | `None` | Максимальное количество соединений |
| `DEEPSEEK__TIMEOUT` | нет | `None` | Таймаут соединения, секунды |
| `DEEPSEEK__BASE_URL` | нет | `None` | Базовый URL API (для совместимых провайдеров) |
| `DEEPSEEK__MODEL` | нет | `deepseek-chat` | Имя модели |
| `UNSPLASH__API_KEY` | да | — | Access Key приложения Unsplash |
| `UNSPLASH__MAX_CONNECTIONS` | нет | `None` | Максимальное количество соединений |
| `UNSPLASH__TIMEOUT` | нет | `None` | Таймаут соединения, секунды |
| `UNSPLASH__PROXY` | нет | `None` | HTTP-прокси для запросов к Unsplash |
| `DEBUG` | нет | `false` | Режим отладки |

### Откуда взять значения

- **DeepSeek API-ключ**: [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).
- **Совместимый провайдер**: ключ можно получить в кабинете провайдера,
  например [VseGPT](https://vsegpt.ru/). Для него укажите также
  `DEEPSEEK__BASE_URL` (например, `https://api.vsegpt.ru/v1`) и
  `DEEPSEEK__MODEL` (например, `deepseek/deepseek-chat`).
- **Unsplash Access Key**: [https://unsplash.com/developers](https://unsplash.com/developers) —
  зарегистрируйте приложение и скопируйте его `Access Key`.

## Работа с S3 (MinIO)

Проект готовится к сохранению сгенерированных сайтов в S3-совместимое хранилище.
Локально для разработки применяется [MinIO](https://min.io/), работа с бакетом
ведётся через библиотеку `aioboto3`.

### Установка и запуск MinIO

Сервер MinIO распространяется как продукт AIStor. Скачайте deb-пакет
(имя файла `minio_*.deb`, бинарник ставится как `/usr/local/bin/minio`)
из официального каталога дистрибутивов:

```shell
$ wget https://dl.min.io/aistor/minio/release/linux-amd64/minio.deb
$ sudo dpkg -i minio.deb
```

1. Настройте `/etc/default/minio`:
   - `MINIO_VOLUMES` — каталог данных (например, `/var/lib/minio/data`);
   - `MINIO_OPTS` — адреса API и консоли (`--address :9000 --console-address :9001`);
   - `MINIO_CONFIG_ENV_FILE=/etc/minio/config.env` — файл дополнительной конфигурации.

2. Укажите корневые учётные данные в `/etc/minio/config.env`:

   ```shell
   MINIO_ROOT_USER=<user>
   MINIO_ROOT_PASSWORD=<password>
   ```

3. Запустите сервис:

   ```shell
   $ sudo systemctl enable --now minio
   $ sudo systemctl status minio
   ```

4. Проверьте готовность: `http://localhost:9000/minio/health/ready` должен
   отвечать `200`.

### Активация лицензии (AIStor)

Без лицензии сборка AIStor блокирует все S3-операции: API отвечает
`AccessDenied ... No license is installed ...`, а `.../minio/health/ready` — `503`.

1. Получите лицензию в личном кабинете SUBNET ([https://min.io](https://min.io)):
   для продукта AIStor доступен бесплатный Community-план (1 узел). Скачанный
   файл `minio.license` содержит JWT — одну длинную строку без переносов.

2. Добавьте содержимое файла в `/etc/minio/config.env` через переменную
   `MINIO_LICENSE` (одной строкой, без кавычек):

   ```shell
   # содержимое minio.license:
   MINIO_LICENSE=eyJhbGciOiJFUzM4NCIs...
   ```

3. Примените лицензию и проверьте:

   ```shell
   $ sudo systemctl restart minio
   $ curl -sf http://localhost:9000/minio/health/ready   # → 200
   ```

> Замечание про `mc`: клиент `mc` из GitHub-релизов
> [minio/mc](https://github.com/minio/mc) (последний — `RELEASE.2025-08-13`)
> не понимает бесплатные лицензии AIStor (JWT без `exp`-claim) и завершается
> ошибкой `License has expired on 0001-01-01`. Надёжный путь — активация через
> переменную `MINIO_LICENSE`, описанная выше. Официальный клиент AIStor — `mcli`
> (`https://dl.min.io/aistor/mc/release/linux-amd64/mcli.deb`).

### Адреса

- **API** — `http://localhost:9000`
- **Веб-интерфейс** — `http://localhost:9001`

При открытии адреса API в браузере происходит автоматический редирект в
веб-интерфейс. Если запросы к API завершаются ошибкой — убедитесь, что используется
порт `9000`.

### Учётные данные

Названия учётных данных MinIO и aioboto3 отличаются:

| MinIO | S3 / aioboto3 |
|---|---|
| `MINIO_ROOT_USER` | `AWS_ACCESS_KEY_ID` |
| `MINIO_ROOT_PASSWORD` | `AWS_SECRET_ACCESS_KEY` |

### Создание бакета и публичность

1. Откройте веб-интерфейс `http://localhost:9001` и войдите под `MINIO_ROOT_USER`.
2. Создайте бакет (раздел **Create Bucket**) — имя должно совпадать с `S3__BUCKET_NAME`.
3. Сделайте бакет публичным с помощью публичной bucket-политики, иначе файлы не будут
   доступны по ссылке без авторизации.

### MIME-типы и Content-Disposition

При загрузке файлов в бакет обязательно указывайте MIME-тип:

- `text/html` — для HTML-файлов;
- `image/png` — для изображений в формате PNG.

`Content-Disposition` определяет способ доступа к файлу по публичной ссылке:

- `inline` — файл открывается прямо в браузере в соответствии с MIME-типом;
- `attachment` — файл скачивается на ПК.

GET-параметр `response-content-disposition`, добавленный к публичной ссылке, позволяет
явно переопределить `Content-Disposition` при раздаче файла:

```
http://localhost:9000/<bucket>/<key>?response-content-disposition=attachment;%20filename="site.html"
```

### Ручная загрузка файла

1. Загрузите HTML-файл через веб-интерфейс (`:9001`).
2. Откройте его по ссылке `{endpoint}/{bucket}/{key}` — файл откроется в браузере.
3. Добавьте к ссылке параметр `response-content-disposition`,
   например `attachment; filename="site.html"` — файл скачается.

### Переменные окружения

Группа `S3` обязательна и читается через Pydantic Settings (`Settings.s3`).
Ключи `S3__ACCESS_KEY_ID` и `S3__SECRET_ACCESS_KEY` не имеют значений по
умолчанию — их обязательно нужно указать в `.env`.

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `S3__ENDPOINT_URL` | нет | `http://localhost:9000` | Адрес S3-совместимого API |
| `S3__ACCESS_KEY_ID` | да | — | AWS Access Key (`MINIO_ROOT_USER`) |
| `S3__SECRET_ACCESS_KEY` | да | — | AWS Secret Key (`MINIO_ROOT_PASSWORD`) |
| `S3__BUCKET_NAME` | нет | `fastai-sites` | Имя бакета |
| `S3__REGION_NAME` | нет | `us-east-1` | Регион S3 |
| `S3__CONNECT_TIMEOUT` | нет | — (дефолт botocore, 60 с) | Таймаут подключения, сек |
| `S3__READ_TIMEOUT` | нет | — (дефолт botocore, 60 с) | Таймаут чтения, сек |
| `S3__MAX_POOL_CONNECTIONS` | нет | — (дефолт botocore, 10) | Лимит одновременных подключений |

### Полезные ссылки

- Статья [aioboto3](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/aioboto3).
- Статья [furl vs urllib](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/furl-vs-urlib).
