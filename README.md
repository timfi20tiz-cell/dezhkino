# 🌾 Семейное хозяйство «Дежкино»

Цифровая экосистема для локального фермерского хозяйства: адаптивный сайт-витрина в эстетике **Patagonia Activism**, встроенный **Telegram Mini App**, интерактивный **Telegram-бот** для приёма заказов и защищённая **панель управления фермера**.

---

## ✨ Ключевые возможности

1. **Витрина продукции (Web & Mobile):**
   * Премиальный природный дизайн (Craft Earth / Forest palette): небелёный лён, глубокий хвойный, тёплая терракота.
   * Плавные кинематографичные анимации появления (**Scroll Reveal** на `IntersectionObserver`).
   * Полноразмерный кинематографичный Hero-баннер.
   * Удобная корзина с адаптацией под мобильные устройства (Bottom Sheet) и Telegram MainButton.

2. **Telegram Mini App & Бот (`aiogram 3`):**
   * Мгновенный запуск витрины прямо внутри Telegram по кнопке в чате или через MenuButton.
   * Дублирующий текстовый каталог в чате по категориям (Мясо и птица, Яйца, Мёд, Травяной сбор).
   * Оформление заказа в 2 клика с моментальным пуш-уведомлением на телефон владельца хозяйства.

3. **Панель фермера (`admin.html`):**
   * Вход по 4-значному PIN-коду (`3484`).
   * Управление ценами позиций в реальном времени.
   * Высококонтрастные тумблеры наличия («В наличии» / «Закончилось») с мгновенной синхронизацией витрины.

---

## 🛠 Стек технологий

* **Frontend:** Чистый HTML5, CSS3 (Custom Variables, Glassmorphism, Micro-interactions), JavaScript (ES6+, WebApp SDK).
* **Backend:** Python 3 (aiogram 3, asynchronous polling, custom lightweight HTTP API).
* **Хранилище:** JSON Data Store (`data/products.json`).

---

## 📁 Структура проекта

```text
dezhkino/
├── web/                      # Клиентская часть (Витрина + Mini App)
│   ├── index.html            # Главная витрина
│   ├── admin.html            # Панель управления фермера (PIN: 3484)
│   ├── css/
│   │   └── style.css         # Стили в эстетике Patagonia Activism
│   ├── js/
│   │   ├── app.js            # Логика корзины, фильтрация, Scroll Reveal
│   │   └── products.js       # База товаров и категорий
│   └── images/               # Фотографии продукции и баннеры
├── bot/                      # Серверная часть Telegram-бота
│   ├── bot.py                # Обработка команд, WebApp, уведомления о заказах
│   ├── requirements.txt      # Зависимости Python
│   └── .env.example          # Шаблон переменных окружения
├── data/
│   └── products.json         # Актуальные данные товаров
├── server.py                 # Сервер статики и API
├── .gitignore                # Исключение секретов и бинарников
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Запуск веб-витрины и API:
```bash
python server.py
```
Витрина будет доступна по адресу: `http://localhost:8000/`  
Панель фермера: `http://localhost:8000/admin.html` (PIN: `3484`)

### 2. Запуск Telegram-бота:
```bash
cd bot
pip install -r requirements.txt
cp .env.example .env
# Заполните в .env токен бота от @BotFather и ваш ADMIN_CHAT_ID
python bot.py
```

---

## 📄 Лицензия
MIT — разработано для семейного хозяйства «Дежкино», 2026.
