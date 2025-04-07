import serial
import time
import random
from datetime import datetime, timezone
from pysolar.solar import get_azimuth

# Your coordinates (example: New York)
LATITUDE = 40.7128
LONGITUDE = -74.0060

# === Configuration ===
SERIAL_PORT = 'COM3'  # Change this to your serial port
BAUD_RATE = 9600
POP_SIZE = 10
GENERATIONS = 20
MUTATION_RATE = 0.1
ANGLE_MIN = 0
ANGLE_MAX = 180

# Vertical tracking config
brightness_threshold_low = 600
brightness_threshold_high = 900
vertical_angle = 90  # Start neutral
vertical_direction = -1  # Start moving left
last_brightness = None
no_improvement_count = 2  # Count of non-improvements before reversing

# === Connect to Arduino ===
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

# === GA Functions ===
def generate_individual():
    return random.randint(ANGLE_MIN, ANGLE_MAX)

def mutate(angle):
    if random.random() < MUTATION_RATE:
        return min(max(angle + random.randint(-10, 10), ANGLE_MIN), ANGLE_MAX)
    return angle

def crossover(a, b):
    # Convert to 8-bit binary
    a_bits = format(a, '08b')
    b_bits = format(b, '08b')

    # Pick random crossover point (not at ends)
    point = random.randint(1, 7)

    # Crossover
    child_bits = a_bits[:point] + b_bits[point:]

    # Convert back to integer
    child = int(child_bits, 2)

    # Clamp to valid range
    return min(max(child, ANGLE_MIN), ANGLE_MAX)


def read_light_level():
    try:
        line = ser.readline().decode().strip()
        return int(line)
    except:
        return 0

def track_vertical_servo(horizontal_angle):
    global vertical_angle, vertical_direction, last_brightness, no_improvement_count

    # Send current position command and get initial brightness
    command = f"{horizontal_angle},{vertical_angle}\n"
    ser.write(command.encode())
    time.sleep(0.3)
    ser.reset_input_buffer()
    current_brightness_before_move = read_light_level()

    print(f"  ↳ Current Brightness: {current_brightness_before_move}, Last: {last_brightness}, Dir: {vertical_direction}, No-improve: {no_improvement_count}")

    # Decision-making based on thresholds
    if current_brightness_before_move >= brightness_threshold_high:
        print("  ↳ Brightness ≥ threshold. Holding position.")
        no_improvement_count = 0
    else:
        # Move servo 1° in current direction
        vertical_angle += vertical_direction
        vertical_angle = max(ANGLE_MIN, min(ANGLE_MAX, vertical_angle))

        # Send new angle to Arduino
        command = f"{horizontal_angle},{vertical_angle}\n"
        ser.write(command.encode())
        time.sleep(0.3)
        ser.reset_input_buffer()
        new_brightness = read_light_level()

        print(f"  ↳ Moved to {vertical_angle}°, New Brightness: {new_brightness}")

        # Check if improved
        if new_brightness > current_brightness_before_move:
            print("  ↳ Brightness improved! Continuing same direction.")
            no_improvement_count = 0
        else:
            no_improvement_count += 1
            print(f"  ↳ No improvement ({no_improvement_count}/10)")

        # Reverse direction if stuck
        if no_improvement_count >= 10:
            vertical_direction *= -1
            no_improvement_count = 0
            print("  ↳ Reversing direction after 10 unsuccessful moves.")

        last_brightness = new_brightness

    return last_brightness, vertical_angle


def evaluate(horizontal_angle):
    global vertical_angle

    # Step 1: Track vertical as before
    brightness, updated_vertical = track_vertical_servo(horizontal_angle)

    # Step 2: Calculate real sun azimuth
    now = datetime.now(timezone.utc)
    sun_azimuth = get_azimuth(LATITUDE, LONGITUDE, now)

    # Normalize azimuth to [0, 180] range for servo
    sun_angle = max(0, min(180, int(sun_azimuth)))

    # Step 3: Calculate how close servo angle is to real sun angle
    fitness = 180 - abs(horizontal_angle - sun_angle)  # higher is better

    print(f"  ☀️ Sun Angle: {sun_angle}, Servo: {horizontal_angle}, Fitness: {fitness}")

    return fitness, updated_vertical

# === Main GA Loop ===
population = [generate_individual() for _ in range(POP_SIZE)]

for generation in range(GENERATIONS):
    print(f"\n🧬 Generation {generation + 1}")
    
    fitness_scores = []
    for angle in population:
        brightness, best_vertical = evaluate(angle)
        fitness_scores.append((angle, best_vertical, brightness))
    
    fitness_scores.sort(key=lambda x: x[2], reverse=True)

    for angle, vert, score in fitness_scores:
        print(f"Angle: {angle}, Vertical: {vert}, Brightness: {score}")
    
    top_half = [x[0] for x in fitness_scores[:POP_SIZE // 2]]
    next_gen = []

    while len(next_gen) < POP_SIZE:
        parents = random.sample(top_half, 2)
        child = mutate(crossover(parents[0], parents[1]))
        next_gen.append(child)

    population = next_gen

# === Final Command ===
best_horizontal, best_vertical, _ = fitness_scores[0]
print(f"\n🏁 Best found position — Horizontal: {best_horizontal}, Vertical: {best_vertical}")
ser.write(f"{best_horizontal},{best_vertical}\n".encode())

ser.close()
