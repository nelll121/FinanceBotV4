# FinanceBot v2 — Контекст для ИИ и архитектура проекта

> Этот документ — единственный источник правды для разработки.
> Старый код не использовать. Писать с нуля по этому документу.
> Версия: 2.0 | Апрель 2026

---

## 1. Что за проект

Персональный Telegram-бот финансового учёта. Поддержка нескольких пользователей, каждый со своей Google Sheets таблицей. ИИ советник на Claude Haiku с утренними/вечерними сводками.

**Один пользователь = одна таблица Google Sheets = один бот**

---

## 2. Стек

```
aiogram==3.x           — Telegram бот (FSM, роутеры, middleware)
gspread==6.x           — Google Sheets прямой доступ
google-auth==2.x       — Service Account авторизация
anthropic              — Claude Haiku API
apscheduler==3.x       — расписание (сводки, напоминания)
python-dotenv==1.x     — .env локально
loguru                 — логирование
```

### requirements.txt
```
aiogram>=3.0
gspread>=6.0
google-auth>=2.0
anthropic>=0.8
apscheduler>=3.10
python-dotenv>=1.0
loguru>=0.7
```

### Procfile (Railway)
```
worker: python -m bot.main
```

---

## 3. Структура файлов

```
FinanceBot/
│
├── bot/
│   ├── __init__.py
│   ├── main.py                  # Точка входа
│   ├── config.py                # ENV переменные, константы таблицы
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py             # /start, регистрация
│   │   ├── expenses.py          # Расходы
│   │   ├── income.py            # Доходы
│   │   ├── debts.py             # Долги
│   │   ├── summary.py           # Сводки
│   │   ├── savings.py           # Накопления и цели
│   │   ├── ai_advisor.py        # ИИ советник (чат режим)
│   │   └── admin.py             # /grant /revoke /users
│   │
│   ├── states/
│   │   ├── __init__.py
│   │   ├── expense_states.py
│   │   ├── income_states.py
│   │   ├── debt_states.py
│   │   └── savings_states.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sheets.py            # Все операции с Google Sheets
│   │   ├── drive.py             # Создание таблицы из шаблона
│   │   ├── ai_service.py        # Все вызовы Claude API
│   │   ├── scheduler.py         # Расписание сводок и напоминаний
│   │   └── users.py             # CRUD users.json
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── main_kb.py           # Главное меню
│   │   ├── categories_kb.py     # Динамические кнопки категорий
│   │   ├── debts_kb.py          # Список долгов
│   │   └── common_kb.py         # Отмена, пропустить, подтвердить
│   │
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py        # fmt_money, fmt_date, parse_date
│       └── middlewares.py       # Проверка доступа, логирование
│
├── data/
│   └── users.json               # База пользователей (не коммитить если есть личные данные)
│
├── AppsScript/
│   └── onEdit.js                # Только onEdit для ручного редактирования таблицы
│
├── .env                         # Не коммитить
├── .env.example                 # Коммитить — без значений
├── .gitignore
├── Procfile
├── requirements.txt
├── CLAUDE_CONTEXT.md            # Этот файл
└── README.md
```

---

## 4. Переменные окружения

```env
# .env.example

BOT_TOKEN=                    # Telegram Bot Token (@BotFather)
ADMIN_USER_ID=                # Telegram ID администратора
ANTHROPIC_API_KEY=            # Claude API ключ администратора
GOOGLE_CREDENTIALS_JSON=      # JSON Service Account одной строкой
TEMPLATE_SHEET_ID=            # ID шаблонной таблицы в Google Drive
TIMEZONE=Asia/Almaty          # Часовой пояс по умолчанию
```

### config.py — структура
```python
from dotenv import load_dotenv
import os, json

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TEMPLATE_SHEET_ID = os.getenv("TEMPLATE_SHEET_ID")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Almaty")

GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON", "{}"))

# Координаты Google Sheets — НЕ МЕНЯТЬ без изменения структуры таблицы
class SheetsConfig:
    # Журнал долгов
    JOURNAL_SHEET   = "📋 Журнал долгов"
    J_TYPE_COL      = 3   # C
    J_NAME_COL      = 4   # D
    J_DESC_COL      = 5   # E
    J_AMOUNT_COL    = 6   # F
    J_REC_COL       = 7   # G
    J_RET_COL       = 8   # H
    J_STATUS_COL    = 9   # I
    J_NOTE_COL      = 10  # J
    J_START_ROW     = 6
    J_END_ROW       = 55

    # Ежедневные расходы
    EXP_DATE_COL    = 2   # B
    EXP_DESC_COL    = 3   # C
    EXP_CAT_COL     = 8   # H
    EXP_AMT_COL     = 11  # K
    EXP_NOTE_COL    = 12  # L
    EXP_DAILY_START = 34
    EXP_DAILY_END   = 94

    # Ежедневные доходы
    INC_DATE_COL    = 14  # N
    INC_DESC_COL    = 15  # O
    INC_CAT_COL     = 20  # T
    INC_AMT_COL     = 23  # W
    INC_NOTE_COL    = 24  # X
    INC_DAILY_START = 34
    INC_DAILY_END   = 94

    # Итого для сводки месяца
    INC_TOTAL_ROW   = 13
    INC_FACT_COL    = 16  # P
    EXP_TOTAL_ROW   = 22
    EXP_FACT_COL    = 20  # T

    # Категории
    EXP_CAT_RANGE_START = 6
    EXP_CAT_RANGE_COL   = 18  # R
    INC_CAT_RANGE_START = 6
    INC_CAT_RANGE_COL   = 14  # N

    # История возвратов
    HISTORY_SHEET   = "📜 История возвратов"

    # Настройки ИИ
    SETTINGS_SHEET  = "⚙️ Настройки"

    MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь",
              "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
```

---

## 5. База пользователей (data/users.json)

```json
{
  "1358492142": {
    "name": "Nooir",
    "sheets_id": "google_spreadsheet_id_here",
    "api_key": null,
    "ai_access": true,
    "timezone": "Asia/Almaty",
    "morning_time": "09:00",
    "evening_time": "21:00",
    "notifications": true,
    "registered_at": "2026-04-19",
    "is_admin": true
  }
}
```

### Логика API ключа
```
api_key = null  +  ai_access = true   →  используется ANTHROPIC_API_KEY из ENV (ключ администратора)
api_key = null  +  ai_access = false  →  ИИ недоступен, бот предлагает добавить свой ключ
api_key = "sk-ant-..."               →  используется собственный ключ пользователя
```

---

## 6. services/users.py — управление пользователями

```python
# Все методы синхронные, работают с data/users.json

get_user(user_id: str) -> dict | None
save_user(user_id: str, data: dict) -> None
user_exists(user_id: str) -> bool
is_registered(user_id: str) -> bool      # есть + sheets_id заполнен
is_admin(user_id: str) -> bool
get_all_users() -> dict
get_api_key(user_id: str) -> str | None  # None если нет доступа
grant_ai_access(user_id: str) -> None    # ai_access = True, api_key = null
revoke_ai_access(user_id: str) -> None   # ai_access = False
set_user_api_key(user_id: str, key: str) -> None
```

---

## 7. services/drive.py — создание таблицы

```python
# Используется только при первой регистрации пользователя

async def create_from_template(user_email: str) -> str:
    """
    Копирует шаблонную таблицу из TEMPLATE_SHEET_ID
    Открывает доступ на user_email
    Возвращает sheets_id новой таблицы
    """
```

### Алгоритм регистрации (handlers/start.py)
```
/start получен
  ↓
user_exists(user_id)?
  ДА → is_registered(user_id)?
         ДА → state.clear() → главное меню (таблицу НЕ трогать)
         НЕТ → продолжить регистрацию (таблица не создана)
  НЕТ → начать регистрацию
         → запросить имя
         → запросить email Google аккаунта
         → drive.create_from_template(email) → sheets_id
         → save_user(user_id, {..., sheets_id})
         → отправить ссылку на таблицу
         → главное меню
```

**ВАЖНО: /start никогда не создаёт таблицу если пользователь уже зарегистрирован**

---

## 8. services/sheets.py — все операции с таблицей

Авторизация через Service Account (GOOGLE_CREDENTIALS_JSON).
Каждый метод принимает `sheets_id` первым аргументом.

```python
import gspread
from google.oauth2.service_account import Credentials
from bot.config import GOOGLE_CREDENTIALS, SheetsConfig as SC
from datetime import datetime

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def _get_spreadsheet(sheets_id: str):
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheets_id)

def _current_month_sheet(sheets_id: str):
    ss = _get_spreadsheet(sheets_id)
    month = SC.MONTHS[datetime.now().month - 1]
    return ss.worksheet(month)
```

### Финансы
```python
get_categories(sheets_id) -> dict
# Читает категории из текущего месяца динамически
# Возвращает: {"expense": ["Еда", "Транспорт", ...], "income": ["Зарплата", ...]}
# Категории берутся прямо из таблицы — если пользователь добавил новую, она появится автоматически

add_expense(sheets_id, category, amount, description="", note="") -> bool
# Находит первую пустую строку в EXP_DAILY_START..EXP_DAILY_END
# Записывает: дата, описание, категория, сумма, примечание

add_income(sheets_id, category, amount, description="", note="") -> bool
# Аналогично для доходов

get_month_summary(sheets_id, month=None) -> dict
# Возвращает: {month, income, expense, savings, podushka, balance, savings_percent}
# Читает итоги из INC_TOTAL_ROW и EXP_TOTAL_ROW

get_day_operations(sheets_id, date: str) -> dict
# date формат: "YYYY-MM-DD"
# Возвращает: {expenses: [{category, amount, desc}], income: [...], total_expense, total_income}
```

### Долги
```python
add_debt(sheets_id, type, name, amount, description="", return_date=None) -> bool
# type: "Мне должны" | "Я должен"
# Находит первую пустую строку в J_START_ROW..J_END_ROW
# Записывает все поля, статус = "Активен"
# После записи долга АВТОМАТИЧЕСКИ вызывает:
#   add_expense если type == "Мне должны"  (дал деньги → расход категории "Займ")
#   add_income  если type == "Я должен"    (получил деньги → доход категории "Займ")

get_active_debts(sheets_id) -> list[dict]
# Только статус "Активен" или "Частично"
# Возвращает: [{index, type, name, desc, amount, return_date, status, note}]
# index — порядковый номер в списке (0-based), НЕ строка таблицы

return_debt_full(sheets_id, debt_index: int) -> bool
# Находит долг по index из get_active_debts
# Статус → "Возвращён", фон → зелёный, примечание с датой
# Записывает в ежедневные операции (доход если "Мне должны", расход если "Я должен")
# Вызывает write_return_history(...)
# Строка остаётся в журнале (для истории), но больше не показывается в боте

return_debt_partial(sheets_id, debt_index: int, paid: float) -> bool
# Обновляет ТУ ЖЕ строку: сумма = остаток, статус = "Частично"
# НЕ создаёт новую строку
# Записывает в ежедневные операции
# Вызывает write_return_history(...)

write_return_history(sheets_id, name, type, paid, remain, original, return_type, desc="", record_date="") -> None
# Записывает в лист "📜 История возвратов"
# Колонки: Дата возврата, Имя, Описание долга, Тип долга, Статус возврата,
#          Изначальная сумма, Возвращено, Остаток, Дата займа

get_return_history(sheets_id, name=None) -> list[dict]
```

### Накопления и цели
```python
get_savings_goals(sheets_id) -> list[dict]
# Читает из листа "🎯 Цели" (если нет — создать автоматически)
# Возвращает: [{name, target_amount, current_amount, percent, created_at}]

add_savings_goal(sheets_id, name: str, target_amount: float) -> bool
# Добавляет новую строку в лист "🎯 Цели"

update_savings_goal(sheets_id, goal_name: str, add_amount: float) -> bool
# Обновляет current_amount цели
# Также записывает в расходы текущего месяца категория "Накопления"
# Описание: "Пополнение цели: {goal_name}"

# Подушка безопасности — это обычная цель с именем "Подушка безопасности"
# Никакой специальной логики, просто обычная цель
```

### ИИ предпочтения
```python
get_ai_preferences(sheets_id) -> dict
# Читает из листа "⚙️ Настройки" начиная с 3-й строки
# Возвращает: {avoid_advice, savings_goal, budget_limit, ai_preferences}

save_ai_preference(sheets_id, key: str, value: str) -> bool
clear_ai_preferences(sheets_id) -> bool
```

### Полный контекст для ИИ
```python
get_full_context(sheets_id) -> dict
# Один метод который загружает всё нужное для ИИ советника
# Возвращает:
# {
#   month_summary: dict,           # итоги текущего месяца
#   active_debts: list,            # активные долги с деталями
#   savings_goals: list,           # цели и прогресс
#   recent_returns: list,          # последние 5 возвратов
#   ai_preferences: dict,          # предпочтения пользователя
#   last_7_days: list,             # операции за последние 7 дней (для анализа)
# }
```

---

## 9. services/ai_service.py — все вызовы Claude

```python
import anthropic
from bot.services.users import get_api_key

def _get_client(user_id: str) -> anthropic.Anthropic:
    key = get_api_key(user_id)
    if not key:
        raise ValueError("NO_API_KEY")
    return anthropic.Anthropic(api_key=key)

async def categorize_expense(user_id: str, text: str, categories: list[str]) -> str | None:
    """
    Определяет категорию по тексту.
    Возвращает название категории из списка или None если не уверен.
    Используется при быстром вводе.
    """

async def get_ai_response(user_id: str, context: dict, history: list, message: str) -> str:
    """
    Обычный ответ в чат режиме ИИ советника.
    context — результат sheets.get_full_context()
    history — список последних 10 сообщений [{role, content}]
    Ответ: простой текст без markdown
    """

async def generate_morning_summary(user_id: str, context: dict) -> str:
    """
    Утренняя сводка с рекомендациями на день.
    Анализирует вчерашние расходы, активные долги, прогресс целей.
    Даёт 1-2 конкретные рекомендации.
    Пример: "Вчера потратил 8 000 ₸ на еду — это выше среднего. 
             Сегодня постарайся уложиться в 3 000 ₸ на обед."
    Ответ: простой текст без markdown, 3-5 предложений
    """

async def generate_evening_summary(user_id: str, context: dict) -> str:
    """
    Вечерняя сводка — итоги дня.
    Показывает что потрачено сегодня, сравнивает с обычным днём.
    Даёт оценку дня и один совет на завтра.
    Ответ: простой текст без markdown, 3-5 предложений
    """

# Системный промпт для всех запросов
SYSTEM_PROMPT = """
Ты личный финансовый советник. 
Отвечай простым текстом без markdown — никаких звёздочек, решёток, жирного текста.
Короткие абзацы. Язык: русский.
Давай конкретные рекомендации с цифрами.
Не задавай вопросов, не мотивируй — только анализ и советы.
"""
```

---

## 10. services/scheduler.py — расписание

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

def setup_scheduler(bot):
    """
    Настраивает задачи для всех пользователей из users.json
    Вызывается при старте бота
    """
    from bot.services.users import get_all_users
    users = get_all_users()
    for user_id, user_data in users.items():
        if user_data.get("notifications"):
            add_user_jobs(bot, user_id, user_data)
    scheduler.start()

def add_user_jobs(bot, user_id: str, user_data: dict):
    morning = user_data.get("morning_time", "09:00")
    evening = user_data.get("evening_time", "21:00")
    h_m, m_m = morning.split(":")
    h_e, m_e = evening.split(":")

    scheduler.add_job(
        send_morning_summary, "cron",
        hour=int(h_m), minute=int(m_m),
        args=[bot, user_id],
        id=f"morning_{user_id}", replace_existing=True
    )
    scheduler.add_job(
        send_evening_summary, "cron",
        hour=int(h_e), minute=int(m_e),
        args=[bot, user_id],
        id=f"evening_{user_id}", replace_existing=True
    )
    scheduler.add_job(
        check_overdue_debts, "cron",
        day_of_week="mon", hour=9, minute=0,
        args=[bot, user_id],
        id=f"debts_{user_id}", replace_existing=True
    )

async def send_morning_summary(bot, user_id: str): ...
async def send_evening_summary(bot, user_id: str): ...
async def check_overdue_debts(bot, user_id: str): ...
```

---

## 11. FSM Состояния

```python
# expense_states.py
class ExpenseStates(StatesGroup):
    category    = State()
    amount      = State()
    description = State()

# income_states.py
class IncomeStates(StatesGroup):
    category    = State()
    amount      = State()
    description = State()

# debt_states.py
class DebtStates(StatesGroup):
    type        = State()   # Мне должны / Я должен
    name        = State()
    amount      = State()
    description = State()   # на что занял/дал
    return_date = State()

class DebtReturnStates(StatesGroup):
    select      = State()   # выбор долга из списка
    amount      = State()   # сумма возврата

# savings_states.py
class SavingsGoalStates(StatesGroup):
    name        = State()   # название цели
    target      = State()   # целевая сумма

class SavingsAddStates(StatesGroup):
    select      = State()   # выбор цели из списка
    amount      = State()   # сумма пополнения

# settings_states.py
class SetupStates(StatesGroup):
    email       = State()   # email для доступа к таблице при регистрации
    api_key     = State()   # ввод собственного API ключа
```

---

## 12. Главное меню и клавиатуры

```python
# main_kb.py — ReplyKeyboard (постоянное меню внизу)
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("💸 Расход"),   KeyboardButton("💰 Доход")],
            [KeyboardButton("💳 Долги"),    KeyboardButton("📊 Сводка")],
            [KeyboardButton("🎯 Цели"),     KeyboardButton("🤖 ИИ чат")],
        ],
        resize_keyboard=True
    )

# Текстовые алиасы (регистронезависимые)
MENU_ALIASES = {
    "расход": "💸 Расход",
    "доход": "💰 Доход",
    "долги": "💳 Долги",
    "сводка": "📊 Сводка",
    "цели": "🎯 Цели",
    "ии": "🤖 ИИ чат",
    "советник": "🤖 ИИ чат",
}

# common_kb.py — общие inline кнопки
def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    ]])

def skip_cancel_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("➡️ Пропустить", callback_data="skip"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
    ]])
```

---

## 13. Handlers — логика каждого модуля

### handlers/start.py
```
Команды: /start
Роутер: router = Router()

/start:
  user_id = str(message.from_user.id)
  
  if is_registered(user_id):
      await state.clear()
      → главное меню  ← ТАБЛИЦА НЕ ТРОГАЕТСЯ
      return
  
  if user_exists(user_id) but not registered:
      → продолжить регистрацию с того места
      return
  
  # Новый пользователь
  → Приветственное сообщение
  → Запросить email Google аккаунта (для доступа к таблице)
  → SetupStates.email

После получения email:
  → drive.create_from_template(email) → sheets_id
  → save_user(user_id, {name, sheets_id, ...defaults})
  → Отправить: "✅ Таблица создана! Ссылка: ..."
  → Главное меню
```

### handlers/expenses.py
```
Триггеры: кнопка "💸 Расход" | текст "расход"

Шаг 1: Показать категории
  → sheets.get_categories(sheets_id)["expense"]
  → Динамические inline кнопки из таблицы
  → ExpenseStates.category

Шаг 2: Выбор категории → запросить сумму
  → ExpenseStates.amount

Шаг 3: Ввод суммы → запросить описание
  → Кнопки: "➡️ Пропустить" / "❌ Отмена"
  → ExpenseStates.description

Шаг 4: Описание или пропуск → записать
  → sheets.add_expense(sheets_id, category, amount, description)
  → Подтверждение → главное меню

Быстрый ввод (из main router):
  Ключевые слова: потратил, купил, заплатил, трата, расход
  → Парсинг суммы (регулярка)
  → ai_service.categorize_expense(user_id, text, categories)
  → Если категория найдена → сразу записать
  → Если нет → показать кнопки категорий
```

### handlers/income.py
```
Триггеры: кнопка "💰 Доход" | текст "доход"
Логика аналогична расходам.

Ключевые слова быстрого ввода:
  поступило, получил, зарплата, пришло, доход
```

### handlers/debts.py
```
Триггеры: кнопка "💳 Долги" | текст "долги"

Показ долгов:
  → sheets.get_active_debts(sheets_id)
  → Если пусто: "✅ Долгов нет" + кнопка "➕ Новый долг"
  → Если есть: список + кнопки "✅ Закрыть долг" / "➕ Новый долг"

Создание долга:
  → DebtStates.type → name → amount → description → return_date
  → sheets.add_debt(...)  ← автоматически пишет в расходы/доходы
  → Подтверждение → главное меню

Закрытие долга:
  → Список активных долгов кнопками
  → DebtReturnStates.select → amount
  → amount >= total: sheets.return_debt_full(...)
  → amount < total:  sheets.return_debt_partial(...)
  → Подтверждение → главное меню

Ключевые слова быстрого ввода:
  "вернул", "отдал", "погасил" → попытаться найти долг по имени
  "занял", "одолжил", "дал в долг" → создать новый долг
  Если нет суммы → запустить пошаговый диалог
```

### handlers/summary.py
```
Триггеры: кнопка "📊 Сводка" | текст "сводка"

Сводка месяца:
  → sheets.get_month_summary(sheets_id)
  → Красивый вывод:
    📊 Апрель 2026
    ══════════════════════
    💚 Доход:      50 000 ₸
    ❤️  Расход:    35 000 ₸
    💼 Баланс:     15 000 ₸
    🎯 Цели:        5 000 ₸
    📈 Накоплено: 30%
    ▓▓▓░░░░░░░

Кнопка "📅 За день":
  → Выбор: Сегодня / Другая дата
  → sheets.get_day_operations(sheets_id, date)
  → Список операций за день
```

### handlers/savings.py
```
Триггеры: кнопка "🎯 Цели" | текст "цели"

Показ целей:
  → sheets.get_savings_goals(sheets_id)
  → Для каждой цели:
    🎯 Машина
    ████░░░░░░ 40%
    40 000 ₸ из 100 000 ₸

Кнопки: "➕ Новая цель" / "💰 Пополнить"

Новая цель:
  → SavingsGoalStates.name → target
  → sheets.add_savings_goal(...)

Пополнить цель:
  → SavingsAddStates.select (список целей кнопками)
  → SavingsAddStates.amount
  → sheets.update_savings_goal(...)  ← пишет в расходы категория "Накопления"
  → Подтверждение с обновлённым прогрессом
```

### handlers/ai_advisor.py
```
Триггеры: кнопка "🤖 ИИ чат" | текст "ии" / "советник"

Вход в режим:
  → ai_service.check_access(user_id)
  → Нет доступа:
      "У тебя нет доступа к ИИ.
       Попроси администратора или введи свой Anthropic API ключ:"
      → SetupStates.api_key
  → Есть доступ:
      → sheets.get_full_context(sheets_id)
      → Сохранить контекст в FSM data
      → Показать меню ИИ советника:
          ReplyKeyboard: ["🔚 Выйти", "💾 Настройки", "🗑 Сбросить"]

В режиме чата:
  → Любой текст → ai_service.get_ai_response(user_id, context, history, text)
  → История хранится в FSM data (максимум 10 сообщений)
  → "🔚 Выйти" → state.clear() → главное меню

Команды внутри чата:
  "запомни ..." → save_ai_preference(...)
  "💾 Настройки" → показать сохранённые предпочтения
  "🗑 Сбросить" → clear_ai_preferences(...)
```

### handlers/admin.py
```
Доступ: только ADMIN_USER_ID

/users
  → Список всех пользователей:
    ID | Имя | ИИ доступ | Свой ключ
    1358492142 | Nooir | ✅ (admin) | —
    9876543210 | Иван  | ✅ | —
    1111111111 | Мария | ❌ | ✅

/grant <user_id>
  → users.grant_ai_access(user_id)
  → Уведомление пользователю: "✅ Тебе выдан доступ к ИИ советнику"

/revoke <user_id>
  → users.revoke_ai_access(user_id)
  → Уведомление пользователю:
    "❌ Доступ к ИИ отозван.
     Введи свой Anthropic API ключ чтобы продолжить:
     /setkey sk-ant-..."

/broadcast <текст>
  → Отправить сообщение всем пользователям
```

---

## 14. utils/middlewares.py

```python
class AccessMiddleware(BaseMiddleware):
    """
    Проверяет что пользователь зарегистрирован.
    Если не зарегистрирован — перенаправляет на /start.
    Исключение: сам /start и команды регистрации.
    """

class LoggingMiddleware(BaseMiddleware):
    """
    Логирует все входящие сообщения через loguru.
    Формат: [USER_ID] [handler_name] текст сообщения
    """
```

---

## 15. utils/formatters.py

```python
def fmt_money(amount) -> str:
    # 10000 → "10 000 ₸"

def fmt_date(d=None) -> str:
    # datetime → "19.04.2026"

def parse_date(date_str: str) -> str:
    # "19.04.2026" → "2026-04-19"

def parse_iso_date(iso_str: str) -> str:
    # "2026-04-19T00:00:00.000Z" → "19.04.2026"
    # Всегда использовать эту функцию для дат из Google Sheets

def progress_bar(current: float, target: float, width=10) -> str:
    # 40%, width=10 → "████░░░░░░ 40%"
```

---

## 16. AppsScript/onEdit.js — минимальный Apps Script

Только для ручного редактирования таблицы.
Вся API логика (addExpense, addDebt, getActiveDebts и т.д.) перенесена в Python через gspread.

Что делает этот файл:
- `onEdit` — автодата при вводе суммы вручную + обработка смены статуса долга вручную
- `handleFullReturn` / `handlePartialReturn` — если статус долга меняется вручную в таблице
- `refreshMonthDebts` — обновляет блоки долгов в месячных листах после каждого возврата
- `checkOverdueDebtsAuto` — триггер по понедельникам, подсвечивает просроченные долги
- `setupTriggers` — запустить один раз вручную для настройки триггеров

Как задеплоить:
1. Google Sheets → Расширения → Apps Script
2. Вставить код ниже (заменить всё что там есть)
3. Запустить `setupTriggers()` один раз вручную
4. Развернуть → Новое развертывание → Веб-приложение (для onEdit триггера)

```javascript
// ═══════════════════════════════════════════════════════════════════
// FinanceBot — Apps Script (минимальная версия)
// Только для ручного редактирования таблицы.
// Вся API логика перенесена в Python бот (gspread).
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════════
// ЛИЧНЫЕ ФИНАНСЫ — Google Apps Script v4
// Исправлено: точные координаты колонок, долги в месяцах, баланс, частичный долг
// ═══════════════════════════════════════════════════════════════════════════════

// ── КОНСТАНТЫ ЖУРНАЛА ─────────────────────────────────────────────────────────
const JOURNAL_SHEET  = "📋 Журнал долгов";
const SUMMARY_SHEET  = "📊 Итоги года";
const MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь",
                "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"];

// Колонки журнала (1-based, из диагностики: B=2...J=10)
const J_NUM    = 2;   // B — №
const J_TYPE   = 3;   // C — Тип
const J_NAME   = 4;   // D — Имя
const J_DESC   = 5;   // E — Описание
const J_AMOUNT = 6;   // F — Сумма
const J_REC    = 7;   // G — Дата записи
const J_RET    = 8;   // H — Дата возврата
const J_STATUS = 9;   // I — Статус
const J_NOTE   = 10;  // J — Примечание
const J_HEADER = 5;   // Строка с заголовками
const J_START  = 6;   // Первая строка данных
const J_END    = 55;  // Последняя строка данных

// ── ТОЧНЫЕ КООРДИНАТЫ МЕСЯЧНОГО ЛИСТА (из диагностики) ───────────────────────
// Доходы
const INC_HEADER_ROW  = 4;   // Строка заголовка блока
const INC_SUBHDR_ROW  = 5;   // Строка подзаголовков (Категория / План / Факт)
const INC_DATA_START  = 6;   // Первая строка данных
const INC_TOTAL_ROW   = 13;  // Строка "Итого" доходов
const INC_CAT_COL     = 14;  // N — Категория
const INC_PLAN_COL    = 15;  // O — Плановый
const INC_FACT_COL    = 16;  // P — Фактический

// Расходы
const EXP_HEADER_ROW  = 4;
const EXP_DATA_START  = 6;   // после подзаголовка строка 6 (аналогично)
const EXP_TOTAL_ROW   = 22;  // Строка "Итого" расходов
const EXP_CAT_COL     = 18;  // R — Категория
const EXP_PLAN_COL    = 19;  // S — Плановый
const EXP_FACT_COL    = 20;  // T — Фактический

// Долги (из диагностики)
const DME_HEADER_ROW  = 5;   // "👤 МНЕ ДОЛЖНЫ"
const DME_DATA_START  = 7;   // Данные с строки 7
const DME_DATA_END    = 14;  // До строки 14 (итого на 15)
const DME_TOTAL_ROW   = 15;  // "Итого мне должны"

const DI_HEADER_ROW   = 17;  // "👤 Я ДОЛЖЕН"
const DI_DATA_START   = 19;  // Данные с строки 19
const DI_DATA_END     = 26;  // До строки 26 (итого на 27)
const DI_TOTAL_ROW    = 27;  // "Итого я должен"

const DEBT_NAME_COL   = 26;  // Z — Имя
const DEBT_AMT_COL    = 27;  // AA — Сумма
const DEBT_DATE_COL   = 28;  // AB — Дата возврата

// Ежедневные операции (из диагностики)
const EXP_DAILY_HEADER = 31; // Строка заголовка секции
const EXP_DAILY_START  = 34; // Первые данные (header+2+subheader+1)
const EXP_DAILY_END    = 94; // Строка перед ИТОГО (95-1)
const EXP_DAILY_TOTAL  = 95;

const EXP_DATE_COL  = 2;    // B
const EXP_DESC_COL  = 3;    // C
const EXP_CAT_COL2  = 8;    // H
const EXP_AMT_COL   = 11;   // K
const EXP_NOTE_COL  = 12;   // L

const INC_DAILY_HEADER = 31; // Та же строка (слева расходы, справа поступления)
const INC_DAILY_START  = 34;
const INC_DAILY_END    = 94;
const INC_DAILY_TOTAL  = 95;

const INC_DATE_COL  = 14;   // N
const INC_DESC_COL  = 15;   // O
const INC_CAT_COL2  = 20;   // T
const INC_AMT_COL   = 23;   // W
const INC_NOTE_COL  = 24;   // X

// ═══════════════════════════════════════════════════════════════════════════════
// МЕНЮ
// ═══════════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════════
// ON EDIT
// ═══════════════════════════════════════════════════════════════════════════════
function onEdit(e) {
  if (!e) return;
  const sheet = e.range.getSheet();
  const name  = sheet.getName();
  const row   = e.range.getRow();
  const col   = e.range.getColumn();
  const val   = String(e.value || "");
  const old   = String(e.oldValue || "");

  // Автодата в ежедневных операциях
  if (MONTHS.includes(name)) {
    if (col === EXP_AMT_COL && Number(val) > 0 &&
        row >= EXP_DAILY_START && row <= EXP_DAILY_END) {
      setDateIfEmpty(sheet, row, EXP_DATE_COL);
    }
    if (col === INC_AMT_COL && Number(val) > 0 &&
        row >= INC_DAILY_START && row <= INC_DAILY_END) {
      setDateIfEmpty(sheet, row, INC_DATE_COL);
    }
  }

  // Логика журнала долгов
  if (name === JOURNAL_SHEET && col === J_STATUS) {
    if (val === "Возвращён") {
      handleFullReturn(sheet, row);
    } else if (val === "Частично") {
      handlePartialReturn(sheet, row);
    } else if (val === "Активен" && old && old !== "Активен" && old !== "") {
      handleRevertToActive(sheet, row, old);
    }
  }
}

function setDateIfEmpty(sheet, row, dateCol) {
  const cell = sheet.getRange(row, dateCol);
  if (!cell.getValue()) {
    cell.setValue(new Date());
    cell.setNumberFormat("DD.MM.YYYY");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ПОЛНЫЙ ВОЗВРАТ ДОЛГА
// ═══════════════════════════════════════════════════════════════════════════════
function handleFullReturn(journalSheet, row) {
  const d = readDebtRow(journalSheet, row);
  if (!d.name || d.amount <= 0) return;

  const targetMonth = monthFromDate(d.returnDate);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const targetSheet = ss.getSheetByName(targetMonth);

  if (!targetSheet) {
    SpreadsheetApp.getUi().alert(
      `⚠️ Лист "${targetMonth}" скрыт.\n\nМеню → 💰 Финансы → Показать все месяцы\nЗатем поменяйте статус снова.`
    );
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  const entryType = d.type === "Мне должны" ? "income" : "expense";
  const entryDate = d.returnDate instanceof Date ? d.returnDate : new Date();
  const note = `Возврат долга: ${d.name}${d.desc ? " — " + d.desc : ""}`;

  const ok = writeDailyEntry(targetSheet, entryType, entryDate, d.name, "Возврат долга", d.amount, note);

  if (ok) {
    journalSheet.getRange(row, J_NOTE).setValue(
      `Закрыт ${fmt(new Date())}. Сумма: ${money(d.amount)}`
    );
    journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#0D2F1A");
    writeReturnHistory(d.name, d.type, d.amount, 0, d.amount, "Полностью", d.desc, d.recordDate instanceof Date ? fmt(d.recordDate) : "");

    const dir = d.type === "Мне должны" ? "поступления" : "расходы";
    SpreadsheetApp.getUi().alert(
      `✅ Записано в ${dir}!\n\nМесяц: ${targetMonth}\n` +
      `${d.type === "Мне должны" ? "От кого" : "Кому"}: ${d.name}\n` +
      `Сумма: ${money(d.amount)}`
    );
    refreshMonthDebts(targetSheet, targetMonth);
  } else {
    SpreadsheetApp.getUi().alert("⚠️ Нет свободных строк в ежедневных операциях.");
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЧАСТИЧНЫЙ ВОЗВРАТ
// Оригинальная строка → статус "Частично", сумма уменьшается на выплаченное
// Новая строка с остатком → статус "Активен"
// ═══════════════════════════════════════════════════════════════════════════════
function handlePartialReturn(journalSheet, row) {
  const d = readDebtRow(journalSheet, row);
  if (!d.name || d.amount <= 0) return;

  const ui = SpreadsheetApp.getUi();

  // Спросить сколько вернули
  const paidResp = ui.prompt(
    "💳 Частичный возврат",
    `Долг: ${d.name} — ${money(d.amount)}\n\nСколько вернули / вернул (₸)?`,
    ui.ButtonSet.OK_CANCEL
  );
  if (paidResp.getSelectedButton() !== ui.Button.OK) {
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }
  const paid = Number(paidResp.getResponseText().replace(/\s/g, ""));
  if (!paid || paid <= 0 || paid >= d.amount) {
    ui.alert("⚠️ Некорректная сумма. Должно быть больше 0 и меньше " + money(d.amount));
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  // Спросить когда ждать следующий платёж
  const dateResp = ui.prompt(
    "📅 Следующий платёж",
    `Остаток: ${money(d.amount - paid)}\n\nКогда ожидать следующий платёж?\n(DD.MM.YYYY или оставь пустым)`,
    ui.ButtonSet.OK_CANCEL
  );
  if (dateResp.getSelectedButton() !== ui.Button.OK) {
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  const remain = d.amount - paid;
  const nextDateStr = dateResp.getResponseText().trim();
  const nextDate = nextDateStr ? parseDate(nextDateStr) : null;
  const targetMonth = monthFromDate(d.returnDate);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const targetSheet = ss.getSheetByName(targetMonth);

  if (!targetSheet) {
    ui.alert(`⚠️ Лист "${targetMonth}" скрыт. Покажите его и повторите.`);
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  // Записать выплаченную сумму в ежедневные операции
  const entryType = d.type === "Мне должны" ? "income" : "expense";
  const note = `Частичный возврат (${money(paid)} из ${money(d.amount)}): ${d.name}`;
  writeDailyEntry(targetSheet, entryType,
    d.returnDate instanceof Date ? d.returnDate : new Date(),
    d.name, "Возврат долга", paid, note);

  // Обновить оригинальную строку:
  // статус = "Частично", сумма = уплаченная, примечание
  journalSheet.getRange(row, J_AMOUNT).setValue(paid);
  journalSheet.getRange(row, J_NOTE).setValue(
    `Частично: ${money(paid)} получено ${fmt(new Date())}. Остаток: ${money(remain)}`
  );
  // Статус остаётся "Частично" (уже установлен пользователем)
  journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#2D2A0D");

  // Создать новую строку с остатком → статус "Активен"
  const emptyRow = findEmptyDebtRow(journalSheet);
  if (emptyRow) {
    journalSheet.getRange(emptyRow, J_NUM).setValue(emptyRow - J_START + 1);
    journalSheet.getRange(emptyRow, J_TYPE).setValue(d.type);
    journalSheet.getRange(emptyRow, J_NAME).setValue(d.name);
    journalSheet.getRange(emptyRow, J_DESC).setValue(d.desc || "");
    journalSheet.getRange(emptyRow, J_AMOUNT).setValue(remain);
    journalSheet.getRange(emptyRow, J_REC).setValue(new Date()).setNumberFormat("DD.MM.YYYY");
    if (nextDate) {
      journalSheet.getRange(emptyRow, J_RET).setValue(nextDate).setNumberFormat("DD.MM.YYYY");
    }
    journalSheet.getRange(emptyRow, J_STATUS).setValue("Активен");
    journalSheet.getRange(emptyRow, J_NOTE).setValue(
      `Остаток от частичного возврата ${fmt(new Date())}`
    );
  }

  const dir = d.type === "Мне должны" ? "поступления" : "расходы";
  ui.alert(
    `✅ Частичный возврат записан!\n\n` +
    `Записано в ${dir}: ${money(paid)}\n` +
    `Остаток ${money(remain)} добавлен новой строкой (Активен)\n` +
    `Текущая строка помечена как Частично\n` +
    `${nextDate ? "Следующий платёж: " + fmt(nextDate) : ""}`
  );

  refreshMonthDebts(targetSheet, targetMonth);
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЗАЩИТА ОТ СЛУЧАЙНОГО СБРОСА СТАТУСА
// ═══════════════════════════════════════════════════════════════════════════════
function handleRevertToActive(journalSheet, row, previousStatus) {
  const d = readDebtRow(journalSheet, row);
  const ui = SpreadsheetApp.getUi();

  const resp = ui.alert(
    "⚠️ Подтверждение",
    `Вы сбрасываете статус "${d.name}" обратно на Активен.\n\n` +
    `Запись в доходах/расходах уже создана — её нужно удалить вручную.\n\n` +
    `Продолжить?`,
    ui.ButtonSet.YES_NO
  );

  if (resp !== ui.Button.YES) {
    journalSheet.getRange(row, J_STATUS).setValue(previousStatus);
  } else {
    journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#21262D");
    journalSheet.getRange(row, J_NOTE).setValue(
      `⚠️ Статус отменён вручную ${fmt(new Date())}`
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЗАПИСЬ В ЕЖЕДНЕВНЫЕ ОПЕРАЦИИ (точные координаты)
// ═══════════════════════════════════════════════════════════════════════════════
function writeDailyEntry(sheet, type, date, description, category, amount, note) {
  const isExp  = type === "expense";
  const sRow   = isExp ? EXP_DAILY_START : INC_DAILY_START;
  const eRow   = isExp ? EXP_DAILY_END   : INC_DAILY_END;
  const dateC  = isExp ? EXP_DATE_COL    : INC_DATE_COL;
  const descC  = isExp ? EXP_DESC_COL    : INC_DESC_COL;
  const catC   = isExp ? EXP_CAT_COL2    : INC_CAT_COL2;
  const amtC   = isExp ? EXP_AMT_COL     : INC_AMT_COL;
  const noteC  = isExp ? EXP_NOTE_COL    : INC_NOTE_COL;

  // Читаем колонку суммы и описания одним запросом
  const amtVals  = sheet.getRange(sRow, amtC,  eRow - sRow + 1, 1).getValues();
  const descVals = sheet.getRange(sRow, descC, eRow - sRow + 1, 1).getValues();

  for (let i = 0; i < amtVals.length; i++) {
    const existAmt  = Number(amtVals[i][0])  || 0;
    const existDesc = String(descVals[i][0]  || "").trim();
    if (existAmt === 0 && existDesc === "") {
      const r = sRow + i;
      sheet.getRange(r, dateC).setValue(date).setNumberFormat("DD.MM.YYYY");
      sheet.getRange(r, descC).setValue(description);
      sheet.getRange(r, catC).setValue(category);
      sheet.getRange(r, amtC).setValue(amount);
      sheet.getRange(r, noteC).setValue(note);
      Logger.log(`✅ Запись в строку ${r} (${type})`);
      return true;
    }
  }
  Logger.log("❌ Нет свободных строк для " + type);
  return false;
}

function writeReturnHistory(name, type, paid, remain, originalAmount, returnType, description, recordDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(HISTORY_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(HISTORY_SHEET);
    setupHistorySheet(sheet);
  }
  const MONEY_FMT = '#,##0 "₸"';
  const lastRow = Math.max(sheet.getLastRow(), 1) + 1;
  sheet.getRange(lastRow, 1).setValue(new Date()).setNumberFormat("DD.MM.YYYY HH:mm");
  sheet.getRange(lastRow, 2).setValue(name);
  sheet.getRange(lastRow, 3).setValue(description || "");
  sheet.getRange(lastRow, 4).setValue(type);
  sheet.getRange(lastRow, 5).setValue(returnType);
  sheet.getRange(lastRow, 6).setValue(originalAmount).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 7).setValue(paid).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 8).setValue(remain).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 9).setValue(recordDate || "");
  const bg = lastRow % 2 === 0 ? "#0D1117" : "#161B22";
  const textColor = returnType === "Полностью" ? "#3FB950" : "#E3B341";
  sheet.getRange(lastRow, 1, 1, 9).setBackground(bg).setFontColor("#C9D1D9");
  sheet.getRange(lastRow, 5).setFontColor(textColor).setFontWeight("bold");
}

function setupHistorySheet(sheet) {
  const headers = [
    "📅 Дата возврата", "👤 Имя", "📝 Описание долга",
    "Тип долга", "Статус возврата",
    "💰 Изначальная сумма", "✅ Возвращено", "📋 Остаток",
    "📆 Дата займа"
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length)
    .setBackground("#1C2333")
    .setFontColor("#E3B341")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("center")
    .setBorder(false, false, true, false, false, false, "#E3B341", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  sheet.setColumnWidth(1, 140); sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 200); sheet.setColumnWidth(4, 120);
  sheet.setColumnWidth(5, 130); sheet.setColumnWidth(6, 150);
  sheet.setColumnWidth(7, 130); sheet.setColumnWidth(8, 110);
  sheet.setColumnWidth(9, 130);
  sheet.setFrozenRows(1);
}

// ═══════════════════════════════════════════════════════════════════════════════
// ОБНОВЛЕНИЕ ДОЛГОВ В МЕСЯЧНЫХ ЛИСТАХ
// Использует точные координаты из диагностики
// ═══════════════════════════════════════════════════════════════════════════════
function refreshMonthDebts(sheet, monthName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const journal = ss.getSheetByName(JOURNAL_SHEET);
  if (!journal || !sheet) return;

  // Читаем все данные журнала
  const jData = journal.getRange(J_START, J_TYPE, J_END - J_START + 1, J_NOTE - J_TYPE + 1).getValues();

  const meDebts = [];
  const iDebts  = [];

  jData.forEach(row => {
    const type   = String(row[0] || "").trim(); // C
    const name   = String(row[1] || "").trim(); // D
    const amount = Number(row[3]) || 0;          // F
    const retD   = row[5];                       // H — дата возврата
    const status = String(row[6] || "").trim();  // I

    if (!type || !name || amount <= 0) return;
    if (status === "Возвращён") return;

    // Определить месяц возврата
    let retMonth = "";
    if (retD instanceof Date && !isNaN(retD)) {
      retMonth = MONTHS[retD.getMonth()];
    } else if (typeof retD === "string" && MONTHS.includes(retD.trim())) {
      retMonth = retD.trim(); // совместимость со старым форматом
    }

    if (retMonth !== monthName) return;

    const retStr = retD instanceof Date ? fmt(retD) : String(retD || "");
    const entry  = { name, amount, retStr, status };

    if (type === "Мне должны")      meDebts.push(entry);
    else if (type === "Я должен")   iDebts.push(entry);
  });

  // Заполнить "МНЕ ДОЛЖНЫ" (строки 7-14)
  fillBlock(sheet, DME_DATA_START, DME_DATA_END, meDebts, true);

  // Заполнить "Я ДОЛЖЕН" (строки 19-26)
  fillBlock(sheet, DI_DATA_START, DI_DATA_END, iDebts, false);

  Logger.log(`✅ Долги обновлены в листе ${monthName}: ${meDebts.length} мне, ${iDebts.length} я`);
}

function fillBlock(sheet, startRow, endRow, debts, isIncoming) {
  const CFMT = '#,##0 "₸";-#,##0 "₸";"-"';
  const color = isIncoming ? "#3FB950" : "#F85149";

  for (let i = startRow; i <= endRow; i++) {
    const idx = i - startRow;
    const debt = debts[idx];

    // Имя
    const nameCell = sheet.getRange(i, DEBT_NAME_COL);
    nameCell.setValue(debt ? debt.name : "—");
    nameCell.setFontColor(debt ? "#C9D1D9" : "#8B949E");

    // Сумма
    const amtCell = sheet.getRange(i, DEBT_AMT_COL);
    amtCell.setValue(debt ? debt.amount : 0);
    amtCell.setNumberFormat(CFMT);
    amtCell.setFontColor(debt ? color : "#8B949E");

    // Дата/статус
    const dateCell = sheet.getRange(i, DEBT_DATE_COL);
    if (debt) {
      dateCell.setValue(debt.retStr || "—");
      // Если долг частично погашен — подсветить жёлтым
      if (debt.status === "Частично") {
        sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#2D2A0D");
      } else {
        sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#21262D");
      }
    } else {
      dateCell.setValue("—");
      sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#21262D");
    }
    dateCell.setFontColor("#8B949E");
  }
}

function checkOverdueDebtsAuto() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const journal = ss.getSheetByName(JOURNAL_SHEET);
  if (!journal) return;
  const today = new Date(); today.setHours(0,0,0,0);
  const data = journal.getRange(J_START, J_TYPE, J_END-J_START+1, J_NOTE-J_TYPE+1).getValues();
  data.forEach((row,i) => {
    const status=row[6], retDate=row[5];
    if (status==="Возвращён"||!(retDate instanceof Date)||isNaN(retDate)) return;
    const ret=new Date(retDate); ret.setHours(0,0,0,0);
    if (ret<today) journal.getRange(i+J_START,J_NUM,1,J_NOTE-J_NUM+1).setBackground("#2D1010");
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// ТРИГГЕРЫ
// ═══════════════════════════════════════════════════════════════════════════════
function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("manageSheetVisibility")
    .timeBased().everyDays(1).atHour(0).create();
  ScriptApp.newTrigger("checkOverdueDebtsAuto")
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(9).create();
  ScriptApp.newTrigger("refreshAllMonthDebts")
    .timeBased().everyDays(1).atHour(1).create();
  Logger.log("✅ Триггеры установлены");
}

// ═══════════════════════════════════════════════════════════════════════════════
// УТИЛИТЫ
// ═══════════════════════════════════════════════════════════════════════════════
function readDebtRow(sheet, row) {
  const data = sheet.getRange(row, J_TYPE, 1, J_NOTE - J_TYPE + 1).getValues()[0];
  return {
    type:       String(data[0] || "").trim(),
    name:       String(data[1] || "").trim(),
    desc:       String(data[2] || "").trim(),
    amount:     Number(data[3]) || 0,
    recordDate: data[4],
    returnDate: data[5],
    status:     String(data[6] || "").trim(),
    note:       String(data[7] || "").trim()
  };
}

function monthFromDate(d) {
  if (d instanceof Date && !isNaN(d)) return MONTHS[d.getMonth()];
  return MONTHS[new Date().getMonth()];
}

function findEmptyDebtRow(sheet) {
  const data = sheet.getRange(J_START, J_TYPE, J_END - J_START + 1, 1).getValues();
  for (let i = 0; i < data.length; i++) {
    if (!String(data[i][0]).trim()) return J_START + i;
  }
  return null;
}

function parseDate(str) {
  const p = str.split(".");
  if (p.length !== 3) return null;
  const d = new Date(Number(p[2]), Number(p[1])-1, Number(p[0]));
  return isNaN(d) ? null : d;
}

function fmt(date) {
  if (!date || !(date instanceof Date)) return "";
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "dd.MM.yyyy");
}

function money(amount) {
  if (!amount) return "0 ₸";
  return new Intl.NumberFormat("ru-RU").format(Math.round(amount)) + " ₸";
}


```

---

## 17. main.py — точка входа

```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from bot.config import BOT_TOKEN
from bot.handlers import start, expenses, income, debts, summary, savings, ai_advisor, admin
from bot.services.scheduler import setup_scheduler
from bot.utils.middlewares import AccessMiddleware, LoggingMiddleware

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(AccessMiddleware())

    # Роутеры
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(expenses.router)
    dp.include_router(income.router)
    dp.include_router(debts.router)
    dp.include_router(summary.router)
    dp.include_router(savings.router)
    dp.include_router(ai_advisor.router)

    # Планировщик
    setup_scheduler(bot)

    logger.info("Бот запущен")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 18. Бизнес-правила — список

1. `/start` никогда не создаёт таблицу повторно если пользователь уже зарегистрирован
2. Долг "Мне должны" → автоматически пишет расход категории "Займ" (дал деньги)
3. Долг "Я должен" → автоматически пишет доход категории "Займ" (получил деньги)
4. Возврат долга "Мне должны" → пишет доход (деньги вернулись)
5. Возврат долга "Я должен" → пишет расход (деньги ушли обратно)
6. Частичный возврат → обновляет ТУ ЖЕ строку, не создаёт новую
7. Пополнение цели накоплений → пишет расход категории "Накопления"
8. Категории читаются динамически из таблицы — новые категории появляются автоматически
9. API ключ: null + ai_access=true → ключ администратора; null + ai_access=false → предложить добавить
10. Дата из Google Sheets всегда через parse_iso_date() перед показом пользователю

---

## 19. Незавершённые задачи (добавить в v2)

- [ ] Утренняя сводка с ИИ анализом (APScheduler)
- [ ] Вечерняя сводка с итогами дня
- [ ] Напоминания о просроченных долгах (по понедельникам)
- [ ] /broadcast для администратора
- [ ] Настройка времени сводок через бота
- [ ] Автоматическое создание таблицы при регистрации (drive.py)

---

## 20. Что НЕ делать

- Не использовать старый код finance_bot.py как основу
- Не использовать requests для обращения к таблице (только gspread)
- Не хранить состояния в глобальных переменных (только FSM data)
- Не создавать дублирующие функции в разных модулях
- Не добавлять markdown в ответы ИИ (system prompt запрещает)
- Не игнорировать parse_iso_date() при работе с датами из Sheets

---

*Версия: 2.0 | Апрель 2026*
*Обновлять при изменении архитектуры*
