import serial
import time

# Connect to Arduino (adjust port accordingly)
arduino = serial.Serial('COM3', 9600, timeout=1)  # Make sure the port is correct
time.sleep(2)  # Wait for connection

def map_value(value, in_min, in_max, out_min, out_max):
    """Map input range to output range."""
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

while True:
    try:
        # Read brightness value from Arduino
        arduino.flush()  # Clear the input buffer
        raw_data = arduino.readline().decode().strip()
        
        if raw_data.isdigit():
            light_level = int(raw_data)
            print(f"Light Level: {light_level}")

            # Map brightness to servo angles
            servo_horizontal = map_value(light_level, 0, 1023, 0, 180)
            servo_vertical = map_value(light_level, 0, 1023, 180, 0)  # Inverted

            # Send servo positions to Arduino
            command = f"{servo_horizontal},{servo_vertical}\n"
            arduino.write(command.encode())  # Send data as bytes
            print(f"Sent: {command.strip()}")

        time.sleep(0.5)  # Small delay for stability

    except KeyboardInterrupt:
        print("Exiting...")
        arduino.close()
        break
