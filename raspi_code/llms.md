# Notes to LLMs

You are writing code for a physical embedded system. The embedded system is running on a Raspberry Pi Zero 2 W, connected via USB to an ESP32, which reads sensor data and sends it using serial to the Raspberry Pi.

The device looks like a mini arcade cabinet, where two players sit facing each other, with the device in the middle. Each player has a joystick (X and Y axis), a momentary push button, and a toggle switch. There is a screen in the middle of the arcade cabinet which both players will look at; this means it's important to make sure any graphics are orientation-agnostic (so it's not upside down for one player).

The ESP32 communicates to the Raspberry Pi via serial. It sends numbers (which are ASCII strings and need to be parsed to ints). These numbers are slash-deliminated like so:

```
2048/2048/2048/2048/1/1/0/0
```
Each number represents:

1. Player 2 joystick Y (NOTE: this is inoperative, so your program must not use this input)
2. Player 2 joystick X
3. Player 1 joystick Y (NOTE: this is inoperative, so your program must not use this input)
4. Player 1 joystick X
5. Player 1 button (1 for unpressed, 0 for pressed)
6. Player 2 button (1 for unpressed, 0 for pressed)
7. Player 1 switch (0 for DOWN, 1 for UP)
8. Player 2 switch (1 for DOWN, 0 for UP; note that this is reverse of P1)

Your task is to code the game or application that I specify. You can view a demo of parsing the serial data from the ESP32 in esp32_input_demo.py. Your game should run full-screen on the Raspberry Pi when I start the program with `python3 <...>.py`. Please use pygame for your game; assume that the dependency is already installed.

At the top of your file, write down a high-level overview (2 paragraphs) of the game I described, and any implementation details that are not already specified in llms.md. Please do not leave any other comments in the code, because I am very good at reading code without comments.

Do not run any terminal commands to install packages; I will do these manually. Also please work ONLY in the file I specify. Do not create any python virtual environments.
