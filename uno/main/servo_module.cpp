#include "lock_module.h"



void motorInit() {
    pinMode(relayPin, OUTPUT);
}

void openDoor() {
    digitalWrite(relayPin, HIGH);
}

void closeDoor() {
    digitalWrite(relayPin, LOW);
}
