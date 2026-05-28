# VK SaaS for Entrepreneurs

SaaS-платформа в формате VK Mini App + backend для предпринимателей — владельцев сообществ ВКонтакте. Четыре модуля: конструктор чат-ботов, рассылки, ИИ-агенты на базе RAG, ИИ-оформление сообщества.

См. полное ТЗ в [`TZ_VK_SaaS_for_Entrepreneurs.md`](./TZ_VK_SaaS_for_Entrepreneurs.md).

## Структура репозитория

```
.
├── backend/          # FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # config, security, db
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # бизнес-логика
│   │   └── workers/  # Celery tasks
│   ├── alembic/      # миграции
│   └── tests/
├── miniapp/          # VK Mini App (React + VKUI)
│   └── src/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Стек

- **Frontend:** React 18 + TypeScript + VKUI + VK Bridge + Vite + Zustand + React Flow
- **Backend:** Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic + Celery
- **Хранилища:** PostgreSQL 15, Redis 7, Qdrant
- **AI:** OpenAI (GPT-4o + text-embedding-3-small + gpt-image-2), Anthropic Claude
- **Хостинг:** Yandex Cloud / Selectel / VK Cloud (РФ-юрисдикция, 152-ФЗ)

## Быстрый старт

### 1. Подготовка окружения

```bash
cp .env.example .env
# отредактируй .env: добавь реальные ключи OpenAI, Anthropic, прокси, VK App
```

### 2. Запуск всего стека через Docker Compose

```bash
docker compose up -d
```

Поднимется: PostgreSQL (5432), Redis (6379), Qdrant (6333), API (8000), Celery worker, Celery beat.

При старте `api` автоматически применяет миграции (`alembic upgrade head`).

### 3. Локальная разработка фронта (отдельно от Docker)

```bash
cd miniapp
npm install
npm run dev
# открой http://localhost:5173
```

## Полезные команды

| Команда | Что делает |
|---------|-----------|
| `docker compose up -d` | Поднять весь стек |
| `docker compose logs -f api` | Логи API |
| `docker compose exec api alembic revision --autogenerate -m "msg"` | Новая миграция |
| `docker compose exec api alembic upgrade head` | Применить миграции |
| `docker compose exec api pytest` | Запустить тесты |
| `docker compose down -v` | Остановить и удалить volumes |

## Дорожная карта (см. ТЗ § 11)

1. **Фундамент** (2-3 нед) ← мы здесь
2. **ИИ-агенты** (4-5 нед)
3. **Конструктор чат-ботов** (4-5 нед)
4. **Рассылки** (3 нед)
5. **ИИ-оформление** (3-4 нед)
6. **Полировка + бета** (2-3 нед)
