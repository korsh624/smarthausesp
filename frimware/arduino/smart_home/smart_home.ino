#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

const char* ssid = "sweet_home";
const char* password = "gelenvagen94";
const char* serverUrl = "http://192.168.0.11:5000/home_environment";  // IP-адрес вашего сервера Flask для данных о температуре и влажности
const char* devicesUrl = "http://192.168.0.11:5000/devices";  // IP-адрес вашего сервера Flask для данных о состоянии устройств

#define DHTPIN 5
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Пины для управления реле
const int lightPin = 14;
const int acPin = 0;
const int heaterPin = 4;

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

  // Изначально выключаем все устройства
  digitalWrite(lightPin, HIGH);    // Выключено на LOW, включено на HIGH
  digitalWrite(acPin, HIGH);       // Выключено на LOW, включено на HIGH
  digitalWrite(heaterPin, HIGH);   // Выключено на LOW, включено на HIGH
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastSendTime >= sendInterval) {
    lastSendTime = currentMillis;

    // Читаем данные с датчика DHT
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Отправляем данные о температуре и влажности на сервер serverUrl
    sendDataToServer(temperature, humidity);

    // Получаем состояние устройств с сервера devicesUrl
    getDevicesState();
  }
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

      // Обработка ответа от сервера для данных о температуре и влажности
      // В данном примере эту часть можно оставить пустой, так как обработка не требуется
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
    http.begin(client, devicesUrl);

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
  // Проверяем состояние устройств по русским названиям
  if (response.indexOf("\"Свет\":true") > 0) {
    digitalWrite(lightPin, LOW);   // Включено на LOW
  } else {
    digitalWrite(lightPin, HIGH);  // Выключено на HIGH
  }

  if (response.indexOf("\"Кондиционер\":true") > 0) {
    digitalWrite(acPin, LOW);      // Включено на LOW
  } else {
    digitalWrite(acPin, HIGH);     // Выключено на HIGH
  }

  if (response.indexOf("\"Обогреватель\":true") > 0) {
    digitalWrite(heaterPin, LOW);  // Включено на LOW
  } else {
    digitalWrite(heaterPin, HIGH); // Выключено на HIGH
  }
}
