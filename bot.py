import telebot
import requests
import json
import os

# Токен от BotFather
TOKEN = '7970021661:AAGlBdhyRePnKZDZEZ3IyNN0s0CvLCyeDmA'

# OpenRouter API ключ (ТОЛЬКО из переменной окружения!)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

# Словарь для хранения состояния бота в каждом чате
bot_active = {}

# Словарь для хранения истории сообщений {chat_id: [последние сообщения]}
chat_history = {}

bot = telebot.TeleBot(TOKEN)

# Функция для добавления сообщения в историю
def add_to_history(chat_id, role, content):
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    
    chat_history[chat_id].append({"role": role, "content": content})
    
    # Храним только последние 20 сообщений
    if len(chat_history[chat_id]) > 40:  # 20 пар (user + assistant)
        chat_history[chat_id] = chat_history[chat_id][-40:]

# Функция для получения истории чата
def get_chat_history(chat_id):
    return chat_history.get(chat_id, [])

# Функция для общения с OpenRouter AI
def ask_ai(question, chat_id):
    try:
        # Получаем историю чата
        history = get_chat_history(chat_id)
        
        # Системный промпт - ВСЕГДА отвечать на русском
        system_prompt = {"role": "system", "content": """Ты умный AI-помощник и патриот России! 🇷🇺

ПРАВИЛА:
- ВСЕГДА отвечай ТОЛЬКО на русском языке
- Будь дружелюбным, умным и полезным
- Помогай с кодом, вопросами, задачами
- Когда пишешь код - ОБЯЗАТЕЛЬНО оборачивай его в блоки:
  ```python
  код здесь
  ```
  или ```lua```, ```javascript``` и т.д.
- Будь кратким но информативным
- Используй эмодзи для настроения 😊
- Ты гордишься Россией и русским языком!

Твоя задача - быть максимально полезным помощником!"""}
        
        # Добавляем текущий вопрос
        messages = [system_prompt] + history + [{"role": "user", "content": question}]
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/telegram-bot",
                "X-Title": "Telegram Bot"
            },
            json={
                "model": "allenai/molmo-2-8b:free",
                "messages": messages
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            # Сохраняем в историю
            add_to_history(chat_id, "user", question)
            add_to_history(chat_id, "assistant", answer)
            
            return answer
        else:
            return f"❌ Ошибка AI: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# Простые ответы без AI
def get_simple_answer(text):
    text_lower = text.lower()
    
    if 'привет' in text_lower or 'здравствуй' in text_lower:
        return 'Привет! 👋 Чем могу помочь?'
    elif 'как дела' in text_lower:
        return 'Отлично! А у тебя как? 😊'
    elif 'спасибо' in text_lower:
        return 'Пожалуйста! 😊'
    elif 'пока' in text_lower:
        return 'Пока! Возвращайся! 👋'
    elif 'кто ты' in text_lower or 'что ты' in text_lower:
        return 'Я бот-помощник! Всегда готов помочь! 🤖'
    elif '?' in text:
        return 'Хороший вопрос! 🤔 Постараюсь помочь!'
    else:
        return 'Понял тебя! 👍 Чем ещё помочь?'

bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f'Привет, {message.from_user.first_name}! 👋\nЯ бот, который всегда отвечает!\nПиши что хочешь!')

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    chat_type = message.chat.type
    
    if chat_type in ['group', 'supergroup']:
        bot.reply_to(message, '''
📋 Как использовать в группе:

1️⃣ Напиши "botauto" + твой вопрос
   Пример: botauto как дела?

2️⃣ Или упомяни меня @username
   Пример: @bot_username помоги

Я отвечу с помощью AI! 🤖
        ''')
    else:
        bot.reply_to(message, '''
📋 Команды:
/start - начать
/help - помощь
/info - информация

Просто пиши мне что угодно и я отвечу с помощью AI! 🤖
        ''')

# Команда /info
@bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(message, 'Я бот, который работает 24/7 и отвечает всем! 🤖')

# Ответы на текст
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    text = message.text
    text_lower = text.lower()
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    # Проверяем команду включения/выключения (работает везде)
    if text_lower == 'botauto':
        if chat_id not in bot_active or not bot_active[chat_id]:
            bot_active[chat_id] = True
            # Очищаем историю при включении
            chat_history[chat_id] = []
            bot.reply_to(message, '✅ Готов! Теперь отвечаю на все сообщения.')
        else:
            bot_active[chat_id] = False
            # Очищаем историю при выключении
            chat_history[chat_id] = []
            bot.reply_to(message, '⏸️ Выключен. Напиши "BotAuto" чтобы включить.')
        return
    
    # Проверяем включен ли бот в этом чате (для групп И личек)
    if chat_id not in bot_active or not bot_active[chat_id]:
        return  # Бот выключен - игнорируем
    
    # Бот включен - отвечаем
    bot.send_chat_action(chat_id, 'typing')
    ai_response = ask_ai(text, chat_id)
    
    if chat_type in ['group', 'supergroup']:
        bot.reply_to(message, f'🤖 {ai_response}', parse_mode='Markdown')
    else:
        bot.reply_to(message, ai_response, parse_mode='Markdown')

# Запуск бота
print('Бот запущен и работает!')
bot.infinity_polling()
