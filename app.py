from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests
import re
from threading import Timer

app = Flask(__name__)

class SmartHomeBot:
    def __init__(self):
        self.devices = {
            "Свет": False,
            "Кондиционер": False,
            "Обогреватель": False,
            "Телевизор": False,
            "Духовка": False,
            "Холодильник": False,
            "Микроволновка": False,
            "Стиральная машина": False
        }
        self.temperature = None
        self.humidity = None
        self.auto_off_conditions = {
            "Обогреватель": {"temperature": None, "humidity": None},
            "Кондиционер": {"temperature": None, "humidity": None}
        }  # Условия для автоматического выключения устройств

    def toggle_device(self, device):
        if device in self.devices:
            self.devices[device] = not self.devices[device]
            return self.devices[device]
        return None

    def handle_command(self, command):
        command = command.lower().strip()
        response = "Неизвестная команда."

        if command.startswith("включи") or command.startswith("выключи"):
            for device in self.devices:
                if device.lower() in command:
                    state = "включен" if command.startswith("включи") else "выключен"
                    self.devices[device] = command.startswith("включи")
                    response = f"{device} {state}."
                    break
        elif command.startswith("выключи через"):
            match = re.search(r'\bвыключи через (\d+) час(?:а|ов|ами)? (\d+) минут(?:ы|у|а|ой|ут)? (\d+) секунд(?:ы|у|а|ой|ут)?\b', command)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                response = f"Выключу устройства через {hours} часов, {minutes} минут, {seconds} секунд."
                self.schedule_action(total_seconds, self._turn_off_all_devices)
        elif command.startswith("включи через"):
            match = re.search(r'\bвключи через (\d+) час(?:а|ов|ами)? (\d+) минут(?:ы|у|а|ой|ут)? (\d+) секунд(?:ы|у|а|ой|ут)?\b', command)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                response = f"Включу устройства через {hours} часов, {minutes} минут, {seconds} секунд."
                self.schedule_action(total_seconds, self._turn_on_all_devices)
        elif command.startswith("подогрей до"):
            match = re.search(r'\bподогрей до (\d+) градус(?:а|ов|ами)?\b', command)
            if match:
                temperature = int(match.group(1))
                # Добавьте здесь логику для управления обогревателем
                self.devices["Обогреватель"] = True  # Пример
                self.auto_off_conditions["Обогреватель"]["temperature"] = temperature
                response = f"Подогреваю до {temperature} градусов."
        elif command.startswith("охлади до"):
            match = re.search(r'\bохлади до (\d+) градус(?:а|ов|ами)?\b', command)
            if match:
                temperature = int(match.group(1))
                # Добавьте здесь логику для управления кондиционером
                self.devices["Кондиционер"] = True  # Пример
                self.auto_off_conditions["Кондиционер"]["temperature"] = temperature
                response = f"Охлаждаю до {temperature} градусов."

        return response

    def update_sensor_data(self, temperature, humidity):
        self.temperature = temperature
        self.humidity = humidity
        self.check_auto_off_devices()  # Проверка условий авто-выключения устройств

    def schedule_action(self, delay_seconds, action):
        timer = Timer(delay_seconds, action)
        timer.start()

    def _turn_off_all_devices(self):
        for device in self.devices:
            self.devices[device] = False

    def _turn_on_all_devices(self):
        for device in self.devices:
            self.devices[device] = True

    def check_auto_off_devices(self):
        for device, conditions in self.auto_off_conditions.items():
            if conditions["temperature"] is not None and conditions["humidity"] is not None:
                if self.temperature == conditions["temperature"] and self.humidity == conditions["humidity"]:
                    self.devices[device] = False


def get_weather_yandex():
    api_key = "demo_yandex_weather_api_key_ca6d09349ba0"  # Замените на ваш настоящий API ключ
    city = "Vladimir"
    url = f"https://api.weather.yandex.ru/v2/forecast?city={city}&lang=ru_RU&limit=1&hours=false&extra=false"

    headers = {
        "X-Yandex-API-Key": api_key
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        weather_data = response.json()
        fact = weather_data["fact"]
        temperature = fact["temp"]
        condition = fact["condition"]
        humidity = fact["humidity"]

        weather = {
            "description": condition,
            "temperature": temperature,
            "humidity": humidity
        }
        return weather

    return None


bot = SmartHomeBot()


@app.route('/')
def index():
    weather = get_weather_yandex()
    return render_template('index.html', temperature=bot.temperature, humidity=bot.humidity, weather=weather)


@app.route('/devices')
def devices():
    weather = get_weather_yandex()
    return render_template('devices.html', devices=bot.devices, temperature=bot.temperature, humidity=bot.humidity, weather=weather)


@app.route('/toggle/<device>')
def toggle(device):
    state = bot.toggle_device(device)
    return redirect(url_for('devices'))


@app.route('/control', methods=['GET', 'POST'])
def control():
    weather = get_weather_yandex()
    response = None
    if request.method == 'POST':
        user_input = request.form['command']
        if user_input.strip():
            response = bot.handle_command(user_input)
    return render_template('control.html', response=response, weather=weather)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    weather = get_weather_yandex()
    response = None
    if request.method == 'POST':
        user_input = request.form['message']
        if user_input.strip():
            response = bot.handle_command(user_input)
    return render_template('chat.html', response=response, weather=weather)


@app.route('/update_sensor_data', methods=['POST'])
def update_sensor_data():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    bot.update_sensor_data(temperature, humidity)
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True)
