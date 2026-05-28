# Техническое задание: SaaS-платформа для предпринимателей в ВКонтакте

**Версия:** 1.0  
**Формат:** ТЗ для разработки через ИИ-ассистенты (Cursor / Claude Code / Windsurf)  
**Дата:** 2026

---

## Оглавление

1. [Общее описание](#1-общее-описание)
2. [Целевая аудитория и роли](#2-целевая-аудитория-и-роли)
3. [Функциональные модули (MVP)](#3-функциональные-модули-mvp)
4. [Архитектура](#4-архитектура)
5. [Технологический стек](#5-технологический-стек)
6. [Модель данных (БД)](#6-модель-данных-бд)
7. [API внутренний (REST)](#7-api-внутренний-rest)
8. [Интеграции с внешними API](#8-интеграции-с-внешними-api)
9. [Биллинг и тарификация](#9-биллинг-и-тарификация)
10. [Безопасность](#10-безопасность)
11. [Этапы разработки (Roadmap)](#11-этапы-разработки-roadmap)
12. [Промпты для вайб-кодинга](#12-промпты-для-вайб-кодинга)

---

## 1. Общее описание

### 1.1 Что мы делаем

SaaS-платформа в формате **VK Mini App + бэкенд-сервис**, которая позволяет предпринимателям (владельцам сообществ ВК) использовать четыре инструмента для автоматизации работы со своей аудиторией:

1. **Конструктор чат-ботов** — визуальный редактор сценариев общения с подписчиками
2. **Автоответчики и рассылки** — массовые и сегментированные сообщения, автоворонки
3. **ИИ-агенты** — LLM-консультанты на базе их базы знаний (прайс, FAQ, услуги)
4. **ИИ-оформление сообщества** — генерация текстов постов, обложек, баннеров, контент-плана

### 1.2 Где это работает

- Основной интерфейс — **VK Mini App** (открывается внутри ВК с десктопа и мобильных)
- Бэкенд работает 24/7 на отдельных серверах и обслуживает входящие события от сообществ клиентов
- Авторизация — через **VK ID** (OAuth)

### 1.3 Бизнес-модель

**Pay-as-you-go (оплата за использование)** — клиенты покупают пакеты внутренних кредитов и тратят их на:
- Отправленные сообщения через бота / рассылку
- Запросы к LLM (ИИ-агенты, генерация контента)
- Генерации изображений

Подробнее в разделе [Биллинг](#9-биллинг-и-тарификация).

---

## 2. Целевая аудитория и роли

### 2.1 Пользовательские роли

| Роль | Описание | Что может делать |
|------|----------|------------------|
| **Owner** | Предприниматель, владелец сообщества ВК | Подключать свои сообщества, настраивать боты/рассылки/ИИ-агентов, пополнять баланс, видеть статистику |
| **Member** | Подписчик сообщества клиента | Взаимодействует с ботами/агентами в чате сообщества (НЕ заходит в наш Mini App) |
| **Admin** | Сотрудник нашей платформы | Управление пользователями, тарифами, мониторинг |

### 2.2 Уровни доступа в Mini App

- **Free trial** — 14 дней, ограниченные кредиты (для теста)
- **Paid** — после первого пополнения, все функции по тарификации

---

## 3. Функциональные модули (MVP)

### 3.1 Модуль 1: Конструктор чат-ботов

**Назначение:** позволить клиенту собрать сценарий общения с подписчиками без программирования.

**Функции:**
- Визуальный редактор сценариев (drag-and-drop, нода-граф)
- Типы нод:
  - **Сообщение** — текст / изображение / кнопки / карусель
  - **Условие** — if/else на основе ответа пользователя
  - **Ожидание ввода** — пауза до ответа подписчика
  - **Переменная** — сохранить ответ пользователя в поле профиля
  - **Действие** — вызвать webhook, отправить email, передать в CRM
  - **Передача оператору** — выйти из бота, уведомить админа
- Триггеры запуска бота:
  - Команда `/start` или вход в сообщество
  - Ключевое слово в сообщении
  - Подписка на сообщество
  - Кнопка в меню сообщества
- Тестирование сценария внутри Mini App
- Аналитика по нодам: сколько прошло, где отвалились

**Технически:**
- Хранение сценария — JSON-граф в БД
- Исполнение — событийная машина состояний (state machine) на бэкенде
- Каждый подписчик клиента имеет state: какая нода активна, переменные, история

### 3.2 Модуль 2: Автоответчики и рассылки

**Функции:**
- **Автоответчик** — ответ на ключевые слова или первое сообщение
- **Рассылка по сегментам:**
  - Все подписчики
  - По полу / возрасту / городу (из данных ВК)
  - По тегам (присвоенным ботом)
  - По активности (писали за N дней)
- **Отложенные рассылки** — отправка в заданное время
- **Автоворонки** — цепочка сообщений с интервалами (день 1: приветствие → день 3: оффер → день 7: напоминание)
- **A/B-тесты** — два варианта сообщения на разные группы

**Ограничения ВК:**
- Сообщения подписчикам, которые не писали группе 24+ часов, требуют permission `messages_for_group` (платная рассылка от ВК) или статуса "promo"
- Лимиты на скорость отправки — встроить очередь и rate limiter

### 3.3 Модуль 3: ИИ-агенты

**Назначение:** клиент создаёт ИИ-консультанта, который отвечает его подписчикам на основе загруженной базы знаний.

**Функции:**
- **Создание агента:**
  - Имя, роль (продавец / консультант / квалификатор лидов / поддержка)
  - System prompt (с подсказками-шаблонами)
  - Tone of voice (формальный / дружеский / экспертный)
  - Выбор LLM-провайдера: GigaChat, YandexGPT, GPT-4o, Claude (по умолчанию — GigaChat ради цены и юрисдикции)
- **База знаний:**
  - Загрузка файлов: PDF, DOCX, TXT, CSV
  - Парсинг сайта по URL
  - Импорт из постов сообщества
  - Ручное добавление Q&A
  - Чанкинг и эмбеддинги → векторная БД (Qdrant / pgvector)
- **RAG-пайплайн:**
  1. Сообщение подписчика → эмбеддинг
  2. Поиск релевантных чанков (top-K)
  3. Сборка промпта: system + контекст + история диалога + вопрос
  4. Запрос к LLM → ответ
- **Гибридная логика:**
  - Если confidence низкий — передать оператору
  - Если в вопросе видны ключевые триггеры (цена / купить) — запустить сценарий из конструктора
- **Лог диалогов** — клиент видит все разговоры агента с подписчиками
- **Дообучение** — клиент помечает удачные/неудачные ответы, мы корректируем prompt

### 3.4 Модуль 4: ИИ-оформление сообщества

**Функции:**

**4.1 Генерация текстов:**
- Посты по теме / контент-плану
- Описание сообщества
- Тексты для меню и кнопок
- Призывы к действию (CTA)
- Ребрендинг существующих постов

**4.2 Генерация изображений:**
- Обложка сообщества (правильные размеры под ВК)
- Аватар сообщества
- Баннеры под посты
- Карточки товаров
- Источники: Kandinsky API (приоритет — русская юрисдикция), DALL-E 3, FLUX
- Шаблоны: бизнес / lifestyle / минимализм / яркий

**4.3 Контент-план:**
- ИИ предлагает план постов на неделю/месяц по теме бизнеса
- Учитывает праздники, тренды, специфику ниши
- Клиент редактирует и подтверждает

**4.4 Автопостинг:**
- Календарь публикаций
- Отложенный постинг через VK API (`wall.post`)
- Кросспостинг (опционально — Telegram, OK)

---

## 4. Архитектура

### 4.1 Высокоуровневая схема

```
┌─────────────────────────────────────────────────────────────┐
│                    КЛИЕНТ (Предприниматель)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │       VK Mini App (React + VKUI + VK Bridge)         │   │
│  │  - Авторизация через VK ID                           │   │
│  │  - Подключение сообществ                             │   │
│  │  - UI всех 4 модулей                                 │   │
│  └────────────────────────┬─────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────┘
                            │ HTTPS (JWT)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (наш сервер)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Gateway (FastAPI / NestJS)           │   │
│  │  - REST API для Mini App                             │   │
│  │  - Callback API endpoint (приём событий от ВК)       │   │
│  │  - WebSocket для real-time UI                        │   │
│  └────┬────────────────────────────────────────────┬────┘   │
│       │                                            │         │
│       ▼                                            ▼         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐  ┌────────┐  │
│  │ Bot      │    │ Mailing  │    │ AI Agent │  │ Content│  │
│  │ Engine   │    │ Worker   │    │ Service  │  │ Service│  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘  └───┬────┘  │
│       │               │               │             │       │
│       └───────────────┴──────┬────────┴─────────────┘       │
│                              ▼                               │
│       ┌──────────────────────────────────────────┐          │
│       │  PostgreSQL │ Redis (queue) │ Qdrant     │          │
│       │  S3 (медиа) │ ClickHouse (аналитика)     │          │
│       └──────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  ВНЕШНИЕ API                                 │
│  VK API │ GigaChat │ YandexGPT │ OpenAI │ Kandinsky │ S3    │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Callback события
┌─────────────────────────────────────────────────────────────┐
│         СООБЩЕСТВА КЛИЕНТОВ (ВК)                             │
│  Подписчики пишут → ВК шлёт Callback на наш Backend         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Ключевые сервисы

| Сервис | Назначение | Технология |
|--------|-----------|-----------|
| **API Gateway** | Точка входа, авторизация, маршрутизация | FastAPI |
| **Bot Engine** | Исполнение сценариев чат-ботов | Python + Redis (state) |
| **Mailing Worker** | Очередь рассылок, rate limiting | Celery + Redis |
| **AI Agent Service** | RAG-пайплайн, обращение к LLM | Python + LangChain/LlamaIndex |
| **Content Service** | Генерация текстов/картинок, автопостинг | Python + APScheduler |
| **Billing Service** | Учёт кредитов, списания, тарифы | Python + PostgreSQL |
| **Webhook Receiver** | Приём Callback от VK | FastAPI (отдельный endpoint) |

---

## 5. Технологический стек

### 5.1 Frontend (VK Mini App)

- **Фреймворк:** React 18 + TypeScript
- **UI-кит:** VKUI (@vkontakte/vkui)
- **Мост:** VK Bridge (@vkontakte/vk-bridge)
- **State:** Zustand или Redux Toolkit
- **Роутинг:** @vkontakte/vk-mini-apps-router
- **Сборка:** Vite
- **Drag-and-drop для конструктора:** React Flow (для нодового редактора)
- **Графики:** Recharts

### 5.2 Backend

- **Язык:** Python 3.11+
- **Web-фреймворк:** FastAPI (асинхронный, OpenAPI из коробки)
- **ORM:** SQLAlchemy 2.0 + Alembic (миграции)
- **Очереди:** Celery + Redis
- **Векторная БД:** Qdrant (или pgvector как простая альтернатива)
- **LLM-оркестрация:** LangChain или LlamaIndex
- **HTTP-клиент:** httpx (асинхронный)

### 5.3 Базы данных

- **PostgreSQL 15+** — основная БД (пользователи, сценарии, статистика)
- **Redis** — кэш, очереди, state-машины ботов
- **Qdrant** — векторная БД для RAG
- **ClickHouse** — аналитика (логи сообщений, метрики) — опционально для MVP
- **S3-совместимое хранилище** — медиа, документы базы знаний (Yandex Object Storage)

### 5.4 Инфраструктура

- **Деплой:** Docker + Docker Compose (на старте), потом Kubernetes
- **Хостинг:** Yandex Cloud / Selectel / VK Cloud (важно — российская юрисдикция для соответствия закону о ПД)
- **CI/CD:** GitHub Actions / GitLab CI
- **Мониторинг:** Prometheus + Grafana, Sentry для ошибок
- **Логи:** Loki или ELK

---

## 6. Модель данных (БД)

### 6.1 Основные таблицы PostgreSQL

```sql
-- Пользователи платформы (предприниматели)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vk_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    email VARCHAR(255),
    phone VARCHAR(20),
    credits_balance DECIMAL(10, 2) DEFAULT 0,
    trial_ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Подключённые сообщества ВК
CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    vk_group_id BIGINT NOT NULL,
    group_name VARCHAR(255),
    group_avatar TEXT,
    access_token TEXT NOT NULL,  -- шифровать при хранении (см. безопасность)
    token_permissions TEXT[],
    callback_server_id INTEGER,
    callback_confirm_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, vk_group_id)
);

-- Подписчики сообществ (для сегментации и истории)
CREATE TABLE subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    vk_user_id BIGINT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    sex SMALLINT,  -- 1=female, 2=male
    city VARCHAR(100),
    birth_date DATE,
    tags TEXT[],
    variables JSONB DEFAULT '{}',  -- кастомные поля из ботов
    last_interaction_at TIMESTAMP,
    can_message BOOLEAN DEFAULT FALSE,  -- писал ли группе за 24 часа
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(community_id, vk_user_id)
);

-- Сценарии чат-ботов
CREATE TABLE bot_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    trigger_type VARCHAR(50),  -- 'keyword', 'start_command', 'subscribe', 'manual'
    trigger_value TEXT,  -- ключевое слово или другое условие
    flow_graph JSONB NOT NULL,  -- весь граф нод
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Текущее состояние подписчика в боте (хранится в Redis с TTL,
-- здесь — fallback для долгих диалогов)
CREATE TABLE bot_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID REFERENCES bot_flows(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    current_node_id VARCHAR(100),
    context JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(flow_id, subscriber_id)
);

-- Рассылки
CREATE TABLE mailings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    name VARCHAR(255),
    message_text TEXT,
    attachments JSONB,
    segment_filter JSONB,  -- условия выборки подписчиков
    scheduled_at TIMESTAMP,
    status VARCHAR(20),  -- 'draft', 'scheduled', 'sending', 'completed', 'failed'
    total_recipients INT DEFAULT 0,
    sent_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ИИ-агенты
CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    name VARCHAR(255),
    role VARCHAR(100),  -- 'consultant', 'sales', 'lead_qualifier', 'support'
    system_prompt TEXT,
    tone VARCHAR(50),
    llm_provider VARCHAR(50),  -- 'gigachat', 'yandexgpt', 'openai', 'claude'
    llm_model VARCHAR(100),
    temperature DECIMAL(2,1) DEFAULT 0.7,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.6,
    fallback_action VARCHAR(50),  -- 'transfer_operator', 'static_message'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- База знаний агентов
CREATE TABLE knowledge_base_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id) ON DELETE CASCADE,
    source_type VARCHAR(50),  -- 'file', 'url', 'manual', 'wall_post'
    source_url TEXT,
    file_name VARCHAR(255),
    file_size INT,
    content_text TEXT,
    chunks_count INT,
    qdrant_collection VARCHAR(100),  -- название коллекции в Qdrant
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- История диалогов агентов
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    messages JSONB NOT NULL,  -- [{role, content, timestamp}, ...]
    tokens_in INT,
    tokens_out INT,
    credits_spent DECIMAL(10, 4),
    status VARCHAR(20),  -- 'active', 'closed', 'transferred'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Контент-планы и посты
CREATE TABLE content_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    text TEXT,
    image_urls TEXT[],
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    vk_post_id BIGINT,
    status VARCHAR(20),  -- 'draft', 'scheduled', 'published', 'failed'
    ai_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Транзакции с кредитами
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20),  -- 'topup', 'spend', 'refund', 'bonus'
    amount DECIMAL(10, 4) NOT NULL,
    balance_after DECIMAL(10, 4),
    description TEXT,
    resource_type VARCHAR(50),  -- 'message', 'llm_request', 'image_gen', etc.
    resource_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Тарифные коэффициенты (управляются админом)
CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) UNIQUE,  -- 'message_send', 'gigachat_1k_tokens', etc.
    credits_cost DECIMAL(10, 4),
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 6.2 Индексы

```sql
CREATE INDEX idx_subscribers_community ON subscribers(community_id);
CREATE INDEX idx_subscribers_vk_user ON subscribers(vk_user_id);
CREATE INDEX idx_bot_states_subscriber ON bot_states(subscriber_id);
CREATE INDEX idx_mailings_status ON mailings(status, scheduled_at);
CREATE INDEX idx_conversations_agent ON agent_conversations(agent_id);
CREATE INDEX idx_credit_tx_user_date ON credit_transactions(user_id, created_at DESC);
```

---

## 7. API внутренний (REST)

### 7.1 Авторизация

Все запросы от Mini App — с JWT-токеном в заголовке `Authorization: Bearer <token>`.  
Токен получается при первом входе через VK Bridge → `bridge.send('VKWebAppGetAuthToken')` → обмен на JWT на бэкенде.

### 7.2 Эндпоинты

**Auth:**
```
POST   /api/auth/vk            — обмен подписи VK launch params на JWT
GET    /api/auth/me            — текущий пользователь
```

**Communities (сообщества клиента):**
```
GET    /api/communities                 — список подключённых
POST   /api/communities/connect         — подключить (передать токен сообщества)
DELETE /api/communities/:id             — отключить
GET    /api/communities/:id/stats       — статистика
POST   /api/communities/:id/sync        — синхронизировать подписчиков
```

**Subscribers:**
```
GET    /api/communities/:id/subscribers       — список (пагинация, фильтры)
GET    /api/communities/:id/subscribers/:sid  — детали + история
POST   /api/communities/:id/subscribers/:sid/tags  — управление тегами
```

**Bot Flows:**
```
GET    /api/flows                  — список сценариев
POST   /api/flows                  — создать
GET    /api/flows/:id              — получить граф
PUT    /api/flows/:id              — обновить
DELETE /api/flows/:id              — удалить
POST   /api/flows/:id/test         — запустить тестовый прогон
POST   /api/flows/:id/activate     — активировать/деактивировать
GET    /api/flows/:id/stats        — статистика по нодам
```

**Mailings:**
```
GET    /api/mailings               — список
POST   /api/mailings               — создать
POST   /api/mailings/:id/preview   — предпросчёт сегмента (сколько получателей)
POST   /api/mailings/:id/send      — отправить или поставить в очередь
GET    /api/mailings/:id/stats     — статистика
```

**AI Agents:**
```
GET    /api/agents                       — список
POST   /api/agents                       — создать
GET    /api/agents/:id                   — детали
PUT    /api/agents/:id                   — обновить
POST   /api/agents/:id/knowledge         — загрузить документ в базу знаний
GET    /api/agents/:id/knowledge         — список документов
DELETE /api/agents/:id/knowledge/:docId  — удалить
POST   /api/agents/:id/chat              — тестовый чат с агентом
GET    /api/agents/:id/conversations     — история диалогов
```

**Content (генерация и автопостинг):**
```
POST   /api/content/generate/text       — сгенерировать пост по теме
POST   /api/content/generate/image      — сгенерировать картинку
POST   /api/content/generate/plan       — контент-план на N дней
GET    /api/content/posts               — список постов
POST   /api/content/posts               — создать пост (можно отложенный)
DELETE /api/content/posts/:id           — удалить
POST   /api/content/posts/:id/publish   — опубликовать сейчас
```

**Billing:**
```
GET    /api/billing/balance             — текущий баланс
GET    /api/billing/transactions        — история транзакций (пагинация)
POST   /api/billing/topup               — создать платёж (возвращает URL)
POST   /api/billing/webhook             — webhook от платёжной системы
GET    /api/billing/pricing             — текущие тарифы
```

**Webhooks (от ВК):**
```
POST   /webhooks/vk/:community_id       — Callback API endpoint
```

### 7.3 Пример: ответ `GET /api/flows/:id`

```json
{
  "id": "uuid",
  "name": "Воронка для интернет-магазина",
  "trigger_type": "keyword",
  "trigger_value": "купить",
  "is_active": true,
  "flow_graph": {
    "nodes": [
      {
        "id": "node-1",
        "type": "message",
        "position": {"x": 100, "y": 100},
        "data": {
          "text": "Привет! Что вас интересует?",
          "buttons": [
            {"label": "Каталог", "next": "node-2"},
            {"label": "Связаться с менеджером", "next": "node-3"}
          ]
        }
      },
      {"id": "node-2", "type": "message", "data": {"text": "Вот наш каталог..."}},
      {"id": "node-3", "type": "transfer_operator", "data": {}}
    ],
    "edges": [
      {"from": "node-1", "to": "node-2", "condition": "button:Каталог"},
      {"from": "node-1", "to": "node-3", "condition": "button:Связаться с менеджером"}
    ]
  }
}
```

---

## 8. Интеграции с внешними API

### 8.1 VK API

**Документация:** https://dev.vk.com/

**Ключевые методы:**
- `groups.getById` — данные сообщества
- `groups.getMembers` — список подписчиков (для синхронизации)
- `users.get` — данные пользователя по id
- `messages.send` — отправить сообщение от имени группы
- `wall.post` — публикация поста
- `photos.getMessagesUploadServer` + `photos.saveMessagesPhoto` — загрузка картинок
- `groups.setLongPollSettings` / Callback API — приём событий

**Callback API:**
- Регистрируется endpoint, ВК шлёт события `message_new`, `wall_post_new`, `group_join`, `group_leave`
- Верификация: первый запрос — `confirmation`, нужно вернуть строку подтверждения
- Secret key для проверки подлинности запросов

**Лимиты API:**
- 20 запросов/сек на access_token
- Использовать `execute` для батчинга
- Лимиты на сообщения: см. https://dev.vk.com/method/messages.send

### 8.2 LLM-провайдеры

**GigaChat (Сбер) — приоритет:**
- API: https://developers.sber.ru/portal/products/gigachat
- Авторизация: OAuth + API key
- Российская юрисдикция ✓

**YandexGPT:**
- API: https://yandex.cloud/ru/services/yandexgpt
- Привязка к Yandex Cloud аккаунту

**OpenAI / Anthropic:**
- Платно в валюте, могут быть проблемы с доступом из РФ
- Использовать через прокси или для опциональных премиум-функций

### 8.3 Image generation

**Kandinsky (FusionBrain):**
- API: https://fusionbrain.ai/docs/
- Бесплатные квоты, потом платно

**FLUX через replicate.com / fal.ai** — альтернатива.

### 8.4 Платёжная система

**ЮKassa** — стандарт для РФ:
- https://yookassa.ru/developers
- Поддержка карт, СБП, кошельков
- Webhook при успешной оплате

**Альтернативы:** CloudPayments, Tinkoff Acquiring.

---

## 9. Биллинг и тарификация

### 9.1 Модель: внутренние кредиты

- 1 кредит ≈ 1 рубль (для прозрачности)
- Клиент пополняет баланс пакетами (500 / 1500 / 5000 / 15000 кредитов)
- При покупке больших пакетов — скидка (бонусные кредиты)
- Каждое действие списывает кредиты по тарифной таблице

### 9.2 Примерная тарифная таблица (настраивается в `pricing_rules`)

| Действие | Стоимость в кредитах | Комментарий |
|----------|---------------------|-------------|
| Отправка сообщения подписчику | 0.10 | через бота или рассылку |
| LLM-запрос GigaChat (1K токенов) | 0.50 | себестоимость + наценка |
| LLM-запрос YandexGPT (1K токенов) | 0.50 | |
| LLM-запрос GPT-4o (1K токенов) | 5.00 | дороже из-за валютной разницы |
| LLM-запрос Claude (1K токенов) | 6.00 | |
| Генерация изображения Kandinsky | 3.00 | |
| Генерация изображения DALL-E 3 | 12.00 | |
| Индексация документа в базу знаний (1MB) | 5.00 | разовая операция |
| Автопостинг (1 пост) | 0.50 | |

### 9.3 Логика списания

1. Перед действием — проверка баланса (с резервированием)
2. После успешного выполнения — фактическое списание
3. При ошибке — возврат резерва
4. Логирование в `credit_transactions`

### 9.4 Лимиты и защита

- Минимальный баланс для активного использования — настраиваемый (например, 50 кредитов)
- При нулевом балансе — пауза рассылок и агентов, уведомление клиенту
- Hard cap на расход в час (защита от взлома и зацикленных диалогов)

---

## 10. Безопасность

### 10.1 Хранение токенов сообществ

- **Шифрование AES-256** при хранении в БД
- Ключ шифрования — в переменных окружения (или в Vault)
- Токены никогда не возвращаются клиенту, никогда не логируются

### 10.2 Защита API

- JWT с коротким TTL (1 час) + refresh tokens (30 дней)
- Rate limiting на endpoints (slowapi / nginx)
- CORS — только домены VK
- Все запросы — HTTPS

### 10.3 Валидация подлинности запросов от VK Mini App

VK при запуске Mini App передаёт launch_params с подписью.  
Backend обязан проверять подпись по алгоритму из документации:  
https://dev.vk.com/mini-apps/auth

### 10.4 Защита Callback endpoint

- Проверка `secret` из настроек Callback API
- Whitelist IP-адресов ВК (опционально)
- Идемпотентность: один и тот же event_id обрабатывается единожды

### 10.5 Соответствие 152-ФЗ

- Данные пользователей хранятся в российской юрисдикции (Yandex Cloud, VK Cloud, Selectel)
- Уведомление в Роскомнадзор как оператор персональных данных
- Политика конфиденциальности, согласие на обработку ПД при регистрации

---

## 11. Этапы разработки (Roadmap)

### Этап 1: Фундамент (2-3 недели)
- Настройка проекта (репозиторий, CI/CD, окружения)
- Регистрация VK Mini App в кабинете разработчика
- Базовая авторизация через VK ID
- Mini App с пустым каркасом: подключение сообществ, профиль, баланс
- БД, миграции, базовые модели

### Этап 2: ИИ-агенты (4-5 недель) — самая ценная функция
- Создание агента, system prompt
- Загрузка документов, эмбеддинги, Qdrant
- RAG-пайплайн с GigaChat
- Интеграция через Callback API: входящее сообщение → ответ агента
- Тестовый чат в Mini App
- Лог диалогов
- Подключение биллинга

### Этап 3: Конструктор чат-ботов (4-5 недель)
- Нода-редактор на React Flow
- Базовые ноды: сообщение, кнопки, ожидание, условие, переменная
- State machine на бэкенде, хранение в Redis
- Интеграция с Callback API
- Тестирование сценариев

### Этап 4: Рассылки и автоответчики (3 недели)
- Создание рассылки, фильтры сегментов
- Очередь Celery + rate limiter
- Отложенные рассылки
- Автоответчик на ключевые слова
- Базовые автоворонки

### Этап 5: ИИ-оформление (3-4 недели)
- Генерация текстов постов (GigaChat)
- Генерация картинок (Kandinsky)
- Контент-план
- Автопостинг через VK API
- Календарь публикаций

### Этап 6: Полировка и запуск (2-3 недели)
- Аналитика и дашборды
- Онбординг для новых пользователей
- Документация
- Beta-тест с 10-20 предпринимателями
- Маркетинг

**Итого:** ~5 месяцев до полного MVP, но через 2 месяца уже можно запускать ИИ-агенты в платное использование.

---

## 12. Промпты для вайб-кодинга

Когда вы будете кодить с ИИ-ассистентом, лучше давать ему контекст по одному модулю/файлу за раз. Ниже — заготовки промптов под каждый шаг.

### 12.1 Промпт для старта проекта

```
Создай монорепозиторий с двумя проектами:
1. /backend — Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Celery, Redis. 
   Подключение к PostgreSQL через DATABASE_URL.
   Структура: app/api, app/services, app/models, app/schemas, app/core (config, db, security).
   Docker Compose с сервисами: api, worker, postgres, redis, qdrant.
2. /miniapp — React 18 + TypeScript + Vite, VKUI, VK Bridge, React Flow, Zustand.

Настрой:
- pre-commit с ruff и mypy для backend
- ESLint + Prettier для frontend
- GitHub Actions: тесты на push, деплой на main
- .env.example для обоих
```

### 12.2 Промпт для модели данных

```
Создай SQLAlchemy 2.0 модели и Alembic миграцию для следующих таблиц 
[вставь раздел 6.1 из ТЗ].

Требования:
- Все таблицы наследуют от Base с полями id, created_at, updated_at
- UUID как primary key через server_default=text("gen_random_uuid()")
- JSONB через postgresql.JSONB
- Связи через relationship() с правильным cascade
- Создай Pydantic schemas для Create / Update / Read для каждой модели
```

### 12.3 Промпт для авторизации через VK

```
Реализуй авторизацию VK Mini App:
1. На фронте: при старте Mini App получи launch_params через VK Bridge 
   и отправь их на /api/auth/vk.
2. На бэкенде: проверь подпись launch_params по алгоритму VK 
   (https://dev.vk.com/mini-apps/auth), создай или найди пользователя 
   по vk_user_id, верни JWT-токен (access + refresh).
3. Middleware на FastAPI: декодирование JWT, инъекция current_user в endpoints.
4. На фронте: сохрани токен в памяти (не в localStorage), 
   обновляй через refresh при 401.
```

### 12.4 Промпт для RAG-пайплайна

```
Реализуй RAG-пайплайн для ИИ-агентов:

1. Загрузка документа:
   - Принять файл (PDF/DOCX/TXT) или URL
   - Извлечь текст (pypdf для PDF, python-docx для DOCX, BeautifulSoup для URL)
   - Разбить на чанки по 500 токенов с overlap 100 (используй tiktoken)
   - Создать эмбеддинги через GigaChat Embeddings API
   - Сохранить в Qdrant с метаданными (agent_id, source_id, chunk_index)

2. Обработка вопроса подписчика:
   - Получить эмбеддинг вопроса
   - Найти top-5 чанков в Qdrant с фильтром по agent_id
   - Собрать prompt: system_prompt агента + найденные чанки + 
     история диалога (последние 6 сообщений) + текущий вопрос
   - Отправить в LLM (GigaChat), получить ответ
   - Сохранить в agent_conversations, списать кредиты

Используй LangChain для оркестрации.
```

### 12.5 Промпт для Callback Receiver

```
Реализуй endpoint POST /webhooks/vk/{community_id}, который принимает 
события Callback API ВК:

1. Найти Community по community_id, проверить secret из тела запроса
2. Если type == "confirmation" — вернуть confirmation_code сообщества
3. Если type == "message_new":
   - Извлечь object.message (текст, user_id, attachments)
   - Найти или создать subscriber
   - Параллельно проверить:
     a) Подходит ли сообщение под триггер какого-то bot_flow → запустить движок
     b) Если активен ai_agent в этом сообществе → передать в RAG-пайплайн
   - Вернуть "ok" немедленно (обработка асинхронно через Celery)

Используй FastAPI BackgroundTasks или Celery для async обработки.
ВК ожидает ответ "ok" в течение 10 секунд, иначе считает event непринятым.
```

### 12.6 Совет по работе с ИИ-кодером

1. **Не давайте всё ТЗ сразу** — модель потеряется. Скармливайте по модулю.
2. **Перед каждым модулем** — приложите соответствующий раздел БД и API из этого ТЗ.
3. **Просите писать тесты** для каждой функции (pytest для backend, vitest для frontend).
4. **Code review через другой ИИ** — после написания скиньте код Claude/GPT с вопросом "найди баги и уязвимости".
5. **Линтеры строгие** — пусть ИИ настроит ruff (Python) и ESLint так, чтобы они валили CI на нарушениях.

---

## Приложение А: Полезные ссылки

- VK Mini Apps: https://dev.vk.com/mini-apps
- VK API: https://dev.vk.com/method
- VKUI: https://vkcom.github.io/VKUI/
- VK Bridge: https://dev.vk.com/bridge/overview
- Callback API: https://dev.vk.com/api/callback/getting-started
- GigaChat API: https://developers.sber.ru/portal/products/gigachat
- Kandinsky API: https://fusionbrain.ai/docs/
- ЮKassa: https://yookassa.ru/developers
- React Flow: https://reactflow.dev/
- LangChain: https://python.langchain.com/

## Приложение Б: Что не входит в MVP (бэклог v2)

- Конструктор лендингов
- Интеграция с CRM (Bitrix24, amoCRM)
- Кросспостинг в Telegram / OK
- Telegram-боты для тех же клиентов
- Маркетплейс готовых шаблонов сценариев
- White label для агентств
- Мобильное приложение для управления (нативное)
- Reseller-программа

---

**Конец документа.**
