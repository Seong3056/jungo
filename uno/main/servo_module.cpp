#include "lock_module.h"

Servo motor;

void motorInit() {
    pinMode(relayPin, OUTPUT);
}

void openDoor() {
    digitalWrite(relayPin, HIGH);
}

void closeDoor() {
    digitalWrite(relayPin, LOW);
}
