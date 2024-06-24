from flask import Flask, render_template, request, jsonify
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
        }

    def toggle_device(self, device):
        if device in self.devices:
            self.devices[device] = not self.devices[device]
            return self.devices[device]
        return None

    def handle_command(self, command):
        command = command.lower().strip()
        response = "Неизвестная команда."

        if command.startswith("включи"):
            response = self.turn_on_device(command)
        elif command.startswith("выключи"):
            response = self.turn_off_device(command)
        elif "выключи через" in command:
            response = self.schedule_turn_off(command)
        elif "включи через" in command:
            response = self.schedule_turn_on(command)
        elif command.startswith("подогрей до"):
            response = self.set_heater_temperature(command)
        elif command.startswith("охлади до"):
            response = self.set_ac_temperature(command)

        return response

    def turn_on_device(self, command):
        for device in self.devices:
            if device.lower() in command:
                self.devices[device] = True
                return f"{device} включен."
        return "Устройство не найдено."

    def turn_off_device(self, command):
        for device in self.devices:
            if device.lower() in command:
                self.devices[device] = False
                return f"{device} выключен."
        return "Устройство не найдено."

    def schedule_turn_off(self, command):
        match = re.search(r'выключи через (\d+)\s*час(?:а|ов|ами)?\s*(\d+)?\s*минут(?:ы|у|а|ой|ут)?\s*(\d+)?\s*секунд(?:ы|у|а|ой|ут)?', command)
        if match:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            Timer(total_seconds, self._turn_off_all_devices).start()
            return f"Выключу устройства через {hours} часов, {minutes} минут, {seconds} секунд."
        return "Неверный формат команды."

    def schedule_turn_on(self, command):
        match = re.search(r'включи через (\d+)\s*час(?:а|ов|ами)?\s*(\d+)?\s*минут(?:ы|у|а|ой|ут)?\s*(\д+)?\s*секунд(?:ы|у|а|ой|ут)?', command)
        if match:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            Timer(total_seconds, self._turn_on_all_devices).start()
            return f"Включу устройства через {hours} часов, {minutes} минут, {seconds} секунд."
        return "Неверный формат команды."

    def set_heater_temperature(self, command):
        match = re.search(r'подогрей до (\д+) градус(?:а|ов|ами)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Обогреватель"] = True
            self.auto_off_conditions["Обогреватель"]["temperature"] = temperature
            return f"Подогреваю до {temperature} градусов."
        return "Неверный формат команды."

    def set_ac_temperature(self, command):
        match = re.search(r'охлади до (\д+) градус(?:а|ов|ами)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Кондиционер"] = True
            self.auto_off_conditions["Кондиционер"]["temperature"] = temperature
            return f"Охлаждаю до {temperature} градусов."
        return "Неверный формат команды."

    def update_sensor_data(self, temperature, humidity):
        self.temperature = temperature
        self.humidity = humidity
        self.check_auto_off_devices()

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
    api_key = "demo_yandex_weather_api_key_ca6d09349ba0"
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
        condition = translate_condition(fact["condition"])
        humidity = fact["humidity"]

        weather = {
            "description": condition,
            "temperature": temperature,
            "humidity": humidity
        }
        return weather

    return None

def translate_condition(condition):
    condition_translation = {
        "clear": "ясно",
        "partly-cloudy": "малооблачно",
        "cloudy": "облачно с прояснениями",
        "overcast": "пасмурно",
        "drizzle": "морось",
        "light-rain": "небольшой дождь",
        "rain": "дождь",
        "moderate-rain": "умеренный дождь",
        "heavy-rain": "сильный дождь",
        "continuous-heavy-rain": "длительный сильный дождь",
        "showers": "ливень",
        "wet-snow": "дождь со снегом",
        "light-snow": "небольшой снег",
        "snow": "снег",
        "snow-showers": "снегопад",
        "hail": "град",
        "thunderstorm": "гроза",
        "thunderstorm-with-rain": "дождь с грозой",
        "thunderstorm-with-hail": "гроза с градом"
    }
    return condition_translation.get(condition, condition)

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
    return jsonify({device: state})

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

@app.route('/device_states', methods=['GET'])
def device_states():
    return jsonify(bot.devices)

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify({"temperature": bot.temperature, "humidity": bot.humidity})

@app.route('/home_environment', methods=['GET', 'POST'])
def home_environment():
    if request.method == 'POST':
        data = request.get_json()
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        bot.update_sensor_data(temperature, humidity)
        return jsonify({"status": "success"}), 200

    weather = get_weather_yandex()
    return render_template('home_environment.html', temperature=bot.temperature, humidity=bot.humidity, weather=weather)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
