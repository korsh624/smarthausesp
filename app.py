from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

# Список для хранения данных о температуре и влажности
temperature_data = []

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/data')
def data():
    # Генерация случайных данных о температуре и влажности    
    # Сохранение данных в список
    temperature_data.append({'temperature': temperature, 'humidity': humidity})
    
    return jsonify(temperature=temperature, humidity=humidity)

@app.route('/all_data')
def all_data():
    global temperature
    if request.method=='GET':
        temperature=temperature_data
        return  render_template('index.html',temperature=temperature)
    else:
        return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)
