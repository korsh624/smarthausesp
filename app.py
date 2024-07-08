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
        }
        self.temperature = None
        self.humidity = None
        self.auto_mode = False
        self.auto_settings = {
            "ac_on_temp": None,
            "heater_on_temp": None,
            "humidifier_on_humidity": None,
            "ac_off_temp": None,
            "heater_off_temp": None,
            "humidifier_off_humidity": None
        }
        self.pending_auto_settings = []
        self.current_auto_setting_step = 0

    def toggle_device(self, device):
        if device in self.devices:
            self.devices[device] = not self.devices[device]
            self.send_command_to_device(device, self.devices[device])
            return self.devices[device]
        return None

    def handle_command(self, command):
        command = command.lower().strip()
        response = ["Неизвестная команда."]

        if self.pending_auto_settings:
            response = [self.process_auto_mode_configuration(command)]
        elif command.startswith("включи"):
            response = [self.turn_on_device(command)]
        elif command.startswith("выключи"):
            response = [self.turn_off_device(command)]
        elif "выключи через" in command:
            response = [self.schedule_turn_off(command)]
        elif "включи через" in command:
            response = [self.schedule_turn_on(command)]
        elif command.startswith("подогрей до"):
            response = [self.set_heater_temperature(command)]
        elif command.startswith("охлади до"):
            response = [self.set_ac_temperature(command)]
        elif command == "авто":
            response = [self.enable_auto_mode()]
        elif command == "авто выключить":
            response = [self.disable_auto_mode()]
        elif command == "авто сброс":
            response = [self.reset_auto_mode()]
        elif command == "список команд":
            response = self.list_commands()
        elif command.startswith("настрой авто"):
            response = [self.initiate_auto_mode_configuration()]

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
            return f"{device} будет выключен через {amount} {unit}."
        return "Неверный формат команды."

    def schedule_turn_on(self, command):
        match = re.search(r'включи (.*?) через (\д+)\с*(час(?:а|ов)?|минут(?:у|ы)?|секунд(?:у|ы)?)', command)
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
            return f"{device} будет включен через {amount} {unit}."
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
        match = re.search(r'подогрей до (\д+) градус(?:а|ов)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Обогреватель"] = True
            self.send_command_to_device("Обогреватель", True)
            self.send_temperature_command("heater", temperature)
            return f"Подогреваю до {temperature} градусов."
        return "Неверный формат команды."

    def set_ac_temperature(self, command):
        match = re.search(r'охлади до (\д+) градус(?:а|ов)?', command)
        if match:
            temperature = int(match.group(1))
            self.devices["Кондиционер"] = True
            self.send_command_to_device("Кондиционер", True)
            self.send_temperature_command("ac", temperature)
            return f"Охлаждаю до {temperature} градусов."
        return "Неверный формат команды."

    def list_commands(self):
        commands = [
            "Доступные команды:",
            "1. Включи [устройство]",
            "2. Выключи [устройство]",
            "3. Включи [устройство] через [число] [часов/минут/секунд]",
            "4. Выключи [устройство] через [число] [часов/минут/секунд]",
            "5. Подогрей до [температура] градусов",
            "6. Охлади до [температура] градусов",
            "7. Авто",
            "8. Авто выключить",
            "9. Авто сброс",
            "10. Список команд",
            "11. Настрой авто"
        ]
        return commands

    def initiate_auto_mode_configuration(self):
        self.pending_auto_settings = [
            "Введите температуру включения кондиционера:",
            "Введите температуру включения обогревателя:",
            "Введите влажность включения увлажнителя:",
            "Введите температуру выключения кондиционера:",
            "Введите температуру выключения обогревателя:",
            "Введите влажность выключения увлажнителя:"
        ]
        self.current_auto_setting_step = 0
        return self.pending_auto_settings[self.current_auto_setting_step]

    def process_auto_mode_configuration(self, input_value):
        try:
            value = int(input_value)
        except ValueError:
            return "Пожалуйста, введите число."

        if self.current_auto_setting_step == 0:
            self.auto_settings["ac_on_temp"] = value
        elif self.current_auto_setting_step == 1:
            self.auto_settings["heater_on_temp"] = value
        elif self.current_auto_setting_step == 2:
            self.auto_settings["humidifier_on_humidity"] = value
        elif self.current_auto_setting_step == 3:
            self.auto_settings["ac_off_temp"] = value
        elif self.current_auto_setting_step == 4:
            self.auto_settings["heater_off_temp"] = value
        elif self.current_auto_setting_step == 5:
            self.auto_settings["humidifier_off_humidity"] = value

        self.current_auto_setting_step += 1

        if self.current_auto_setting_step < len(self.pending_auto_settings):
            return self.pending_auto_settings[self.current_auto_setting_step]
        else:
            self.pending_auto_settings = []
            return (f"Автоматический режим настроен: Кондиционер включается при {self.auto_settings['ac_on_temp']}°C и "
                    f"выключается при {self.auto_settings['ac_off_temp']}°C, Обогреватель включается при "
                    f"{self.auto_settings['heater_on_temp']}°C и выключается при {self.auto_settings['heater_off_temp']}°C, "
                    f"Увлажнитель включается при {self.auto_settings['humidifier_on_humidity']}% и выключается при "
                    f"{self.auto_settings['humidifier_off_humidity']}%.")

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

    def reset_auto_mode(self):
        self.auto_settings = {
            "ac_on_temp": 0,
            "heater_on_temp": 0,
            "humidifier_on_humidity": 0,
            "ac_off_temp": 0,
            "heater_off_temp": 0,
            "humidifier_off_humidity": 0
        }
        self.auto_mode = False
        self.devices["Кондиционер"] = False
        self.devices["Обогреватель"] = False
        self.devices["Увлажнитель"] = False
        self.send_command_to_device("Кондиционер", False)
        self.send_command_to_device("Обогреватель", False)
        self.send_command_to_device("Увлажнитель", False)
        return "Автоматический режим сброшен и все устройства выключены."

    def check_auto_mode_conditions(self):
        if self.temperature is not None and self.humidity is not None:
            if self.temperature > self.auto_settings["ac_on_temp"]:
                self.devices["Кондиционер"] = True
                self.send_command_to_device("Кондиционер", True)
            elif self.temperature <= self.auto_settings["ac_off_temp"]:
                self.devices["Кондиционер"] = False
                self.send_command_to_device("Кондиционер", False)

            if self.temperature < self.auto_settings["heater_on_temp"]:
                self.devices["Обогреватель"] = True
                self.send_command_to_device("Обогреватель", True)
            elif self.temperature >= self.auto_settings["heater_off_temp"]:
                self.devices["Обогреватель"] = False
                self.send_command_to_device("Обогреватель", False)

            if self.humidity < self.auto_settings["humidifier_on_humidity"]:
                self.devices["Увлажнитель"] = True
                self.send_command_to_device("Увлажнитель", True)
            elif self.humidity >= self.auto_settings["humidifier_off_humidity"]:
                self.devices["Увлажнитель"] = False
                self.send_command_to_device("Увлажнитель", False)

    def send_command_to_device(self, device, state):
        command = f"{device}:{'ON' if state else 'OFF'}"
        url = f"http://localhost:5000/toggle/{device.lower()}"
        try:
            requests.get(url)
        except requests.exceptions.RequestException as e:
            print(f"Error sending command to device: {e}")

    def send_temperature_command(self, device_type, temperature):
        url = f"http://localhost:5000/{device_type}/set_temperature"
        data = {'temperature': temperature}
        try:
            requests.post(url, json=data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending temperature command to device: {e}")

    def get_device_states(self):
        return self.devices

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
    return render_template('devices.html', devices=bot.devices, temperature=bot.temperature, humidity=bot.humidity,
                           weather=weather)

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
    messages = []
    if request.method == 'POST':
        user_input = request.form['message']
        if user_input.strip():
            user_message = {"sender": "user", "text": user_input}
            messages.append(user_message)
            bot_responses = bot.handle_command(user_input)
            for bot_response in bot_responses:
                bot_message = {"sender": "bot", "text": bot_response}
                messages.append(bot_message)
    return render_template('chat.html', messages=messages, weather=weather)

@app.route('/update_sensor_data', methods=['POST'])
def update_sensor_data():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    bot.update_sensor_data(temperature, humidity)
    return jsonify({"status": "success"}), 200

@app.route('/device_states', methods=['GET'])
def device_states():
    return jsonify(bot.get_device_states())

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
