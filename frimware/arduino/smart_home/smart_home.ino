#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <UniversalTelegramBot.h>
#include <WiFiClientSecure.h>

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
const int humidifierPin = 2;   // Пин для управления увлажнителем
const int device1Pin = 0;      // Пин для устройства device_1
const int device2Pin = 15;     // Пин для устройства device_2

unsigned long lastSendTime = 0;
unsigned long sendInterval = 500;  // маленький интервал чтобы устройства включались мгновенно

// Телеграм бот токен
#define BOT_TOKEN "7345075005:AAHy76MKiXKTU3nXfGmE8NR2n4uOnd1WtpY"

WiFiClientSecure client;
UniversalTelegramBot bot(BOT_TOKEN, client);

void handleNewMessages(int numNewMessages);
void handleDeviceStateResponse(String response);

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
  pinMode(device1Pin, OUTPUT);
  pinMode(device2Pin, OUTPUT);

  // Изначально выключаем все устройства
  digitalWrite(lightPin, HIGH);         // Свет выключен (HIGH для выключения)
  digitalWrite(acPin, HIGH);            // Кондиционер выключен (HIGH для выключения)
  digitalWrite(heaterPin, HIGH);        // Обогреватель выключен (HIGH для выключения)
  digitalWrite(humidifierPin, HIGH);    // Увлажнитель выключен (HIGH для выключения)
  digitalWrite(device1Pin, HIGH);       // Device_1 выключен (HIGH для выключения)
  digitalWrite(device2Pin, HIGH);       // Device_2 выключен (HIGH для выключения)
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

  int numNewMessages = bot.getUpdates(bot.last_message_received + 1);
  while (numNewMessages) {
    handleNewMessages(numNewMessages);
    numNewMessages = bot.getUpdates(bot.last_message_received + 1);
  }
}

void sendDataToServer(float temperature, float humidity) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;
    String serverUrl = "http://192.168.0.11:5000/home_environment";  // URL сервера Flask для отправки данных
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Округляем температуру и влажность до десятых
    temperature = round(temperature * 10.0) / 10.0;
    humidity = round(humidity * 10.0) / 10.0;

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
  bool device1State = doc["device_1"];
  bool device2State = doc["device_2"];

  digitalWrite(lightPin, lightState ? LOW : HIGH);          // Свет
  digitalWrite(acPin, acState ? LOW : HIGH);                // Кондиционер
  digitalWrite(heaterPin, heaterState ? LOW : HIGH);        // Обогреватель
  digitalWrite(humidifierPin, humidifierState ? LOW : HIGH);// Увлажнитель
  digitalWrite(device1Pin, device1State ? LOW : HIGH);      // Device_1
  digitalWrite(device2Pin, device2State ? LOW : HIGH);      // Device_2

  Serial.print("Light state: ");
  Serial.println(lightState);
  Serial.print("AC state: ");
  Serial.println(acState);
  Serial.print("Heater state: ");
  Serial.println(heaterState);
  Serial.print("Humidifier state: ");
  Serial.println(humidifierState);
  Serial.print("Device 1 state: ");
  Serial.println(device1State);
  Serial.print("Device 2 state: ");
  Serial.println(device2State);
}

void handleNewMessages(int numNewMessages) {
  for (int i = 0; i < numNewMessages; i++) {
    String chat_id = String(bot.messages[i].chat_id);
    String text = bot.messages[i].text;

    // Проверка и выполнение команд
    if (text == "/light_on") {
      digitalWrite(lightPin, LOW);
      bot.sendMessage(chat_id, "Light is ON", "");
    } else if (text == "/light_off") {
      digitalWrite(lightPin, HIGH);
      bot.sendMessage(chat_id, "Light is OFF", "");
    } else if (text == "/ac_on") {
      digitalWrite(acPin, LOW);
      bot.sendMessage(chat_id, "AC is ON", "");
    } else if (text == "/ac_off") {
      digitalWrite(acPin, HIGH);
      bot.sendMessage(chat_id, "AC is OFF", "");
    } else if (text == "/heater_on") {
      digitalWrite(heaterPin, LOW);
      bot.sendMessage(chat_id, "Heater is ON", "");
    } else if (text == "/heater_off") {
      digitalWrite(heaterPin, HIGH);
      bot.sendMessage(chat_id, "Heater is OFF", "");
    } else if (text == "/humidifier_on") {
      digitalWrite(humidifierPin, LOW);
      bot.sendMessage(chat_id, "Humidifier is ON", "");
    } else if (text == "/humidifier_off") {
      digitalWrite(humidifierPin, HIGH);
      bot.sendMessage(chat_id, "Humidifier is OFF", "");
    } else if (text == "/device1_on") {
      digitalWrite(device1Pin, LOW);
      bot.sendMessage(chat_id, "Device 1 is ON", "");
    } else if (text == "/device1_off") {
      digitalWrite(device1Pin, HIGH);
      bot.sendMessage(chat_id, "Device 1 is OFF", "");
    } else if (text == "/device2_on") {
      digitalWrite(device2Pin, LOW);
      bot.sendMessage(chat_id, "Device 2 is ON", "");
    } else if (text == "/device2_off") {
      digitalWrite(device2Pin, HIGH);
      bot.sendMessage(chat_id, "Device 2 is OFF", "");
    } else {
      bot.sendMessage(chat_id, "Unknown command", "");
    }
  }
}
