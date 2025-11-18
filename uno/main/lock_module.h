#ifndef LOCK_MODULE_H
#define LOCK_MODULE_H

#include <Arduino.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

extern LiquidCrystal_I2C lcd;
void lcdInit();
void showMessage(const String &msg, int delayTime = 1000);
void showPrompt();

#define ROWS 4
#define COLS 4
extern Keypad keypad;
extern String inputCode;
extern const int CODE_LEN;
void keypadInit();
void handleKeypad();

#define relayPin 10
void motorInit();
void openDoor();
void closeDoor();

#define MAGNET_PIN 13
void magnetInit();
bool isMagnetDetected();

#define TRIG_PIN A1
#define ECHO_PIN A0
void ultrasonicInit();
float getUltrasonicDistance();   // ⭐ main → 모듈로 이동한 함수
void handleUltrasonic();

#endif
