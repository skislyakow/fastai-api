# fastai-api
AI site generator

## Локальная установка

Инструкции по развёртыванию и настройке окружения смотрите в [CONTRIBUTING.md](CONTRIBUTING.md).

На **Windows 11** все команды выполняйте из **Git Bash** (устанавливается вместе
с Git): терминал PowerShell в этом случае не подходит, т.к. многие команды
рассчитаны на bash-синтаксис.

На **Ubuntu 24.04** достаточно обычного терминала — команды выше работают как есть.

### Проверка, что инсталляция работает

После установки и запуска убедитесь, что приложение поднялось:

```shell
$ fastapi dev src/main.py
```

Признаки исправной инсталляции:

- **Код запущен** — в консоли идёт лог `Uvicorn running on http://127.0.0.1:8000`
  (или `http://0.0.0.0:8000`), строка `Application startup complete.`;
- **Нет неожиданных ошибок** — в логе отсутствуют `ERROR` / `Traceback`;
- **Результат соответствует инструкции** — в браузере открывается страница
  http://127.0.0.1:8000/docs (Swagger-документация API) и/или главная страница
  фронтенда http://127.0.0.1:8000/.

Пример лога успешного запуска (может отличаться деталями):

```shell
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Настройка переменных окружения

Скопируйте шаблон `example.env` в файл `.env` и заполните значения:

```shell
$ cp example.env .env
```

Файл `.env` хранит переменные окружения и **не должен попадать в git** — он уже
добавлен в `.gitignore`. Файл `example.env` — шаблон без реальных значений и
секретов, поэтому он безопасен для хранения в репозитории.

Убедиться, что `.env` не попадёт в коммит, можно так:

```shell
$ git check-ignore -v .env
.gitignore:1:.env	.env
```

Имя файла и номер строки (`.gitignore:1`) — строка в `.gitignore`, по которой
файл игнорируется. Файл не появится ни в `git status`, ни в `git diff`, ни в
коммите. После отправки изменений в origin проверьте последний коммит — файл
`.env` в нём отсутствует.

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
| `GOTENBERG__ENDPOINT_URL` | да | — | URL API Gotenberg для скриншотов |
| `GOTENBERG__MAX_CONNECTIONS` | нет | `5` | Лимит одновременных подключений |
| `GOTENBERG__TIMEOUT` | нет | `10` | Таймаут клиента Gotenberg, сек (на 2–5 сек больше `WAIT_DELAY`) |
| `GOTENBERG__WIDTH` | нет | `1280` | Ширина скриншота, пикс |
| `GOTENBERG__WAIT_DELAY` | нет | `8` | Пауза на загрузку анимаций страницы, сек |
| `GOTENBERG__DEFAULT_SCREENSHOT_FORMAT` | нет | `jpeg` | Формат скриншота: `png`, `jpeg`, `webp` |
| `DEBUG` | нет | `false` | Режим отладки |

### Откуда взять значения

- **DeepSeek API-ключ**: [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).
- **Совместимый провайдер**: ключ можно получить в кабинете провайдера,
  например [VseGPT](https://vsegpt.ru/). Для него укажите также
  `DEEPSEEK__BASE_URL` (например, `https://api.vsegpt.ru/v1`) и
  `DEEPSEEK__MODEL` (например, `deepseek/deepseek-chat`).
- **Unsplash Access Key**: [https://unsplash.com/developers](https://unsplash.com/developers) —
  зарегистрируйте приложение и скопируйте его `Access Key`.
- **Gotenberg**: используется публичный демо-API
  `https://demo.gotenberg.dev` (проверка доступности —
  `GET /health`). Для локального сервера укажите свой URL в
  `GOTENBERG__ENDPOINT_URL`.

## Генерация скриншотов (Gotenberg)

После завершения генерации HTML приложение рендерит скриншот страницы через
[Gotenberg](https://gotenberg.dev/) — сервис, который превращает HTML в JPEG из
headless-браузера.

Как это работает:

1. `_relay_html()` в `src/routers/sites.py` после сохранения HTML вызывает
   `render_screenshot()` из `src/gotenberg_client.py`.
2. `render_screenshot()` отправляет итоговый HTML в Gotenberg
   (`ScreenshotHTMLRequest`, пакет `gotenberg-api`) и возвращает JPEG-байты.
3. `upload_screenshot()` из `src/s3_client.py` загружает их в бакет по
   постоянному ключу `screenshot.jpg` с `ContentType="image/jpeg"` и
   `ContentDisposition="inline"`.

Ключ `screenshot.jpg` фиксированный, поэтому `screenshotUrl` в ответах API **не
меняется** — при каждой генерации перезаписывается только содержимое объекта.

Если Gotenberg недоступен или рендер завершился ошибкой, `render_screenshot()`
возвращает `None`, а генерация сайта продолжается: HTML сохраняется, скриншот
остаётся прежним.

Правило таймаутов: `GOTENBERG__TIMEOUT` должен быть на 2–5 секунд больше
`GOTENBERG__WAIT_DELAY`, иначе страница не успеет догрузить анимации до
создания кадра.

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
$ minio --version   # проверка установки: выводит версию сервера
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

В списке бакетов у `fastai-sites` отображается тип доступа **PUBLIC** (раздел
**Access Policy** — `public`). Новый бакет пуст: объекты появляются после ручной
загрузки или генерации сайта. Если приложение уже запущено, бакет создаётся и
становится публичным автоматически (`ensure_bucket` при старте, см.
CONTRIBUTING).

### MIME-типы и Content-Disposition

При загрузке файлов в бакет из кода (`put_object`) обязательно указывайте
`ContentType` (MIME-тип) и `ContentDisposition="inline"`:

- `text/html` — для HTML-файлов;
- `image/jpeg` — для скриншотов (например, `screenshot.jpg`);
- `image/png` — для изображений в формате PNG.

Пример кодовой загрузки — `src/prototype_s3.py` (запуск: `uv run python
src/prototype_s3.py`).

`Content-Disposition` определяет способ доступа к файлу по публичной ссылке:

- `inline` — файл открывается прямо в браузере в соответствии с MIME-типом;
- `attachment` — файл скачивается на ПК.

GET-параметр `response-content-disposition`, добавленный к публичной ссылке, позволяет
явно переопределить `Content-Disposition` при раздаче файла:

```
http://localhost:9000/<bucket>/<key>?response-content-disposition=attachment;%20filename="site.html"
```

### Ручная загрузка файла

Фронтенд показывает превью сгенерированных сайтов и скриншоты по ссылкам из
API (`htmlCodeUrl`, `screenshotUrl`). При запуске приложения файлов в бакете ещё
нет, поэтому их кладут вручную. По задаче в первую очередь в корень бакета
`fastai-sites` кладут демо-файлы:

- `index.html` — HTML демо-сайта;
- `index.png` — демо-скриншот.

Публичные адреса:

```
http://localhost:9000/fastai-sites/index.html
http://localhost:9000/fastai-sites/index.png
```

Ссылки, которые отдаёт API, ведут на ключи `sites/1/index.html` и
`screenshot.jpg`, поэтому до первой генерации их тоже кладут вручную:

```
http://localhost:9000/fastai-sites/sites/1/index.html
http://localhost:9000/fastai-sites/screenshot.jpg
```

Формат адреса: `{endpoint}/{bucket}/{key}`. Пока файлы не загружены в бакет,
ссылки вернут `404` и фронтенд будет выглядеть сломанным. После первой
генерации сайта HTML и `screenshot.jpg` заливаются приложением автоматически
(см. раздел «Генерация скриншотов (Gotenberg)»).

Загрузка через веб-интерфейс (`:9001`):

1. Загрузите файлы: HTML — в папку `sites/1/`, скриншот — в корень бакета.
2. Откройте файл по публичной ссылке — файл откроется в браузере.
3. Добавьте к ссылке параметр `response-content-disposition`,
   например `attachment; filename="site.html"` — файл скачается.

### Настройка подключения к S3 (.env)

Приложение читает настройки S3 из файла `.env`: переменные объединяются в
группу по общему префиксу `S3__`.

1. Скопируйте шаблон:

   ```shell
   $ cp example.env .env
   ```

2. Заполните обязательные переменные группы `S3`. Минимальный набор для
   локального MinIO:

   ```dotenv
   # группа S3
   S3__ENDPOINT_URL=http://localhost:9000
   S3__ACCESS_KEY_ID=<MINIO_ROOT_USER>
   S3__SECRET_ACCESS_KEY=<MINIO_ROOT_PASSWORD>
   S3__BUCKET_NAME=fastai-sites
   S3__REGION_NAME=us-east-1
   S3__CONNECT_TIMEOUT=5
   S3__READ_TIMEOUT=60
   S3__MAX_POOL_CONNECTIONS=10
   ```

3. Запустите приложение: в консоли появится JSON всех настроек, а секретные
   значения (`S3__ACCESS_KEY_ID`, `S3__SECRET_ACCESS_KEY`) выводятся звёздочками.

#### Переменные группы `S3`

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
