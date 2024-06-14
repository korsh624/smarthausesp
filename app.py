from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests

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

        return response

    def update_sensor_data(self, temperature, humidity):
        self.temperature = temperature
        self.humidity = humidity

bot = SmartHomeBot()

def get_weather_yandex():
    api_key = "demo_yandex_weather_api_key_ca6d09349ba0"
    city = "Moscow"
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
