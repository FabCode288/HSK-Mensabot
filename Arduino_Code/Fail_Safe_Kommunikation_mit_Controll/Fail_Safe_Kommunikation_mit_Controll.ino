#include <ContinuousStepper.h>

ContinuousStepper<StepperDriver> stepper_left;
ContinuousStepper<StepperDriver> stepper_right;

// ================= CONFIG =================
#define STEP_PIN_LEFT 3
#define DIR_PIN_LEFT    6
#define STEP_PIN_RIGHT 2
#define DIR_PIN_RIGHT   5

#define ENABLE_PIN 8

#define BAUDRATE 115200

#define HEARTBEAT_TIMEOUT 500  // ms

// ================= STEPPER =================
const float steps_per_rev = 50.0;
const float gear_ratio = 39.878;
const float motor_acc = 100000.0;

float radToSteps(float rad_s) {
  return rad_s * (steps_per_rev / (2.0 * PI));
}

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

unsigned long last_msg_time = 0;
unsigned long last_heartbeat_sent = 0;
unsigned long last_debug_sent = 0;

String input_line = "";

bool debug_print = false;

// ================= HELPERS =================
void stopMotors() {
  target_speed_left = 0.0;
  target_speed_right = 0.0;
}

void sendHeartbeat() {
  Serial.println("HB");
}

void sendReady() {
  Serial.println("READY");
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
      int comma3 = line.indexOf(',', comma2 + 1);

      // Prüfen ob alle Kommas existieren
      if (comma1 < 0 || comma2 < 0 || comma3 < 0) {
          return;
      }

      // DATEN EXTRAHIEREN

      int v_left_int = line.substring(comma1 + 1, comma2).toInt();
      int v_right_int = line.substring(comma2 + 1, comma3).toInt();
      int received_checksum = line.substring(comma3 + 1).toInt();

      // XOR CHECKSUM BERECHNEN

      String payload = line.substring(0, comma3);

      uint8_t calculated_checksum = 0;

      for (size_t i = 0; i < payload.length(); i++) {
          calculated_checksum ^= (uint8_t)payload[i];
      }

      // CHECKSUM VERGLEICH

      if (calculated_checksum != received_checksum) {
          return;
      }

      // FIXED POINT -> FLOAT

      float v_left = v_left_int / 100.0f;
      float v_right = v_right_int / 100.0f;

      // MOTOR COMMANDS

      target_speed_left = v_left * gear_ratio;
      target_speed_right = -1.0f * v_right * gear_ratio;
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
      int comma3 = line.indexOf(',', comma2 + 1);

      // Prüfen ob alle Kommas existieren
      if (comma1 < 0 || comma2 < 0 || comma3 < 0) {
          return;
      }

      // DATEN EXTRAHIEREN

      int v_left_int = line.substring(comma1 + 1, comma2).toInt();
      int v_right_int = line.substring(comma2 + 1, comma3).toInt();
      int received_checksum = line.substring(comma3 + 1).toInt();

      // XOR CHECKSUM BERECHNEN

      String payload = line.substring(0, comma3);

      uint8_t calculated_checksum = 0;

      for (size_t i = 0; i < payload.length(); i++) {
          calculated_checksum ^= (uint8_t)payload[i];
      }

      // CHECKSUM VERGLEICH

      if (calculated_checksum != received_checksum) {
          return;
      }

      // FIXED POINT -> FLOAT

      float v_left = v_left_int / 100.0f;
      float v_right = v_right_int / 100.0f;

      // MOTOR COMMANDS

      target_speed_left = v_left * gear_ratio;
      target_speed_right = -1.0f * v_right * gear_ratio;
    }

    return;
  }

  // ---------- ESTOP ----------
  if (state == ESTOP) {

    if (line == "RESET") {
      state = WAITING;
      return;
    }

    // ESTOP bleibt sonst aktiv
    return;
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(BAUDRATE);

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);  // Motor aktiv

  stepper_left.begin(STEP_PIN_LEFT, DIR_PIN_LEFT);
  stepper_right.begin(STEP_PIN_RIGHT, DIR_PIN_RIGHT);
  stepper_left.setAcceleration(motor_acc);
  stepper_right.setAcceleration(motor_acc);

  stopMotors();
}

// ================= LOOP =================
void loop() {
  //Serial.print("State: "); //Debug
  //Serial.println(state);
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

  // ---------- HEARTBEAT SEND ----------
  if (now - last_heartbeat_sent > 200 && (state == READY || state == ACTIVE || state == ESTOP)) {
    sendHeartbeat();
    last_heartbeat_sent = now;
  }

  if (now - last_debug_sent > 1000 && debug_print) {
    Serial.print("State: "); //Debug
    Serial.println(state);
    Serial.print("Output: ");
    Serial.print(target_speed_left);
    Serial.print(", ");
    Serial.print(target_speed_right);
    Serial.print(", ");
    Serial.print(radToSteps(target_speed_left));
    Serial.print(", ");
    Serial.println(radToSteps(target_speed_right));
    Serial.print("Beschleunigungswert: ");
    Serial.println(stepper_right.acceleration());


    last_debug_sent = now;
  }

  // ---------- MOTOR CONTROL ----------
  if (state == ACTIVE) {

    stepper_left.spin(radToSteps(target_speed_left));
    stepper_right.spin(radToSteps(target_speed_right));
  } else {
    stepper_left.spin(0);
    stepper_right.spin(0);
  }

  stepper_left.loop();
  stepper_right.loop();
}

/*
==========================================================
WICHTIGE FUNKTIONEN (Kurzüberblick)

STATE MACHINE:
- WAITING  → wartet auf "PING"
- READY    → Verbindung steht, wartet auf erstes CMD
- ACTIVE   → verarbeitet CMD kontinuierlich
- ESTOP    → blockiert alles, wartet auf RESET

KOMMUNIKATION:
- ROS → Arduino:
    "PING"
    "CMD,x,y"
    "ESTOP"
    "RESET"

- Arduino → ROS:
    "READY"
    "HB" (Heartbeat)

SICHERHEIT:
- Timeout → zurück zu WAITING
- ESTOP → sofort Motor Stop
- kein Deadlock bei Verbindungsverlust

MOTOR:
- Rampensteuerung intern deaktiviert, Rampen über ROS
- rad/s → Steps/s Umrechnung

==========================================================
*/
