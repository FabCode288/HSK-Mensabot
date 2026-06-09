#include <ContinuousStepper.h>
#include <stdint.h>

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

#pragma pack(push,1)

struct Packet
{
    uint8_t header1;
    uint8_t header2;

    uint8_t type;

    int16_t value1;
    int16_t value2;

    uint16_t checksum;
};

static_assert(
    sizeof(Packet) == 9,
    "Packet size invalid");

#pragma pack(pop)

union PacketBuffer
{
    Packet packet;
    uint8_t bytes[sizeof(Packet)];
};

enum PacketType : uint8_t
{
    PKT_PING  = 1,
    PKT_READY = 2,
    PKT_HB    = 3,

    PKT_CMD   = 10,

    PKT_ESTOP = 20,
    PKT_RESET = 21
};

// ================= VARIABLES =================

float target_speed_left = 0.0;
float target_speed_right = 0.0;

unsigned long last_msg_time = 0;
unsigned long last_heartbeat_sent = 0;
unsigned long last_debug_sent = 0;

bool debug_print = false;

PacketBuffer rx_buffer;

size_t rx_index = 0;

// ================= HELPERS =================
void stopMotors() {
  target_speed_left = 0.0;
  target_speed_right = 0.0;
}

uint16_t calculateChecksum(
    const Packet& packet)
{
    return static_cast<uint16_t>(
        packet.type ^
        packet.value1 ^
        packet.value2);
}

void sendPacket(
    uint8_t type,
    int16_t value1 = 0,
    int16_t value2 = 0)
{
    PacketBuffer tx;

    tx.packet.header1 = 0xAA;
    tx.packet.header2 = 0x55;

    tx.packet.type = type;

    tx.packet.value1 = value1;
    tx.packet.value2 = value2;

    tx.packet.checksum =
        calculateChecksum(
            tx.packet);

    Serial.write(
        tx.bytes,
        sizeof(tx.bytes));
}

void sendHeartbeat() {
  sendPacket(PKT_HB);
  }

void sendReady() {
  sendPacket(PKT_READY);
}

// ================= PARSER =================
void processPacket(const Packet& packet)
{
  last_msg_time = millis();

  // ---------- WAITING ----------
  if (packet.type == PKT_PING) {
    sendReady();
    state = READY;
    return;
  }

  // ---------- READY ----------
  if (state == READY) {
    if (packet.type == PKT_ESTOP) {
      state = ESTOP;
      stopMotors();
      return;
    }

    if (packet.type == PKT_CMD) {
      state = ACTIVE;

      // FIXED POINT -> FLOAT
      float v_left = packet.value1 / 100.0f;
      float v_right = packet.value2 / 100.0f;

      // MOTOR COMMANDS
      target_speed_left = v_left * gear_ratio;
      target_speed_right = -1.0f * v_right * gear_ratio;
    }

    return;
  }

  // ---------- ACTIVE ----------
  if (state == ACTIVE) {
    if (packet.type == PKT_ESTOP) {
      state = ESTOP;
      stopMotors();
      return;
    }

    if (packet.type == PKT_CMD) {

      // FIXED POINT -> FLOAT
      float v_left = packet.value1 / 100.0f;
      float v_right = packet.value2 / 100.0f;

      // MOTOR COMMANDS
      target_speed_left = v_left * gear_ratio;
      target_speed_right = -1.0f * v_right * gear_ratio;
    }

    return;
  }

  // ---------- ESTOP ----------
  if (state == ESTOP) {
    if (packet.type == PKT_RESET) {
      state = WAITING;
      return;
    }

    // ESTOP bleibt aktiv
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
      uint8_t byte = Serial.read();

      switch(rx_index)
      {
          case 0:

              if(byte != 0xAA)
                  continue;

              rx_buffer.bytes[rx_index++] = byte;

              break;

          case 1:

              if(byte != 0x55)
              {
                  rx_index = 0;
                  continue;
              }

              rx_buffer.bytes[rx_index++] = byte;

              break;

          default:

              rx_buffer.bytes[rx_index++] = byte;

              if(rx_index >= sizeof(Packet))
              {
                  rx_index = 0;

                  uint16_t checksum =
                      calculateChecksum(
                          rx_buffer.packet);

                  if(checksum ==
                    rx_buffer.packet.checksum)
                  {
                      processPacket(
                          rx_buffer.packet);
                  }
              }

              break;
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
IMPORTANT FUNCTIONS (Overview)

STATE MACHINE:
- WAITING  -> waits for a PING packet
- READY    -> connection established, waits for first CMD packet
- ACTIVE   -> continuously processes CMD packets
- ESTOP    -> blocks all motion, waits for RESET packet

COMMUNICATION PROTOCOL:

Packet Structure:
- Header 1  : 0xAA
- Header 2  : 0x55
- Type      : Packet type identifier
- Value 1   : Data field (e.g. left wheel velocity)
- Value 2   : Data field (e.g. right wheel velocity)
- Checksum  : XOR checksum over type, value1 and value2

Packet Types:

ROS -> Arduino:
- PKT_PING   (1)
- PKT_CMD    (10)
- PKT_ESTOP  (20)
- PKT_RESET  (21)

Arduino -> ROS:
- PKT_READY  (2)
- PKT_HB     (3)

CONNECTION SEQUENCE:
- ROS sends PKT_PING
- Arduino responds with PKT_READY
- First PKT_CMD switches Arduino to ACTIVE state
- Arduino periodically sends PKT_HB while connected

SAFETY:
- Heartbeat timeout -> return to WAITING state
- ESTOP -> immediate motor stop
- Invalid checksum -> packet discarded
- Automatic re-synchronization using packet headers
- No deadlock on communication loss

MOTOR CONTROL:
- Motion commands transmitted as fixed-point int16 values
  (value = velocity * 100)
- Fixed-point values converted back to float on Arduino
- rad/s -> steps/s conversion via radToSteps()
- Motion ramping handled by ROS
- Stepper acceleration handled by ContinuousStepper

==========================================================
*/
