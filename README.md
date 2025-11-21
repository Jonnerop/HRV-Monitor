
# Cardio Pulse PRO

**Cardio Pulse PRO** is a heart rate detection and analysis device developed as a first-year hardware project at Metropolia University of Applied Sciences. It measures heart rate variability (HRV) using photoplethysmography (PPG) and provides insights into stress and recovery levels.

---

## Features

- **Real-Time Monitoring**: Measure heart rate and HRV in real-time.
- **Stress and Recovery Insights**: Analyze autonomic nervous system activity using HRV data.
- **Wi-Fi Connectivity**: Seamlessly integrate with Kubios Cloud for advanced HRV analysis.
- **User-Friendly Interface**: Rotary encoder navigation and OLED display.
- **Data Storage**: Locally store and access measurement history.

---

## Technical Specifications

- **Microcontroller**: Raspberry Pi Pico W
- **Heart Rate Sensor**: Crowtail Pulse Sensor v2.0
- **Display**: SSD1306-compatible OLED (128x64 pixels)
- **Interface**: Rotary encoder with push-button
- **Connectivity**: Wi-Fi for cloud integration and USB for power and data transfer

---

## Components

1. **Raspberry Pi Pico W**
2. **Crowtail Pulse Sensor v2.0**
3. **SSD1306 OLED Display**
4. **Rotary Encoder**
5. **Protoboard with Grove Connectors**
6. **USB-C Cable**

---

## Getting Started

### Prerequisites

- [Thonny IDE](https://thonny.org)
- MicroPython Firmware for Raspberry Pi Pico W

### Setup

1. **Assemble Hardware**:
   - Connect the OLED display and pulse sensor to the Raspberry Pi Pico W using Grove connectors.
   - Connect the device to a power source via USB.

2. **Install Software**:
   - Load the MicroPython firmware onto the Raspberry Pi Pico W.
   - Clone or download the repository.

3. **Configure Wi-Fi**:
   - Edit the `connect_to_wlan.py` file to include your Wi-Fi credentials.
   - Run the script to connect the device to your network.

4. **Run the Application**:
   - Open the main program in Thonny and execute it on the connected Raspberry Pi Pico W.

---

## Usage

1. **Power On**: Connect the device to a power source. A green LED indicates it is active.
2. **Navigate Menu**:
   - Use the rotary encoder to scroll and select options on the OLED display.
3. **Start Measurements**:
   - Select "Start Measurement" to begin. Place your finger on the sensor as instructed.
4. **View Results**:
   - Analyze HR, HRV, stress, and recovery metrics on-screen or via Kubios Cloud integration.
5. **Save History**:
   - Measurement results are saved locally for later access.

---

## Troubleshooting

- **Connectivity Issues**:
  - Ensure Wi-Fi credentials are correct and the network is within range.
- **Inaccurate Readings**:
  - Maintain steady contact with the sensor and minimize movement.
- **Power Issues**:
  - Check USB connections and ensure the power source meets voltage requirements.

---

## Documentation

- [User Manual](./User_Manual.pdf)
- [Project Report](./Project_Report.pdf)

---

## Contributors

- **Ade Aiho**
- **Topias Aho**
- **Jonne Roponen**
