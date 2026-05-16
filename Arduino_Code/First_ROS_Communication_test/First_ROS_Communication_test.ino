// ================= CONFIG =================
#define STEP_PIN_LEFT   13
#define DIR_PIN_LEFT    12
#define STEP_PIN_RIGHT  6
#define DIR_PIN_RIGHT   10

#define TIMEOUT_MS 10000
#define BAUDRATE 115200

// Stepper Parameter
const float steps_per_rev = 200.0 * 16.0; // Beispiel: 1/16 Microstepping

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
unsigned long last_step_time_left = 0;
unsigned long last_step_time_right = 0;

// Ramp factor
const float ramp = 0.1;

// Serial buffer
String input_line = "";

// ================= HELPER =================

float rad_to_steps_per_sec(float rad_s) {
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

  pinMode(STEP_PIN_LEFT, OUTPUT);
  pinMode(DIR_PIN_LEFT, OUTPUT);
  pinMode(STEP_PIN_RIGHT, OUTPUT);
  pinMode(DIR_PIN_RIGHT, OUTPUT);

  stopMotors();
}

// ================= STEP GENERATION =================

void stepMotor(int step_pin, int dir_pin, float speed, unsigned long &last_step_time) {
  if (speed == 0.0) return;

  float steps_per_sec = rad_to_steps_per_sec(speed);
  if (steps_per_sec < 0) {
    digitalWrite(dir_pin, LOW);
    steps_per_sec = -steps_per_sec;
  } else {
    digitalWrite(dir_pin, HIGH);
  }

  unsigned long interval = 1000000.0 / steps_per_sec;

  unsigned long now = micros();
  if (now - last_step_time >= interval) {
    digitalWrite(step_pin, HIGH);
    delayMicroseconds(2);
    digitalWrite(step_pin, LOW);
    last_step_time = now;
  }
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

  // ---------- STEP OUTPUT ----------
  stepMotor(STEP_PIN_LEFT, DIR_PIN_LEFT, current_left, last_step_time_left);
  stepMotor(STEP_PIN_RIGHT, DIR_PIN_RIGHT, current_right, last_step_time_right);
}