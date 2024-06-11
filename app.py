from flask import Flask, request, render_template
import json, serial.tools.list_ports

app = Flask(__name__)

# Глобальные переменные для хранения данных
temperature = None
humidity = None

@app.route('/data', methods=['POST'])
def data():
    global temperature, humidity
    data = request.json
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return 'Data received', 200

@app.route('/')
def index():
    global temperature, humidity
    return render_template('index.html', temperature=temperature, humidity=humidity)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
def serialportsdata():
    ports = list(serial.tools.list_ports.comports())
    # Выводим информацию о каждом порте
    for port in ports:
        print(f"Порт: {port.device}")
        print(f"Описание: {port.description}")
        print(f"Производитель: {port.manufacturer}\n")
