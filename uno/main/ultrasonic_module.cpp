#include "lock_module.h"

void ultrasonicInit() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

// ------------------------------------------------------
// 🔹 초음파 거리 측정 함수 (이제 여기로 이동됨)
// ------------------------------------------------------
float getUltrasonicDistance() {
  long duration;
  float distance;

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH, 2350);
  distance = duration * 0.034 / 2.0;

  if (distance <= 0) return 999;  

Serial.print(distance);
  Serial.println(" cm");
  
  return distance;
}

// ------------------------------------------------------
// 기존 handleUltrasonic는 main에서 1회 감지 로직으로 바뀌었으므로
// 비워두거나 필요 시 로그만 유지
// ------------------------------------------------------
void handleUltrasonic() {
  // main.ino에서 개별 제어하므로 이 함수는 현재 사용되지 않음.
}
