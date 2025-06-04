# ESP32 GPS & Sensor Network: Main Unit and Component Units

This project demonstrates a wireless network of ESP32 devices communicating via ESP‑NOW. The system is organized into two roles:

- **Main Unit:** Acts as the central hub. It receives data from multiple Component Units, displays a summary on an OLED screen, logs incoming data to an SD card, and supports Bluetooth for additional interactions.
- **Component Units:** Each Component Unit is equipped with a sensor (in this example, a GPS module) that gathers data and transmits it to the Main Unit using ESP‑NOW.

---

## Features

- **ESP‑NOW Communication:** Reliable, low-latency, connectionless communication between ESP32 devices.
- **GPS Data Collection (Component Units):** Uses the [TinyGPS++](https://github.com/mikalhart/TinyGPSPlus) library to parse GPS data and send formatted messages.
- **Centralized Data Handling (Main Unit):**
  - **OLED Display:** Shows a list of Component Units and their GPS status using the [U8g2](https://github.com/olikraus/u8g2) library.
  - **SD Card Logging:** Saves incoming data into a CSV log file for later analysis.
  - **Bluetooth Connectivity:** Provides Bluetooth serial functionality for additional commands and debugging.
- **Dynamic Component Tracking:** The Main Unit tracks up to 10 Component Units by using the last two octets of their MAC addresses for identification.

---

## Hardware Requirements

### For Each Component Unit
- **ESP32 Development Board**
- **GPS Module** (e.g., Neo-6M)
  - **Connections:**
    - **GPS TX** → ESP32 RX (e.g., GPIO16)
    - **GPS RX** → ESP32 TX (e.g., GPIO17)
- Appropriate power supply and wiring.

### For the Main Unit
- **ESP32 Development Board**
- **OLED Display** (SSD1306, 128x64, I2C)
  - **I2C Wiring:** Connect to ESP32 SDA and SCL pins.
- **SD Card Module**
  - **SPI Wiring:** CS is set to GPIO5 by default (update in code if necessary).
- **Bluetooth:** Built into the ESP32.
- Appropriate power supply and wiring.

---

## Software Dependencies

Ensure you have the following libraries installed in your Arduino IDE:

- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [ESP‑NOW](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_now.html) (included with ESP32 core)
- [TinyGPS++](https://github.com/mikalhart/TinyGPSPlus)
- [U8g2](https://github.com/olikraus/u8g2)
- [SD](https://www.arduino.cc/en/Reference/SD)
- [BluetoothSerial](https://github.com/espressif/arduino-esp32)

---

## Setup Instructions

### Component Unit Setup

1. **Install Required Libraries:** Make sure the required libraries (TinyGPS++, ESP‑NOW, WiFi) are installed.
2. **Configuration:**
   - Open the Component Unit sketch.
   - Replace the placeholder `mainUnitMAC` array with the MAC address of your Main Unit.
   - Verify the GPS module’s wiring (using UART1 with pins defined as GPIO16 and GPIO17).
3. **Upload:** Program the ESP32 with the Component Unit sketch.

### Main Unit Setup

1. **Install Required Libraries:** Ensure libraries such as U8g2, SD, BluetoothSerial, ESP‑NOW, and WiFi are installed.
2. **Hardware Connections:**
   - Connect the OLED display via I2C (SDA/SCL).
   - Connect the SD card module via SPI (using GPIO5 for CS by default).
3. **Upload:** Program the ESP32 with the Main Unit sketch.
4. **Operation:**
   - The Main Unit initializes Wi‑Fi (in station mode), sets up ESP‑NOW with a receive callback, and initializes the OLED and SD card.
   - Data received from Component Units is displayed on the OLED and logged to the SD card.
   - Bluetooth is available for further interactions (e.g., issuing a `TEST_SD` command via the serial monitor).

---

## How It Works

### Component Units:
- Continuously read data from the attached GPS module.
- Format a message containing a timestamp, latitude, and longitude.
- Transmit the formatted message every 5 seconds via ESP‑NOW to the Main Unit.

### Main Unit:
- Receives incoming ESP‑NOW packets from various Component Units.
- Extracts a short identifier from the sender’s MAC address (using the last two octets).
- Checks each message for a valid GPS fix (determined by the presence of “Lat:” in the data).
- Updates an OLED display with the list of active Component Units and their GPS status.
- Logs each received message to an SD card in CSV format.
- Provides Bluetooth functionality for debugging and additional commands.

---

## Troubleshooting

- **ESP‑NOW Issues:**
  - Ensure all devices are operating in `WIFI_STA` mode.
  - Double-check that the Main Unit’s MAC address is correctly entered in each Component Unit’s sketch.
  
- **SD Card Errors:**
  - Verify that the SD card module is wired correctly.
  - Ensure the SD card is formatted as FAT32.

- **GPS Data Issues:**
  - Make sure the GPS module has a clear view of the sky to acquire a fix.
  - Confirm the wiring and correct baud rate (set to 9600).

- **OLED Display Problems:**
  - Check the I2C connections (SDA and SCL).
  - Ensure the display’s I2C address matches the default used by U8g2.

---

## Future Enhancements

- **Mobile App Integration:** Implement an app for real-time monitoring and remote control.
- **Enhanced Error Handling:** Add more robust error recovery for network and sensor issues.
- **Expanded Component Support:** Increase the number of Component Units and add support for additional sensors.

---

## License

This project is released under the MIT License.

---

## Acknowledgements

- Thanks to the developers of the ESP32 Arduino Core, TinyGPS++, U8g2, and other libraries used in this project.
- Appreciation to the ESP32 community for ongoing support and inspiration.

---

## NAN Memory System Prototype

This repository also includes a small Python prototype located in `nan.py` and
`nan_cli.py`. The updated version stores all agent memory in a Redis server and
can generate memory items using a local [Ollama](https://ollama.ai) instance.
Run `python3 nan_cli.py` to launch an interactive CLI for experimenting with
agents, their Redis-backed memory stores, and on-demand text generation.
