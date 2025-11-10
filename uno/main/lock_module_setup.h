#ifndef LOCK_MODULE_SETUP_H
#define LOCK_MODULE_SETUP_H

#include <Arduino.h>
#include <Keypad.h>
#include <LiquidCrystal.h>
#include <Servo.h>

// ===== LCD =====
extern LiquidCrystal lcd;
void lcdInit();

// ===== Keypad =====
#define ROWS 4
#define COLS 4
extern char keys[ROWS][COLS];
extern byte rowPins[ROWS];
extern byte colPins[COLS];
extern Keypad keypad;
void keypadInit();

// ===== Servo =====
extern Servo motor;
#define MOTOR_PIN 10
void motorInit();

// ===== Magnet Sensor (SEN030600) =====
#define MAGNET_PIN 13
void magnetInit();
bool isMagnetDetected();

// ===== Ultrasonic Sensor (HC-SR04) =====
#define TRIG_PIN A5
#define ECHO_PIN A4
void ultrasonicInit();
float getDistance();
bool isObjectDetected(float range = 30.0);

#endif
