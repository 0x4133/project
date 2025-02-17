#include <BluetoothSerial.h>
#include <esp_now.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>

// OLED display configuration using U8g2
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

// SD Card chip select pin
#define SD_CS 5

// File for logging data
File logFile;

// Bluetooth Serial instance
BluetoothSerial btSerial;

// Buffer to hold incoming data
uint8_t dataBuffer[250]; // Increased size to accommodate larger data packets

// Define a structure for component information
struct ComponentInfo
{
  String macAddress; // Store last two octets of the component's MAC address
  bool hasGPSLock;   // Indicates whether a valid GPS fix is present
};

// Maximum number of components to track
#define MAX_COMPONENTS 10
ComponentInfo components[MAX_COMPONENTS];
int componentCount = 0;

// Function to find or add a component to the tracking list
int findOrAddComponent(String macAddress)
{
  for (int i = 0; i < componentCount; i++)
  {
    if (components[i].macAddress == macAddress)
    {
      return i;
    }
  }
  // Add new component if there is space
  if (componentCount < MAX_COMPONENTS)
  {
    components[componentCount].macAddress = macAddress;
    components[componentCount].hasGPSLock = false; // Initialize status
    return componentCount++;
  }
  else
  {
    // List is full
    return -1;
  }
}

// Update the OLED display with component statuses
void updateDisplay()
{
  u8g2.clearBuffer(); // Clear display buffer

  u8g2.setFont(u8g2_font_ncenB08_tr); // Choose a readable font
  u8g2.setCursor(0, 10);
  u8g2.print("Components:");

  int y = 20;
  for (int i = 0; i < componentCount; i++)
  {
    if (y > 64 - 10)
      break; // Prevent display overflow

    u8g2.setCursor(0, y);
    u8g2.printf("%s, GPS[%s]", components[i].macAddress.c_str(),
                components[i].hasGPSLock ? "true" : "false");
    y += 10;
  }
  u8g2.sendBuffer(); // Write buffer to the display
}

// Callback function for ESP-NOW data reception from a component
void onComponentDataReceived(const esp_now_recv_info_t *recv_info, const uint8_t *data, int len)
{
  Serial.println("Data received from component");

  // Extract the last two octets of the MAC address for identification
  char macStr[6];
  snprintf(macStr, sizeof(macStr), "%02X:%02X",
           recv_info->src_addr[4], recv_info->src_addr[5]);
  Serial.print("From: ");
  Serial.println(macStr);
  Serial.print("Data length: ");
  Serial.println(len);

  // Prevent buffer overflow
  if (len >= sizeof(dataBuffer))
  {
    Serial.println("Data too large for buffer");
    return;
  }
  memcpy(dataBuffer, data, len);
  dataBuffer[len] = '\0'; // Ensure null-termination

  String receivedData = String((char *)dataBuffer);
  Serial.print("Received Data: ");
  Serial.println(receivedData);

  // Determine if the component has a valid GPS fix by checking for "Lat:" in the message
  bool gpsLock = receivedData.indexOf("Lat:") != -1;

  // Add or update the component's information
  int compIndex = findOrAddComponent(String(macStr));
  Serial.print("Component index: ");
  Serial.println(compIndex);
  if (compIndex >= 0)
  {
    components[compIndex].hasGPSLock = gpsLock;
  }
  else
  {
    Serial.println("Component list is full. Cannot add new component.");
  }

  // Refresh OLED display with new information
  updateDisplay();

  // Log the received data to the SD card
  writeToSDCard("Received Component Data", receivedData);
}

// (Placeholder) Function to scan for nearby Bluetooth devices
void scanBluetoothDevices()
{
  if (!btSerial.hasClient())
  {
    Serial.println("Scanning for Bluetooth devices...");
    // ESP32 does not support full Bluetooth scanning like Wi-Fi,
    // but you may handle connections or use other techniques here.
  }
  else
  {
    Serial.println("A Bluetooth client is connected.");
  }
}

// Write a log entry to the SD card
void writeToSDCard(String testLabel, String data)
{
  String logEntry = testLabel + ", " + data + "\n";

  if (!SD.exists("/log.csv"))
  {
    Serial.println("Log file does not exist, creating new one.");
  }

  logFile = SD.open("/log.csv", FILE_APPEND);
  if (logFile)
  {
    logFile.print(logEntry);
    logFile.flush(); // Ensure data is written immediately
    logFile.close();
    Serial.println("Data saved to SD card.");
  }
  else
  {
    Serial.println("Error opening file for writing.");
  }
}

void setup()
{
  Serial.begin(115200);

  // Initialize Bluetooth for the Main Unit
  if (!btSerial.begin("ESP32_MainUnit"))
  {
    Serial.println("Bluetooth initialization failed!");
    while (1)
      ;
  }
  Serial.println("Bluetooth initialized as Main Unit");

  // Initialize Wi-Fi in station mode (required for ESP-NOW)
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // Disconnect from any network
  delay(100);
  Serial.println("Wi-Fi initialized in station mode");

  // Display the Main Unit's MAC Address
  Serial.print("Main Unit MAC Address: ");
  Serial.println(WiFi.macAddress());

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK)
  {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  Serial.println("ESP-NOW Initialized");

  // Register the callback for receiving data from components
  esp_now_register_recv_cb(onComponentDataReceived);
  Serial.println("ESP-NOW receive callback registered.");

  // Initialize OLED display
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.sendBuffer();
  Serial.println("OLED initialized.");

  // Display an initial message
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 10, "Waiting for Component Data...");
  u8g2.sendBuffer();

  // Initialize SD card
  if (!SD.begin(SD_CS))
  {
    Serial.println("SD card initialization failed!");
    while (1)
      ; // Halt if the SD card fails to initialize
  }
  Serial.println("SD card initialized.");
}

void loop()
{
  // Check for manual SD logging test via the Serial Monitor
  if (Serial.available())
  {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command.equalsIgnoreCase("TEST_SD"))
    {
      writeToSDCard("Manual Test", "Test data written to SD card manually.");
    }
  }

  // Optionally scan for Bluetooth devices
  scanBluetoothDevices();

  delay(1000); // Small delay to avoid flooding the loop
}