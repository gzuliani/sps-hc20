# SPS HC20 Suite

## Introduction

The *SPS HC20 Suite* contains two programs that control the SPS HC20 scoreboard
by means of the custom-made, Arduino-based interface described in
"[Controllo di un tabellone segnapunti con Arduino](https://gzuliani.github.io/arduino/arduino-scoreboard.html)" (italian only).

 * **consolle.py** emulates the actual consolle that controls the scoreboard;
 * **report.py** keeps track of an handball match events to help the technical
   delegates (score and time keepers) to compile the official match report
   sheet.

## Prerequisites

### Arduino

Arduino is natively supported by Windows 10 and almost all modern Linux
distributions (those with a 2.6 or more recent kernel, see
"[Install the Arduino Software (IDE) on Linux](https://www.arduino.cc/en/Guide/Linux/)"
for details).
The drivers for Windows 7 and previous versions can be downloaded from the
[official page](https://www.arduino.cc/en/Guide/ArduinoUno#toc3).

### Python

The code uses the _pyserial_ module.

**Warning**: if you intend to compile the Python code with _py2exe_ and run it
on Windows XP then the 2.7 release of _pyserial_ must be used, see for example
"[On Windws[sic] XP not support CancelIO](https://github.com/pyserial/pyserial/issues/148)".

## Issues

The scoreboard's siren may emit a very short buzz at program startup. The
problem is attributable to the Arduino board's autoreset feature that causes
the firmware to restart everytime the serial port is opened (see for example
"[Arduino reset after serial connection opened](https://github.com/pyserial/pyserial/issues/156)"):

> Iep, Linux feature. I was solving this years ago, but no avail. After
> opening, Linux flip flop with RTS even if you are not using rts/cts flow
> control, it's hardcoded,

Other sources confirm this is the case, see for example
"[DTR and RTS control lines toggle unintentionally when opening port](https://github.com/pyserial/pyserial/issues/124)".
Several platform-dependent solutions have been proposed, see for example
"[Disable DTR on ttyUSB0](https://raspberrypi.stackexchange.com/questions/9695/disable-dtr-on-ttyusb0/31298#31298)"
for Linux-like environments,
"[Disable DTR in pyserial from code](https://stackoverflow.com/questions/15460865/disable-dtr-in-pyserial-from-code)"
for Windows.
A simple work-around is to delay the scoreboard connection until the program is
up and running:

 1. switch the computer on;
 2. connect the Arduino board to the computer;
 3. start the desired program;
 4. connect the scoreboard to the Arduino board.

A more reliable solution would be disabling the autoreset feature (see
"[DisablingAutoResetOnSerialConnection](https://playground.arduino.cc/Main/DisablingAutoResetOnSerialConnection)"
for details), but it has its drawbacks: it prevents any future firmware upload.

## Credits

Icons made by Freepik from www.flaticon.com.
