# GrovePi DSLink
This DSLink runs on a Raspberry Pi with the GrovePi+ installed, with support for all of the sensors included in the starter kit.

## Getting Started
### Requirements
- Raspberry Pi 2
- GrovePi+
- Raspbian
- Python 2 and virtualenv

### Steps
1. Get the sources: ```wget https://github.com/DexterInd/GrovePi/archive/master.zip```.
2. Unzip the sources: ```unzip master.zip```.
3. Change into scripts directory: ```cd GrovePi-master/Script```.
4. Set permissions to execute: ```sudo chmod +x install.sh```.
5. Run the install script: ```sudo ./install.sh```.
6. If the script asks for permission to install packages, answer: "y".
7. Your Raspberry Pi will reboot.
8. If you are running DGLux under a different user than pi, use: ```sudo usermod -a -G i2c YOUR_USER```, and reboot.
9. Install the DSLink via DGLux or clone the sources and run it manually.

## Supported Sensors
- LED
- RGB LCD
- Buzzer
- Button
- Sound Sensor
- Relay
- Ultrasonic Ranger
- Temperature & Humidity Sensor
- Rotary Angle Sensor
- Light Sensor
