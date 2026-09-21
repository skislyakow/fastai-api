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

1. Установите deb-пакет MinIO:

   ```shell
   $ sudo dpkg -i minio_*.deb
   ```

2. Укажите путь к хранилищу в `/etc/default/minio` (переменная `MINIO_VOLUMES`)
   и учётные данные в `/etc/minio/config.env` (`MINIO_ROOT_USER` и `MINIO_ROOT_PASSWORD`).

3. Запустите сервис:

   ```shell
   $ sudo systemctl enable --now minio
   $ sudo systemctl status minio
   ```

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

Переменные группы `S3` готовятся к добавлению в код и будут читаться через
Pydantic Settings:

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `S3__ENDPOINT_URL` | нет | `http://localhost:9000` | Адрес S3-совместимого API |
| `S3__ACCESS_KEY_ID` | да | — | AWS Access Key (`MINIO_ROOT_USER`) |
| `S3__SECRET_ACCESS_KEY` | да | — | AWS Secret Key (`MINIO_ROOT_PASSWORD`) |
| `S3__BUCKET_NAME` | да | — | Имя бакета |
| `S3__REGION_NAME` | нет | `us-east-1` | Регион S3 |

### Полезные ссылки

- Статья [aioboto3](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/aioboto3).
- Статья [furl vs urllib](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/furl-vs-urlib).
