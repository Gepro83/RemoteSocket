/*
 * Sketch for controlling a remote control plug and delivering humidity
 * and temperature data via the serial interface
 * This program listens for 2 commands on the serial
 * port:
 *    - '1'   switches the plug on 
 *    - '0'  switches the plug off
 *              
 *  as a conformation for receiving a command it is copied back to serial out  
 *  two times within a second. 
 */

#include <RCSwitch.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>

// Settings for DHT humidity/temperature sensor
#define DHTPIN 7     
#define DHTTYPE DHT22   
// Initialize DHT sensor for normal 16mhz Arduino
DHT dht(DHTPIN, DHTTYPE); 

// Settings for remote plug transmitter 
RCSwitch remotePlug = RCSwitch();
// Tri-state codes for buttons on the plug used in this project
// they were discovered using a different sketch
char on[] = "00000F0FFF0F";
char off[] = "00000F0FFFF0";

// Initialise dht sensor and transmitter
void setup() {
  Serial.begin(9600);
  dht.begin();
  // Transmitter is connected to Arduino Pin #10  
  remotePlug.enableTransmit(10);
  // Set pulse length. (Discovered using a different sketch)
  remotePlug.setPulseLength(317);
  // Set number of transmission repetitions
  remotePlug.setRepeatTransmit(3);
  
}

void loop() {    
  delay(3000);
  // read humidity and temperature and perform sanity check
  float hum = dht.readHumidity();
  float temp = dht.readTemperature();
  if(hum > 100.0 || hum < 10.0 || temp < -15.0 || temp > 90.0) {
    // if a reading makes no sense skip everything
    return;
  }
  //Print temp and humidity values to serial monitor
  Serial.print(hum);
  Serial.print("-");
  Serial.print(temp);
}

// is called when data is available
void serialEvent() {
  char command = (char)Serial.read();
  if(command == '0') {
    remotePlug.sendTriState(off);
  }
  if(command == '1') {
    remotePlug.sendTriState(on);  
  }
}


