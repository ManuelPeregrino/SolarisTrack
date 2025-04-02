#include <Servo.h>

Servo servo1, servo2;
const int photoResistor = A0;
const int baudRate = 9600;

void setup() {
    Serial.begin(baudRate);
    servo1.attach(9);
    servo2.attach(10);
    
    // Start at zero degrees
    servo1.write(0);
    servo2.write(0);
    delay(2000);
}

void loop() {
    if (Serial.available()) {
        String data = Serial.readStringUntil('\n');
        int commaIndex = data.indexOf(',');
        if (commaIndex > 0) {
            int angle1 = data.substring(0, commaIndex).toInt();
            int angle2 = data.substring(commaIndex + 1).toInt();

            servo1.write(angle1);
            servo2.write(angle2);
            delay(2000); // Allow servo movement

            int luminosity = analogRead(photoResistor);
            Serial.println(luminosity); // Send data back to Python
        }
    }
}
