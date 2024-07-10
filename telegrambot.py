from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import re

# Ваш токен Telegram бота
TELEGRAM_BOT_TOKEN = '7345075005:AAHy76MKiXKTU3nXfGmE8NR2n4uOnd1WtpY'

# URL вашего Flask-приложения
FLASK_APP_URL = 'http://localhost:5000'  # Замените на актуальный URL, если требуется


# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Добро пожаловать в умный дом! Вот доступные команды:\n"
        "1. Включи [устройство]\n"
        "2. Выключи [устройство]\n"
        "3. Включи [устройство] через [число] [часов/минут/секунд]\n"
        "4. Выключи [устройство] через [число] [часов/минут/секунд]\n"
        "5. Подогрей до [температура] градусов\n"
        "6. Охлади до [температура] градусов\n"
        "7. Авто\n"
        "8. Авто выключить\n"
        "9. Авто сброс\n"
        "10. Список команд\n"
        "11. Настрой авто\n"
    )


# Команда 1. Включи [устройство]
def turn_on_device(update: Update, context: CallbackContext):
    device = " ".join(context.args)
    response = requests.post(f'{FLASK_APP_URL}/devices/{device}/on')
    if response.status_code == 200:
        update.message.reply_text(f"{device} включено.")
    else:
        update.message.reply_text(f"Не удалось включить {device}.")


# Команда 2. Выключи [устройство]
def turn_off_device(update: Update, context: CallbackContext):
    device = " ".join(context.args)
    response = requests.post(f'{FLASK_APP_URL}/devices/{device}/off')
    if response.status_code == 200:
        update.message.reply_text(f"{device} выключено.")
    else:
        update.message.reply_text(f"Не удалось выключить {device}.")


# Команда 3 и 4. Включи/Выключи [устройство] через [число] [часов/минут/секунд]
def delayed_action(update: Update, context: CallbackContext):
    command = " ".join(context.args)
    match = re.match(r'(Включи|Выключи) (\w+) через (\d+) (часов|минут|секунд)', command)
    if match:
        action, device, time_value, time_unit = match.groups()
        time_seconds = int(time_value) * {'часов': 3600, 'минут': 60, 'секунд': 1}[time_unit]

        def execute_action():
            url = f'{FLASK_APP_URL}/devices/{device}/{"on" if action == "Включи" else "off"}'
            requests.post(url)

        Timer(time_seconds, execute_action).start()
        update.message.reply_text(f"{action} {device} через {time_value} {time_unit}.")
    else:
        update.message.reply_text("Некорректная команда.")


# Команда 5. Подогрей до [температура] градусов
def heat_to(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Пожалуйста, укажите устройство и температуру.")
        return

    device = context.args[0]
    temperature = context.args[1]
    response = requests.post(f'{FLASK_APP_URL}/devices/{device}/heat_to', json={"temperature": temperature})
    if response.status_code == 200:
        update.message.reply_text(f"{device} подогрето до {temperature} градусов.")
    else:
        update.message.reply_text(f"Не удалось подогреть {device} до {temperature} градусов.")


# Команда 6. Охлади до [температура] градусов
def cool_to(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Пожалуйста, укажите устройство и температуру.")
        return

    device = context.args[0]
    temperature = context.args[1]
    response = requests.post(f'{FLASK_APP_URL}/devices/{device}/cool_to', json={"temperature": temperature})
    if response.status_code == 200:
        update.message.reply_text(f"{device} охлаждено до {temperature} градусов.")
    else:
        update.message.reply_text(f"Не удалось охладить {device} до {temperature} градусов.")


# Команда 7. Авто
def auto(update: Update, context: CallbackContext):
    update.message.reply_text("Режим авто включен.")


# Команда 8. Авто выключить
def auto_off(update: Update, context: CallbackContext):
    update.message.reply_text("Режим авто выключен.")


# Команда 9. Авто сброс
def auto_reset(update: Update, context: CallbackContext):
    update.message.reply_text("Настройки авто сброшены.")


# Команда 10. Список команд
def list_commands(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Доступные команды:\n"
        "1. Включи [устройство]\n"
        "2. Выключи [устройство]\n"
        "3. Включи [устройство] через [число] [часов/минут/секунд]\n"
        "4. Выключи [устройство] через [число] [часов/минут/секунд]\n"
        "5. Подогрей до [температура] градусов\n"
        "6. Охлади до [температура] градусов\n"
        "7. Авто\n"
        "8. Авто выключить\n"
        "9. Авто сброс\n"
        "10. Список команд\n"
        "11. Настрой авто\n"
    )


# Команда 11. Настрой авто
def configure_auto(update: Update, context: CallbackContext):
    update.message.reply_text("Настройка авто режима.")


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("turn_on_device", turn_on_device))
    dispatcher.add_handler(CommandHandler("turn_off_device", turn_off_device))
    dispatcher.add_handler(CommandHandler("delayed_action", delayed_action))
    dispatcher.add_handler(CommandHandler("heat_to", heat_to))
    dispatcher.add_handler(CommandHandler("cool_to", cool_to))
    dispatcher.add_handler(CommandHandler("auto", auto))
    dispatcher.add_handler(CommandHandler("auto_off", auto_off))
    dispatcher.add_handler(CommandHandler("auto_reset", auto_reset))
    dispatcher.add_handler(CommandHandler("list_commands", list_commands))
    dispatcher.add_handler(CommandHandler("configure_auto", configure_auto))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
