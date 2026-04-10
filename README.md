# lab4testing

Проєкт для лабораторної роботи №4, у якому об'єднані:
- unit-тести з лаби 1;
- BDD-тести з лаби 2;
- інтеграційні тести з лаби 3;
- CI/CD-конфігурація для автоматичного запуску всіх тестів.

## Структура
- `app/eshop.py` — основна бізнес-логіка eshop;
- `services/` — сервіси доставки, DynamoDB, SQS;
- `tests/unit/` — unit-тести з перших двох лабораторних;
- `tests/integration/` — інтеграційні тести з LocalStack;
- `features/` — BDD feature-файли та step definitions;
- `.github/workflows/ci.yml` — сценарій CI/CD для GitHub Actions.

## Як запускати локально
1. Встановити залежності:
   `pip install -r requirements.txt`
2. Підняти LocalStack:
   `docker compose up -d`
3. Запустити unit + integration тести:
   `pytest -v`
4. Запустити BDD тести:
   `behave`
5. Зупинити LocalStack:
   `docker compose down -v`

## Що перевіряє CI/CD
- автоматичне встановлення залежностей;
- підняття LocalStack;
- запуск unit-тестів;
- запуск інтеграційних тестів;
- запуск BDD-тестів;
- завершення оточення після виконання.
