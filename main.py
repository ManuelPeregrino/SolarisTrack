import serial
import time
import random
from datetime import datetime, timezone
from pysolar.solar import get_altitude, get_azimuth
import matplotlib.pyplot as plt

# --- Constants ---
LATITUDE = 16.6267
LONGITUDE = -93.1002

POPULATION_SIZE = 10
GENERATIONS = 50
MUTATION_RATE = 0.1
PRUNE_PERCENTAGE = 0.5  # Keep top 50%
SERIAL_PORT = 'COM3'    # Change to match your Arduino port
BAUD_RATE = 9600

# --- Setup Serial ---
def setup_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(0.5)  # Wait for Arduino to reset
    return ser

# --- Get Current Sun Angles ---
def get_sun_angles():
    date_time_utc = datetime.now(timezone.utc)
    elevation_deg = get_altitude(LATITUDE, LONGITUDE, date_time_utc)
    azimuth_deg = get_azimuth(LATITUDE, LONGITUDE, date_time_utc)

    zenith_deg = 90 - elevation_deg
    azimuth_deg = max(0, min(180, azimuth_deg))
    zenith_deg = max(0, min(180, zenith_deg))

    return azimuth_deg, zenith_deg

# --- Individual Fitness Evaluation ---
def fitness(candidate, target_azimuth, target_zenith):
    angle1, angle2 = candidate
    error_azimuth = abs(angle1 - target_azimuth)
    error_zenith = abs(angle2 - target_zenith)
    
    total_error = error_azimuth + error_zenith
    return total_error  # Lower error = better fitness

# --- Create Initial Population ---
def create_population():
    return [(random.randint(0, 180), random.randint(0, 180)) for _ in range(POPULATION_SIZE)]

# --- Selection ---
def select_best(population, target_azimuth, target_zenith):
    graded = [(fitness(ind, target_azimuth, target_zenith), ind) for ind in population]
    graded.sort(key=lambda x: x[0])
    
    survivors = [ind for (_, ind) in graded[:int(POPULATION_SIZE * PRUNE_PERCENTAGE)]]
    best_fitness = graded[0][0]
    
    return survivors, best_fitness

# --- Crossover ---
def crossover(parent1, parent2):
    child1 = (parent1[0], parent2[1])
    child2 = (parent2[0], parent1[1])
    return child1, child2

# --- Mutation ---
def mutate(individual):
    if random.random() < MUTATION_RATE:
        angle_index = random.choice([0, 1])
        mutated = list(individual)
        mutated[angle_index] = random.randint(0, 180)
        return tuple(mutated)
    else:
        return individual

# --- Send to Arduino ---
def send_to_arduino(ser, angles):
    data = f"{angles[0]},{angles[1]}\n"
    ser.write(data.encode('utf-8'))
    print(f"Sent angles to Arduino -> Azimuth: {angles[0]}°, Zenith: {angles[1]}°")

# --- Main Genetic Algorithm Loop ---
def genetic_algorithm():
    ser = setup_serial()

    # Initialize population
    population = create_population()
    fitness_history = []

    for generation in range(GENERATIONS):
        target_azimuth, target_zenith = get_sun_angles()
        print(f"\nGeneration {generation+1}: Sun Azimuth: {target_azimuth:.2f}, Zenith: {target_zenith:.2f}")

        # Selection
        survivors, best_fitness = select_best(population, target_azimuth, target_zenith)
        fitness_history.append(best_fitness)

        # Best individual controls the servos
        best_individual = survivors[0]
        send_to_arduino(ser, best_individual)

        # Reproduce
        children = []
        while len(children) + len(survivors) < POPULATION_SIZE:
            parents = random.sample(survivors, 2)
            child1, child2 = crossover(parents[0], parents[1])
            children.append(mutate(child1))
            if len(children) + len(survivors) < POPULATION_SIZE:
                children.append(mutate(child2))

        population = survivors + children

        time.sleep(5)  # Wait before next generation

    ser.close()
    print("Serial connection closed.")
    plot_fitness(fitness_history)

# --- Plot Fitness Evolution ---
def plot_fitness(fitness_history):
    plt.figure(figsize=(10, 6))
    plt.plot(fitness_history, marker='o')
    plt.title("Genetic Algorithm Fitness Evolution")
    plt.xlabel("Generation")
    plt.ylabel("Fitness (Lower is Better)")
    plt.grid(True)
    plt.show()

# --- Run Program ---
if __name__ == "__main__":
    genetic_algorithm()
