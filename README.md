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
