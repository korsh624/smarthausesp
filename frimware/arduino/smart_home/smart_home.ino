#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>  // Для работы с JSON
#include <DHT.h>

const char* ssid = "sweet_home";
const char* password = "gelenvagen94";
const char* devicesUrl = "http://192.168.0.11:5000/device_states";  // URL для получения данных о состоянии устройств

#define DHTPIN 5
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Пины для управления реле
const int lightPin = 12;
const int acPin = 13;
const int heaterPin = 14;
const int humidifierPin = 2;  // Пин для управления увлажнителем

unsigned long lastSendTime = 0;
unsigned long sendInterval = 2000;  // 2 секунды

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  dht.begin();

  // Инициализация пинов для управления реле
  pinMode(lightPin, OUTPUT);
  pinMode(acPin, OUTPUT);
  pinMode(heaterPin, OUTPUT);
  pinMode(humidifierPin, OUTPUT);

  // Изначально выключаем все устройства
  digitalWrite(lightPin, HIGH);        // Свет выключен (HIGH для выключения)
  digitalWrite(acPin, HIGH);           // Кондиционер выключен (HIGH для выключения)
  digitalWrite(heaterPin, HIGH);       // Обогреватель выключен (HIGH для выключения)
  digitalWrite(humidifierPin, HIGH);   // Увлажнитель выключен (HIGH для выключения)
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastSendTime >= sendInterval) {
    lastSendTime = currentMillis;

    // Получаем состояние устройств с сервера
    getDevicesState();

    // Читаем данные с датчика DHT
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Отправляем данные о температуре и влажности на сервер
    sendDataToServer(temperature, humidity);
  }
}

void sendDataToServer(float temperature, float humidity) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;
    String serverUrl = "http://192.168.0.11:5000/home_environment";  // URL сервера Flask для отправки данных
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Формируем JSON данные для отправки
    StaticJsonDocument<200> doc;
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;

    String jsonStr;
    serializeJson(doc, jsonStr);

    int httpResponseCode = http.POST(jsonStr);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(httpResponseCode);
      Serial.println(response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
}

void getDevicesState() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;
    http.begin(client, devicesUrl);  // Используем правильную сигнатуру begin

    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(httpResponseCode);
      Serial.println(response);

      // Обработка ответа от сервера для данных о состоянии устройств
      handleDeviceStateResponse(response);
    } else {
      Serial.print("Error on getting devices state: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
}

void handleDeviceStateResponse(String response) {
  // Обрабатываем ответ от сервера Flask для данных о состоянии устройств
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, response);

  // Пример обработки состояний устройств
  bool lightState = doc["Свет"];
  bool acState = doc["Кондиционер"];
  bool heaterState = doc["Обогреватель"];
  bool humidifierState = doc["Увлажнитель"];

  digitalWrite(lightPin, lightState ? LOW : HIGH);          // Свет
  digitalWrite(acPin, acState ? LOW : HIGH);                // Кондиционер
  digitalWrite(heaterPin, heaterState ? LOW : HIGH);        // Обогреватель
  digitalWrite(humidifierPin, humidifierState ? LOW : HIGH);// Увлажнитель

  Serial.print("Light state: ");
  Serial.println(lightState);
  Serial.print("AC state: ");
  Serial.println(acState);
  Serial.print("Heater state: ");
  Serial.println(heaterState);
  Serial.print("Humidifier state: ");
  Serial.println(humidifierState);
}
