#include <esp_now.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <WiFi.h>

// GPS setup
TinyGPSPlus gps;
HardwareSerial ss(1); // Using UART1 for the GPS module

// Replace with your Main Unit's MAC address
uint8_t mainUnitMAC[] = {0xC8, 0xF0, 0x9E, 0xFD, 0x47, 0x44}; // Update with your Main Unit MAC

// Communication peer information
esp_now_peer_info_t peerInfo;

void setup()
{
  Serial.begin(115200);
  ss.begin(9600, SERIAL_8N1, 16, 17); // Configure GPS RX/TX pins

  // Initialize Wi-Fi for ESP-NOW
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK)
  {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  Serial.println("ESP-NOW Initialized");

  // Set up the Main Unit as the communication peer
  memcpy(peerInfo.peer_addr, mainUnitMAC, 6);
  peerInfo.channel = 0; // Use default channel
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK)
  {
    Serial.println("Failed to add Main Unit as peer");
    return;
  }
  Serial.println("Main Unit added successfully as peer");
}

void loop()
{
  // Parse GPS data
  while (ss.available() > 0)
  {
    gps.encode(ss.read());
  }

  // Send GPS data to the Main Unit
  sendGPSData();
  delay(5000); // Wait 5 seconds between transmissions
}

void sendGPSData()
{
  char data[128]; // Buffer for outgoing message

  if (gps.location.isValid())
  {
    snprintf(data, sizeof(data), "Time:%lu, Lat:%.6f, Lon:%.6f",
             millis(),
             gps.location.lat(), gps.location.lng());
  }
  else
  {
    snprintf(data, sizeof(data), "Time:%lu, Waiting for GPS signal...", millis());
  }

  // Transmit data via ESP-NOW
  esp_err_t result = esp_now_send(mainUnitMAC, (uint8_t *)data, strlen(data));

  if (result == ESP_OK)
  {
    Serial.println("Data sent successfully to Main Unit");
    Serial.println(data);
  }
  else
  {
    Serial.print("Error sending data: ");
    Serial.println(esp_err_to_name(result));
  }
}