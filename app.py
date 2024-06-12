from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Хранение данных
data_storage = {
    "temperature": None,
    "humidity": None
}

# Маршрут для обработки входящих данных от ESP8266
@app.route('/data', methods=['POST'])
def receive_data():
    if request.is_json:
        data = request.get_json()
        temperature = data.get('temperature')
        humidity = data.get('humidity')

        if temperature is not None and humidity is not None:
            data_storage["temperature"] = temperature
            data_storage["humidity"] = humidity
            return jsonify({"status": "success", "message": "Данные получены"}), 200
        else:
            return jsonify({"status": "error", "message": "Неверные данные"}), 400
    else:
        return jsonify({"status": "error", "message": "Запрос должен быть в формате JSON"}), 400

# Маршрут для отображения данных
@app.route('/')
def index():
    return render_template('index.html', temperature=data_storage["temperature"], humidity=data_storage["humidity"])

# Маршрут для получения данных в формате JSON
@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data_storage)

if __name__ == '__main__':
    app.run(debug=True)
