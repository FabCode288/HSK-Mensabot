/*
==========================================================
 HIGH PERFORMANCE ROS STEPPER CONTROLLER
 Arduino UNO + CNC Shield

 FEATURES:
 - KEINE Rampen
 - ROS kontrolliert vollständig die Bewegung
 - Hardwaretimer-basierte Step-Erzeugung
 - Direct Port Manipulation
 - Sehr geringe CPU-Last
 - Keine Stepper-Library nötig

 CNC Shield Mapping:
 LEFT:
   STEP -> D3 (PD3)
   DIR  -> D6 (PD6)

 RIGHT:
   STEP -> D2 (PD2)
   DIR  -> D5 (PD5)

==========================================================
*/

#include <TimerOne.h>

// ================= CONFIG =================

#define ENABLE_PIN 8

#define BAUDRATE 115200
#define HEARTBEAT_TIMEOUT 500

// ================= STEPPER =================

// Prüfen!
// 1.8° Motor mit 1/4 Microstepping = 800
const float steps_per_rev = 800.0 * 2;

const float gear_ratio = 39.878;

// Timer ISR Rate
// 100 µs = 10 kHz ISR
const uint32_t TIMER_PERIOD_US = 100;

// ================= STATES =================

enum State {
  DISCONNECTED,
  WAITING,
  READY,
  ACTIVE,
  ESTOP
};

State state = WAITING;

// ================= VARIABLES =================

float target_speed_left = 0.0;
float target_speed_right = 0.0;

// Frequenz in Steps/s
volatile uint32_t step_freq_left = 0;
volatile uint32_t step_freq_right = 0;

// Anzahl ISR-Ticks bis nächster Toggle
volatile uint32_t interval_left = 0;
volatile uint32_t interval_right = 0;

// ISR Counter
volatile uint32_t counter_left = 0;
volatile uint32_t counter_right = 0;

// Step-Ausgangszustand
volatile bool step_state_left = false;
volatile bool step_state_right = false;

unsigned long last_msg_time = 0;
unsigned long last_heartbeat_sent = 0;
unsigned long last_debug_sent = 0;

String input_line = "";

bool debug_print = false;

// ================= HELPERS =================

float radToSteps(float rad_s) {
  return rad_s * (steps_per_rev / (2.0 * PI));
}

void stopMotors() {

  target_speed_left = 0.0;
  target_speed_right = 0.0;

  step_freq_left = 0;
  step_freq_right = 0;

  interval_left = 0;
  interval_right = 0;
}

void sendHeartbeat() {
  Serial.println("HB");
}

void sendReady() {
  Serial.println("READY");
}

// ================= SPEED UPDATE =================

void updateMotorSpeeds() {

  // ==================================================
  // LEFT MOTOR
  // ==================================================

  float motor_rad_left =
    target_speed_left * gear_ratio;

  float steps_left =
    abs(radToSteps(motor_rad_left));

  step_freq_left = (uint32_t)steps_left;

  // DIR
  if (target_speed_left >= 0.0) {
    PORTD |= (1 << PD6);    // D6 HIGH
  } else {
    PORTD &= ~(1 << PD6);   // D6 LOW
  }

  // Interval berechnen
  if (step_freq_left > 0) {

    interval_left =
      (1000000UL / step_freq_left)
      / TIMER_PERIOD_US
      / 2UL;

    if (interval_left < 1)
      interval_left = 1;

  } else {

    interval_left = 0;
  }

  // ==================================================
  // RIGHT MOTOR
  // ==================================================

  float motor_rad_right =
    target_speed_right * gear_ratio;

  float steps_right =
    abs(radToSteps(motor_rad_right));

  step_freq_right = (uint32_t)steps_right;

  // DIR
  if (target_speed_right >= 0.0) {
    PORTD |= (1 << PD5);    // D5 HIGH
  } else {
    PORTD &= ~(1 << PD5);   // D5 LOW
  }

  // Interval berechnen
  if (step_freq_right > 0) {

    interval_right =
      (1000000UL / step_freq_right)
      / TIMER_PERIOD_US
      / 2UL;

    if (interval_right < 1)
      interval_right = 1;

  } else {

    interval_right = 0;
  }
}

// ================= TIMER ISR =================
//
// Läuft mit 10 kHz
//
// KEINE floats
// KEINE digitalWrite
// Nur Counter + Port Toggle
//
// Sehr schnell.
//
void stepperISR() {

  // ==================================================
  // LEFT
  // ==================================================

  if (interval_left > 0) {

    counter_left++;

    if (counter_left >= interval_left) {

      counter_left = 0;

      // D3 toggeln
      PORTD ^= (1 << PD3);
    }
  }

  // ==================================================
  // RIGHT
  // ==================================================

  if (interval_right > 0) {

    counter_right++;

    if (counter_right >= interval_right) {

      counter_right = 0;

      // D2 toggeln
      PORTD ^= (1 << PD2);
    }
  }
}

// ================= PARSER =================

void processLine(String line) {

  line.trim();

  last_msg_time = millis();

  // ---------- WAITING ----------

  if (line == "PING") {

    Serial.println("READY");

    state = READY;
  }

  // ---------- READY ----------

  if (state == READY) {

    if (line == "ESTOP") {

      state = ESTOP;

      stopMotors();

      return;
    }

    if (line.startsWith("CMD,")) {

      int comma1 = line.indexOf(',');
      int comma2 = line.indexOf(',', comma1 + 1);

      if (comma1 < 0 || comma2 < 0)
        return;

      float v_left =
        line.substring(comma1 + 1, comma2).toFloat();

      float v_right =
        line.substring(comma2 + 1).toFloat();

      target_speed_left = v_left;
      target_speed_right = -1 * v_right;

      updateMotorSpeeds();

      state = ACTIVE;

      return;
    }

    return;
  }

  // ---------- ACTIVE ----------

  if (state == ACTIVE) {

    if (line == "ESTOP") {

      state = ESTOP;

      stopMotors();

      return;
    }

    if (line.startsWith("CMD,")) {

      int comma1 = line.indexOf(',');
      int comma2 = line.indexOf(',', comma1 + 1);

      if (comma1 < 0 || comma2 < 0)
        return;

      float v_left =
        line.substring(comma1 + 1, comma2).toFloat();

      float v_right =
        line.substring(comma2 + 1).toFloat();

      target_speed_left = v_left;
      target_speed_right = -1 * v_right;

      updateMotorSpeeds();
    }

    return;
  }

  // ---------- ESTOP ----------

  if (state == ESTOP) {

    if (line == "RESET") {

      state = WAITING;

      return;
    }

    return;
  }
}

// ================= SETUP =================

void setup() {

  Serial.begin(BAUDRATE);

  // STEP + DIR Pins Output
  DDRD |= (1 << PD2);   // D2
  DDRD |= (1 << PD3);   // D3
  DDRD |= (1 << PD5);   // D5
  DDRD |= (1 << PD6);   // D6

  pinMode(ENABLE_PIN, OUTPUT);

  digitalWrite(ENABLE_PIN, LOW);

  stopMotors();

  // Timer starten
  Timer1.initialize(TIMER_PERIOD_US);
  Timer1.attachInterrupt(stepperISR);
}

// ================= LOOP =================

void loop() {

  // ---------- SERIAL READ ----------

  while (Serial.available()) {

    char c = Serial.read();

    if (c == '\n') {

      processLine(input_line);

      input_line = "";

    } else {

      input_line += c;
    }
  }

  unsigned long now = millis();

  // ---------- TIMEOUT ----------

  if (state == ACTIVE || state == ESTOP) {

    if (now - last_msg_time > HEARTBEAT_TIMEOUT) {

      state = WAITING;

      stopMotors();
    }
  }

  // ---------- HEARTBEAT ----------

  if (now - last_heartbeat_sent > 200 &&
      (state == READY ||
       state == ACTIVE ||
       state == ESTOP)) {

    sendHeartbeat();

    last_heartbeat_sent = now;
  }

  // ---------- DEBUG ----------

  if (now - last_debug_sent > 1000 &&
      debug_print) {

    Serial.print("State: ");
    Serial.println(state);

    Serial.print("StepFreq L/R: ");
    Serial.print(step_freq_left);
    Serial.print(" / ");
    Serial.println(step_freq_right);

    Serial.print("Interval L/R: ");
    Serial.print(interval_left);
    Serial.print(" / ");
    Serial.println(interval_right);

    last_debug_sent = now;
  }
}

/*
==========================================================
 PERFORMANCE NOTES

 100 µs Timer:
 -> 10 kHz ISR

 Max stabile Frequenz:
 ~5-15 kSteps/s pro Motor
 abhängig von Serial-Last.

==========================================================

 WICHTIG

 Library installieren:

 TimerOne

==========================================================

 MICROSTEPPING PRÜFEN

 steps_per_rev muss stimmen.

 Beispiele:

 Vollschritt:
 200

 1/2:
 400

 1/4:
 800

 1/8:
 1600

==========================================================

 WICHTIGER HINWEIS

 Der STEP-Pin wird getoggelt.

 Deshalb:

 Max Stepfrequenz ≈ ISR_Frequenz / 2

==========================================================
*/