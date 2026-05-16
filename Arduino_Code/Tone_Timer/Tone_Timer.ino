#include <ContinuousStepper.h>
#include <ContinuousStepper/Tickers/Tone.hpp>

// ================= STEPPER =================
ContinuousStepper<StepperDriver, ToneTicker> stepper_left;
ContinuousStepper<StepperDriver, ToneTicker> stepper_right;

// ================= CONFIG =================
#define STEP_PIN_LEFT   3
#define DIR_PIN_LEFT    6

#define STEP_PIN_RIGHT  2
#define DIR_PIN_RIGHT   5

#define ENABLE_PIN      8

#define BAUDRATE 115200
#define HEARTBEAT_TIMEOUT 500

// ================= MOTOR CONFIG =================
constexpr float STEPS_PER_REV = 200.0f;// * 2.0f;
constexpr float GEAR_RATIO = 39.878f;

// niedrig halten zum Testen
constexpr float MOTOR_ACC = 50000.0f;

// rad/s -> motor steps/s
inline float radToSteps(const float rad_s)
{
    return rad_s * (STEPS_PER_REV / (2.0f * PI));
}

// ================= STATES =================
enum State
{
    DISCONNECTED,
    WAITING,
    READY,
    ACTIVE,
    ESTOP
};

State state = WAITING;

// ================= VARIABLES =================
float target_speed_left = 0.0f;
float target_speed_right = 0.0f;

unsigned long last_msg_time = 0;
unsigned long last_heartbeat_sent = 0;
unsigned long last_debug_sent = 0;

String input_line;

bool debug_print = false;

// ================= HELPERS =================
inline void stopMotors()
{
    target_speed_left = 0.0f;
    target_speed_right = 0.0f;

    stepper_left.spin(0);
    stepper_right.spin(0);
}

inline void sendHeartbeat()
{
    Serial.println(F("HB"));
}

inline void sendReady()
{
    Serial.println(F("READY"));
}

// ================= CMD PARSER =================
void parseCMD(const String& line)
{
    int comma1 = line.indexOf(',');
    int comma2 = line.indexOf(',', comma1 + 1);

    if (comma1 < 0 || comma2 < 0)
        return;

    const float v_left =
        line.substring(comma1 + 1, comma2).toFloat();

    const float v_right =
        line.substring(comma2 + 1).toFloat();

    target_speed_left = v_left * GEAR_RATIO;
    target_speed_right = -v_right * GEAR_RATIO;
}

// ================= LINE PROCESS =================
void processLine(String& line)
{
    line.trim();

    if (line.length() == 0)
        return;

    last_msg_time = millis();

    // ---------- PING ----------
    if (line == F("PING"))
    {
        sendReady();
        state = READY;
        return;
    }

    // ---------- ESTOP ----------
    if (line == F("ESTOP"))
    {
        state = ESTOP;
        stopMotors();
        return;
    }

    // ---------- RESET ----------
    if (state == ESTOP)
    {
        if (line == F("RESET"))
        {
            state = WAITING;
        }

        return;
    }

    // ---------- CMD ----------
    if (line.startsWith(F("CMD,")))
    {
        parseCMD(line);

        if (state == READY)
            state = ACTIVE;

        return;
    }
}

// ================= SETUP =================
void setup()
{
    Serial.begin(BAUDRATE);

    pinMode(ENABLE_PIN, OUTPUT);
    digitalWrite(ENABLE_PIN, LOW);

    stepper_left.begin(STEP_PIN_LEFT, DIR_PIN_LEFT);
    stepper_right.begin(STEP_PIN_RIGHT, DIR_PIN_RIGHT);

    stepper_left.setAcceleration(MOTOR_ACC);
    stepper_right.setAcceleration(MOTOR_ACC);

    stopMotors();

    input_line.reserve(64);
}

// ================= LOOP =================
void loop()
{
    // ---------- SERIAL ----------
    while (Serial.available())
    {
        char c = Serial.read();

        if (c == '\n')
        {
            processLine(input_line);
            input_line = "";
        }
        else
        {
            input_line += c;
        }
    }

    const unsigned long now = millis();

    // ---------- TIMEOUT ----------
    if ((state == ACTIVE || state == ESTOP) &&
        (now - last_msg_time > HEARTBEAT_TIMEOUT))
    {
        state = WAITING;
        stopMotors();
    }

    // ---------- HEARTBEAT ----------
    if ((state == READY ||
         state == ACTIVE ||
         state == ESTOP) &&
        (now - last_heartbeat_sent > 200))
    {
        sendHeartbeat();
        last_heartbeat_sent = now;
    }

    // ---------- DEBUG ----------
    if (debug_print &&
        (now - last_debug_sent > 1000))
    {
        Serial.print(F("L: "));
        Serial.print(radToSteps(target_speed_left));

        Serial.print(F(" R: "));
        Serial.println(radToSteps(target_speed_right));

        last_debug_sent = now;
    }

    // ---------- MOTOR ----------
    if (state == ACTIVE)
    {
        stepper_left.spin(
            radToSteps(target_speed_left));

        stepper_right.spin(
            radToSteps(target_speed_right));
    }
    else
    {
        stepper_left.spin(0);
        stepper_right.spin(0);
    }
}