#!/usr/bin/env python3

import time
import gpiod
from gpiod.line import Direction, Value

GPIO_CHIP = "/dev/gpiochip4"
PIN = 16

request = gpiod.request_lines(
    GPIO_CHIP,
    consumer="lidar_reset",
    config={
        PIN: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.INACTIVE
        )
    }
)

request.set_value(PIN, Value.INACTIVE)
time.sleep(0.6)
request.set_value(PIN, Value.ACTIVE)

time.sleep(0.5)

request.release()

print("[INFO] [lidar_reset] Rebooting Lidars...")
time.sleep(12.0)
print("[INFO] [lidar_reset] Lidar reset complete.")