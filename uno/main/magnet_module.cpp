#include "lock_module.h"

void magnetInit() {
  pinMode(MAGNET_PIN, INPUT);
}

bool isMagnetDetected() {
  return (digitalRead(MAGNET_PIN) == LOW);
}
