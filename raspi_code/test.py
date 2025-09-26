import time
import serial

ser = serial.Serial("/dev/ttyUSB0", 115200)

while True:
    # Read lines from serial until there's none left
    while ser.in_waiting:
        line = ser.readline().decode('utf-8').rstrip()
        
        # Process the line if it contains data
        if line:
            try:
                # Split the line by "/" and convert to integers
                values = line.split("/")
                if len(values) == 8:
                    p1_joy_x = int(values[0])      # Player 1 joystick X
                    p1_joy_y = int(values[1])      # Player 1 joystick Y
                    p2_joy_x = int(values[2])      # Player 2 joystick X
                    p2_joy_y = int(values[3])      # Player 2 joystick Y
                    p1_button = int(values[4])     # Player 1 button
                    p2_button = int(values[5])     # Player 2 button
                    p1_switch = int(values[6])     # Player 1 switch
                    p2_switch = int(values[7])     # Player 2 switch
                    
                    # Process the values (example: print them)
                    print(f"P1: Joy({p1_joy_x},{p1_joy_y}) Btn:{p1_button} Sw:{p1_switch}")
                    print(f"P2: Joy({p2_joy_x},{p2_joy_y}) Btn:{p2_button} Sw:{p2_switch}")
                    
            except (ValueError, IndexError) as e:
                print(f"Error parsing line: {line} - {e}")
