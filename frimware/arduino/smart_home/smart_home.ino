#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <GPRS_Shield_Arduino.h>
#include <DHT.h>

// Константы для работы с SMS
#define MESSAGE_LENGTH 160
#define SERVER_ADDRESS "http://yourserver.com" // Замените на ваш адрес сервера
#define VERIFICATION_PASSWORD "1234"

// Настройки для GPRS Shield
GPRS gprs(Serial1); // Объект для работы с GPRS модулем

// Параметры для датчика температуры и влажности (DHT22)
#define DHTPIN 12      // Пин, к которому подключен датчик
#define DHTTYPE DHT22  // Тип датчика (DHT11, DHT22, DHT21, AM2301, AM2302, AM2321)
DHT dht(DHTPIN, DHTTYPE); // Объект для работы с датчиком DHT

// Флаги для управления реле
#define RELAY_1_PIN 4
#define RELAY_2_PIN 5
#define RELAY_3_PIN 6
#define RELAY_4_PIN 7
#define RELAY_5_PIN 8
#define RELAY_6_PIN 9
#define RELAY_7_PIN 10
#define RELAY_8_PIN 11
bool relayStates[8] = { false }; // Массив для хранения состояния каждого реле

// Класс для работы с нейронной сетью, используемой для классификации SMS
class NeuralNetwork {
public:
  NeuralNetwork() {}
  // Метод для классификации данных о температуре, влажности и освещенности
  int classify(float temperature, float humidity, float lightLevel) {
    return random(0, 2); // Возвращаем случайное значение 0 или 1 (имитация классификации)
  }
};

void setup() {
  // Инициализация последовательного соединения для отладки
  Serial.begin(9600);
  while (!Serial) {}
  // Инициализация последовательного соединения для GPRS модуля
  Serial1.begin(9600);
  gprs.powerOn(); // Включаем GPRS модуль

  // Пытаемся инициализировать GPRS модуль
  while (!gprs.init()) {
    delay(1000); // Задержка в 1 секунду перед повторной попыткой
  }

  // Настройка пинов для реле как выходы
  pinMode(RELAY_1_PIN, OUTPUT);
  pinMode(RELAY_2_PIN, OUTPUT);
  pinMode(RELAY_3_PIN, OUTPUT);
  pinMode(RELAY_4_PIN, OUTPUT);
  pinMode(RELAY_5_PIN, OUTPUT);
  pinMode(RELAY_6_PIN, OUTPUT);
  pinMode(RELAY_7_PIN, OUTPUT);
  pinMode(RELAY_8_PIN, OUTPUT);

  // Инициализация датчика температуры и влажности
  dht.begin();
  // Отправка SMS о запуске системы
  gprs.sendSMS("+79190173269", "System started");
}

void loop() {
  // Чтение данных с датчика DHT22
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Проверка, что данные с датчика корректные
  if (isnan(temperature) || isnan(humidity)) {
    return; // Если данные некорректны, выходим из функции
  }

  // Создание объекта нейронной сети и классификация текущих данных
  NeuralNetwork neuralNetwork;
  int classification = neuralNetwork.classify(temperature, humidity, 0);

  // Если классификация вернула 1, выполняем управление
  if (classification == 1) {
    controlTemperature(temperature);
    controlLight();
    controlHumidity(humidity);
  }

  // Проверка на наличие новых SMS
  if (gprs.readable()) {
    char message[160], phone[16], datetime[24];
    gprs.readSMS(message, phone, datetime); // Чтение SMS
    String sms = String(message); // Преобразование SMS в строку
    processSMSCommands(sms); // Обработка команды из SMS
  }

  // Отправка данных на сервер
  sendTemperature(temperature);
  sendHumidity(humidity);

  delay(10000); // Задержка в 10 секунд перед следующим циклом
}

// Функция для отправки данных на сервер
void sendToServer(const String& endpoint, float value) {
  String url = SERVER_ADDRESS + endpoint + "?value=" + String(value);

  // Настройка URL для HTTP запроса
  Serial1.println("AT+HTTPPARA=\"URL\",\"" + url + "\"");
  delay(100);

  // Выполнение HTTP запроса
  Serial1.println("AT+HTTPACTION=0");
  delay(3000);

  // Чтение ответа от сервера
  if (Serial1.available()) {
    while (Serial1.available()) {
      char c = Serial1.read();
      Serial.print(c);
    }
  }
}

// Функция для отправки температуры на сервер
void sendTemperature(float temperature) {
  sendToServer("/temperature", temperature);
}

// Функция для отправки влажности на сервер
void sendHumidity(float humidity) {
  sendToServer("/humidity", humidity);
}

// Функция для управления температурой
void controlTemperature(float currentTemperature) {
  if (currentTemperature < 20) {
    digitalWrite(RELAY_1_PIN, HIGH); // Включаем отопление
    relayStates[0] = true;
  } else if (currentTemperature > 25) {
    digitalWrite(RELAY_2_PIN, HIGH); // Включаем кондиционер
    relayStates[1] = true;
  } else {
    digitalWrite(RELAY_1_PIN, LOW); // Выключаем отопление
    digitalWrite(RELAY_2_PIN, LOW); // Выключаем кондиционер
    relayStates[0] = false;
    relayStates[1] = false;
  }
}

// Функция для управления освещением
void controlLight() {
  if (relayStates[0] || relayStates[1]) {
    digitalWrite(RELAY_3_PIN, LOW); // Выключаем свет
    relayStates[2] = false;
  } else {
    digitalWrite(RELAY_3_PIN, HIGH); // Включаем свет
    relayStates[2] = true;
  }
}

// Функция для управления влажностью
void controlHumidity(float currentHumidity) {
  if (currentHumidity < 30) {
    digitalWrite(RELAY_4_PIN, HIGH); // Включаем увлажнитель
    relayStates[3] = true;
  } else {
    digitalWrite(RELAY_4_PIN, LOW); // Выключаем увлажнитель
    relayStates[3] = false;
  }
}

// Функция для обработки команд из SMS
void processSMSCommands(String sms) {
  if (sms.indexOf("/lights_on") != -1) {
    digitalWrite(RELAY_3_PIN, HIGH); // Включаем свет
    relayStates[2] = true;
  } else if (sms.indexOf("/lights_off") != -1) {
    digitalWrite(RELAY_3_PIN, LOW); // Выключаем свет
    relayStates[2] = false;
  }
}

// Функция для верификации пользователя по SMS
void verifyUser(String sms) {
  String delimiter = " ";
  int index = sms.indexOf(delimiter);
  String name = sms.substring(0, index);
  String phoneNumber = sms.substring(index + delimiter.length());

  char message[100];
  sprintf(message, "Verification SMS sent to %s. Please confirm.", phoneNumber.c_str());

  gprs.sendSMS(phoneNumber.c_str(), message); // Отправка SMS с подтверждением верификации
}
