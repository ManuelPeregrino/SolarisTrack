import serial
import time
import random
import matplotlib.pyplot as plt
from pysolar.solar import get_altitude, get_azimuth
from datetime import datetime
import pytz
import numpy as np

# --- Genetic Algorithm Parameters ---
POPULATION_SIZE = 10
GENERATIONS = 20
MUTATION_RATE = 0.1
LATITUDE = 16.6267
LONGITUDE = -93.1002
SERIAL_PORT = "COM3"  # Change according to your system
BAUD_RATE = 9600

def int_to_binary_array(value):
    return list(map(int, f"{value:08b}"))  # Convert to 8-bit binary and split into list

def binary_array_to_int(binary_array):
    return int("".join(map(str, binary_array)), 2)

def crossover_binary(parent1, parent2):
    parent1_bin1 = int_to_binary_array(parent1[0])
    parent1_bin2 = int_to_binary_array(parent1[1])
    parent2_bin1 = int_to_binary_array(parent2[0])
    parent2_bin2 = int_to_binary_array(parent2[1])

    point = random.randint(1, 7)  # Random crossover point

    child1_bin1 = parent1_bin1[:point] + parent2_bin1[point:]
    child1_bin2 = parent1_bin2[:point] + parent2_bin2[point:]
    child2_bin1 = parent2_bin1[:point] + parent1_bin1[point:]
    child2_bin2 = parent2_bin2[:point] + parent1_bin2[point:]

    child1_bin1 = mutate_bits(child1_bin1)
    child1_bin2 = mutate_bits(child1_bin2)
    child2_bin1 = mutate_bits(child2_bin1)
    child2_bin2 = mutate_bits(child2_bin2)

    child1 = (binary_array_to_int(child1_bin1), binary_array_to_int(child1_bin2))
    child2 = (binary_array_to_int(child2_bin1), binary_array_to_int(child2_bin2))
    return child1, child2

def mutate_bits(binary_array):
    return [bit if random.random() > MUTATION_RATE else 1 - bit for bit in binary_array]

def get_sun_position():
    now = datetime.now(pytz.utc)
    altitude = get_altitude(LATITUDE, LONGITUDE, now)
    azimuth = get_azimuth(LATITUDE, LONGITUDE, now)
    return max(0, int(azimuth)), max(0, int(altitude))

def evaluate_fitness(angle, luminosity):
    sun_azimuth, sun_altitude = get_sun_position()
    error = abs(sun_azimuth - angle[0]) + abs(sun_altitude - angle[1])
    return 1 / (1 + error + (255 - luminosity))  # Higher luminosity = better fitness

def send_angles_to_arduino(ser, angles):
    command = f"{angles[0]},{angles[1]}\n"
    ser.write(command.encode())
    time.sleep(1)
    return read_luminosity(ser)

def read_luminosity(ser):
    ser.flush()
    try:
        data = ser.readline().decode().strip()
        return int(data) if data.isdigit() else 0
    except:
        return 0

# --- Genetic Algorithm Execution ---
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for connection

# Initialize population
population = [(random.randint(0, 180), random.randint(0, 90)) for _ in range(POPULATION_SIZE)]
luminosity_records = []
fitness_evolution = []

for generation in range(GENERATIONS):
    print(f"Generation {generation + 1}")
    fitness_scores = []
    
    for individual in population:
        luminosity = send_angles_to_arduino(ser, individual)
        fitness = evaluate_fitness(individual, luminosity)
        fitness_scores.append((fitness, individual, luminosity))
    
    fitness_scores.sort(reverse=True, key=lambda x: x[0])  # Sort by fitness
    best_fitness = fitness_scores[0][0]
    fitness_evolution.append(best_fitness)
    luminosity_records.append(fitness_scores[0][2])

    # Selection (keep top half)
    selected = [x[1] for x in fitness_scores[:POPULATION_SIZE // 2]]

    # Crossover + Mutation
    next_generation = []
    while len(next_generation) < POPULATION_SIZE:
        p1, p2 = random.sample(selected, 2)
        c1, c2 = crossover_binary(p1, p2)
        next_generation.extend([c1, c2])
    
    population = next_generation[:POPULATION_SIZE]
    time.sleep(5)

ser.close()

# --- Plot Evolution ---
plt.figure(figsize=(10, 5))
plt.plot(range(1, GENERATIONS + 1), fitness_evolution, marker='o', linestyle='-', label='Fitness')
plt.xlabel('Generation')
plt.ylabel('Fitness Score')
plt.title('Genetic Algorithm Evolution')
plt.legend()
plt.show()
