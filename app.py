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
            "Увлажнитель": False,
            "device_1": False,
            "device_2": False
        }
        self.temperature = None
        self.humidity = None
        self.auto_mode = False

    def toggle_device(self, device):
        if device in self.devices:
            self.devices[device] = not self.devices[device]
            self.send_command_to_device(device, self.devices[device])
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
        elif command == "авто":
            response = self.enable_auto_mode()
        elif command == "авто выключить":
            response = self.disable_auto_mode()
        elif command == "список команд":
            response = self.list_commands()
        elif command.startswith("настрой авто"):
            response = self.configure_auto_mode(command)

        return response

    def turn_on_device(self, command):
        for device in self.devices:
            if device.lower() in command:
                self.devices[device] = True
                self.send_command_to_device(device, True)
                return f"{device} включен."
        return "Устройство не найдено."

    def turn_off_device(self, command):
        for device in self.devices:
            if device.lower() in command:
                self.devices[device] = False
                self.send_command_to_device(device, False)
                return f"{device} выключен."
        return "Устройство не найдено."

    def schedule_turn_off(self, command):
        match = re.search(r'выключи (.*?) через (\d+)\s*(час(?:а|ов)?|минут(?:у|ы)?|секунд(?:у|ы)?)', command)
        if match:
            device = match.group(1).strip()
            amount = int(match.group(2))
            unit = match.group(3)

            if unit.startswith("час"):
                total_seconds = amount * 3600
            elif unit.startswith("минут"):
                total_seconds = amount * 60
            else:
                total_seconds = amount

            Timer(total_seconds, self._turn_off_device, [device]).start()
            return f"Выключу {device} через {amount} {unit}."
        return "Неверный формат команды."

    def schedule_turn_on(self, command):
        match = re.search(r'включи (.*?) через (\d+)\s*(час(?:а|ов)?|минут(?:у|ы)?|секунд(?:у|ы)?)', command)
        if match:
            device = match.group(1).strip()
            amount = int(match.group(2))
            unit = match.group(3)

            if unit.startswith("час"):
                total_seconds = amount * 3600
            elif unit.startswith("минут"):
                total_seconds = amount * 60
            else:
                total_seconds = amount

            Timer(total_seconds, self._turn_on_device, [device]).start()
            return f"Включу {device} через {amount} {unit}."
        return "Неверный формат команды."

    def _turn_off_device(self, device):
        if device in self.devices:
            self.devices[device] = False
            self.send_command_to_device(device, False)

    def _turn_on_device(self, device):
        if device in self.devices:
            self.devices[device] = True
            self.send_command_to_device(device, True)

    def set_heater_temperature(self, command):
        match = re.search(r'подогрей до (\d+) градус(?:а|ов)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Обогреватель"] = True
            self.send_command_to_device("Обогреватель", True)
            return f"Подогреваю до {temperature} градусов."
        return "Неверный формат команды."

    def set_ac_temperature(self, command):
        match = re.search(r'охлади до (\d+) градус(?:а|ов)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Кондиционер"] = True
            self.send_command_to_device("Кондиционер", True)
            return f"Охлаждаю до {temperature} градусов."
        return "Неверный формат команды."

    def list_commands(self):
        commands = """
        Доступные команды:
        1. Включи [устройство]
        2. Выключи [устройство]
        3. Включи [устройство] через [число] [часов/минут/секунд]
        4. Выключи [устройство] через [число] [часов/минут/секунд]
        5. Подогрей до [температура] градусов
        6. Охлади до [температура] градусов
        7. Авто
        8. Выключить авто
        9. Список команд
        10. Настрой авто [температура кондиционера] [температура обогревателя] [влажность увлажнителя]
        """
        return commands.strip()

    def configure_auto_mode(self, command):
        match = re.search(r'настрой авто (\d+) (\d+) (\d+)', command)
        if match:
            ac_temp = int(match.group(1))
            heater_temp = int(match.group(2))
            humidifier_humidity = int(match.group(3))
            return f"Авто настройки: Кондиционер {ac_temp}°C, Обогреватель {heater_temp}°C, Увлажнитель {humidifier_humidity}%."
        return "Неверный формат команды."

    def update_sensor_data(self, temperature, humidity):
        self.temperature = temperature
        self.humidity = humidity
        if self.auto_mode:
            self.check_auto_mode_conditions()

    def enable_auto_mode(self):
        self.auto_mode = True
        return "Автоматический режим включен."

    def disable_auto_mode(self):
        self.auto_mode = False
        return "Автоматический режим выключен."

    def check_auto_mode_conditions(self):
        if self.temperature is not None and self.humidity is not None:
            if self.temperature > 25:
                self.devices["Кондиционер"] = True
                self.devices["Обогреватель"] = False
            elif self.temperature < 20:
                self.devices["Кондиционер"] = False
            if self.temperature < 15:
                self.devices["Обогреватель"] = True
            elif self.temperature >= 20:
                self.devices["Обогреватель"] = False
            if self.humidity < 50:
                self.devices["Увлажнитель"] = True
            else:
                self.devices["Увлажнитель"] = False

    def send_command_to_device(self, device, state):
        command = f"{device}:{'ON' if state else 'OFF'}"
        url = f"http://localhost:5000/toggle/{device.lower()}"
        try:
            requests.get(url)
        except requests.exceptions.RequestException as e:
            print(f"Error sending command to device: {e}")

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
