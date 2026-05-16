#include <ContinuousStepper.h>

ContinuousStepper<StepperDriver> stepper;

#define STEP_PIN 2
#define DIR_PIN 5

#define ENABLE_PIN 8

const float steps_per_rev = 800.0 *2;

float current_speed_rad = 0.0;

// ===================== Umrechnung =====================
float radToSteps(float rad_s) {
  return rad_s * (steps_per_rev / (2.0 * PI));
}

// ===================== Setup =====================
void setup() {
  Serial.begin(115200);

  stepper.begin(STEP_PIN, DIR_PIN);

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Motor aktiv

  Serial.println("Bereit. Geschwindigkeit in rad/s eingeben:");
}

// ===================== Loop =====================
void loop() {

  // -------- Serial Input lesen --------
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    float new_speed = input.toFloat();

    // einfache Validierung
    if (!isnan(new_speed)) {
      current_speed_rad = new_speed;

      Serial.print("Neue Geschwindigkeit: ");
      Serial.print(current_speed_rad);
      Serial.println(" rad/s");
    }
  }

  // -------- Motor steuern --------
  stepper.spin(radToSteps(current_speed_rad));
  stepper.loop();
}