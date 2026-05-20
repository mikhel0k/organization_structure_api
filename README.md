# Organization Structure API

API для подразделений и сотрудников.

## Запуск

```bash
docker-compose up --build
```

http://localhost:8000/docs

## Миграции

При `docker-compose up` применяются автоматически (сервис `migrate`).

Создать новую:

```bash
docker-compose run --rm migrate alembic revision --autogenerate -m "init"
```

## Тесты

```bash
docker-compose run --rm -e TEST_DATABASE_URL=postgresql://postgres:postgres@db:5432/org_structure_test api pytest -v
```
# organization_structure_api
