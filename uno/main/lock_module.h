#ifndef LOCK_MODULE_H
#define LOCK_MODULE_H

#include <Arduino.h>
#include <Keypad.h>
#include <LiquidCrystal.h>
#include <Servo.h>

// ===== LCD =====
extern LiquidCrystal lcd;
void lcdInit();
void showMessage(const String &msg, int delayTime = 1000);
void showPrompt();

// ===== Keypad =====
#define ROWS 4
#define COLS 4
extern Keypad keypad;
extern String inputCode;
extern const int CODE_LEN;
void keypadInit();
void handleKeypad();

// ===== Servo =====
#define relayPin 10
void motorInit();
void openDoor();
void closeDoor();

// ===== Magnet Sensor =====
#define MAGNET_PIN 13
void magnetInit();
bool isMagnetDetected();

// ===== Ultrasonic Sensor =====
#define TRIG_PIN A1
#define ECHO_PIN A0
void ultrasonicInit();
float getDistance();
bool isObjectDetected(float range = 30.0);
void handleUltrasonic();

#endif
