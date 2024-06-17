#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

const char* ssid = "sweet_home";
const char* password = "gelendvagen94";
const char* serverUrl = "http://127.0.0.1:5000/";  // замените на IP-адрес вашего сервера Flask

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Пины для управления устройствами
const int lightPin = 12;
const int acPin = 13;
const int heaterPin = 14;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  dht.begin();

  // Инициализация пинов для управления устройствами
  pinMode(lightPin, OUTPUT);
  pinMode(acPin, OUTPUT);
  pinMode(heaterPin, OUTPUT);

  // Изначально выключаем все устройства
  digitalWrite(lightPin, LOW);
  digitalWrite(acPin, LOW);
  digitalWrite(heaterPin, LOW);

  // Пример запланированных действий
  scheduleTurnOnDevice("Свет", 10);  // Включить свет через 10 секунд
  scheduleTurnOffDevice("Обогреватель", 20);  // Выключить обогреватель через 20 секунд
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  sendDataToServer(temperature, humidity);
  delay(1);  // Измерения каждые 60 секунд
  handleServerResponse;
  turnOnDevice;
  turnOffDevice;
  scheduleTurnOnDevice;
  scheduleTurnOffDevice;
}

void sendDataToServer(float temperature, float humidity) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    String postData = "{\"temperature\":" + String(temperature) + ",\"humidity\":" + String(humidity) + "}";
    int httpResponseCode = http.POST(postData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(httpResponseCode);
      Serial.println(response);

      handleServerResponse(response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
}

void handleServerResponse(String response) {
  // Обрабатываем ответ от сервера Flask
  if (response.indexOf("\"Свет\":true") > 0) {
    digitalWrite(lightPin, HIGH);
  } else {
    digitalWrite(lightPin, LOW);
  }

  if (response.indexOf("\"Кондиционер\":true") > 0) {
    digitalWrite(acPin, HIGH);
  } else {
    digitalWrite(acPin, LOW);
  }

  if (response.indexOf("\"Обогреватель\":true") > 0) {
    digitalWrite(heaterPin, HIGH);
  } else {
    digitalWrite(heaterPin, LOW);
  }
}

void turnOnDevice(String device) {
  // Включение устройства по имени
  if (device == "Свет") {
    digitalWrite(lightPin, HIGH);
  } else if (device == "Кондиционер") {
    digitalWrite(acPin, HIGH);
  } else if (device == "Обогреватель") {
    digitalWrite(heaterPin, HIGH);
  }
}

void turnOffDevice(String device) {
  // Выключение устройства по имени
  if (device == "Свет") {
    digitalWrite(lightPin, LOW);
  } else if (device == "Кондиционер") {
    digitalWrite(acPin, LOW);
  } else if (device == "Обогреватель") {
    digitalWrite(heaterPin, LOW);
  }
}

void scheduleTurnOnDevice(String device, unsigned long delaySeconds) {
  // Запланированное включение устройства через delaySeconds секунд
  delay(delaySeconds * 1000);
  turnOnDevice(device);
}

void scheduleTurnOffDevice(String device, unsigned long delaySeconds) {
  // Запланированное выключение устройства через delaySeconds секунд
  delay(delaySeconds * 1000);
  turnOffDevice(device);
}
