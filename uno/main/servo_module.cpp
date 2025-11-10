#include "lock_module.h"

Servo motor;

void motorInit() {
  motor.attach(10);
  motor.write(90);
}

void openDoor() {
  motor.write(0);
}

void closeDoor() {
  motor.write(90);
}
