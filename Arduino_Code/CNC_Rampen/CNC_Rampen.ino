/*
==========================================================
 HIGH PERFORMANCE ROS STEPPER CONTROLLER
 Arduino UNO + CNC Shield

 FEATURES:
 - Hardwaretimer-basierte Step-Erzeugung
 - Direct Port Manipulation
 - Sehr geringe CPU-Last
 - Sanfte Beschleunigungsrampe
 - SOFORTIGES Bremsen
 - Funktioniert vorwärts + rückwärts
 - Keine externe Stepper-Library nötig

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

const float steps_per_rev = 800.0;

const float gear_ratio = 39.878;

// Timer ISR:
// 100 µs = 10 kHz
const uint32_t TIMER_PERIOD_US = 70;

// Beschleunigungsrampe
// höher = aggressiver
// niedriger = weicher
const float ACCEL_STEP = 100.0;

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

// Ziel-Frequenz
volatile float target_freq_left = 0.0;
volatile float target_freq_right = 0.0;

// Aktuelle Frequenz
volatile float current_freq_left = 0.0;
volatile float current_freq_right = 0.0;

// ISR Intervalle
volatile uint32_t interval_left = 0;
volatile uint32_t interval_right = 0;

// ISR Counter
volatile uint32_t counter_left = 0;
volatile uint32_t counter_right = 0;

// Richtungen
volatile bool dir_left = true;
volatile bool dir_right = true;

unsigned long last_msg_time = 0;
unsigned long last_heartbeat_sent = 0;
unsigned long last_debug_sent = 0;
unsigned long last_ramp_update = 0;

String input_line = "";

bool debug_print = false;

// ================= HELPERS =================

float radToSteps(float rad_s) {
  return rad_s * (steps_per_rev / (2.0 * PI));
}

void sendHeartbeat() {
  Serial.println("HB");
}

void sendReady() {
  Serial.println("READY");
}

void stopMotors() {

  target_speed_left = 0.0;
  target_speed_right = 0.0;

  target_freq_left = 0.0;
  target_freq_right = 0.0;

  current_freq_left = 0.0;
  current_freq_right = 0.0;

  interval_left = 0;
  interval_right = 0;
}

// ================= TARGET UPDATE =================
//
// Wird nur bei neuem CMD aufgerufen
//
void updateTargetSpeeds() {

  // LEFT
  float motor_rad_left =
    target_speed_left * gear_ratio;

  target_freq_left =
    abs(radToSteps(motor_rad_left));

  dir_left = (target_speed_left >= 0.0);

  // RIGHT
  float motor_rad_right =
    target_speed_right * gear_ratio;

  target_freq_right =
    abs(radToSteps(motor_rad_right));

  dir_right = (target_speed_right >= 0.0);
}

// ================= RAMP UPDATE =================
//
// WICHTIG:
//
// - Beschleunigung = weich
// - Bremsen = sofort
// - Richtungswechsel:
//      erst stoppen
//      dann weich anfahren
//
// Dadurch funktioniert
// Vorwärts + Rückwärts korrekt.
//
void updateRamp() {

  // ==================================================
  // LEFT
  // ==================================================

  bool current_dir_left =
    (PORTD & (1 << PD6));

  // ---------- Richtungswechsel ----------
  if (dir_left != current_dir_left &&
      current_freq_left > 0.0) {

    // erst sofort bremsen
    current_freq_left = 0.0;
  }
  else {

    // Richtung setzen
    if (dir_left) {
      PORTD |= (1 << PD6);
    } else {
      PORTD &= ~(1 << PD6);
    }

    // ---------- Beschleunigen ----------
    if (current_freq_left < target_freq_left) {

      current_freq_left += ACCEL_STEP;

      if (current_freq_left > target_freq_left)
        current_freq_left = target_freq_left;
    }
    else {

      // ---------- Bremsen ----------
      current_freq_left = target_freq_left;
    }
  }

  // Interval berechnen
  if (current_freq_left > 0.0) {

    interval_left =
      (1000000UL / current_freq_left)
      / TIMER_PERIOD_US
      / 2UL;

    if (interval_left < 1)
      interval_left = 1;

  } else {

    interval_left = 0;
  }

  // ==================================================
  // RIGHT
  // ==================================================

  bool current_dir_right =
    (PORTD & (1 << PD5));

  // ---------- Richtungswechsel ----------
  if (dir_right != current_dir_right &&
      current_freq_right > 0.0) {

    current_freq_right = 0.0;
  }
  else {

    // Richtung setzen
    if (dir_right) {
      PORTD |= (1 << PD5);
    } else {
      PORTD &= ~(1 << PD5);
    }

    // ---------- Beschleunigen ----------
    if (current_freq_right < target_freq_right) {

      current_freq_right += ACCEL_STEP;

      if (current_freq_right > target_freq_right)
        current_freq_right = target_freq_right;
    }
    else {

      // ---------- Bremsen ----------
      current_freq_right = target_freq_right;
    }
  }

  // Interval berechnen
  if (current_freq_right > 0.0) {

    interval_right =
      (1000000UL / current_freq_right)
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
// Nur ultra schnelle Pulse
//
// KEINE floats
// KEINE divisions
// KEINE digitalWrite
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

      updateTargetSpeeds();

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

      updateTargetSpeeds();
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

  // ---------- RAMP UPDATE ----------
  //
  // 1 kHz Rampenregelung
  //
  if (now - last_ramp_update >= 1) {

    updateRamp();

    last_ramp_update = now;
  }

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

    Serial.print("CurrentFreq L/R: ");
    Serial.print(current_freq_left);
    Serial.print(" / ");
    Serial.println(current_freq_right);

    Serial.print("TargetFreq L/R: ");
    Serial.print(target_freq_left);
    Serial.print(" / ");
    Serial.println(target_freq_right);

    last_debug_sent = now;
  }
}

/*
==========================================================
 RAMPE

 ACCEL_STEP bestimmt:
 wie schnell beschleunigt wird.

 Höher:
   aggressiver

 Niedriger:
   weicher

==========================================================

 VERHALTEN

 Beschleunigen:
   weich

 Bremsen:
   sofort

 Richtungswechsel:
   sofort stoppen
   dann weich neu anfahren

==========================================================

 PERFORMANCE

 ISR:
 10 kHz

 Max Stepfrequenz:
 ~5 kHz stabil

==========================================================

 WICHTIG

 TimerOne Library installieren

==========================================================
*/