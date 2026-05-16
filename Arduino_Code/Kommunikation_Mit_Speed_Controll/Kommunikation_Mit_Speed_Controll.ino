#include <ContinuousStepper.h>

// ================= MOTOR =================
ContinuousStepper<StepperDriver> stepper_left;
ContinuousStepper<StepperDriver> stepper_right;

#define STEP_PIN_LEFT   2
#define DIR_PIN_LEFT    5

#define STEP_PIN_RIGHT  3
#define DIR_PIN_RIGHT   6

#define ENABLE_PIN 8

// ================= CONFIG =================
#define TIMEOUT_MS 5000
#define BAUDRATE 115200

const float steps_per_rev = 800.0 *2; //Wegen 2 Wicklungen im Motor and und B, diese Wechseln sich ab, deswegen immer die Doppelte Anzahl an Steps

// ================= STATE =================
enum State {
  DISCONNECTED,
  CONNECTED
};

State state = DISCONNECTED;

// ================= VARIABLES =================
float target_left = 0.0;
float target_right = 0.0;

float current_left = 0.0;
float current_right = 0.0;

unsigned long last_cmd_time = 0;

String input_line = "";

// Ramp
const float ramp = 0.1;

// ================= HELPER =================

float radToSteps(float rad_s) {
  return rad_s * (steps_per_rev / (2.0 * PI));
}

void stopMotors() {
  target_left = 0.0;
  target_right = 0.0;
  current_left = 0.0;
  current_right = 0.0;
}

// ================= SETUP =================
void setup() {
  Serial.begin(BAUDRATE);

  stepper_left.begin(STEP_PIN_LEFT, DIR_PIN_LEFT);
  stepper_right.begin(STEP_PIN_RIGHT, DIR_PIN_RIGHT);

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Motor aktiv

  stopMotors();
}

// ================= PARSER =================

void processLine(String line) {
  line.trim();

  // ---------- HANDSHAKE ----------
  if (state == DISCONNECTED) {
    if (line == "HELLO") {
      Serial.println("READY");
      state = CONNECTED;
      last_cmd_time = millis();
    }
    return;
  }

  // ---------- COMMAND ----------
  if (line.startsWith("CMD,")) {
    int comma1 = line.indexOf(',');
    int comma2 = line.indexOf(',', comma1 + 1);

    if (comma1 < 0 || comma2 < 0) return;

    float v_left = line.substring(comma1 + 1, comma2).toFloat();
    float v_right = line.substring(comma2 + 1).toFloat();

    if (isnan(v_left) || isnan(v_right)) return;

    target_left = v_left;
    target_right = v_right;

    last_cmd_time = millis();
  }
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

  // ---------- TIMEOUT ----------
  if (state == CONNECTED) {
    if (millis() - last_cmd_time > TIMEOUT_MS) {
      stopMotors();
      state = DISCONNECTED;
      Serial.println("ERROR");
    }
  }

  // ---------- RAMP ----------
  current_left += (target_left - current_left) * ramp;
  current_right += (target_right - current_right) * ramp;

  // ---------- MOTOR CONTROL ----------
  stepper_left.spin(radToSteps(current_left));
  stepper_right.spin(radToSteps(current_right));

  stepper_left.loop();
  stepper_right.loop();
}