# Manual

DLC pro Digital Laser Controller Manual

Manual: M-063 Version 26 Copyright  2026 TOPTICA Photonics SE

TOPTICA Photonics SE Lochhamer Schlag 19 D-82166 Graefelfing/Munich Tel.: +49 89 85837-0 Fax: +49 89 85837-200 email: info@toptica.com https://www.toptica.com (January 2026 Subject to change without notice)

Dear Customer, Welcome to the TOPTICA community! We have designed this product to be easy to use and reliable so that you can focus on your work. If you have questions or need advice on how to integrate it into your setup, please contact us immediately so we can walk you through the process. We will provide you with quick and competent help through our service staff and product managers. You can always contact TOPTICA service on the Internet by

- Email: service@toptica.com
- Web form: service.toptica.com
The service department at our headquarters in Munich can be reached by phone

- Tel: +49 89 85837150
For up-to-date phone numbers and addresses of our regional offices please refer to our web site: www.toptica.com/contact-us/

Please have your product ID and serial number ready when contacting us, so we can quickly retrieve all relevant information. As we are constantly improving our products, we greatly value all customer feedback. We encourage you to tell us what you like about our products as well as any suggestions for improvement.

Best regards,

Harald Ellmann Director Service TOPTICA Photonics SE

# 1 The Digital Laser Controller DLC pro

Figure 1

The Digital Laser Controller DLC pro

TOPTICA´s DLC pro is a revolutionary diode laser controller that is completely digital and therefore flexible and easy to use. Its digital nature makes life easier. Settings can be remembered and stored and new features can be realized in firmware and software which does not require additional hardware, soldering or sending modules back and forth. The digital nature also makes this technology better: Digital signals have no drift and provide exceptional noise performance of current and voltage outputs when combined with highly-optimized D/A converters and driving stages.

## 1.1 Highlights of the Digital World

The DLC pro is a digital laser controller. Here, we would like to give you a taste of the new features that become available in the digital world and complement the laser performance improvements.

- The provided TOPAS DLC pro PC-GUI control software allows easy remote operation of the connected laser heads. It includes long-term plots and recordings of various parameters. TOPAS
DLC pro is provided on the USB flash drive – that comes together with the DLC pro laser system and is part of each new software release, too. Currently, its OS requirements are Windows 8 or newer. See section 6.

- Network connections to the DLC pro can be made either through a direct link to a PC or through
a network (see section 5.3.4). When connected to a network, a single DLC pro may be monitored and controlled from several PCs simultaneously. Vice versa, it is also possible to control several DLC pro controllers from a single PC.

- Especially in combination with a remote desktop connection, these features improve support and
service. The service report allows generating an overview of controller and laser head parameters, e.g., for trouble shooting. See section 6.9.

- Remote operation of the DLC pro, e.g., by an experimental control program, may also be performed with a simple command language. The Remote Command Reference for TCP/IP and USB
lists and documents the available commands and parameters, as well as the language syntax. The reference is provided on the USB flash drive. See sections 5.14 and the Parameters window in section 6.9 for accessing parameters.

- For remote control of the DLC pro from Python programs, we provide an easy-to-use software
development kit (SDK). See www.toptica.com/laser-sdk for more information of the TOPTICA Python Laser SDK, which is available for pip install.

- Labview example VIs for remote operation are available for download on our DLC pro website
and also included on the USB flash drive. These examples use the command language mentioned above.

- DLC pro Lock is a software license key that enables access to additional features. If not purchased
already with the system, a license key for a 30-day-trial is available on the USB flash drive. See section 11.20. With additional Dual- or Quad-Laser-Operation upgrade, DLC pro lock is valid for all lasers.

- Updates are available for download in the DLC pro section of the TOPTICA webpage. For each
new release, we include a list of changes of the command language and release notes in the documentation folder. The latest version of the DLC pro manual and the Remote Command Reference for TCP/IP and USB are included as PDF files, too. See section 11.19.

- Subscribe to receive email notifications for such updates by sending an email with subject
„subscribe“ to DLCpro@toptica.com. See section 11.18.

- The status of frequency locks is not only indicated by the TOPAS DLC pro PC-GUI and the touchscreen user interface, but also available in real-time via the digital I/O ports of the MC+ module.
Trigger signals synchronized with the scans are provided, too. See section 10.2.3.

- TOPTICA’s laser heads feature a non-volatile memory with all relevant laser parameters, allowing
for an easy exchange of laser heads. Furthermore, your operational parameters will be saved to the DLC pro memory.

- Screen shots of the touchscreen user interface can easily be taken with a connected USB flash
drive and by pressing the save button for a few seconds. See section 11.13.

- Features only available with the digital controller DLC pro include the fast Fourier transformation of
signals (see section 5.4.2), air pressure compensation (see section 11.12), and active power stabilization (see section 5.4.6), to name just a few.

## 1.2 Design of the Digital Laser Controller DLC pro

Figure 2

Block diagram of the DLC pro (example)

PS+ TC MC+ CC PC2 SI

Power Supply Module Temperature Control Module Main Controller Current Controller Piezo Controller System Integrator

S-slot M-slot L-slot P-slot

(Small slot) (Medium slot) (Large slot) (Power slot)

Ext-slot only for SI module

The Digital Laser Controller DLC pro is a complete solution for running, controlling, and stabilizing tunable diode lasers. It consists of a housing with slots on the rear panel, where various plug-in modules can be integrated, depending on the type of laser head being controlled. The user interface and a number of BNC inputs and outputs (I/O board) for connection to the user‘s experiment or apparatus are located on the DLC pro front panel. A tunable External Cavity Diode Laser (ECDL) works with a DLC pro comprising a current controller (e.g., CC-500) to provide the laser diode current, a temperature controller (TC) for temperature control and stabilization, a piezo controller (PC2-1/PC2-2) for high-voltage generation to drive a piezo-electric element, and a main controller (MC+) that contains central computing, interfaces, and signal-processing hardware. The MC+ module generates scans for tuning the laser and processes input signals to comfortably stabilize the laser with multiple PIDs and modulation/demodulation if required. The MC+ module also contains digital inputs and outputs as well as interfaces for communication. A power supply module (PS+) provides the required power. The DLC pro hardware is described in detail in section 10. The SI (System Integrator) module offers the possibility to switch the parameter emission-buttonenabled (which is equal to operating the Emission push button) remotely and to connect external Laser Radiation Emission Warning LEDs.

The user interface consists of a touchscreen with four digital rotary/push knobs and eight push buttons arranged around the display. Sections 4 and 5 describe how to control the laser with this user interface. Beside the touchscreen, the DLC pro can also be controlled via TCP/IP or USB by a computer. A comfortable graphical user interface (TOPAS DLC pro, please refer to section 6) for Windows is supplied. Moreover, the DLC pro may also be remotely controlled by other software and by hardware sending control commands (please refer to section 11.14).

## 1.3 Dual- or Quad-Laser Operation with one DLC pro

### 1.3.1 Upgrade for Control of a 2nd Laser (Dual-Laser-Operation)

NOTE !

To use the DLC pro for control of two lasers (Dual-Laser-Operation), an Upgrade for Control of a 2nd Laser is required. When the Dual-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.2 for a step-by-step description on how to upgrade your DLC pro. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling two laser systems of the type DL pro, DFB pro, DL pro BFY, TA pro, BoosTA pro or two modules in the TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, the second laser is operated in the same way. After pressing the Laser 1/2 buttons on the DLC pro front panel or tapping the symbols aside (see section 5.11), you can control the laser which is connected to the DLC pro as laser 1/2. The front panel controls change accordingly. Additional information on the connection and operation of two lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Dual-Laser-Operation upgrade, frequency locking of both lasers is possible.

### 1.3.2 Upgrade for Control of 4 Lasers (Quad-Laser-Operation)

NOTE !

To use the DLC pro for control of up to four lasers (Quad-Laser-Operation), an Upgrade for Control of 4 Lasers is required. When the Quad-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.3 for a step-by-step description on how to upgrade your DLC pro. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling up to four laser systems of the type DL pro, DFB pro, DL pro BFY, or up to four DL pro, DFB pro or DL pro BFY modules in the MDL pro or TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, all other lasers are operated in the same way. After pressing the Laser 1 .. 4 buttons on the DLC pro front panel or tapping the symbols aside (see section 5.11), you can control the laser which is connected to the DLC pro as laser 1 .. 4. The front panel controls change accordingly. Additional information on the connection and operation of three or four lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

## 1.4 PDH Module for Pound-Drever-Hall Locking

NOTE !

When the PDH module is acquired, TOPTICA also provides relevant software to update your DLC pro. Please refer to section 11.4 for a step-by-step description on how to install a PDH module. If purchased along with the DLC pro, the PDH module and the software is already installed.

# 2 Safety Instructions and Warnings

Before using the DLC pro, please read and follow the Safety Instructions and Warnings. TOPTICA laser systems with DLC pro are manufactured according to the International Laser Safety Standards EN 60825-1:2014+A11:2021, IEC 60825-1:2014 and comply with US laws 21 CFR §1040.10 and §1040.11. The following safety terms are used in this manual: The DANGER ! heading in this manual explains danger that could result in personal injury or death. The CAUTION ! heading in this manual explains hazards that could damage the instrument. In addition, a NOTE ! heading provides information to the user that may be beneficial in the use of the instrument. CAUTION ! Before connecting the cables to the laser head, the DLC pro must be switched off and disconnected from the mains supply. This complete power down is required for exchange of laser heads, too.

## 2.1 General Safety Terms

DANGER ! Before operating the Digital Laser Controller DLC pro, please read this manual carefully to CAUTION ! prevent personal injury and damage to the electronics and connected diode lasers. The following safety instructions must be followed at all times. DANGER ! CAUTION !

Possibility of electrical shock ! Wherever this symbol is attached, the possibility of an electrical shock may appear. Use only equipment and accessories supplied by TOPTICA. Caution ! Wherever this symbol is attached read and understand the manual before operating the device. The manual must be consulted in order to find out the nature of the potential HAZARDS and any actions which have to be taken to avoid them.

DANGER ! During installation, maintenance, and service, all persons in the room must wear appropriate laser safety goggles while the laser is in operation. The recommended protection stage is dependent on the laser system. For details, please refer to the laser head manual. DANGER ! Laser safety goggles selected for adjustment purposes do not protect against an intentionally focused direct beam which will increase the optical power densities by a few orders of magnitude. DANGER ! Regular functional checks and performance inspections at the supplier are recommended for all laser safety goggles. DANGER ! The DLC pro and the laser head are both equipped with LEDs that indicate laser emission. CAUTION ! (Please refer to the laser head manual and to section 4.1 in this manual for detailed information). Be aware of laser emission when at least one of these LEDs lights up. DANGER ! Before connecting/disconnecting any cables at the DLC pro or the connected laser CAUTION ! device, switch off the DLC pro and disconnect it from the mains supply. This complete power down is required for exchange of laser heads, too. DANGER ! The equipment must be positioned so that the disconnecting device can be easily reached by the operator. DANGER ! Use of controls or adjustments or performance of procedures other than those specified herein may result in hazardous radiation exposure.

DANGER ! If the equipment is used in a manner not specified by the manufacturer, the protection provided by the equipment may be impaired. DANGER ! For safe operation and for proper grounding, please use the supplied mains cable only. Improper or missing grounding can lead to serious injury. DANGER ! Operation of this electrical equipment in outdoor areas, wet or dirty atmospheres, potentially explosive atmosphere, corrosive atmosphere, and other environments that deviate from normal environmental conditions (IEC 61010-1 clause 1.4.1) is not allowed. DANGER ! Plug-in modules should only be opened by trained personnel. Before exchanging and opening any module, the Digital Laser Controller DLC pro must be switched off and disconnected from the mains supply. DANGER ! Always switch off the PC Piezo Control module(s) and disconnect the piezo supply cable at the PC module panel when opening the housing of the connected laser device, e.g., for internal adjustments. Dangerous voltages can be present inside the connected laser device. DANGER ! Do not look into the laser beam as the output can exceed the limits for class 1 specified by US laws 21 CFR 1040.10 and 2 CFR 1040.11 and the Laser Safety Standards EN 608251:2014+A11:2021, IEC 60825-1:2014. Take precautions to eliminate exposure to a direct or reflected beam. DANGER ! The Digital Laser Controller DLC pro can operate very powerful lasers (up to class 4). Therefore, it is imperative to take great care and observe the statutory warning labels on the unit. To set up an external interlock, the MC+ module of the Digital Laser Controller DLC pro is equipped with an external interlock connector. By using an appropriate door switch, laser emission of the laser heads connected to the DLC pro can be switched off. DANGER ! Do not open the Digital Laser Controller DLC pro during operation. Only authorized and specially-trained service personnel should perform internal tuning and replacement of components. Be aware that under certain circumstances, parts of the equipment may remain under high voltage conditions (e.g., piezo-electric elements) even when the device is disconnected from the mains supply. CAUTION ! Check the adjusted parameters of the Digital Laser Controller DLC pro before switching on the connected laser, e.g. if exchanging laser heads ! In particular, pay attention to the Imax and Umax limitations and the correct setting of the laser diode polarity (please refer to section 4.5.4). As long as the laser emission is switched off by the Emission push button on the DLC pro front panel, the laser diode is short-circuited and therefore protected by the relay integrated in the TOPTICA diode laser head. CAUTION ! Special precautions are necessary if the Digital Laser Controller DLC pro is to be operated in surroundings of high electro-magnetic radiation such as close to a plasma discharge. Please contact TOPTICA for technical support. CAUTION ! Please assure with particular care that the electrical safety conditions are met especially concerning the high-voltage outputs. Also carefully read the operating instructions for the Digital Laser Controller DLC pro before starting the device.

## 2.2 Service Operations

For certain installation or alignment procedures, the exchange of components or internal electronics settings, tools are required to perform the respective procedure at the DLC pro. All operations, which require tools to be used, are declared as service operations. Service operations require additional knowledge and may only be carried out by specially trained personnel. DANGER ! Before carrying out service operations, switch off the DLC pro and disconnect it from the CAUTION ! mains supply.

## 2.3 Safety Features

### 2.3.1 External Interlock Connector

The DLC pro provides an external interlock connector located at the MC+ module (see Figure 143). The external interlock is equal to the function of the key switch on the front panel of the DLC pro (see section 4.1). All lasers connected to the DLC pro are disabled when the external interlock circuit is open.

Figure 3

External interlock connector (Phoenix MC 0.5/2-G-2.5)

NOTE !

We recommend setting up an external interlock circuit with a door switch. When the interlock circuit shown in Figure 3 is opened, the connected laser is switched off and cannot be switched on. After closing the interlock circuit, the Emission push button on the DLC pro front panel must be pressed to switch ON the connected laser. By using the DLC pro SI module, laser emission of the connected laser can also be activated/deactivated remotely by a positive/negative TTL Slope or by software commands. Connection of external laser radiation emission warning indicators is also possible. For details, please refer to section 10.2.12. The type of the interlock plug is Phoenix FK-MC 0.5/2-ST-2.5. The interlock plug supplied with the DLC pro should only be used for first adjustment purposes. For safe operation, the circuit shown in Figure 3 must be installed. Always follow the required safety measures applicable to the working environment.

### 2.3.2 AC Mains Voltage and Fuse DLC pro with PS+ Module

The DLC pro with PS+ module (see section 10.2.1) works with a wide range of input voltages. CAUTION ! The mains voltage input of the DLC pro with PS+ module is a wide-range input for input voltages of 100 .. 240 V~, 50/60 Hz. The mains supply is protected by a 250 V~, 4 A T (slow blow) fuse 5 x 20 mm, which is accessible at the PS+ module at the rear of the DLC pro next to the mains plug. For exchanging the fuse, please refer to section 11.8.1. DANGER ! Before exchanging the fuse, make sure to switch off and disconnect the DLC pro from the mains supply !

### 2.3.3 AC Mains Voltage and Fuse DLC pro with PS HP Module

The external power adaptor of a DLC pro with PS HP module (see section 10.2.2) works with a wide range of input voltages. The PS HP module has no accessible fuse. CAUTION ! The PS HP module is delivered together with an external power adaptor. The mains voltage input of this external power adaptor is a wide-range input for input voltages of 100 .. 240 V~, 50/60 Hz. Do not use other equipment than the external power adaptor delivered by TOPTICA.

## 2.4 Identification of Manufacturer

Manufacturer (name and address), production date, product ID number and compliance with CE standard are noted on the identification label. The crossed out wheeIed dust bin symbol indicates that products must be collected and disposed of separately from household waste (please refer to section 11.25 for details).

Size: Color: Location:

38 mm x 19 mm Silver/black Bottom side of the DLC pro

# 3 Installation

## 3.1 Inspection after Delivery

The DLC pro is packaged in a carton designed to give maximum protection during shipment. If the outside of the shipping carton is damaged, notify your shipping department immediately. The shipping agent may wish to notify the carrier at this point. If the shipping carton is not damaged externally, remove the DLC pro from the carton. If any damage is visually evident, notify TOPTICA and your shipping agent. We recommend saving the carton for future storage or transportation. After unpacking, please check the package contents. If any item is missing, please contact TOPTICA (for contact details, please refer to section 11.26). Package Contents:

1.
2.
3.
4.
DLC pro Laser Control Electronics Keys for the Key Switch on the DLC pro front panel Interlock plug Mains cable (DLC pro with PS+ power supply module) Mains cable, external power adaptor, connection cable (DLC pro with PS HP power supply module) USB flash drive

5.
## 3.2 Installation Instructions

Figure 4

DLC pro Laser Control Electronics

Follow these instructions when installing the DLC pro Laser Control Electronics:

- 
- 
- 
- 
- 
For general and environmental specifications, please refer to section 11.1.1. Do not block the ventilation grilles of the DLC pro. Do not place more than 4 DLC pro units on top of each other. Always tighten the cable connector screws. Install the DLC pro only in an area free of vibrations.

# 4 Operation

## 4.1 DLC pro Front Panel

Figure 5

DLC pro front panel

1

Key Switch

5

Input Connectors - Fast

9

Power/Standby Push Button and LED

2

USB Connector

6

Output Connectors

10 Emission Push Button and Laser Radiation Emission LED

3

Rotary Knob

7

Push Buttons

4

Input Connectors - Fine

8

Touchscreen

The user interface and the I/O board are located on the front panel of the DLC pro. The user interface operator controls are described in this section, while the I/O board is described in the hardware section 10.1.1.

## 4.2 DLC pro Rear Panel

Figure 6

DLC pro rear panel (example DLC DL pro)

11 ON/OFF Switch

13 Mains Connector

12 Fuse Cartridge

14 Scan Trigger and Lock Status Digital Signals

The DLC pro accepts numerous modules for various laser configurations on the rear panel. The different modules are described in detail in section 10.2. Please refer to section 11.6 for the mounting positions of the modules.

4.3

1

Description of Interfaces and Controls

Key Switch

The Key Switch must be set to position Enable Laser before laser emission of all connected lasers can be switched on by pressing the Emission push button. Key Switch in Position 0: No laser emission possible. Key Switch in Position Enable Laser:

2

USB Connector

Laser emission possible.

The USB 2.0 host connector can be used, e.g., to load/save configuration data on a USB flash drive, or to perform a software/firmware update (please refer to sections 11.17 and 11.18). NOTE !

This USB connector cannot be used for remote control of the DLC pro. Please use the USB or Ethernet connector on the MC+ module (rear panel of the DLC pro) for remote control.

3

Rotary Knob

The rotary knob changes the respective operating parameters. Please refer to section 4.4.1 for detailed information.

4

Input Connectors Fine

- BNC-connectors
Input connectors for analog voltages that are internally converted by a 24-bit A/D converter into digital signals. The use of the connectors can be configured via touchscreen or TOPAS DLC pro PC-GUI. Fine 1 and 2

5

Input Connectors Fast

- BNC-connectors
Input connectors for analog voltages that are internally converted by a 16-bit A/D converter into digital signals. The use of the connectors can be configured via touchscreen or TOPAS DLC pro PC-GUI. Fast 3 and 4

6

Output Connectors

- BNC-connectors
Input Resistance: 10 kΩ Input Voltage: - 4 V .. + 4 V Sample Rate: 675 kHz

Input Resistance: 10 kΩ Input Voltage: - 4 V .. + 4 V Sample Rate: 200 kHz

Output connectors for analog voltages that are internally converted by a 16-bit D/A converter from digital signals. The use of the connectors can be configured via touchscreen or TOPAS DLC pro PC-GUI. The outputs are enabled/disabled in the IO window (see section 6.9) where the applied signals can be further customized. A and B

Output Voltage: - 4 V .. + 4 V at ≥ 100 kΩ load Sample Rate: 2.7 MHz

CAUTION ! During power up (boot procedure) of the DLC pro, the voltage level at the two output connectors starts with -4 V before they get reset by the software to the stored value. 7

Push Buttons

Push buttons for selecting the touchscreen operation modes and to perform frequent tasks. Please refer to section 5 for detailed information.

8

Touchscreen

Please refer to sections 4.4 and 5 for detailed description on operating the touchscreen.

9

Power/Standby Push Button and LEDs

10 Emission Push Button and Laser Radiation Emission Warning LED

Push button for toggling between power and standby mode of the DLC pro. A green LED indicates that the DLC pro is on, a red LED indicates standby mode. The standby function of the push button can be configured in the parameter menu (please refer to section 5.14) or in the Parameters window of the TOPAS DLC pro PC-GUI (please refer to section 6.9). Standby

Touchscreen switches off. The standby status of the PC, CC, and TC modules is as configured.

Power

The operating parameters resume as they were set before switching to standby.

NOTE !

If a power down is required, e.g. for exchanging laser heads, using the Power/Standby Push Button is not sufficient. Please use the ON/OFF Switch on the DLC pro rear panel instead and disconnect the DLC pro from mains.

The Emission push button switches on/off (toggle function) one or more CC modules and thus laser emission for all laser channels is activated. After pressing the Emission push button, the LED lights up white when laser emission is enabled and thus at least one of the connected lasers emits laser light. The LED lights up red when the connected laser head(s) are disabled (Laser 1 .. 4 buttons, see section 5.11), or when a laser safetyrelated issue leads to a condition in which the laser cannot be switched on or has been switched off automatically. In this case, check the system messages (please refer to section 11.16). To switch on the laser again, press the push button twice to actively switch off/on the laser. DLC pro SI Module: In addition to operating the Emission push button, laser emission of the connected laser heads can also be activated/deactivated remotely. For details see section 10.2.12. Operation of the Emission push button overrides the remote activation/ deactivation, and vice versa. DANGER ! When the Laser Radiation Emission Warning LED lights up white, be aware that there is laser emission.

11 ON/OFF Switch

NOTE !

Laser emission can only be switched on with the Emission push button if:

- Laser 1 .. 4 is enabled by the corresponding push buttons
(see section 5.11).

- the external interlock circuit is closed (see section 2.3.1).
- the key switch is in the Enable Laser position.
- the CC modules are activated in the parameter menu
(please refer to section 5.14) or in the Parameters window of the TOPAS DLC pro PC-GUI (please refer to section 6.9).

NOTE !

During the boot procedure, the white Laser Radiation Emission Warning LED lights up for a short time as a function test.

NOTE !

If laser emission is switched on by the Emission push button, the short circuit relay inside the laser head, which secures the laser diode, is opened.

ON/OFF switch for DLC pro laser driver electronics. For detailed description, please refer to sections 10.2.1 and 10.2.2. NOTE !

After switching off, please wait for at least 10 seconds before switching the DLC pro on again.

12 Fuse Cartridge

The mains supply is protected by a 250 V~, 4 A T (slow blow) fuse 5 x 20 mm, which is accessible after removing the fuse cartridge. For exchanging the fuse, please refer to section 11.8.1. DANGER ! Before exchanging the fuse, make sure to switch off and disconnect the device from the mains supply ! NOTE !

13 Mains Connector

Connector for the supplied mains cable. NOTE !

14 Digital I/O Connector

Only DLC pro with PS or PS+ Power Supply Module.

Only DLC pro with PS or PS+ Power Supply Module: For description of the PS HP power supply module, please refer to section 10.2.2.

Connector for multi-purpose digital inputs and outputs, e.g., scan trigger and lock status digital signals are available. Please refer to section 10.2.3.

## 4.4 Rotary Knob and Touchscreen Operation

### 4.4.1 Rotary Knob

Figure 7

Rotary knob and corresponding parameter value

The user can select the digit and set the value of the parameter to be changed using the rotary knob. Changing a Parameter Value

- Press the rotary knob once to change between selecting or setting a digit. The background color
is white for selecting digits and black for setting values.

- Background color white: Turn the rotary knob to move the cursor below the numbers and select
the digit to be changed.

- Background color black: Turn the rotary knob to increase/decrease the value of the selected digit
(cursor). All digits left of the one selected change accordingly. NOTE !

In order to ensure a fluent user interface, not every single tick of a dial is communicated immediately, but several ticks might be collected before doing so. Due to this please rotate the knob slow enough in order to avoid jumps across narrow features due to this accumulation of ticks.

NOTE !

Depending on the operation mode of the DLC pro, the rotary knobs are assigned to certain control parameters. In some operation modes, the assignment of a rotary knob (corner parameter) can be selected in a drop-down menu which is available after tapping the parameter name corresponding to the rotary knob (see section 4.4.2).

### 4.4.2 Selecting a Corner Parameter

Figure 8

Corner parameter (example top-right) and drop-down menu

In some screens the displayed corner parameter and thus the rotary knob assignment can be selected. The little white arrow near the corner parameter indicates that there are further options available that can be selected in a drop-down menu which appears after tapping on the corner parameter.

### 4.4.3 Touchscreen

4.4.3.1

Gestures

Use the following gestures to operate the DLC pro via touchscreen.

Figure 9

Gestures for touchscreen operation

Tap

Briefly touch surface with fingertip.

Selects, for example, a parameter value, opens the numerical editor or selects a candidate in Scan/Lock mode.

Drag

Move fingertip over surface without losing contact.

Moves a displayed graph or element left/ right or up/down.

Flick

Quickly brush surface with fingertip.

Used, for example, to scroll in the parameter menu.

Pinch

Touch surface with two fingers and bring them closer together.

Zooms out of the displayed graph.

Spread

Touch surface with two fingers and move them apart.

Zooms into the displayed graph.

4.4.3.2

Numerical Editor

The user can change a parameter value via a touchscreen keypad (numerical editor).

Figure 10

Parameter value and touchscreen keypad

Changing a Parameter Value

- To open the numerical editor, tap the parameter value to be changed. A keypad is displayed on
the touchscreen.

- Use the touch keys to enter/change the parameter value.
⊗ Key

Deletes the parameter value.

← Key

Deletes the number to the left of the cursor position.

- / + Key
Toggles between a negative or positive sign being added to the parameter value or an exponent at the position of the cursor.

E Key

E represents "times ten raised to the power of" and is followed by the exponent.

Cancel

The new parameter value is ignored. The numerical editor returns to the value that was active before the editor was opened.

Apply

The new parameter value is applied, and the numerical editor remains opened.

OK

The new parameter value is applied, and the numerical editor is closed.

### 4.4.4 Touchscreen Display Settings

General touchscreen settings are configured in the parameter menu with the Home screen selected. When auto-dark is enabled (parameter: display > auto-dark), the touchscreen is switched dark after the time set in display > idle-timeout (minimum time is 2 seconds). When tapping on the touchscreen, it is switched on for the idle-timeout set. The parameter display > brightness (range 0 (dark) .. 100 (max. brightness)) determines the brightness of the touchscreen when switched on. Parameter display > state shows the state of the touchscreen. Press the Load/Save button or tap the corresponding symbol twice to store the settings to the flash memory of the DLC pro.

## 4.5 DLC pro Set Up and Initial Power Up

The following sections describe the basic setup and operation of a DL pro laser system controlled by the DLC pro. Please refer to sections 4.1 and 4.2 for location of the interfaces and controls. Please follow the instructions provided in sections 4.5.2 to 4.5.5 in the given order. NOTE !

For detailed information on the setup and operation of your laser system, please refer to the respective laser head manual.

NOTE !

The DLC pro laser driver electronics, that are shipped together with laser systems containing a frequency-conversion stage, such as a DL-/TA-SHG/FHG pro, are pre-configured by TOPTICA especially for use with their particular laser head. Any connection of a different type of laser head with such a DLC pro may lead to unwanted results.

### 4.5.1 Control of the DLC pro

The DLC pro can be operated in three different ways:

- Using the rotary knobs, push buttons, and the touchscreen on the DLC pro front panel. This way of
operation is possible without any additional software installation and is the preferred way for quickstart and for interacting with the laser while making adjustments at the optical table. Please refer to sections 4.4.1 and 4.4.3 for basic rotary knob and touchscreen operation.

- Using TOPAS DLC pro software (PC-GUI) installed on a PC. This way of operation requires software
installation on a control computer (Please refer to section 6 for detailed information on the software and installation). The PC-GUI offers complete access to all parameters and is especially useful for controlling and monitoring the laser from your desk.

- Using software commands to remotely control the DLC pro via USB or Ethernet. The software commands may also be integrated in user-specific software. For a detailed description of the software
commands, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro. Labview VIs and an example using these VIs are provided on this drive as well as on the DLC pro product page at www.toptica.com.

NOTE !

We recommend operating the DLC pro via Ethernet over using a USB connection due to the higher communication bandwidth. Using a USB to Ethernet adapter on the PC side allows fast communication while having a point-to-point connection between PC and DLC pro – without connecting the DLC pro to the local network or disconnecting the PC from it.

### 4.5.2 Mains Supply DLC pro

4.5.2.1

DLC pro with PS+ Power Supply Module

Connect the DLC pro to mains via the supplied mains cable. The DLC pro works with a wide range of input voltages. CAUTION ! The mains voltage input of the DLC pro is a wide-range input for input voltages of 100 .. 240 V~, 50/60 Hz.

4.5.2.2

DLC pro with PS HP Power Supply Module

Connect the PS HP module to the DLC pro, and the PS HP external power adaptor to mains via the supplied cables as described in section 10.2.2. The PS HP external power adaptor works with a wide range of input voltages. CAUTION ! The PS HP module is delivered together with an external power adaptor. The mains voltage input of this external power adaptor is a wide-range input for input voltages of 100 .. 240 V~, 50/60 Hz. Do not use other equipment than the external power adaptor delivered by TOPTICA.

### 4.5.3 Cable Connections

CAUTION ! Before connecting the cables to the laser head, the DLC pro must be switched off and disconnected from the mains supply. NOTE !

For detailed information on the cable connections of your laser system, please refer to the respective laser head manual.

Figure 11

Basic cable connections between DLC pro and laser head (example DLC DL pro). The laser head is connected to DLC pro as laser 1

Basic Connections for laser 1: A B C

Temperature control connection to laser head 1 Current control connection to laser head 1 Piezo control connection to laser head 1

NOTE !

Dual-Laser-Operation: For examples and general rules on TC, CC, and PC module connection, please refer to section 11.2.1. Quad-Laser-Operation: For examples and general rules on TC, CC, and PC module connection, please refer to section 11.3.1.

### 4.5.4 Laser Configuration for DL pro Laser Heads with EEPROM

NOTE !

All TOPTICA DL pro and TA pro laser heads with serial number 20000 and higher are equipped with an EEPROM. For detailed information on the configuration of your laser system, please refer to the respective laser head manual.

Laser heads equipped with an EEPROM have the operating parameters stored on this EEPROM and they are read out during the boot procedure of the DLC pro with the laser head connected. CAUTION ! Before interchanging laser heads, the DLC pro must be switched off and disconnected from the mains supply. When the DLC pro is switched on at the ON/OFF switch at on the rear panel, the EEPROM of the new laser head is read out during the boot procedure and settings, such as current limits are set accordingly. CAUTION ! As long as the laser emission is switched off by the Emission push button on the DLC pro front panel, the laser diode is short-circuited and therefore protected by the relay integrated in the TOPTICA diode laser head. NOTE !

External CAN devices must be powered simultaneously or before power up of the DLC pro to be properly detected during the boot procedure.

Switch on the ON/OFF switch on the DLC pro rear panel and wait for the DLC pro to start. The boot procedure takes approximately 30 to 60 seconds and is finished when an acoustic signal is played and the Home screen (see Figure 13) is displayed on the touchscreen. Please note that you may need to enable the CC, TC or PC modules in the parameter menu.

### 4.5.5 Switching on the Laser

DANGER ! For your safety, we recommended that you set up an external interlock circuit. If no interlock circuit is connected, please use the supplied interlock plug to close the external interlock circuit. For detailed information, please refer to section 2.3.1. DANGER ! Do not look into the laser beam of the connected laser as the output can exceed the limits for class 1 specified by US laws 21 CFR 1040.10 and 2 CFR 1040.11 and the Laser Safety Standards EN 60825-1:2014+A11:2021, IEC 60825-1:2014. Take precautions to eliminate exposure to a direct or reflected beam. Always wear appropriate laser safety goggles. NOTE !

For detailed information on operating your laser system, please refer to the respective laser head manual.

1.
Close the external interlock circuit.

2.
Set the key switch on the DLC pro front panel to the Enable Laser position.

3.
Select the Scan/Lock mode by pressing the Scan/Lock Mode button or tapping the corresponding symbol and select the Scan sub-screen by tapping the Scan function mode field at the bottom of the touchscreen. Adjust the desired set current with the top-right rotary knob, or enter it in the Laser tab of the PC-GUI.

4.
Enable the desired laser for laser emission by pressing the Laser 1 .. 4 buttons on the DLC pro front panel for one second (see section 5.11 for details). Press the Emission push button on the DLC pro front panel. The enabled laser is switched on and the white Laser Radiation Emission Warning LED lights up and indicates laser emission.

5.
If necessary, coarsely adjust the wavelength of the connected laser. Please refer to the laser head manual.

6.
In the Scan sub-screen of the Scan/Lock mode, optimize the mode hop-free tuning as described in the laser head manual by adjusting the available parameters with the rotary knobs. If necessary, assign the top-left rotary knob to adjust Feed Forward or Tset (for assignment, please refer to section 4.4.2).

NOTE !

7.
Feed Forward adjustment is normally not necessary unless the Set Current Iset or the Scan Frequency is changed considerably.

Store the settings by pressing the Load/Save button Menu > Save Configuration in the PC-GUI.

on the DLC pro front panel twice or via

## 4.6 Power Down

NOTE !

For detailed information on operating your laser system, please refer to the respective laser head manual.

1.
Press the Emission push button on the DLC pro front panel. All connected lasers are switched off and the Laser Radiation Emission Warning LED turns off. In case of a DLC pro for Dual- or Quad-Laser-Operation, please refer to section 5.11 for switching off only one laser by disabling it with the Laser 1 .. 4 buttons on the DLC pro front panel.

2.
Press the Power/Standby push button to set the system into standby mode. The factory settings for the standby mode are such that every module but the TC module is switched off. During longer breaks, switch off the key switch on the DLC pro front panel (for laser safety reasons) and switch off the DLC pro with the ON/OFF switch on the rear panel.

## 4.7 Normal Power Up

NOTE !

For detailed information on operating your laser system, please refer to the respective laser head manual.

NOTE !

External CAN devices must be powered simultaneously or before power up of the DLC pro to be properly detected during the boot procedure.

1.
Depending on the status, switch on the DLC pro by the ON/OFF switch on the rear panel (wait for boot procedure to be completed) or press the Power/Standby push button.

2.
Press the Emission push button on the DLC pro front panel. The enabled lasers are switched on and the white Laser Radiation Emission Warning LED indicates laser emission.

3.
Switch to the Scan sub-screen of the Scan/Lock mode (for touchscreen operation see section 5.4, for PC-GUI operation see section 7.2) and optimize the scan by tuning Iset and T set. Changing the Feed Forward is usually not required.

## 4.8 Seed Laser + BoosTA pro Combination

In addition to a DL pro, DFB pro or CTL as seed laser head, a BoosTA pro tapered amplifier can be connected to the DLC pro, if at least one CC-5000 module is installed in the DLC pro laser driver electronics. The operation and control of the respective seed laser head is unchanged, and controls for the BoosTA pro are added in the user interfaces: In the touchscreen user interface, the top-left parameter of the Scan/Lock screen can be changed to display/control the amplifier actual and set current (see section 5.4.7.1). The TOPAS DLC pro PC-GUI shows additional fields for the amplifier current and temperature in the Laser tab (see section 7.1.10). Please refer to the BoosTA pro manual for details about how to connect and power up/down the laser heads correctly.

## 4.9 User Levels

One feature of the DLC pro is the option to restrict or allow reading and/or changing parameters according to the expert knowledge of the user. Five user levels are available: READ-ONLY: USER:

Parameters can be read but their values cannot be changed. User level for daily operation of the laser. The DLC pro touchscreen interface is acting in this user level. To operate the laser remotely via network access, we recommend introducing a password for the USER level (please refer to section 4.9.1). Please note that now operation of the laser directly via the operator controls at the DLC pro is still possible. For locking the touchscreen and the operator controls at the DLC pro by a pincode, please refer to section 4.9.2. MAINTENANCE: User level for operations needed to maintain the laser (according to the laser safety standard). SERVICE: User level for operations that may change the laser safety classification such as changing the maximum operating current of the laser (service operation according to the laser safety standard). INTERNAL: For internal TOPTICA use only. DANGER ! The user levels MAINTENANCE and SERVICE may only be accessed by authorized and specially-trained service personnel. The passwords for the user levels MAINTENANCE and SERVICE are noted in the Electronics/Software section of the Production and Quality Control Data Sheet. Maintenance and service operations need to be performed by using the TOPAS DLC pro PC-GUI as for the touchscreen interface the USER level is fixed. For changing the user level, click Menu > Device Configuration and select the Userlevel section (please refer to section 6.9). NOTE !

The user level required for changing a certain parameter is noted in the parameter description in the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro. The user level nomenclatures in the Remote Command Reference and in this manual correspond as follows: 4 > READ-ONLY 3 > USER 2 > MAINTENANCE 1 > SERVICE 0 > INTERNAL

### 4.9.1 Introducing a Password for the USER Level

NOTE !

When a password for the USER level is introduced, only DLC pro remote control operation by TOPAS DLC pro, or by sending control commands is affected: Parameter values cannot be changed anymore (read-only) unless the password is entered. Operation of the laser directly via the operator controls at the DLC pro is still possible. For locking the touchscreen and the operator controls at the DLC pro by a pincode, please refer to section 4.9.2.

Please proceed as described below to introduce a password for the USER level:

1.
Select Menu > Device Configuration > Userlevel section and change to the SERVICE level.

2.
Select change-password in the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9) and click on its right so that Execute appears. Click Execute to open a dialog window.

3.
Enter the desired password in the input field and click Execute to set the password.

4.
Select Menu > Device Configuration > Userlevel section and change to the USER level.

5.
Switch the DLC pro off and on at the ON/OFF switch on the rear panel to reboot.

NOTE !

After switching off, please wait for at least 10 seconds before switching the DLC pro on again.

NOTE !

If a password for the USER level is introduced, this password plus the MAINTENANCE password must be entered as a combined but single password for changing to the MAINTENANCE level. The SERVICE password remains unchanged.

### 4.9.2 Locking Touchscreen and Operator Controls at the DLC pro via a Pincode

NOTE !

When the touchscreen and the operator controls at the DLC pro are locked by a pincode, operation of the Emission and Power/Standby push buttons is still possible.

Please proceed as described below to introduce a pincode for locking the touchscreen and the operator controls at the DLC pro:

Figure 12

Locking the touchscreen and the operator controls at the DLC pro

1.
Press the Lock On/Off button for longer than 4 seconds until a numerical editor appears.

2.
Enter a pincode and tap Lock. The touchscreen and the operator controls at the DLC pro are locked. This is indicated by a red lock symbol and a transparent touchscreen appearance.

3.
To unlock the touchscreen and the operator controls, again press the Lock On/Off button for longer than 4 seconds. Enter the previously entered (see 2.) pincode and tap Unlock. The touchscreen and the operator controls at the DLC pro are unlocked.

NOTE !

In case the pincode is lost, a Master PIN to unlock the touchscreen is noted in the Electronics/Software section of the Production and Quality Control Data Sheet. For a DLC pro delivered with firmware lower than 2.0.0 please contact TOPTICA Service (see section 11.26) to obtain the Master PIN.

## 4.10 Laser Current Settings and Clips

A number of laser current related parameters ensure that the laser is operated in a safe way. The order is as follows (assuming positive current values): 0 ≤ current-set, current-act ≤ current-clip ≤ current-clip-limit ≤ maximal current of supply The maximal current of supply depends on the CC module(s) of the DLC pro and their operating mode (CC-500/CC-700: two channel or one channel) and their setting. current-set

Set Current is the operating current to which the output of the CC module is regulated when the laser is switched on. Actual Current is the current as measured internally. Named Maximum Current in the various menus and tabs on the touchscreen and the TOPAS DLC pro PC-GUI. Current-clip may be changed in the USER level and is intended to limit the operating current of the laser to a certain range, e.g., a level needed to reach the desired power level for the experiment.

current-act current-clip

current-clip-limit

4.11

May be changed in the Parameters window of the TOPAS DLC pro PC-GUI. The SERVICE level is required to change the value as in some cases the laser class may be affected or at least the power level may be changed. Current-clip-limit may be used to limit the power of the laser to fulfill safety regulations. The laser is classified with the power emitted at this current.

Loading/Saving of Device Parameter Configurations

DANGER ! Before handling configurations, always switch off the laser emission of the connected laser heads via the Emission push button on the DLC pro front panel ! Loading a configuration with the laser emission switched on may result in the direct emission of hazardous laser radiation ! The DLC pro allows to save and load several device parameter configurations, which include laser head operation parameters as well as not laser head specific settings of the DLC pro, e.g., display settings. A configuration file contains the laser head type and its serial number and can only be loaded if this data matches the selected laser head. Please refer to sections 5.13.1 and 6.9 for detailed information on how to load/save device parameter configurations via the DLC pro touchscreen or the TOPAS DLC pro PCGUI.

## 4.12 Loading the Factory Settings

DANGER ! Always switch off the laser emission of the connected laser heads when handling factory settings ! NOTE !

Factory settings are certain laser head specific operation parameters, such as laser diode maximum voltages and currents, laser diode polarity, photo diode calibration data and other mostly laser safety related settings. For additional information please refer to section 11.15. Please note that the factory settings may have been changed formerly by the user, e.g. after an exchange of the laser diode.

In general, the operation parameters for the connected laser head are saved by pressing the Load/Save button on the DLC pro front panel twice or via Menu > Save Configuration in the PC-GUI. During the boot procedure of the DLC pro, these operation parameters are loaded again. To load and use the parameter values in the factory settings, you have the following options: DLC pro Touchscreen Please use the Factory Settings section in the Configuration Manager (see section 5.13.1). TOPAS DLC pro PC-GUI Configuration Manager Run the TOPAS DLC pro PC-GUI on the control computer and connect to the laser head (please refer to section 6). Please use the Configuration Manager which is available in the TOPAS DLC pro menu (see section 6.9). TOPAS DLC pro PC-GUI Parameters Window

1.
Run the TOPAS DLC pro PC-GUI on the control computer and connect to the laser head (please refer to section 6).

2.
In the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9), look for the factory settings and click apply to load.

NOTE !

3.
In case of an amplified or frequency converted laser system, the factory settings of the Master Oscillator (dl), the Amplifier (amp), the SHG stage (nlo > shg), and fhg stage (nlo > fhg) are treated separately. For a CTL laser system, please load the factory settings for (dl) and (ctl) separately.

If these settings should be used after the next DLC pro boot procedure, please click Menu > Save Configuration.

# 5 Touchscreen User Interface

For operation of the DLC pro via the touchscreen user interface, use the touchscreen as well as the rotary knobs and the push buttons. For basic rotary knob and touchscreen operation, please refer to section 4.4. NOTE !

The screenshot function (please refer to section 11.13) allows for storing screenshots of the actual touchscreen display on a USB flash drive.

## 5.1 Upgrade for Control of a 2nd Laser (Dual-Laser-Operation)

NOTE !

To use the DLC pro for control of two lasers (Dual-Laser-Operation), an Upgrade for Control of a 2nd Laser is required. When the Dual-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.2 for a step-by-step description on how to upgrade your DLC pro. For installation of the modules, please refer to sections 11.5 and 11.6. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling two laser systems of the type DL pro, DFB pro, DL pro BFY, TA pro, BoosTA pro or two modules in the TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, the second laser is operated in the same way. After pressing the Laser 1/2 buttons on the DLC pro front panel or tapping the symbols aside (see section 5.11), you can control the laser which is connected to the DLC pro as laser 1/2. The front panel controls change accordingly. Additional information on the connection and operation of two lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Dual-Laser-Operation upgrade, frequency locking of both lasers is possible.

## 5.2 Upgrade for Control of 4 Lasers (Quad-Laser-Operation)

NOTE !

To use the DLC pro for control of up to four lasers (Quad-Laser-Operation), an Upgrade for Control of 4 Lasers is required. When the Quad-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.3 for a step-by-step description on how to upgrade your DLC pro. For installation of the modules, please refer to sections 11.5 and 11.6. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling up to four laser systems of the type DL pro, DFB pro, DL pro BFY, or up to four DL pro, DFB pro or DL pro BFY modules in the MDL pro or TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, all other lasers are operated in the same way. After pressing the Laser 1 .. 4 buttons on the DLC pro front panel or tapping the symbols aside (see section 5.11), you can control the laser which is connected to the DLC pro as laser 1 .. 4. The front panel controls change accordingly. Additional information on the connection and operation of three or four lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

## 5.3 Home Screen

Figure 13

Home screen (example DLC DL pro)

Pressing the Home button or tapping the corresponding symbol allows to access the Home screen. Depending on the type of the connected laser head, it offers various sub menus which are described in the following sections.

### 5.3.1 Classic Control

Tap Classic Control to operate the DLC pro in a way similar to the front panel operation of the plug-in modules of the DC 110 Laser Driver Electronics. Please note that the Classic Control is not available for the operation of all types of laser heads.

Figure 14

Classic Control showing operating parameters for CC module and TC module (example)

The display shows two columns with the most important operating parameters of two selectable modules which can be directly adjusted without entering the parameter menu. Tap the top or bottom Right/Left Parameter to assign the rotary knobs to various functions (see section 4.4.2). The operating parameters displayed for each module are a selection from the complete parameter menu (please refer to section 5.14). To select the modules to be displayed, tap the red fields at the top of the touchscreen and choose the desired modules. Press the Load/Save button or tap the corresponding symbol twice to store the settings to the flash memory of the DLC pro. Tap Close to return to the Home screen. NOTE !

DLC TA pro and DLC TA pro AL: For certain alignment procedures, it is necessary to operate Master Oscillator and Tapered Amplifier independently from one another. Please use the Classic Control for this purpose.

### 5.3.2 Information

Tap Information on the Main screen to display various details of your DLC pro on the touchscreen, including serial numbers, version number of the installed firmware and system software, and time of operation of the laser head.

Figure 15

Information screen

You can scroll the lower section of the screen to get access to all functions of the Information screen: System Info

Shows a detailed system summary.

Legal Info

This product incorporates certain third party software. The license and copyright information associated with this software is available after tapping Legal Info.

Service Report

Store a service report to a USB flash drive which first must be inserted at the USB connector on the DLC pro front panel (see section 4.1).

Service Script

Functionality to run a service script provided by TOPTICA: Create a directory \toptica on a FAT formatted USB flash drive. Copy the service script to the \toptica directory on the USB flash drive. Plug the USB flash drive into the USB connector on the DLC pro front panel (please refer to section 4.1).

### 5.3.3 System Messages

Tap System Messages to display current messages on the touchscreen.

Figure 16

System Messages

The system messages are displayed together with the date and the time of the occurrence. If there is a current message, the total number of current system messages is displayed in the bottom right area of the touchscreen next to the small bell symbol (e.g., 0/1 means: 0 messages not confirmed so far, 1 current message total). The description of the warnings and errors is displayed along with the time at which they occurred (see also section 11.16). Tap Reload to refresh the displayed messages. Tap Back to return to the Home screen. NOTE !

A system message is only deleted, if the cause of the malfunction is resolved.

NOTE !

Only current system messages are displayed on the touchscreen. For checking all system messages since the last boot procedure of the DLC pro, you need to use the TOPAS DLC pro PC-GUI. Click on the red Error indicator in the header (please refer to section 6.5) to open the System Messages window (please refer to section 6.6) and select Message Log.

### 5.3.4 Network Settings

Tap Network Settings to enter the menu for network configuration.

Figure 17

Network Settings

In the first window (Figure 17 top left), the current network settings (DHCP status, IP-Address, Netmask, and MAC-Address) are displayed. Please ask your network administrator for information on how to configure the network interface. NOTE !

To connect the DLC pro directly to a computer, disable DHCP on both devices and set the same subnet mask (e.g., 255.255.255.0) and different IP addresses (e.g., 192.168.1.200 and 192.168.1.201).

Back

Tap to close the window and return to the Home screen.

Edit

Tap to open a window (Edit Settings, Figure 17 top right) for changing the network settings.

Edit Settings Window

Tap the setting to be changed. A numerical editor (Figure 17 bottom right) opens to change the value. Tap OK to use the new setting or Cancel to discard the change.

Enable DHCP

When selected, the device’s network adapter configuration is set for automatic setup by a DHCP server. In order to use the DHCP mechanism, tap OK. When not selected, the device’s network adapter configuration is set to a static IP configuration. The desired IP address and netmask have to be provided in the IP-address and Netmask field, respectively. In order to use the new static address, click OK.

IP-Address

Tap to open a numerical editor for setting up a fixed IP address. Enter a valid IPv4 address in the format “xxx.xxx.xxx.xxx”. (e.g., "192.168.51.247"). Tap OK to use the new setting or Cancel to discard the change.

Netmask

Tap to open a numerical editor for setting up a fixed subnet mask. Enter a valid IPv4 netmask in the format “xxx.xxx.xxx.xxx”. (e.g., "255.255.255.0"). Tap OK to use the new setting or Cancel to discard the change.

OK

Tap OK to apply the new settings.

Cancel

Tap to discard the new setting.

### 5.3.5 Laser Config

Tap Laser Config to display a menu for basic laser head parameters on the touchscreen. Please note that the Laser Config menu is not available for all types of laser heads.

Figure 18

Laser Config screen (example DLC DL pro/DLC DFB pro)

NOTE !

DLC TA pro/-AL, DLC BoosTA pro and Seed Laser + BoosTA pro Combination: Configuration of the laser head is only possible in the TOPAS DLC pro PC-GUI (Laser Menu > Laser Config).

The Laser Config screen allows the configuration of the selected laser head (Laser 1 .. 4 buttons, see section 5.11). Depending on the laser type, some or all of these values can be changed. You can adjust the settings directly without entering the parameter menu. For TOPTICA laser heads, please refer to the corresponding Production and Quality Control Data Sheet for the proper operating parameters. See next page for an example.

Example: Basic Laser Head Current Parameters for Laser 1: Maximum Current Parameter: laser1:dl:cc:current-clip Use Tuning Clip Checking the box limits the laser diode current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only). CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip boxes for diode laser and amplifier (depending on the connected laser head) is mandatory before performing a motor scan. This avoids damage to the laser diode (and the amplifier) during a motor scan. Set Current Maximum Voltage Laser Diode Polarity

NOTE !

Iset Umax 0: Negative LD polarity 1: Positive LD polarity

Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

Basic Laser Head Temperature Parameters for Laser 1: Set Temperature Tset Press the Load/Save button or tap the corresponding symbol twice to store the settings to the flash memory of the DLC pro.

### 5.3.6 Optimization (DLC CTL)

Tap Optimization to access the optimization routines for SMILE parameters and FLOW on the touchscreen. For detailed information on SMILE and FLOW, please refer to the CTL manual. CAUTION ! Do not change any operating parameters (e.g., Iset, T set) of the laser during SMILE or FLOW optimization. NOTE !

Dual- or Quad-Laser-Operation: The optimization routine only affects the laser selected by the Laser 1 .. 4 button (see section 5.11).

NOTE !

Normally DLC pro saves the optimized parameters automatically after a SMILE or FLOW optimization is performed. If a new laser head has been connected to the DLC pro and the new system configuration has not yet been saved by pressing the Save button, the resulting SMILE and FLOW parameters are not automatically saved as they would not be compatible with the operation parameters of the previous laser head. In this case press the Save button before performing a SMILE or FLOW optimization.

NOTE !

The SMILE or FLOW buttons may be grayed, if a SMILE or FLOW optimization is not possible, e.g. due to an active power stabilization. During a SMILE or FLOW optimization, an active wide scan, scan or ARC is temporarily deactivated.

Figure 19

Optimization screen (DLC CTL)

SMILE

Tap SMILE to start an optimization of SMILE parameters. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the CTL manual.

FLOW

Tap FLOW to start an optimization of the laser threshold and subsequently the SMILE optimization. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the CTL manual.

Abort

Tap Abort to stop the optimization. The previous SMILE/FLOW parameter values are resumed.

Back

Tap Back to return to the Home screen.

### 5.3.7 Optimization TA pro AL

NOTE !

The TA pro AL laser head is equipped with the AutoAlign option (motorized mirrors). Depending on the laser head setup, some optimization routines may not be available.

NOTE !

Dual- or Quad-Laser-Operation: The optimization routine only affects the laser selected by the Laser 1 .. 4 button (see section 5.11).

Tap Optimization to access the optimization routines for laser beam alignment on the touchscreen. For detailed information, please refer to the TA pro AL manual.

Figure 20

Optimization screen (DLC TA pro AL, example)

Probe Power

Only available with DLC TA pro AL laser in DL pro and TA pro configuration. Tap Probe Power to start an optimization of the probe laser beam power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the TA pro AL manual.

Amp. Power

Only available with DLC TA pro AL laser in TA pro and BoosTA pro configuration. Tap Amp. Power to start an optimization of the Tapered Amplifier power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the TA pro AL manual.

Fiber Power

Only available with DLC TA pro AL laser in TA pro and BoosTA pro configuration. Tap Fiber Power to start an optimization of the fiber output power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the TA pro AL manual.

Fiber Power Advanced

When selected, a combination of optimization algorithms is performed. For details, please refer to the TA pro AL manual.

All Stages

Tap All Stages to start the available optimization procedures in a preset sequence:

1.
Probe Power optimization

2.
Amp. Power optimization

3.
Fiber Power optimization

Abort

Tap Abort to stop an optimization. The system behavior at Abort can be set by the in the context parameter menu (parameter Power Optimization > XXX Stage > Servo Return at Abort).

Back

Tap Back to return to the Home screen.

The parameters for the optimization routines are set in the context parameter menu (please refer to section 5.3.7.1) which is available after pressing the Parameter button or tapping the corresponding symbol.

5.3.7.1

Optimization Context Parameter Menu

The parameters for the optimization routines are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button with the Optimization screen selected. On the following pages, detailed information about each accessible parameter is provided. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Power Optimization Seed Probe Stage (only DLC TA pro AL laser in DL pro and TA pro config.) Settings for seed probe stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:dl:power-optimization:stage1:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:dl:power-optimization:stage1:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] If the power has decreased by this margin at the end of the optimization routine, action is taken as defined by the parameter Servo Return at Power Decrease. laser1:dl:power-optimization:stage1:regress-tolerance (real) Amplifier Stage (only DLC TA pro AL laser in TA pro and BoosTA pro config.) Settings for amplifier stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:dl:power-optimization:stage2:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:dl:power-optimization:stage2:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:dl:power-optimization:stage2:regress-tolerance (real)

Fiber Stage (only DLC TA pro AL laser in DL pro and TA pro config.) Settings for fiber stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:dl:power-optimization:stage3:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:dl:power-optimization:stage3:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:dl:power-optimization:stage3:regress-tolerance (real) Fiber Advanced Stage (only DLC TA pro AL laser in DL pro and TA pro config.) Settings for fiber advanced stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:dl:power-optimization:stage4:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:dl:power-optimization:stage4:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:dl:power-optimization:stage4:regress-tolerance (real)

Servo Positions Seed Probe Stage (only DLC TA pro AL laser in DL pro and TA pro config.) Servo positions of seed probe stage Servo Position PROBE-1-H Set horizontal position of first mirror laser1:dl:servo:probe1-hor:value (integer) Servo Position PROBE-1-V Set vertical position of first mirror laser1:dl:servo:probe1-vert:value (integer) Amplifier Stage Servo positions of amplifier stage Servo Position TA-1-H Set horizontal position of first mirror laser1:dl:servo:ta1-hor:value (integer) Servo Position TA-1-V Set vertical position of first mirror laser1:dl:servo:ta1-vert:value (integer) Servo Position TA-2-H Set horizontal position of second mirror laser1:dl:servo:ta2-hor:value (integer) Servo Position TA-2-V Set vertical position of second mirror laser1:dl:servo:ta2-vert:value (integer) Fiber Stage Servo positions of fiber stage Servo Position FIBER-1-H Set horizontal position of first mirror laser1:dl:servo:fiber1-hor:value (integer) Servo Position FIBER-1-V Set vertical position of first mirror laser1:dl:servo:fiber1-vert:value (integer)

### 5.3.8 Optimization (DLC DL-/TA-SHG/FHG pro)

NOTE !

This Optimization screen is only available for DLC DL-/TA-SHG/FHG pro systems with the AutoAlign option (motorized mirrors). Depending on the laser head setup, some optimization routines may not be available.

Tap Optimization to access the optimization routines for laser beam alignment on the touchscreen. For detailed information, please refer to the DL-/TA-SHG/FHG pro manual.

Figure 21

Optimization screen (example DLC DL-/TA-FHG pro system with AutoAlign option)

Amp. Power

Only available with DLC TA-SHG/FHG pro systems. Tap Amp. Power to start an optimization of the Tapered Amplifier power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the DL-/TA-SHG/FHG pro manual.

SHG Power

Tap SHG Power to start an optimization of the SHG power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the DL-/TA-SHG/FHG pro manual.

FHG Power

Only available with DLC DL-/TA-FHG pro systems. Tap FHG Power to start an optimization of the SHG power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the DL-/TA-SHG/FHG pro manual.

Fiber Power

Only available on systems with option FiberMon. Tap Fiber Power to start an optimization of the fiber output power. The progress bar on the touchscreen indicates the status of the optimization. For details, please refer to the DL-/TA-SHG/FHG pro manual.

SHG Power Advanced

When selected, a combination of optimization algorithms is performed. For details, please refer to the DL-/TA-SHG/FHG pro manual.

All Stages

Tap All Stages to start the available optimization procedures in a preset sequence:

1.
Amplifier Power optimization (only DLC TA-SHG/FHG pro)

2.
SHG Power optimization

3.
FHG Power optimization (only DLC DL-/TA-FHG pro)

4.
Fiber Power optimization (only with option FiberMon)

Abort

Tap Abort to stop an optimization. The system behavior at Abort can be set by the in the context parameter menu (parameter Power Optimization > XXX Stage > Servo Return at Abort).

Back

Tap Back to return to the Home screen.

The parameters for the optimization routines are set in the context parameter menu (please refer to section 5.3.8.1) which is available after pressing the Parameter button or tapping the corresponding symbol.

5.3.8.1

Optimization Context Parameter Menu

The parameters for the optimization routines are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button with the Optimization screen selected. On the following pages, detailed information about each accessible parameter is provided. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Power Optimization Amplifier Stage (only DLC TA-SHG/FHG pro) Settings for amplifier stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage1:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage1:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] If the power has decreased by this margin at the end of the optimization routine, action is taken as defined by the parameter Servo Return at Power Decrease. laser1:nlo:power-optimization:stage1:regress-tolerance (real) SHG Stage Settings for SHG stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage2:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage2:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:nlo:power-optimization:stage2:regress-tolerance (real)

SHG Advanced Stage Settings for SHG Advanced stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage3:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage3:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:nlo:power-optimization:stage3:regress-tolerance (real) FHG Stage Settings for FHG stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage5:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage5:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:nlo:power-optimization:stage5:regress-tolerance (real) Fiber Stage (only with option FiberMon) Settings for fiber stage Servo Return at Abort Enable or disable servo return at abort [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage4:restore-on-abort (boolean) Servo Return at Power Decrease Servo return behavior at power decrease [1: enabled], [0: disabled] laser1:nlo:power-optimization:stage4:restore-on-regress (boolean) Optimization Margin Enter failure margin for optimization in [%] laser1:nlo:power-optimization:stage4:regress-tolerance (real)

Servo Positions Amplifier Stage (only DLC TA-SHG pro) Servo positions of amplifier stage Servo Position TA-1-H Set horizontal position of first mirror laser1:nlo:servo:ta1-hor:value (integer) Servo Position TA-1-V Set vertical position of first mirror laser1:nlo:servo:ta1-vert:value (integer) Servo Position TA-2-H Set horizontal position of second mirror laser1:nlo:servo:ta2-hor:value (integer) Servo Position TA-2-V Set vertical position of second mirror laser1:nlo:servo:ta2-vert:value (integer) SHG Stage Servo positions of SHG stage Servo Position SHG-1-H Set horizontal position of first mirror laser1:nlo:servo:shg1-hor:value (integer) Servo Position SHG-1-V Set vertical position of first mirror laser1:nlo:servo:shg1-vert:value (integer) Servo Position SHG-2-H Set horizontal position of second mirror laser1:nlo:servo:shg2-hor:value (integer) Servo Position SHG-2-V Set vertical position of second mirror laser1:nlo:servo:shg2-vert:value (integer) FHG Stage Servo positions of FHG stage Servo Position FHG-1-H Set horizontal position of first mirror laser1:nlo:servo:fhg1-hor:value (integer) Servo Position FHG-1-V Set vertical position of first mirror laser1:nlo:servo:fhg1-vert:value (integer) Servo Position FHG-2-H Set horizontal position of second mirror laser1:nlo:servo:fhg2-hor:value (integer) Servo Position FHG-2-V Set vertical position of second mirror laser1:nlo:servo:fhg2-vert:value (integer)

Fiber Stage (only with option FiberMon) Servo positions of fiber stage Servo Position Fiber-1-H Set horizontal position of first mirror laser1:nlo:servo:fiber1-hor:value (integer) Servo Position Fiber-1-V Set vertical position of first mirror laser1:nlo:servo:fiber1-vert:value (integer) Servo Position Fiber-2-H Set horizontal position of second mirror laser1:nlo:servo:fiber2-hor:value (integer) Servo Position Fiber-2-V Set vertical position of second mirror laser1:nlo:servo:fiber2-vert:value (integer)

### 5.3.9 Stabilization (DLC TA-SHG/FHG pro)

NOTE !

The Stabilization screen is only available for DLC TA-SHG/FHG pro systems.

Tap Stabilization to access the screen for the stabilization of various power levels within the laser system during operation by changing the Tapered Amplifier current. For detailed information, please refer to the DL-/TA-SHG/FHG pro manual.

Figure 22

Stabilization screen (example DLC TA-SHG pro)

Rotary Knobs:

- 
- 
- 
- 
Top-left: Bottom-left: Top-right: Bottom-right:

Pow P: P gain for power stabilization [mA/mW] Pow Gain: Overall gain for power stabilization Pow I: I gain for power stabilization [mA/mW/ms] Pow Set Level: Desired power level for the stabilization [mW]

Further parameters for the stabilization can be set in the context parameter menu (please refer to section 5.3.9.1) which is available after pressing the Parameter button or tapping the corresponding symbol. Tap Stabilization On/Off to enable/disable the power stabilization with the chosen settings. NOTE !

If the input channel of External Power is changed during a running power stabilization, the power stabilization is switched OFF.

Display Mode Selection The display of the touchscreen changes depending on the selected display mode. To select the display mode, tap the corresponding symbol.

Show all: Displays all available data starting from the latest DLC pro boot procedure. The maximum Memory Depth (maximum time interval of displayed signals) depends on the setting of Power Stabilization > Sampling Interval in the context parameter menu.

Show latest: Displays the latest signals within the time range selected in the context parameter menu (Power Stabilization > Display Range).

Show chosen: Pinch and spread the graph on the display to choose a time range freely. This display mode is automatically switched to from the other display modes if a graph is pinched or spread. Delete: Deletes all stored signal data and clears the touchscreen display.

Trace Scaling: Tap to select the desired trace scaling.

Input Channel Selection Tap the symbol and select the input channel to be stabilized to the desired Pow Set Level adjusted at the bottom-right rotary knob. External

The External Power is stabilized with the chosen settings

Amp.

The Amplifier Power is stabilized with the chosen settings.

SHG

The SHG Power is stabilized with the chosen settings.

FHG

The FHG Power is stabilized with the chosen settings (only DLC TA-FHG pro).

Fiber

The Fiber Power is stabilized with the chosen settings (only with option FiberMon).

5.3.9.1

Stabilization Context Parameter Menu

The parameters for power stabilization are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button with the Stabilization screen selected. On the following pages, detailed information about each accessible parameter is provided. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Power Stabilization Enable Power Stabilization Enable or disable power stabilization [1: enabled], [0: disabled] laser1:power-stabilization:enabled (boolean) Differential Gain Enter diff. gain for power stabilization in [mA/mW*µs] laser1:power-stabilization:gain:d (real) Hold Output Current on Unlock Select unlock behavior of output channel [1: enabled], [0: disabled] laser1:power-stabilization:hold-output-on-unlock (boolean) Sign Positive Select on for positive, off for negative [1: on], [0: off] laser1:power-stabilization:sign (boolean) Actual Level Actual power level [mW] laser1:power-stabilization:input-channel-value-act (real) Window

Enable Stabilization Detection Enable or disable window for power stabilization [1: enabled], [0: disabled] laser1:power-stabilization:window:enabled (boolean) Window Level Enter level for out-of-stabilization detection Level in [mW] laser1:power-stabilization:window:level-low (real) Window Hysteresis Hysteresis between out-of- and in-lock stabilization value Hysteresis in [mW] laser1:power-stabilization:window:level-hysteresis (real)

Sampling Interval Enter time interval between two data points in [s] Display Range Enter time interval for latest data in [min]

External Power External Power settings Physical Channel Select physical input for external power laser1:pd-ext:input-channel Photo Diode Value Photo diode voltage of the physical channel [V] laser1:pd-ext:photodiode (real) Calibration Factor Enter calibration factor for external power laser1:pd-ext:cal-factor (real) Calibration Offset Enter calibration offset for external power laser1:pd-ext:cal-offset (real) Monitor Diodes Amplifier Power (only DLC TA-SHG pro) Read actual amplifier power Amplifier power in [mW] laser1:nlo:pd:amp:power SHG Power Read actual SHG power SHG power in [mW] laser1:nlo:pd:shg:power FHG Power Read actual FHG power FHG power in [mW] laser1:nlo:pd:fhg:power Fiber Power (only with option FiberMon) Read actual fiber power Fiber power in [mW] laser1:nlo:pd:fiber:power External Power Read actual external power External power in [mW] laser1:pd-ext:power Trace Scaling Left/Red Y Minimum Enter Ymin for red curve Reasonable values depend on the selected power Left/Red Y Maximum Enter Ymax for red curve Reasonable values depend on the selected power Right/Blue Y Minimum Enter Ymin for blue curve Reasonable values depend on the selected signal Right/Blue Y Maximum Enter Ymax for blue curve Reasonable values depend on the selected signal

Trace Selection Right/Blue Signal Select signal for blue curve [„None"] [„Seed Power (mW)", laser1:nlo:pd:dl:power] [„Amp. Power (mW)", laser1:nlo:pd:amp:power] [„SHG Power (mW)“, laser1:nlo:pd:shg:power] [„FHG Power (mW)“, laser1:nlo:pd:fhg:power] (only DLC TA-FHG pro) [„Fiber Power (mW), laser1:nlo:pd:fiber:power] (only with option FiberMon) [„External Power (mW)“, laser1:pd-ext:power] [„Amp. Current (mA)", laser1:amp:cc:current-act] [„SHG Intra-Cav. Signal (V)", laser1:nlo:pd:shg-int:photodiode] [„SHG Cav. Rej. Signal (V)", laser1:nlo:pd:shg-pdh-dc:photodiode] [„FHG Intra-Cav. Signal (V)", laser1:nlo:pd:fhg-int:photodiode] (only DLC TA-FHG pro) [„FHG Cav. Rej. Signal (V)", laser1:nlo:pd:fhg-pdh-dc:photodiode] (only DLC TA-FHG pro) [„SHG PC Voltage (V)", laser1:nlo:shg:pc:voltage-act] [„FHG PC Voltage (V)", laser1:nlo:fhg:pc:voltage-act] (only DLC TA-FHG pro) [„PowerLock Set Level (mW)", laser1:power-stabilization:setpoint]

5.4

Scan/Lock Mode

NOTE !

To utilize the DLC pro Lock function modes, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence is already installed. Otherwise a 30-day trail licence is provided on the USB flash drive in the Options Folder. Dual- or Quad-Laser-Operation: With a single Lock option installed, in combination with the Dual- or Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

NOTE !

Without a Lock option installed, only the scan and power stabilization functions of the Scan/Lock mode will be accessible.

NOTE !

DLC pro with PDH module: The PDH module itself can be used without Lock option license. The Error signals are applied to the SMB-connectors of the PDH module (rear side of the DLC pro) and can be used together with an external controller. Operation parameters of the PDH module are set at the rotary knobs in PDH Ch1/PDH Ch2 function mode and in the context parameter menu (please refer to section 5.4.8).

NOTE !

A DLC DL-SHG/FHG pro is not equipped with power stabilization functionality, as the feedback onto the Master Oscillator current would disturb the lock of the SHG/FHG cavity.

### 5.4.1 Function Modes

Depending on the selected function mode, the assignment of the rotary knobs (please refer to section 5.4.7) and the display might change. To select the desired function mode, tap the corresponding symbol (please refer to Figure 23). Scan: Parameters for the scan function.

Lockpoint: Parameters for identifying lockpoint candidates. Tap the desired Lockpoint Candidate to select it. The selection is indicated by an additional red circle as shown in Figure 24. NOTE !

When Lock Settings > Lock Without Lockpoint is enabled in the context parameter menu, no lockpoint candidates are displayed.

ReLock: Parameters for the ReLock function (please refer to section 5.4.11). NOTE !

By default, the Lockpoint function mode is active. To switch to ReLock function mode, tap Lockpoint and select ReLock.

PID 1, PID 2: Parameters of the PID controllers.

NOTE !

By default, PID 1 is active. To select PID 2, tap PID 1 and select PID 2.

LIR: Lock-In parameters for the Top of Fringe lock type.

PDH Ch1, PDH Ch2: PDH parameters, e.g. for the Top of Fringe PDH lock type (only with PDH module). NOTE !

By default, PDH Ch1 is active. To select PDH Ch2, tap PDH Ch1 and select PDH Ch2.

Power: Parameters for the power stabilization.

FALC 1.. 4: FALC pro module operating parameters (only with FALC pro module connected).

NOTE !

By default, the Power function mode is active. To switch to FALC X function mode, tap Power and select the desired FALC X. The DLC pro supports up to four FALC pro modules in a CAN link chain.

PFD 1.. 4: PFD pro module operating parameters (only with PFD pro module connected).

NOTE !

By default, the Power function mode is active. To switch to PFD X function mode, tap Power and select the desired PFD X. The DLC pro supports up to four PFD pro modules in a CAN link chain.

### 5.4.2 Display Modes

The display of the touchscreen changes depending on the selected display mode. To select the display mode, tap the corresponding symbol (please refer to Figure 23). xy: Signals (Y-direction) are plotted against the scan voltage of the laser (X-direction). t (Time): Signals (Y-direction) are plotted against time (X-direction).

f (Frequency): The fast Fourier transformation of the time-dependent signal (Y-direction) is plotted against the frequency (X-direction). Trace Scaling: Tap to select the desired trace scaling.

Up to two signal traces, referred to as Input Trace (red) and Auxiliary Trace (blue) may be displayed on the touchscreen in xy display mode, the axis labelling is displayed in the corresponding color. The input channels of the two signals can be selected in the parameter menu which appears on the touchscreen after pressing the Parameter button in Scan/Lock mode (please refer to Figure 23). Depending on the setting (Input/Auxiliary trace scaling), the graphs are autoscaled in Y-direction to the full display size or they can be free scaled by gestures (pinch and spread) on the touchscreen. The graph can also be fixed to its current size. The zero level in X and Y-direction is displayed as a broken line. On the axis the distance to the zero level is indicated by the offset value and the direction to the zero level is indicated by the small triangle. The other value at the axis indicates the scaling per division.

### 5.4.3 Scan Function Mode

The internal grating of a tunable laser head can be slightly moved by a piezo element for wavelength tuning (scanning). A variable voltage (Scan Amplitude) is added to a constant voltage (Scan Offset). In Scan function mode, scanning can be enabled/disabled, and all parameters for scanning are set. The scan of the laser as well as the signals depending on the scan (e.g., an absorption signal) can be displayed on the touchscreen.

Figure 23

Touchscreen in Scan function mode (example)

Enter Scan function mode by pressing the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 23 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols which appear after tapping. Select and select the Scan function mode field at the bottom of the touchscreen. The display as well as the assignment of the rotary knobs change as needed for setting the most important scan parameters and to optimize the mode hop free tuning of the selected ECDL laser (Laser 1 .. 4 buttons, see section 5.11). Further scan and display parameters are set in the context parameter menu (please refer to section 5.4.8) which appears on the touchscreen after pressing the Parameter button in Scan/Lock mode.

NOTE !

Scanning continues as long as the scan is enabled even if you leave Scan/Lock mode. Enabling/disabling the scan is done by tapping the symbol at the top of the touchscreen (gray: scan disabled, red: scan enabled) or in the PC-GUI. Please note that the scan can only be enabled when the laser is not locked (see section 5.4.5).

For optimizing the scan, the Feed Forward allows to apply a ramp proportional to the piezo scan ramp (which scans the laser frequency) to the laser diode current. This leads to a change of the refractive index n of the semiconductor material in the laser diode and thus improves the mode-hop free tuning of the laser. The procedure for setting the Feed Forward to eliminate mode hops is described in the laser head manual. NOTE !

For DFB pro or DL pro BFY laser heads, and laser systems with a DFB pro Master Oscillator, the Feed Forward current ramp is proportional to the temperature scan ramp.

In addition, you can optimize the scan by changing the laser temperature (Set Temperature). As desired for optimization, assign the top-left rotary knob (please refer to section 5.4.7.1).

NOTE !

The Set Current comprises the Feed Forward part dependent on the Scan Offset, not the part dependent on the Scan Amplitude. Due to this, the displayed Set Current changes when the Scan Offset is adjusted. The Actual Current in addition comprises the time-dependent Feed Forward part of the Scan Amplitude and possibly additional offsets from PID outputs. To display the actual laser current, select Actual Current as top-eft parameter (see section 4.4.2). With a large Feed Forward factor, the set current may also be restricted to values below the clip-limit.

NOTE !

Additional offsets to the Scan Offset e.g., due to PID settings or Analog Remote Control (ARC) may lead to a shifting of the displayed signal in X-direction.

NOTE !

If the scan amplitude is set to values below a minimal amplitude the signal trace will collapse to a vertical line as no scan is generated any more. Please note that the scan may be switched off by tapping the symbol at the top of the touchscreen.

On the touchscreen, the scan-dependent signal is displayed in Y-direction. The parameters Scan Offset and Scan Amplitude are displayed in the bottom-left and bottom-right corner of the display and can be changed by the corresponding rotary knobs. Changes done at the knobs are reflected by the graphical display and changes made with touch gestures on the display are reflected in the numbers in the corners. For example, dragging the display graph right/left changes the scan offset while pinching the graph in X-direction increases the scan amplitude.

### 5.4.4 Synchronized Scanning of Lasers

At a DLC pro for Dual- or Quad-Laser-Operation (see section 1.3) the scan of all connected lasers can be synchronized. The settings for the synchronization can be performed in the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9) or via software commands (see section 11.14). laser-common:scan:sync-laser1 .. 4 laser-common:scan:frequency laser-common:scan:sync laser-common:scan:save

Select the lasers to be synchronized. Enter the common scan frequency. When the command is executed, the scan generators of all selected lasers are set to the common scan frequency. Save the scan-synchronization settings to be used after the next DLC pro boot procedure.

When the scan is enabled by tapping the symbol at the top of the touchscreen, the scans of the selected lasers then are started simultaneously and the lasers are scanned with the same frequency, and with zero relative phase-shift.

### 5.4.5 Lock Function Modes

NOTE !

To utilize the DLC pro Lock function modes, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence is already installed. Otherwise a 30-day trail licence is provided on the USB flash drive in the Options Folder. Dual- or Quad-Laser-Operation: With a single Lock option installed, in combination with the Dual- or Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

For higher demands on frequency stability, the laser frequency can be locked actively to the wavelength of interest, such as atomic or molecular resonances and cavities. Proportional-Integral-Differential (PID) controllers are used to stabilize the laser frequency to a reference. Locking the laser to a specific wavelength is based on a spectroscopic signal provided by the experimental setup which serves as a reference (Lock Input signal). The laser can be locked to a slope or to an extremum of the Lock Input signal. The DLC pro provides the scan to find the resonance and lockpoint candidates, derives the Error signal for the Top of Fringe lock type via a lock-in detection unit, and provides two separate PID controllers for the feedback loop. In addition, the ReLock function (please refer to section 5.4.11) is provided to detect out-of-lock states of the laser to reset the PID controller(s) and to relock the system.

Figure 24

Touchscreen in Lockpoint function mode (example). Lockpoint candidates for Top of Fringe lock type shown

Enter the desired function mode for locking (please refer to section 5.4.1) by pressing the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 24 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols which appear after tapping. Select and select the desired function mode field at the bottom of the touchscreen. The display as well as the assignment of the rotary knobs (please refer to section 5.4.7) change as needed for setting the most important lock parameters of the selected ECDL laser (Laser 1 .. 4 buttons, see section 5.11).

Further lock and display parameters are set in the context parameter menu (please refer to section 5.4.8) which appears on the touchscreen after pressing the Parameter button in Scan/Lock mode. Please refer to sections 5.4.9 and 5.4.10 for examples on locking. NOTE !

If you want to lock without automatically derived lockpoint candidates, please enable Lock Settings > Lock Without Lockpoint in the context parameter menu).

### 5.4.6 Power Stabilization Function Mode

The DLC pro Power function mode allows the stabilization of various power stages (PowerLock) during operation by changing the laser diode or amplifier current, dependent on the laser head. The controls for the power stabilization are accessible at the DLC pro front panel in Scan/Lock mode after tapping the Power symbol at the bottom of the touchscreen. Further power stabilization parameters are set in the context parameter menu (please refer to section 5.4.8) which appears on the touchscreen after pressing the Parameter button in Scan/Lock mode. Dependent on the laser head, you can choose between the stabilization of the following power stages by selecting the context parameter Power Stabilization > Input Channel: DL pro:

External Power

Laser diode current is controlled

DFB pro/DL pro BFY: External Power

Laser diode current is controlled

CTL:

External Power, CTL Power

Laser diode current is controlled

TA pro:

External Power, Amp. Power

Amplifier current is controlled

TA pro AL: DL pro config.: External Power TA pro/ BoosTA pro config.: External Power, Amp. Power

Laser diode current is controlled Amplifier current is controlled

TA-SHG pro:

External Power, Amp. Power, Amplifier current is controlled SHG Power, Fiber Power (only with option FiberMon)

TA-FHG pro:

External Power, Amp. Power, Amplifier current is controlled SHG Power, FHG Power, Fiber Power (only with option FiberMon)

TOPO smart

no power stabilization available

TOPO

no power stabilization available

NOTE !

For stabilization of the External Power stage, please refer to section 5.4.6.1 for configuration of the input channel and calibration of the external photo diode.

To change the power level of the selected stage, adjust Pow Set Level by the bottom-right rotary knob. Gain parameters for the stabilization can also be adjusted at the rotary knobs. The power stabilization is switched on and off by pressing the Stabilization On/Off button or by tapping the corresponding symbol (see section 5.9). When the stabilization is switched off, you can choose whether the laser diode or amplifier current shall stay at its current value (1) or return to the value before the stabilization was switched on (0) by setting the context parameter Power Stabilization > Hold Output Current on Unlock. NOTE !

If the input channel for External Power is changed (see section 5.4.6.1) during a running power stabilization, the power stabilization is switched OFF.

NOTE !

DLC TA-SHG/FHG pro: If a power stabilization loop to the SHG/FHG or fiber monitor photo diode is active and the SHG/FHG cavity falls out of lock, the Tapered Amplifier current will be set to its maximum value allowed by laser1:amp:cc:current-clip. Once the SHG/FHG cavity returns into lock, this may result in an unexpectedly high SHG/FHG output power for a short time, until the SHG/FHG power has returned to its Pow Set Level, again.

NOTE !

DLC TA-SHG/FHG pro: For convenient Power Stabilization it is recommended to use the Stabilization screen (see section 5.3.9). For detailed information, please see the power stabilization example in the DL-/TA-SHG/FHG pro manual.

5.4.6.1

Configuration of the External Power Stabilization

DANGER ! Do not look into the exiting beam of the laser head as the output can exceed the limits for class 1 specified by the US laws 21 CFR 1040.10 and 2 CFR 1040.11 and the Laser Safety Standards EN 60825-1:2014+A11:2021, IEC 60825-1:2014. Take precautions to eliminate exposure to a direct or reflected beam. Always wear appropriate laser safety goggles. When External Power is selected as input channel for the power stabilization, the laser diode or amplifier current (dependent on the laser head) is stabilized onto the signal of an external photo diode. Please follow the steps noted below to configure an External Power stabilization (configuration is also possible via the TOPAS DLC pro PC-GUI).

1.
The external photo diode can be connected to one of the four BNC-connectors (Fine 1/2, Fast 3/4) on the DLC pro front panel. Please select the appropriate BNC-connector in the context parameter menu with the Scan/Lock screen selected (Power Stabilization > External Power > Physical Channel).

2.
Connect the external photo diode to the selected BNC-connector on the DLC pro front panel.

3.
Position and align the external photo diode in your experimental beam path as desired.

4.
Switch ON laser emission. Check in the DLC pro Scan/Lock screen context parameter menu whether the Power Stabilization > External Power > Photo Diode Value is between 0.5 .and 4 V. If the value is above 4 V, please use an optical attenuator to reduce the incident laser power. If the value is below 0.5 V, please amplify the photo diode signal in order to improve the signal-to-noise ratio.

5.
Switch OFF laser emission. Now enter the dark voltage Power Stabilization > External Power > Photo Diode Value (with the laser switched off) into Power Stabilization > External Power > Calibration Offset. Check that Power Stabilization > Actual Level now shows approximately 0 mW.

6.
Switch ON laser emission. Determine the laser power in front of the external photo diode with a suitable (thermal or calibrated) power meter. Divide the measured power in mW by the voltage calculated by (Power Stabilization > External Power > Photo Diode Value minus Power Stabilization > External Power > Calibration Offset) and enter the resulting value in the parameter Power Stabilization > External Power > Calibration Factor. Now, the external photo diode is calibrated and Power Stabilization > Actual Level shows the actual laser power at the external photo diode.

7.
Save the configuration by pressing the Load/Save button on the DLC pro front panel twice.

5.4.6.2

Setup of the Power Stabilization (Example Amp. Power)

Please follow the description below for setting-up and optimizing a power stabilization.

1.
Enable the desired laser (Laser 1 .. 4 buttons, see section 5.11) and switch on laser emission by pressing the Emission button on the DLC pro front panel.

2.
Select the Power function mode by tapping the Power symbol on the touchscreen in Scan/Lock mode.

3.
Select the desired stabilization stage, Amp. Power in this example (context parameter: Power Stabilization > Input Channel).

4.
Select the desired behavior of the amplifier current when the stabilization is switched off (context parameter: Power Stabilization > Hold Output Current on Unlock.

5.
Select the t (time) display mode and disable the scan by tapping the symbols at the top of the touchscreen. It is recommended to select Display Settings > Trace Selection > Auxiliary Trace Signal > None for an easier adjustment of the power stabilization. The PowerLock input signal is displayed as Input Trace (red) by default.

6.
Adjust the desired Pow Set Level at the bottom-right rotary knob. Select Autoscale as trace scaling for the Input Trace. Zoom out by pinching on the touchscreen until both, the Input Trace and the red Power Set Level line are displayed.

7.
Set the corner parameters Pow I and Pow P to zero with the corresponding rotary knobs. Set Pow D to zero in the context parameter menu (Power Stabilization > Differential Gain) Set Pow Gain to 1 as a start value.

8.
Tap Stabilization On/Off (see section 5.9) to enable the power stabilization.

9.
Increase Pow I until the stabilization is working. This is indicated on the touchscreen by overlapping of the red Input Trace with the red Power Set Level line. Increase Pow I further until the Input Trace shows oscillation. Then decrease Pow I to well below the oscillation threshold. DLC TA pro/-AL and DLC TA-SHG/FHG pro: For some values of the PowerLock signal, it may not be possible to let the power signal oscillate by increasing Pow I. In this case we recommend that you work with the highest Pow I possible.

10.
Perform step 9 for Pow P adjustment. DLC TA pro/-AL and DLC TA-SHG/FHG pro: For some values of the PowerLock signal, it may not be possible to let the power signal oscillate by increasing Pow P. In this case we recommend that you work with the highest Pow P possible.

11.
The differential gain will have only limited influence on the power stabilization performance. Optionally perform step 9 with the parameter Power Stabilization > Differential Gain in the context menu.

12.
Once properly set up, the power stabilization can be enabled/disabled by tapping the Stabilization On/Off symbol. The Pow Set Level can be modified at the bottom-right rotary knob. Please readjust the PID parameters, if necessary.

### 5.4.7 Scan/Lock Mode Rotary Knob Assignments

The functions assigned to the rotary knobs depend on the selected function mode.

5.4.7.1

Scan Rotary Knobs

Parameter settings for the Scan function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.4.7.2

As selected in the drop-down menu (see section 4.4.2). Available corner parameters depend on the laser system: Feed Forward or Master Feed Forward [mA/V] [mA/K] only DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator Feed Forward (PC > CC) [mA/V] only DL pro SMC with single mode control Feed Forward (CC > PC) [V/mA] only DL pro SMC with single mode control Set Temperature or Master Set Temperature [° C] for optimization, Display of Actual Current or Master Actual Current [mA]. Amplifier Set Current [mA]. Amplifier Actual Current [mA]. Amplifier Feed Forward [mA/V]. Scan Frequency [Hz]. Set Wavelength [nm] (only DLC CTL). Scan Offset [V] if laser is scanned with piezo. This parameter is displayed in X-direction on the touchscreen. Laser Diode Set Current [mA]. Scan Amplitude [V] if laser is scanned with piezo. This parameter is displayed in X-direction on the touchscreen.

Lockpoint Rotary Knobs

Parameter settings for the Lockpoint function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
Lock Level [V]: Voltage level for Side of Fringe lockpoint with or without lockpoint candidates. Side of Fringe lock type: In the xy signal display mode, lockpoint candidates are displayed where the signal crosses the displayed Lock Level. Top of Fringe lock type: no function. Comp. Offset [V]: Only when Side of Fringe as Lock Type is selected in the context parameter menu and FALC pro module is connected. Set compensation offset voltage for Side of Fringe lockpoint candidates. PID1/2 Gain: Overall gain factor of the selected PID controller. Laser Diode Set Current [mA]. P/N Tolerance [V]: If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by adjusting the P/N Tolerance rotary knob correctly for the signal and signal-to-noise ratio used.

5.4.7.3

ReLock Rotary Knobs

Parameter settings for the ReLock function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.4.7.4

No function. Hysteresis [V]: Difference between the <Level High> or <Level Low> voltage that determines the out-of-lock state and the signal voltage that determines whether the laser can be locked again. If the signal has left the ReLock window defined by <Level High> and <Level Low>, the corresponding PID controller output is frozen. To reactivate the PID controller, the input signal must be within an "inner" window defined by (<Level High> - <Hysteresis>) and (<Level Low> + <Hysteresis>). Level High [V]: Upper voltage limit of the ReLock window. Level Low [V]: Lower voltage limit of the ReLock window.

PID1/PID2 Rotary Knobs

Parameter settings for the PID1 and PID2 function modes. NOTE !

By default, PID 1 is active. To select PID 2, tap PID 1 and select PID 2.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.4.7.5

PID1/2 P: Proportional gain of the selected PID controller. The unit depends on the selected PID output channel. PID1/2 Gain: Overall gain factor of the selected PID controller. PID1/2 Sign: Signal polarity of the PID controller. PID1/2 I: Integral gain of the selected PID controller. The unit depends on the selected PID output channel. PID1/2 D: Differential gain of the selected PID controller. The unit depends on the selected PID output channel.

LIR Rotary Knobs

Parameter settings for the LIR function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.4.7.6

Lock Level [V]: Set level for the PID controller used for the Top of Fringe lock type (normally set to zero). LockIn Ph [°]: Phase shift of the local oscillator used for demodulation with respect to the applied modulation. Mod Freq [Hz]: Frequency of the local oscillator. Mod Amp: Amplitude of the modulation signal. The unit depends on the selected Lock-In output channel.

PDH Ch1/PDH Ch2 Rotary Knobs

Parameter settings for the PDH Ch1 and PDH Ch2 function modes (only with PDH module). NOTE !

By default, PDH Ch1 is active. To select PDH Ch2, tap PDH Ch1 and select PDH Ch2.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
Lock Level [V]: Set level for the PID controller used for the Top of Fringe PDH lock type (normally set to zero). LockIn Ph [°]: Phase shift of the local oscillator used for demodulation with respect to the applied modulation. Scan Frequency [Hz]. Mod Amp [dBm]: Amplitude of the modulation signal.

5.4.7.7

FALC 1 .. 4 Rotary Knobs

Parameter settings for the FALC 1 .. 4 function modes (only with FALC pro module connected). NOTE !

Select the desired FALC X at the function mode buttons (see section 5.4.1).

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
As selected in the drop-down menu (see section 4.4.2). I1, I2, I3, D1, D2 Enabled: Enable (True) or disable (False) the respective integrator or differentiator. As selected in the drop-down menu (see section 4.4.2). Input Offset [V]: Compensates an offset of the input signal. Main Gain [dB]: Output gain value of the main circuit branch. Unlim Sign: Select the sign (behavior) of the Unlim integrator. Positive: Output signal is in phase with the Error Output of the FALC pro module. Negative: Output signal is inverted with respect to the Error Output. Main Enabled: Enable (True) or disable (False) the main circuit branch of the FALC pro. Unlim Enabled: Enable (True) or disable (False) the unlimited integrator of the FALC pro. As selected in the drop-down menu (see section 4.4.2). I1, I2, I3 Corner Frequencies [Hz, kHz]: Select left corner frequencies for respective integrator from preset values. Unlim Slew Rate: Specify the slew rate setting of the Unlim integrator [1 .. 12]. As selected in the drop-down menu (see section 4.4.2). Input Gain [dB]: Specify the input gain factor of the input signal. Available values are 1 and 5. D1, D2 Corner Frequencies [kHz, MHz]: Select left corner frequencies for respective differentiator from preset values. Unlim Input Offset [mV]: Compensates an offset between the input of the Unlim integrator and the FALC pro internal error signal. Unlim Gain [V/V/s]: Display of the resulting integrator gain [V/V/s] that is specified by the output range (context parameter FALC X > Unlim Output Range) and the Unlim Slew Rate.

5.4.7.8

PFD 1 .. 4 Rotary Knobs

Parameter settings for the PFD 1 .. 4 function modes (only with PFD pro module connected). NOTE !

Select the desired PFD X at the function mode buttons (see section 5.4.1). The combination and availability of the corner parameters depend on the individual selections in the context parameter menu (see section 5.4.8). Please refer to the PFD pro manual for details on the PFD pro module.

- Top-left:
As selected in the drop-down menu (see section 4.4.2). Center Frequency [MHz]: Set the center frequency required for the experiment. Automatic Gain: Enable (True) or disable (False) the automatic gain control loop. Frequency 1 [MHz]: Up to four target frequencies (Frequency 1 .. 4) can be chosen, allowing the required beat frequency to jump between them based on external digital trigger signals. For correlation between Frequency 1.. 4 and Digital Input 0 or 1, please refer to the PFD Control window description in section 6.9.

- Bottom-left:
As selected in the drop-down menu (see section 4.4.2). RF Divider: Set the division value for the required beat frequency of the experiment to match the divided internal reference signal (Ref Divider) for the phase comparison. Phase Detector Level [dBm]: Displays the level of the input signal (RF LF connector) after amplification by automatic or manual gain control. Feed Forward Factor [V/MHz]: Scaling factor for the feed forward voltage signal in relation to frequency difference Frequency 1 .. 4 - Feed Forward Offset (to be set in the context parameter menu). Frequency 3 [MHz]: See description of Frequency 1 above.

- Top-right:
As selected in the drop-down menu (see section 4.4.2). Scan Frequency [Hz]: Set the frequency of the internally generated triangular scan. Frequency Slope [MHz/s]: Set the slope of the externally triggered scan ramp. Manual Gain [dB]: Set the gain factor for the input signal (RF LF connector of the PFD pro module) so that the Phase Detector Level is around 0 dBm. Frequency 2 [MHz]: See description of Frequency 1 above.

- Bottom-right:
As selected in the drop-down menu (see section 4.4.2). Frequency Amplitude [MHz]: Set the peak-to-peak amplitude of the externally triggered scan cycle. Ref Divider: Set the division value for the internal reference signal to match the divided required beat frequency of the experiment (RF Divider). Filter Frequency [MHz]: Set the filter frequency for the tunable bandpass filter. Frequency 4 [MHz]: See description of Frequency 1 above.

5.4.7.9

Power Stabilization Rotary Knobs

Parameter settings of the PID controller for the Power function mode.

- 
- 
- 
- 
Top-left: Bottom-left: Top-right: Bottom-right:

Pow P [mA/mW]: Proportional gain of the PID controller. Pow Gain: Overall gain factor of the PID controller. Pow I [mA/mW/ms]: Integral gain of the PID controller. Pow Set Level [mW]: Reference level for power stabilization.

### 5.4.8 Scan/Lock Mode Context Parameter Menu

Additional scan/lock and display parameters are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button in Scan/Lock mode. On the following pages, detailed information about each accessible parameter is provided. This includes parameters that control the modulation, which is essential for a Top of Fringe lock. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Scan Enable Scan Enable or disable scan [1: enabled], [0: disabled] laser1:scan:enabled (boolean) Scan Frequency Select scan frequency Scan frequency in [Hz] laser1:scan:frequency (real) Scan Start Enter scan start The unit is dependent on the scan output channel "PC Voltage" [V] "CC Current" [mA] "Out A", "Out B" [V] "EOM Voltage Slow" [V] "TC Set Temperature" [°C] "OPO Slow PZT Voltage" [V] "OPO Fast PZT Voltage" [V] laser1:scan:start (real) Scan End Enter scan end The unit is dependent on the scan output channel "PC Voltage" [V] "CC Current" [mA] "Out A", "Out B" [V] "EOM Voltage Slow" [V] "TC Set Temperature" [°C] "OPO Slow PZT Voltage" [V] "OPO Fast PZT Voltage" [V] laser1:scan:end (real) Scan Output Select scan output channel ["PC Voltage", 50], ["CC Current", 51], ["Out A", 20], ["Out B", 21] ["EOM Voltage Slow", 58] only laser systems with intra-cavity EOM ["TC Set Temperature", 56] only DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator ["OPO Slow PZT Voltage", 150], ["OPO Fast PZT Voltage", 151] only DLC TOPO laser systems laser1:scan:output-channel (integer)

Scan Shape Select scan shape ["Triangle", 1], ["Sine", 0] laser1:scan:signal-type (integer) Feed Forward

(DLC TA pro/-AL and DLC TA-SHG/FHG pro: Feed Forward for Master Oscillator) (not DLC CTL)

Feed Forward (Feed Forward PC > CC for DL pro SMC with single mode control) Enable or disable Feed Forward PC > CC [1: enabled], [0: disabled] laser1:dl:cc:feedforward-enabled (boolean) CAUTION ! Make sure to only enable Forward PC > CC or Feed Forward CC > PC. Feed Forward Factor Enter Feed Forward factor (for PC > CC direction) Feed forward factor in [mA/V] [mA/K] only DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator laser1:dl:cc:feedforward-factor (real) Feed Forward CC > PC (only for DL pro SMC with single mode control) Enable or disable Feed Forward CC > PC [1: enabled], [0: disabled] laser1:dl:pc:feedforward-enabled (boolean) CAUTION ! Make sure to only enable Forward CC > PC or Feed Forward PC > CC. Feed Forward Factor (only for DL pro SMC with single mode control) Enter Feed Forward factor for CC > PC direction Feed forward factor in [V/mA] laser1:dl:pc:feedforward-factor (real) Output Filters The output filters allow to limit the rate of change of the output signal to the value set by Slew Rate. PC PC output filter Enable Enable or disable PC output filter [1: enabled], [0: disabled] laser1:dl:pc:output-filter:slew-rate-enabled (boolean) Slew Rate Enter slew rate (maximum rate of change) for PC output filter in [V/s] [1: enabled], [0: disabled] laser1:dl:pc:output-filter:slew-rate (real) CC CC output filter Enable Enable or disable CC output filter [1: enabled], [0: disabled] laser1:dl:cc:output-filter:slew-rate-enabled (boolean) Slew Rate Enter slew rate (maximum rate of change) for CC output filter in [mA/s] [1: enabled], [0: disabled] laser1:dl:cc:output-filter:slew-rate (real)

Analog Remote Control (ARC) PC Analog PC remote control Please refer to section 11.11.1 for an example on how to configure the PC ARC. Enable Enable or disable analog PC remote control [1: enabled], [0: disabled] laser1:dl:pc:external-input:enabled (boolean) Signal Input Select signal input for PC ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:pc:external-input:signal (integer) Factor Enter factor for PC in [V/V] laser1:dl:pc:external-input:factor (real) EOM Analog EOM remote control Please refer to section 11.11.1 for an example on how to configure the EOM ARC. Enable Enable or disable analog EOM remote control [1: enabled], [0: disabled] laser1:dl:eom:external-input:enabled (boolean) Signal Input Select signal input for EOM ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:eom:external-input:signal (integer) Factor Enter factor for EOM in [V/V] laser1:dl:eom:external-input:factor (real) CC Analog CC remote control Please refer to section 11.11.1 for an example on how to configure the CC ARC. Enable Enable or disable analog CC remote control [1: enabled], [0: disabled] laser1:dl:cc:external-input:enabled (boolean) Signal Input Select signal input for CC ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:cc:external-input:signal (integer) Factor Enter factor for CC in [mA/V] laser1:dl:cc:external-input:factor (real)

TC Analog TC remote control Please refer to section 11.11.1 for an example on how to configure the TC ARC. Enable Enable or disable analog TC remote control [1: enabled], [0: disabled] laser1:dl:tc:external-input:enabled (boolean) Signal Input Select signal input for TC ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:tc:external-input:signal (integer) Factor Enter factor for TC in [K/V] laser1:dl:tc:external-input:factor (real)

Amplifier (only DLC TA pro/-AL and DLC TA-SHG/FHG pro) Enable Amplifier Enable or disable amplifier [1: enabled], [0: disabled]. laser1:amp:cc:enabled (boolean) Amplifier Set Current Enter amplifier set current Amplifier set current in [mA] laser1:amp:cc:current-set (real) Amplifier Actual Current Shows actual amplifier current Actual amplifier current in [mA] laser1:amp:cc:current-act (real) Max Amplifier Current Enter maximum amplifier current Maximum amplifier current in [mA] laser1:amp:cc:current-clip (real) Amplifier Set Temperature Enter amplifier set temperature Amplifier set temperature in [° C] laser1:amp:tc:temp-set (real) Amplifier Act Temperature Shows actual amplifier temperature Actual amplifier temperature in [° C] laser1:amp:tc:temp-act (real) Feed Forward Enable Amplifier Feed Forward Enable or disable amplifier Feed Forward [1: enabled], [0: disabled] laser1:amp:cc:feedforward-enabled (boolean) Amplifier Feed Forward Factor Enter amplifier Feed Forward factor Feed forward factor in [mA/V] laser1:amp:cc:feedforward-factor (real) Output Filter The output filter allows to limit the rate of change of the output signal to the value set by Slew Rate. Enable Enable or disable amplifier output filter [1: enabled], [0: disabled] laser1:amp:cc:output-filter:slew-rate-enabled (boolean) Slew Rate Enter slew rate (maximum rate of change) for amplifier output filter in [mA/V] [1: enabled], [0: disabled] laser1:amp:cc:output-filter:slew-rate (real) Limits Actual Seed Power Shows actual seed power Actual seed power in [mW] laser1:dl:pd:power (real)

Minimum Seed Power Enter minimum seed power Minimum seed power in [mW] laser1:amp:seed-limits:power-min (real) Maximum Seed Power Enter maximum seed power Maximum seed power in [mW] laser1:amp:seed-limits:power-max (real) Actual Output Power Shows actual output power of the TA pro/-AL Actual output power in [mW] laser1:amp:pd:amp:power (real) Minimum Output Power Enter minimum output power of the TA pro/-AL Minimum output power in [mW] laser1:amp:output-limits:power-min (real) Maximum Output Power Enter maximum output power of the TA pro/-AL Maximum output power in [mW] laser1:amp:output-limits:power-max (real) Lock Settings Lock Input Signal (available signals depending on system model) Select the lock input signal The lock input signal provides the input for the locking logic (PID controllers, Lock-In, PDH) ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Only with PDH Module ["PDH In 1", 41], ["PDH In 2", 43] laser1:dl:lock:spectrum-input-channel (integer) Error Input Signal (only available when Top of Fringe PDH is selected as Lock Type, but the Lock Input Signal is not a PDH-channel) Error input signal for PIDs ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4], ["PDH-Error 1", 40], ["PDH-Error 2", 42] laser1:dl:lock:error-channel (integer) Error Input Inverted (only available when Top of Fringe PDH is selected as Lock Type, the Lock Input Signal is not a PDH-channel, and FALC Selection is not None) Select if error input signal is inverted laser1:dl:lock:error-channel-inverted (boolean) Lock Type (available options depending on system model) Select whether to lock on edge or extremum [“Top of Fringe“, 1]: LIR lock to an extremum [“Side of Fringe“, 2]: lock to an edge (slope) Only with PDH Module [“Top of Fringe PDH“, 3]: PDH lock to an extremum laser1:dl:lock:type (integer) NOTE !

Lock Type Top of Fringe PDH: If the PDH photo diode is DC-coupled, the Lock Input Signal can be derived by selecting PDH In 1/PDH In 2 from the SMB-connectors on the PDH module.

PDH Selection (only available when Top of Fringe PDH is selected as Lock Type, and FALC Selection is not None) Select PDH channel to be used ["PDH Channel 1", 1], ["PDH Channel 2", 2] laser1:dl:lock:pdh-selection (integer) Lock Without Lockpoint Select Lock mode without Lockpoint [1: Lock without Lockpoint], [0: Lock with Lockpoint] laser1:dl:lock:lock-without-lockpoint (boolean) PID Selection Select PIDs used for locking ["None", 0], ["PID 1", 1], ["PID 2", 2], ["PID 1+2", 3] laser1:dl:lock:pid-selection (integer) FALC Selection (only available with FALC 1 .. 4 connected) Select FALC module to link for Click & Lock ["None", 0], ["FALC 1", 1], ["FALC 2", 2], ["FALC 3", 3], ["FALC 4", 4] laser1:dl:lock:falc-selection (integer) Lock Candidate Separation Enter the min. lock-point separation for side of fringe Separation in [samples] laser1:dl:lock:candidate-filter:edge-min-distance (integer) Peak Lock Candidates Select to include peak lock candidates [1: included], [0: not included] laser1:dl:lock:candidate-filter:top (boolean) Trough Lock Candidates Select to include trough lock candidates [1: included], [0: not included] laser1:dl:lock:candidate-filter:bottom (boolean) Positive-Edge Lock Candidates Select to include lock candidates on positive edges [1: included], [0: not included] laser1:dl:lock:candidate-filter:positive-edge (boolean) Negative-Edge Lock Candidates Select to include lock candidates on negative edges [1: included], [0: not included] laser1:dl:lock:candidate-filter:negative-edge (boolean)

PID 1 Output Channel Select the output channel for PID 1 ["PC Voltage", 50], ["CC Current", 51], ["Out A", 20], ["Out B", 21] ["EOM Voltage Slow", 58] only laser systems with intra-cavity EOM laser1:dl:lock:pid1:output-channel (integer) Use I Cut-off Enable or disable I cut-off on or off [1: on], [0: off] laser1:dl:lock:pid1:gain:i-cutoff-enabled (boolean) I Cut-off Frequency Enter I cut-off frequency. Frequency in Hz below which the integral gain of the PID controller is limited. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions. Frequency in [Hz] laser1:dl:lock:pid1:gain:i-cutoff (real) Use Limit Select to turn limit for PID 1 output on or off [1: on], [0: off] laser1:dl:lock:pid1:outputlimit:enabled (boolean) Limit Symmetric PID1 output limit relative to lock starting point The unit depends on the output channel "PC Voltage" [V] "CC Current" [mA] "Out A", "Out B" [V] laser1:dl:lock:pid1:outputlimit:max (real) Enable PID 1 Enable or disable PID 1 individually [1: enabled], [0: disabled] laser1:lock:PID1:enabled (boolean)

PID 2 Output Channel Select the output channel for PID 2 ["PC Voltage", 50], ["CC Current", 51], ["Out A", 20], ["Out B", 21] ["EOM Voltage Slow", 58] only laser systems with intra-cavity EOM laser1:dl:lock:pid2:output-channel (integer) Use Limit Select to turn limit for PID 2 output on or off [1: on], [0: off] laser1:dl:lock:pid2:outputlimit:enabled (boolean) Limit Symmetric PID 2 output limit relative to lock starting point The unit depends on the output channel "PC Voltage" [V] "CC Current" [mA] "Out A", "Out B" [V] laser1:dl:lock:pid2:outputlimit:max (real) Enable PID 2 Enable or disable PID 2 individually [1: enabled], [0: disabled] laser1:lock:PID2:enabled (boolean) Lock-In Enable Lock-In Modulation Enable or disable Lock-In modulation [1: enabled], [0:disabled] laser1:dl:lock:lockin:modulation-enabled Lock-In Modulation Frequency Enter Lock-In modulation/demodulation frequency Frequency in [Hz] laser1:dl:lock:lockin:frequency (real) Lock-In Modulation Amplitude Enter Lock-In modulation amplitude The unit is dependent on the output channel "PC Voltage" [V] "CC Current" [mA] "Out A", "Out B" [V] laser1:dl:lock:lockin:amplitude (real) Lock-In Demodulation Phase Enter phase difference between Lock-In modulation and demodulation Phase in [°] laser1:dl:lock:lockin:phase-shift (real) Output Channel Select the output channel for Lock-In modulation ["PC Voltage", 50], ["CC Current", 51], ["Out A", 20], ["Out B", 21] laser1:dl:lock:lockin:modulation-output-channel (integer)

PDH (only with PDH module) Channel 1 PDH Modulation Enabled Enable or disable demodulation/LO signal [1: enabled], [0: disabled] pdh1:channel1:modulation-enabled (boolean) PDH Modulation Frequency Select PDH modulation/demodulation frequency [1: 25 MHz], [0: 5 MHz] pdh1:channel1:use-fast-oscillator (boolean) PDH Modulation Amplitude Enter PDH modulation amplitude Amplitude in [dBm] pdh1:channel1:modulation-amplitude-dbm (real) PDH Demodulation Phase Enter phase difference between PDH modulation and demodulation Phase in [°] pdh1:channel1:phase-shift (real) Maximum Input Level Enter the maximum signal level expected on the RF input ["-10 dBm", 0]: Signal level valid up to -10 dBm ["0 dBm", 1]: Signal level valid up to 0 dBm ["+10 dBm", 2]: Signal level valid up to +10 dBm pdh1:channel1:input-level-max (integer) LO Output Enabled Enable or disable output of the LO signal pdh1:channel1:lo-output-enabled (boolean) LO Output Amplitude Enter LO Amplitude pdh1:channel1:lo-output-amplitude-dbm (real) NOTE !

When LO Output is enabled, the LO Amplitude can be set as desired. This may affect the error signal generated by the PDH module. If you wish to output the demodulation signal and ensure optimum error signal quality at the same time, set LO Amplitude to 8.8 dBm.

Channel 2 PDH Modulation Enabled Enable or disable demodulation/LO signal [1: enabled], [0: disabled] pdh1:channel2:modulation-enabled (boolean) PDH Modulation Frequency Select PDH modulation/demodulation frequency [1: 25 MHz], [0: 5 MHz] pdh1:channel2:use-fast-oscillator (boolean) PDH Modulation Amplitude Enter PDH modulation amplitude Amplitude in [dBm] pdh1:channel2:modulation-amplitude-dbm (real) PDH Demodulation Phase Enter phase difference between PDH modulation and demodulation Phase in [°] pdh1:channel2:phase-shift (real) Maximum Input Level Enter the maximum signal level expected on the RF input ["-10 dBm", 0]: Signal level valid up to -10 dBm ["0 dBm", 1]: Signal level valid up to 0 dBm ["+10 dBm", 2]: Signal level valid up to +10 dBm pdh1:channel2:input-level-max (integer) LO Output Enabled Enable or disable output of the LO signal pdh1:channel2:lo-output-enabled (boolean) LO Output Amplitude Enter LO Amplitude pdh1:channel2:lo-output-amplitude-dbm (real) NOTE !

When LO Output is enabled, the LO Amplitude can be set as desired. This may affect the error signal generated by the PDH module. If you wish to output the demodulation signal and ensure optimum error signal quality at the same time, set LO Amplitude to 8.8 dBm.

FALC 1 .. 4 (only with FALC pro module connected) Serial Number Displays serial number of FALC X. falcX:serial-number (string) Path Selection (only with DLC pro Lock option) Select path(s) to link for Click & Lock. ["None", 0], ["Unlim", 1], ["Main", 2], ["Unlim + Main", 3] falcX:path-selection (integer) Hold State Hold state of the linked path(s). falcX:hold-state (boolean) Monitor Output Configuration Select signal for analog Monitor output of the FALC pro module. ["Error", 0], ["Main", 1], ["Main RMS", 2] falcX:mon:config (integer) Enable Main Path Enable or disable main path. falcX:main:enabled (boolean) Use External Gain Input Use external gain input for main path. falcX:main:gain:use-external-input (boolean) Enable Unlim Path Enable or disable unlim path. falcX:unlim:enabled (boolean) Hold Unlim Path Hold unlim path. falcX:unlim:hold (boolean) Unlim Output Range Set maximum absolute voltage of the Unlimited integrator output signal. falcX:unlim:output-range (real)

PFD 1 .. 4 (only with PFD pro module connected) Serial Number Displays serial number of PFD X. pfdX:serial-number (string) RF-Path Select RF-Path. ["LF", 0], ["LF-TF", 1], ["HF", 2] pfdX:rf-path (integer) NOTE !

To utilize the HF path of the PFD pro, a license is required. When the PFD pro HF is acquired, the USB flash drive with the license key is part of the delivery content. The license is unlimited in time but linked to the individual hardware of the PFD pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).

Reference Path Select Reference Path. ["Internal", 0], ["External", 1] pfdX:reference-path (integer) Frequency Plan Mode This section allows to configure the properties of the required beat frequency (RF HF and RF LF connector at the PFD pro module, see PFD pro manual) for the phase comparison. ["Tunable Filter, 0" only with RF Path LF-TF selected], ["Adjustable", 1], ["Scan", 2], ["Scan External", 3], ["Hop External", 4] pfdX:reference-frequency:mode (integer) Hopping External Feed Forward Offset Enter voltage offset for Feed Forward output. The PFD pro allows to generate a voltage signal equivalent to (Frequency 1 .. 4 - Feed Forward Offset) x Feed Forward Factor. Frequency 1 .. 4 and Feed Forward Factor are available as corner parameters at the rotary knobs (see section 5.4.7.8). This voltage is applied to the Aux 2 connector of the PFD pro module. (see PFD pro manual for details). pfdX:reference-frequency:hopping:feed-forward-offset (real)

Lock Detection and ReLock Enable Lock Detection Lock detection for ReLock, Hold, etc. [1: enabled], [0: disabled] laser1:dl:lock:window:enabled (boolean) Window Input Signal Select input signal for lock detection window ["Fine In 1, 0"], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Only with PDH Module ["PDH In 1", 41], ["PDH In 2", 43] laser1:dl:lock:window:input-channel (integer) Window Level Low Enter lower level for out-of-lock detection Level in [V] laser1:dl:lock:window:level-low (real) Window Level High Enter upper level for out-of-lock detection Level in [V] laser1:dl:lock:window:level-high (real) Window Hysteresis Hysteresis between out-of-lock and in-lock value Hysteresis in [V] laser1:dl:lock:window:level-hysteresis (real) Out-of-lock Action Delay Delay to action after out-of-lock state is detected Enter the delay between detection of the out-of-lock state and the initialization of a reset/relock procedure. Delay in [ms] laser1:dl:lock:relock:delay (real) Enable PID 1/2 Reset PID reset upon out-of-lock state [1: enabled], [0: disabled] laser1:dl:lock:reset:enabled (boolean) ReLock

Enable ReLock ReLock upon out-of-lock state [1: enabled], [0: disabled] laser1:dl:lock:relock:enabled (boolean) ReLock Amplitude Enter amplitude for ReLock scan Amplitude in [V] laser1:dl:lock:relock:amplitude (real) ReLock Frequency Enter frequency for ReLock scan Frequency in [Hz] laser1:dl:lock:relock:frequency (real) ReLock Output Channel Select output channel for ReLock ["PC Voltage", 50], ["CC Current", 51], ["Out A", 20], ["Out B", 21] laser1:dl:lock:relock:output-channel (integer)

Power Stabilization Settings Enable Power Stabilization Enable or disable power stabilization [1: enabled], [0: disabled] laser1:power-stabilization:enabled (boolean) Differential Gain Enter diff. gain for power stabilization in [mA/mW*µs] laser1:power-stabilization:gain:d (real) Hold Output Current on Unlock Select unlock behavior of output channel [1: enabled], [0: disabled] laser1:power-stabilization:hold-output-on-unlock (boolean) Sign Positive Select on for positive, off for negative [1: on], [0: off] laser1:power-stabilization:sign (boolean) Input Channel Select power stabilization input channel Selectable signal channels depend on laser head. Please refer to section 5.4.6 for reference laser1:power-stabilization:input-channel (integer) Window Settings Enable Stabilization Detection Enable or disable window for power stabilization [1: enabled], [0: disabled] laser1:power-stabilization:window:enabled (boolean) Window Level Enter level for out-of-stabilization detection Level in [mW] laser1:power-stabilization:window:level-low (real) Window Hysteresis Hysteresis between out-of- and in-lock stabilization value Hysteresis in [mW] laser1:power-stabilization:window:level-hysteresis (real)

External Power External Power settings Physical Channel Select physical input for external power laser1:pd-ext:input-channel Photo Diode Value Photo diode voltage of the physical channel [V] laser1:pd-ext:photodiode (real) Calibration Factor Enter calibration factor for external power laser1:pd-ext:cal-factor (real) Calibration Offset Enter calibration offset for external power laser1:pd-ext:cal-offset (real) Feed Forward (only DLC CTL) Power Stabilization Feed Forward Enable power stabilization Feed Forward (for description, please refer to section 7.7.4) Enable or disable power stabilization Feed Forward [1: enabled], [0: disabled] laser1:power-stabilization:feedforward-enabled (boolean) Feed Forward Factor (only DLC CTL) Enter power stabilization Feed Forward factor (for description, please refer to section 7.7.4) Power stabilization Feed Forward factor in [V/mA] laser1:power-stabilization:feedforward-factor (real) Display Settings Trace Scaling Input Trace Y Minimum Enter Ymin for left axis. Reasonable values depend on the selected signal Input Trace Y Maximum Enter Ymax for left axis. Reasonable values depend on the selected signal Auxiliary Trace Y Minimum Enter Ymin for right axis. Reasonable values depend on the selected signal Auxiliary Trace Y Maximum Enter Ymax for right axis. Reasonable values depend on the selected signal X-Axis Autoscale Enable Autoscale for X-Axis. [1: enabled], [0: disabled]

Trace Selection Input Trace Signal (available signals depending on system model) Select signal for input trace (red curve) ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4], ["Out A", 20] ["Out B", 21], ["CC Current", 51], ["CC AIn1", 52], ["CC AIn2", 53], ["PC Voltage", 50] ["SC Output", 101], ["Laser PD", 54], ["External Power", 55], ["PowerLock Input", 102] ["Lock Input", 100], ["Lock-In Output", 30], ["PID 1 Output", 31], ["PID 2 Output", 32] Only with PDH Module ["PDH In 1", 41], ["PDH Error 1", 40], ["PDH In 2", 43], ["PDH Error 2", 42] Only DLC TA pro/-AL ["Amp. Current", 63], ["AMP AIn", 60], ["Seed Power", 61], ["Amp. Power", 62] Only DLC CTL ["CTL Power", 70], ["CTL Photodiode", 69] Only DLC DL-/TA-SHG/FHG pro ["SHG PC Voltage", 90], ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86] Only DLC DL-/TA-FHG pro ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:scope:channel1:signal (integer) Only DLC TOPO ["Pump Power", 144], ["Depl. Pump Power", 145], ["Signal Power", 146] ["OPO Slow PZT Voltage", 150], ["OPO Fast PZT Voltage", 151] Only laser systems wit intra-cavity EOM ["EOM Voltage Slow", 58] Auxiliary Trace Signal (available signals depending on system model) Select signal for auxiliary trace (blue curve) ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4], ["Out A", 20] ["Out B", 21], ["CC Current", 51], ["CC AIn1", 52], ["CC AIn2", 53], ["PC Voltage", 50] ["SC Output", 101], ["Laser PD", 54], ["External Power", 55], ["PowerLock Input", 102] ["Lock Input", 100], ["Lock-In Output", 30], ["PID 1 Output", 31], ["PID 2 Output", 32] Only with PDH Module ["PDH In 1", 41], ["PDH Error 1", 40], ["PDH In 2", 43], ["PDH Error 2", 42] Only DLC TA pro/-AL ["Amp. Current", 63], ["AMP AIn", 60], ["Seed Power", 61], ["Amp Power", 62] Only DLC CTL ["CTL Power", 70], ["CTL Photodiode", 69] Only DLC DL-/TA-SHG/FHG pro ["SHG PC Voltage", 90], ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86] Only DLC DL-/TA-FHG pro ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:scope:channel2:signal (integer) Only DLC TOPO ["Pump Power", 144], ["Depl. Pump Power", 145], ["Signal Power", 146] ["OPO Slow PZT Voltage", 150], ["OPO Fast PZT Voltage", 151] Only laser systems wit intra-cavity EOM ["EOM Voltage Slow", 58]

Display Refresh Rate NOTE !

The actual display refresh rate may be limited by the Scan > Scan Frequency, or the Lock Detection and ReLock > Out-of-lock Action > ReLock > ReLock Frequency, both set in the context parameter menu. Keep that in mind when setting very low Scan Frequency or ReLock Frequency values. Select display refresh rate Frequency in [Hz] ["1 Hz", 1], ["2 Hz", 2], ["3 Hz", 3], ["4 Hz", 4], ["5 Hz", 5], ["10 Hz", 10] laser1:scope:update-rate (integer) Display Mode Select display mode [“X/Y”, 0], ["Time", 1], ["Frequency", 2] laser1:scope:variant (integer) Time Time Base Select time base Time in [ms] [“50 µs”, 0.05], [“100 µs”, 0.1], [“200 µs”, 0.2], [“500 µs”, 0.5], [“1 ms”, 1] [“2 ms”, 2], [“5 ms”, 5], [“10 ms”, 10], [“20 ms”, 20], [“50 ms”, 50] [“100 ms”, 100], [“200 ms”, 200], [“500 ms”, 500], [“1 s”, 1000] Laser1:scope:channelx:scope-timescale (real) Frequency Frequency Base Select frequency base Frequency in [kHz] [“500 Hz”, 0.5], [“1 kHz”, 1], [“2.5 kHz”, 2.5], [“5 kHz”, 5] [“10 kHz”, 10], [“25 kHz”, 25], [“50 kHz”, 50], [“100 kHz”, 100] [“250 kHz”, 250], [“500 kHz”, 500], [“1 MHz”, 1000] laser1:scope:channelx:scope-spectrum-range (real)

Pressure Compensation (not DLC DFB pro/DLC DL pro BFY) Pressure compensation settings Pressure Compensation Enable or disable pressure compensation [1: enabled], [0: disabled] laser1:dl:pressure-compensation:enabled (boolean) Averaged Air Pressure Shows averaged air pressure in [hPa] laser1:dl:pressure-compensation:air-pressure (real) Pressure Comp. Factor Set the factor for linear pressure compensation in [V/hPa] laser1:dl:pressure-compensation:factor (real) NOTE !

Please refer to section 11.12 for further information on the pressure compensation.

Pressure Comp. Voltage Shows pressure compensation voltage laser1:dl:pressure-compensation:compensation-voltage (real)

### 5.4.9 Side of Fringe Locking with Touchscreen

NOTE !

In the following, only the basic steps of Side of Fringe locking are described. For a more detailed application example, please refer to section 8.3.1.

Once the laser scans across the spectral function (please refer to section 5.4), a typical application is to lock the laser frequency to the slope of a Doppler-free absorption line. Prerequisites:

- Experimental setup connected to the DLC pro (for details, see section 8.1):
- Lock option license key activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).
- Lock Input signal connected to Fine In or Fast In (BNC connectors on DLC pro front panel).
- Laser head connected to the DLC pro as described in section 4.5.3.
Figure 25

Touchscreen in Lockpoint function mode; Lockpoint candidates for Side of Fringe lock type (example)

1.
Switch to Scan/Lock mode by pressing the Scan/Lock Mode button.

2.
Select the xy display mode by tapping the xy symbol. Select the Lockpoint function mode by tapping the Lockpoint symbol.

3.
Select the input channel of the Lock Input signal in the parameter menu (Lock Settings > Lock Input signal).

4.
Select Lock Settings > Lock Type > Side of Fringe in the parameter menu.

5.
Select the PID controller(s) for regulating the lockpoint (Lock Settings > PID Selection). Ensure that each PID output is configured correctly.

NOTE !

6.
Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

Zoom and drag the Lock Input signal and adjust the laser current (Set Current rotary knob) until the laser scans mode hop-free across the desired lockpoint and the lockpoint in the spectrum is clearly visible on the display.

NOTE !

The current lock voltage level is displayed as a red line. Lockpoint candidates are displayed where the Lock Input signal crosses the lock voltage level line.

7.
Set the desired lock level voltage by turning the Lock Level rotary knob.

8.
Locking with lockpoint candidates: Select the lockpoint by tapping on the Lockpoint Candidate. For a clearer display, unwanted lockpoint candidates can be deselected in the context parameter menu (Lock Settings > Positive-Edge/Negative-Edge Lock Candidates). Locking without lockpoint candidates: Enable Lock Settings > Lock Without Lockpoint in the context parameter menu. Move the spectrum on the touchscreen in x-direction so that the desired region to trigger the lock is located in the center.

9.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. Locking without lockpoint candidates: The laser scans to the center of the spectrum (Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on.

10.
Select the PID 1 or PID 2 function modes by tapping on the PID symbols.

11.
Adjust the PID Gain settings with the rotary knobs. See section 9.3 for information on PID controller configuration.

When the laser is locked, the touchscreen shows the Lock Input signal during the last scan before the lock was enabled (default black trace) and the actual Lock Input signal as a point cloud (default red) in red brackets. NOTE !

Due to the enabled lock, the scan is disabled. In xy display mode the Lock Input signal now appears as a point cloud because the scan output (X-axis) remains constant and all Y-values are plotted against this constant X-value.

In case one of the used PID controller outputs is equal to the scan output, the X-value does not remain constant, reflecting the action of the PID controller. Depending on the required action of the PID controller to keep the lock stable, the point cloud may leave the displayed X-axis range. In this case a red arrow shows the direction to the point cloud. The red arrow also helps to judge if the laser is still locked. When the laser is out-of-lock, the red arrow will not point into the expected direction (please see also Figure 68).

To unlock the laser:

1.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). The PID controller(s) switch(es) OFF, and the scan starts again. NOTE !

If you wish to keep the selected PID output channel at the current value after the lock is switched off, check the parameter box laserX:dl:lock:pid1/2:hold-output-on-unlock in the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9). The parameter can be accessed in user level MAINTENANCE, for changing the user level, please refer to section 6.9, Device Configuration section.

### 5.4.10 Top of Fringe (Lock-In/PDH) Locking with Touchscreen

NOTE !

In the following, only the basic steps on Top of Fringe locking are described. For a more detailed application example, please refer to section 8.3.2. Only Top of Fringe (Lock-In): The Lock Wizard in the TOPAS DLC pro PC-GUI (Laser Menu > Optimization Tools > Lock Wizard, see section 6.8) is an interactive tool which helps to setup a Top of Fringe lock.

NOTE !

If your DLC pro is equipped with a PDH module (see section 10.2.11), you can also use the PDH Ch1/PDH Ch2 function modes for Top of Fringe locking, instead of the LIR function mode described in this section. In this case connect your experimental setup as shown in section 8.3.3 and follow the instructions below for Lock-In accordingly. For an application example of a Top of Fringe PDH lock with high-finesse cavity, please refer to section 8.2.

NOTE !

It is possible to route the Lock-In Error signal to the Out A/B BNC connectors on the DLC pro front panel. Please refer to section 7.2.3 for details. By routing the Lock-In Error signal to analog outputs, the signal resolution may be reduced. Please use the parameters io:out-a:external-input:factor or io:out-b:external-input:factor, respectively, in order to increase signal-to-noise.

Prerequisites:

- Experimental setup connected to the DLC pro (for details, see sections 8.3.2 or 8.3.3):
- Lock option license key activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).
- Only Lock-In: Lock Input signal connected to Fine In or Fast In (BNC connectors on DLC pro front
panel).

- Only PDH Lock: Lock Input signal connected to in 1 or in 2 (SMB connectors on PDH module
panel).

- Laser head connected to the DLC pro as described in section 4.5.3.
Figure 26

Touchscreen in Lockpoint function mode; Lockpoint candidates for Top of Fringe lock type (example)

1.
Switch to Scan/Lock mode by pressing the Scan/Lock Mode button.

2.
Select the xy display mode by tapping the xy symbol. Select the Lockpoint function mode by tapping the Lockpoint symbol.

3.
Select the input channel of the Lock Input signal in the parameter menu (Lock Settings > Lock Input signal) depending on the desired Lock Type and the experimental setup.

4.
Select Lock Settings > Lock Type > Top of Fringe or Top of Fringe PDH in the parameter menu.

NOTE !

5.
To display only the Lock Input signal, select Display Settings > Trace Selection > Auxiliary Trace Signal > None in the parameter menu. Lockpoint candidates are displayed at the extrema of the Lock Input signal. If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by adjusting the P/N Tolerance rotary knob correctly for the signal and signal-tonoise ratio used. This parameter is 0 for automatic detection, and automatic detection does not always work perfectly. The parameter should be set to a value that is larger than the peak-to-peak noise and smaller than the peaks that the laser should be locked to.

Select the PID controller(s) to regulate the lockpoint (Lock Settings > PID Selection). Ensure that each PID output is configured correctly.

NOTE !

Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

6.
Zoom and drag the Lock Input signal, and adjust the laser current (Set Current rotary knob) until the laser scans mode hop-free across the desired part of the spectrum and the desired lockpoint is clearly visible on the display.

7.
Switch to the LIR function mode by tapping the Lockpoint symbol and selecting the LIR symbol. Display the Lock-In Output signal (Error signal) as the Auxiliary trace (Display Settings > Trace Selection > Auxiliary Trace Signal).

Figure 27

Error signal (blue) and Lock Input signal (red) displayed in LIR lock function mode

8.
Set the Lock Level to zero at the top-left rotary knob. Adjust the Modulation Frequency, Modulation Amplitude, and Lock-In Phase of the Error signal (rotary knobs). Modify the demodulation phase (Lock-In Phase) until the blue Error signal matches the derivative of the red Lock Input signal and the Error signal runs in the correct direction through the signal extremum to which you want to lock:

- Lockpoint is in signal valley: rising flank of the blue Error signal.
- Lockpoint is on signal peak: falling flank of the blue Error signal.
NOTE !

9.
10.
Please refer to section 9.3 for information on how to configure the PID controller(s). Please refer to section 8.3.2 for reasonable settings of the Lock-In parameters.

Switch to Lockpoint function mode. Locking with lockpoint candidates: Select the lockpoint by tapping on the Lockpoint Candidate. For a clearer display, unwanted lockpoint candidates can be deselected in the context parameter menu (Lock Settings > Peak/Trough Lock Candidates). Locking without lockpoint candidates: Enable Lock Settings > Lock Without Lockpoint in the context parameter menu. Move the spectrum on the touchscreen in x-direction so that the desired region to trigger the lock is located in the center. Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. Locking without lockpoint candidates: The laser scans to the center of the spectrum (Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on.

11.
Select the PID 1 or PID 2 lock function mode by tapping on the PID symbols.

12.
Adjust the PID Gain settings with the rotary knobs to optimize the lock. See section 9.3 for information on PID controller configuration.

NOTE !

The laser is actually locked to the Lock-In Output signal. The Lock-In Output signal is the input signal for the PID controller(s).

When the laser is locked, the touchscreen shows the Lock Input signal during the last scan before the lock was enabled (default black trace) and the actual Lock Input signal as a point cloud (default red) in red brackets. NOTE !

Due to the enabled lock, the scan is disabled. In xy display mode the Lock Input signal now appears as a point cloud because the scan output (X-axis) remains constant and all Y-values are plotted against this constant X-value.

In case one of the used PID controller outputs is equal to the scan output, the X-value does not remain constant, reflecting the action of the PID controller. Depending on the required action of the PID controller to keep the lock stable, the point cloud may leave the displayed X-axis range. In this case a red arrow shows the direction to the point cloud. The red arrow also helps to judge if the laser is still locked. When the laser is out-of-lock, the red arrow will not point into the expected direction (please see also Figure 68). To unlock the laser:

1.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). The PID controller(s) switch(es) off, and the scan starts again. NOTE !

If you wish to keep the selected PID output channel at the current value after the lock is switched off, check the parameter box laserX:dl:lock:pid1/2:hold-output-on-unlock in the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9). The parameter can be accessed in user level MAINTENANCE, for changing the user level, please refer to section 6.9, Device Configuration section.

### 5.4.11 ReLock Window and Procedure

The ReLock feature is provided to detect out-of-lock states of the laser, to reset the PID controller(s), and to relock the system if the out-of-lock state is detected (see Figure 29). In order to determine whether the system is in-lock state or not, the DLC pro needs input. The user defines a Window Input signal and conditions for this signal to determine the lock state (ReLock window, see Figure 28). The Window Input signal can be, for example, a Doppler-broadened absorption signal to distinguish between various Doppler free lines. It may be a fluorescence signal or a TTL signal from some other source within the experimental setup. It could also be the Lock Input signal. In the ReLock window, the user can choose a voltage range for the Window Input signal which defines the in-lock state. If the signal leaves this range, the out-of-lock state is detected. The system can only return into the in-lock state if the signal is within the chosen voltage range, again. To prevent the system from hopping between the two states due to noisy signals, a certain hysteresis can be defined between the out-of-lock and in-lock voltages.

Figure 28

ReLock window

Please configure the Window Input signal and its corresponding levels by selecting the signal in the context parameter menu (Lock Detection and ReLock > Window Input Signal) and by defining the parameters of the ReLock window (Lock Detection and ReLock > Window Level Low and High, Window Hysteresis). You can also define the limits of the ReLock window with the rotary knobs: Level High, Level Low, Hysteresis. Please note that Level High must be ≥ Level Low + 2 x Hysteresis.

Figure 29

DLC pro ReLock procedure (schematic)

When the out-of-lock-state is detected, the output of the respective PID controller(s) (Lock Settings > PID

Selection) is frozen.

- If the in-lock state is reached during the following configurable delay time (Lock Detection and
ReLock > Out-of-Lock Action > Delay), the PID controller is activated again.

- If the out-of-lock state is still detected after the delay time has expired, the PID controllers are reset
to zero if reset is enabled (Lock Detection and ReLock > Out-of-Lock Action > Enable PID1/2 Reset) The speed of the reset is dependent on the Slew Rate settings (Output Filters > PC > or CC > Slew Rate) of the selected PID output channels. During this reset, the system cannot change back into the in-lock state.

- The Relock scan is initiated as configured (Lock Detection and ReLock > Out-of-Lock
Action > ReLock submenu) until the in-lock state is reached, again. If no ReLock scan is configured, the in-lock state may be reached due to drifts of the laser system or user interaction, again. If ReLock is enabled, the DLC pro applies a scan to the ReLock Output Channel with the Relock Frequency as scan frequency and the ReLock Amplitude as scan amplitude.

5.4.11.1

ReLock Configuration with Touchscreen

Prerequisites:

- The Laser is ready to be locked (see sections 5.4.10 and 5.4.9).
- A separate signal for out-of-lock detection (Window Input signal) is connected to Fine In or Fast In
(BNC-connectors on DLC pro front panel).

Figure 30

1.
Touchscreen in ReLock function mode; Lockpoint candidates for Top of Fringe lock type shown and ReLock window for out-of-lock detection (example)

Select the xy display mode by tapping the xy symbol.

2.
Enable the out-of-lock detection in the parameter menu (Lock Detection and ReLock > Enable Lock Detection).

3.
Select the ReLock function mode by tapping the Lockpoint symbol and selecting ReLock.

4.
Select the Window Input signal in the parameter menu (Lock Detection and ReLock > Window Input Signal). To display the Window Input signal, select its channel (Display Settings > Trace Selection > Auxiliary Trace Signal) in the parameter menu.

5.
Define the limits of the ReLock window for out-of-lock detection with the rotary knobs: Level High, Level Low, Hysteresis.

6.
Define the Delay between out-of-lock detection and reset/relock scan activation in the parameter menu (Lock Detection and ReLock > Out-of-Lock Action > Delay).

7.
Enable/disable Reset for both PID controller(s) (Lock Detection and ReLock > Out-of-Lock Action > Enable PID1/2 Reset) and define the Slew Rate (Output Filters > PC > or CC > Slew Rate) of the selected PID output channels.

8.
Enable/disable the ReLock in the parameter menu (Lock Detection and ReLock > Out-of-Lock Action > ReLock > Enable ReLock).

9.
Define ReLock amplitude, frequency, and output channel of the ReLock scan in the parameter menu (Lock Detection and ReLock > Out-of-Lock Action > ReLock > ReLock Amplitude, ReLock Frequency and ReLock Output Channel).

The ReLock should now be configured and work as intended. NOTE !

In case the Lock Detection and ReLock > Out-of-lock Action > ReLock > ReLock Frequency is lower than the Scan > Scan Frequency (both set in the context parameter menu), the xy display mode of the touchscreen does not show a whole ReLock scan period. Use the t (time) display mode for proper display.

### 5.4.12 Wide Scan Mode

NOTE !

The Wide Scan mode is available for all laser heads. Depending on the laser head type, a different set of parameters can be scanned. In Wide Scan mode, the number of recorded data points will be much bigger than displayed by the screen resolution. In order to show even narrow spectral features, the display actually shows an enveloped graph which considers the minimal and maximal values in each interval represented by a data point (or data bar actually). It is possible to zoom into the recorded data while the scan is still in progress. Use the Full Range button to return to the full scale display in an easy way. When Wide Scan > Scan Shape > Triangle is selected in the context parameter menu (see section 5.4.12.1), do not use the screen display for analysis, as it shows artifacts. The full resolution of all recorded data points can be exported from the Wide Scan Display of the TOPAS DLC pro PC-GUI.

The wavelength of a laser head can be tuned, for example, by varying either the laser diode temperature, the operating current or the piezo voltage. CTL laser heads can additionally be tuned by performing a motor scan. The Wide Scan mode allows to scan different, laser head depending parameters over a large range and to record data with a high resolution. Operation is described in the wide scan relevant sections of this manual (e.g., this section, sections 6.9 and 7.1.1). To access the Wide Scan mode relevant operator controls, either press the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 31 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols which appear after tapping. Select to change the display of the touchscreen as well as the assignment of the rotary knobs as needed for setting the most important wide scan parameters.

Figure 31

Touchscreen in Wide Scan mode (example DLC CTL)

The parameter to be scanned (Wide Scan > X-Axis signal) is selected in the context parameter menu (please refer to section 5.4.12.1) which appears on the touchscreen after pressing the Parameter button in Wide Scan mode. Further wide scan parameters are also set in the context parameter menu.

Rotary Knobs:

- Top-left:
- Bottom-left:
- Top-right:
NOTE !

Set <value> [mA, V, °C, nm] of the parameter to be scanned when wide scan is not running. Actual <value> [mA, V, °C, nm] of the parameter to be scanned when wide scan is running. Start <value> [mA, V, °C, nm] of the parameter to be scanned. As selected in the drop-down menu (see section 4.4.2): Scan Speed [mA/s, V/s, K/s, nm/s]

A high Scan Speed together with a small Wide Scan > Set Recorder Stepsize (context parameter menu, see section 5.4.12.1) leads to a higher Recorder > Sampling Rate. At a Sampling Rate above 100 kHz, dropouts during recording may occur.

- Bottom-right:
Actual <value> [mA, V, °C, nm] of the parameter to be scanned or Set Current of laser diode [mA]. End <value> [mA, V, °C, nm] of the parameter to be scanned. <value> can be Current, Voltage, Temperature or Wavelength.

After the Start and End values are set, the wide scan is operated by tapping the buttons Play, Stop, and Repeat (see Figure 31). When the laser is scanning, the top-left parameter changes from Set value to Actual value. A progress bar and a display in the format [min:s] at the bottom of the graph indicate the remaining time of the wide scan (see Figure 31). After the wide scan is finished, the laser returns to the Set value. NOTE !

In case the laser should remain at the Actual value after the wide scan is finished or stopped, please uncheck the box at the parameter laserX:wide-scan:restore-on-end (Parameters window of the TOPAS DLC pro PC-GUI, see section 6.9). With this setting, after the wide scan is finished or stopped, the Actual value becomes the new Set value.

Play: The Start value of the parameter to be scanned is accessed and the wide scan is initiated with the set Scan Speed. Play Trigger: The icon in the Play button indicates that the wide scan is initiated by a input trigger signal and not by tapping the Play button (Wide Scan > Trigger Configuration > Input Trigger > Input Trigger Enable is set to 1 in the context parameter menu, see section 5.4.12.1). After tapping the Play Trigger button, the Start value of the parameter to be scanned is accessed. The wide scan then is initiated with the set Scan Speed when a trigger signal is applied to the selected Wide Scan > Trigger Configuration > Input Trigger > Trigger Input Channel. When the trigger signal is removed, the wide scan continues until the End value is reached. Tap the Stop button to discontinue the wide scan.

Stop: Wide scan is stopped and the Set value is accessed.

Repeat: Wide scan is continuously repeated within the set values. The scan shape for a repeated wide scan can be selected in the context parameter menu (please refer to section 5.4.12.1). Sawtooth wide scan shape: Return to the start value is performed as fast as possible. Triangle wide scan shape (default): Return to the start value is performed with scan speed. NOTE !

When Analog Remote Control (ARC) for the selected Wide Scan > X-Axis signal is enabled in the context parameter menu (see section 5.4.12.1), the ramp of the wide scan is superimposed by the ARC signal. This may lead to distorted visualization at the touchscreen display.

Center: Select to set the Set value (e.g., the laser diode temperature) to the center value of the actual detail of the touchscreen display (Xaxis). The display of Actual value will change accordingly. Zoom Range: Select to set the Start and End value (e.g., the laser diode temperature) to the outer values of the actual detail of the touchscreen display (X-axis). The display of Start and End value will change accordingly. Full Range: Tap to scale the touchscreen display so that the entire wide scan from Start value to End value is displayed. Trace Scaling: Tap to select the desired trace scaling.

Notes on the Functionality of the Wide Scan: The wide scan precisely scans a laser parameter and simultaneously acquires data on two input channels. It enables recording up to 5 million data points per channel in a scan. Depending on the laser type, users can decide to scan one of the following parameters:

- 
- 
- 
- 
Set wavelength or piezo voltage for DLC CTL Laser diode temperature or current for DLC DFB pro or DLC DL pro BFY Piezo voltage or laser diode current for DLC DL pro One of the analog outputs Out A or Out B for any of the above

This scan option also works for lasers that are part of a DLC TA pro/-AL or DLC DL-/TA-SHG/FHG pro system, then the available parameters for scanning are according to the seed laser. The scan range is limited by the physical boundaries of the chosen parameter to be scanned. E.g. a wide scan of the CTL wavelength is limited by the minimum and the maximum wavelength of the CTL. A wide scan of the temperature of a DFB pro or DL pro BFY is limited by the tuning properties of the respective laser diode and/or the working range of the thermistor. In Wide Scan mode, it is recommended not to change the Set value of the parameter to be scanned once the scan has started. For slowly changing parameters, like the laser temperature, please be patient while the laser tunes to the start point of the scan. In general, the number of data points recorded will be much bigger than the one displayed on the screen. In order to visualize narrow spectral features, the display actually shows an envelope graph which represents the minimum and maximum values of an interval by a data point each. The envelope is re-calculated whenever the zoom range or the data points change. It is possible to zoom into the recorded data while the scan is still in progress. Use the Full Range button to return to the full-scale display of the scan. A new scan will always start from the set limits, which may differ from the range displayed on the touchscreen, in particular after a zoom. Once a feature of interest has been found, one may wish to investigate it further, or lock the laser frequency to it. The button Center changes the Set value of the parameter to be scanned (e.g., the laser diode temperature, CTL wavelength, ...) to the center of the currently zoomed window. Once the change has taken effect, it is possible to switch to Scan/Lock mode (see section 5.4), e.g., for investigating narrow features with a reduced/faster scan or to lock the laser. Alternatively, the button Zoom Range sets the Start and End values of the wide scan to the left and right borders of the current zoom. The wide scan can then be repeated more slowly and/or with higher resolution. The number of data points to be recorded per channel, depends on selected scan shape, scan amplitude and recorder step size. For example, doing a sawtooth scan with the wavelength of a CTL laser head over a range of 50 nm, while recording with a step size of 0.00001 nm, will result in about 5,000,000 samples per channel. Exporting this data with the PC-GUI will produce a 170 MB "comma-separated-values" file (*.csv), which might be difficult to handle for data visualization software. Equally, the response of the touchscreen can be slower, as the visualization of up to 5 million data points requires quite a bit of computation. If the full number of data points is not required, it is therefore recommended to reduce the scan resolution. The scan resolution is indicated by the context parameter Wide Scan > Actual Recorder Stepsize, which can be influenced by:

1.
The context parameter Wide Scan > Set Recorder Stepsize is used to configure the target resolution. Set it to 0 if you need the highest possible resolution or give it a reasonable value of your choice.

2.
The context parameter Recorder > Sample Count Limit is used to configure a maximum number of data points per channel. Use this to limit the amount of data for better touchscreen performance or smaller exported file sizes.

The Actual Recorder Stepsize will be calculated by first trying to achieve the target step size while considering the constraints of the data acquisition hardware and data transfer rates, but eventually increasing the value to reduce the resulting sample count to below the given limit.

While the wide scan of each single laser can record up to 5 million data points per channel during a scan, in a multi-laser setup, memory constraints result in limitations for the overall number of data points. The wide scans of all lasers need to share 100 MB of internal DLC pro memory (Please note that the size of a CSV file is approximately a factor of three higher than the internal memory requirements of the corresponding wide scan run). It is up to the user to distribute the memory among the available wide scans. The wide scan doing the first scan gets all the memory it requests and will keep it until it gets started again or until the user releases its memory. For the next laser's wide scan the user must eventually reduce the sample count such that its memory requirements can be satisfied by the memory left over by the first wide scan. The available memory for the third and fourth laser results correspondingly. The predicted amount of required memory for the next run is indicated for each wide scan by the context parameter Wide Scan > Memory Size. Note on Thermal Tuning of a DFB pro or DL pro BFY Laser: The Wide Scan mode offers a very high temperature resolution: 1 bit corresponds to 1.4 x 10-6 K. The actual temperature resolution may differ, due to electronic noise and the properties of the TEC in the diode package. The effective temperature resolution is on the order of 50 µK. The limits of a wide scan are ultimately given by the measurement range of the thermistor inside the laser head, which typically works from 2.2 °C to 51.8 °C. The useable temperature range of a specific DFB pro or DL pro BFY laser depends on the characteristics of the respective diode: When the temperature is tuned, the gain of the semiconductor medium typically shifts about 4 times faster than the grating-defined lasing wavelength. This may cause the diode to jump into a “free-running” (i.e. no longer frequency-stabilized) operation mode at the gain maximum. These operation regimes are excluded by TOPTICA, by restricting the temperature range accordingly.

5.4.12.1

Wide Scan Mode Context Parameter Menu

Additional wide scan and display parameters are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button in Wide Scan mode. On the following pages, detailed information about each accessible parameter is provided. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user-specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Wide Scan Settings CTL Control (only DLC CTL) Microsteps Enable or disable microsteps scan [1: enabled], [0: disabled] laser1:ctl:motor:microsteps (boolean) NOTE !

The motor of the CTL laser head is able to perform so-called microsteps (µ-steps, < 1 pm) while scanning. By default, these microsteps are enabled. Above a certain Scan Speed (top-right rotary knob), the CTL automatically switches the microsteps off, e.g., when returning to the Start Wavelength (bottom-left rotary knob) with a sawtooth Wide Scan > Scan Shape. If for some reason the user wants to disable microsteps, they can be disabled. SMILE Enable or disable mode control (SMILE) [1: enabled], [0: disabled] laser1:ctl:mode-control:loop-enabled (boolean) Wide Scan X-Axis Signal (available signals depending on system model) Select signal channel for X-Axis ["CC Current", 51], ["PC Voltage", 50], ["TC Temp", 57], ["TC Set Temp", 56], ["CTL Wavelength", 79], ["CTL Set Wavelength", 78], ["Out A", 20], ["Out B", 21] laser1:wide-scan:output-channel (integer) Scan Offset Enter scan offset Scan offset in [mA], [V], [°C], [nm] laser1:wide-scan:offset (real) Scan Amplitude Enter scan amplitude Scan amplitude in [mA], [V], [K], [nm] laser1:wide-scan:amplitude (real) Set Recorder Stepsize Enter set value for recorder stepsize Set recorder stepsize in [mA], [V], [K], [nm] laser1:wide-scan:recorder-stepsize-set (real)

NOTE !

A high Scan Speed (top-right rotary knob) together with a small Set Recorder Stepsize leads to a higher Recorder > Sampling Rate. At a Sampling Rate above 100 kHz, dropouts during recording may occur.

Act. Rec. Stepsize (Actual Recorder Stepsize) Read actual value for recorder stepsize Actual recorder stepsize in [mA], [V], [K], [nm] laser1:wide-scan:recorder-stepsize (real) NOTE !

Set Recorder Stepsize and Actual Recorder Stepsize values < 0.00001 are shown as 0.00000 due to the displayed number of decimal digits. Memory Size Read actual value of required memory size for the next wide scan run in Bytes laser1:wide-scan:memory-size (integer) Scan Shape Select scan shape ["Triangle", 1], ["Sawtooth", 0] laser1:wide-scan:shape (integer) Scan Duration Read scan duration Scan duration in [s] laser1:wide-scan:duration (integer) Trigger Configuration Wide scan trigger configuration Input Trigger Trigger input for scan start Input Trigger Enable Enable or disable input trigger [1: enabled], [0: disabled] laser1:wide-scan:trigger:input-enabled (boolean) Trigger Input Channel Enter trigger input channel ["Digital Input 2"], ["Digital Input 3"] at Digital I/O connector on MC+ module (please refer to section 11.10.4) laser1:wide-scan:trigger:input-channel (integer)

NOTE !

Quad-Laser-Operation: The Digital Inputs 2 and 3 are linked to both, the lock hold function and the wide scan input trigger (see section 10.2.3). If that is not desired, the lock hold function can be deactivated via the parameter laserX:dl:lock:di-hold-enabled (parameter menu of the touchscreen (please refer to section 5.14) or Parameters window of the TOPAS DLC pro PC-GUI (please refer to section 6.9).

Output Trigger Trigger output at specified Trigger Threshold NOTE !

The Trigger Output Channels (Digital Outputs, see section 10.2.3) can be configured for wide scan trigger in the IO window of the TOPAS DLC pro PC-GUI (see section 6.9). Configuration is also possible in the parameter menu (touchscreen, see section 5.14): The parameter io:digital-outX:mode must be set to 2, the Trigger Output Channels (Digital Outputs) must be linked to laser 1 .. 4 by setting the parameter io:digital-outX:linked-laser to 1 .. 4. Trigger Threshold Enter output trigger position [mA, V, K, nm] Trigger output level is high if current value is above threshold. laser1:wide-scan:trigger:output-threshold (real)

Feed Forward (not DLC CTL) Feed Forward Enable or disable Feed Forward [1: enabled], [0: disabled] laser1:dl:cc:feedforward-enabled (boolean) Feed Forward Factor Enter Feed Forward factor Feed forward factor in [mA/K], [mA/V] laser1:dl:cc:feedforward-factor (real) Recorder Sample Count Limit Maximum number of samples for the recorder. Used for calculation of Actual Recorder Stepsize in order to limit the sample count laser1:recorder:sample-count-limit (integer) Sample Count Read the actual number of data points of the recorder laser1:recorder:sample-count (integer) Sampling Interval Read the sampling interval of the recorder Sampling interval in [ms] laser1:recorder:sampling-interval (real) Sampling Rate Read the sampling rate of the recorder Sampling interval in [Hz] laser1:recorder:sampling-rate (real) NOTE !

Sample Count, Sampling Interval, and Sampling Rate are only displayed properly during a running wide scan. Low-Pass Filter Configuration Recorder low-pass filter configuration Low-Pass Filter Channel 1 Low-pass filter configuration for channel 1 Enable Enable or disable low-pass filter for channel 1 [1: enabled], [0: disabled] laser1:recorder:channel1:low-pass-filter:enabled (boolean) Cut-Off Frequency Enter cut-off frequency for channel 1 Cut-off frequency in [Hz] laser1:recorder:channel1:low-pass-filter:cut-off-frequency (real) Low-Pass Filter Channel 2 Low-pass filter configuration for channel 2 Enable Enable or disable low-pass filter for channel 2 [1: enabled], [0: disabled] laser1:recorder:channel2:low-pass-filter:enabled (boolean) Cut-Off Frequency Enter cut-off frequency for channel 2 Cut-off frequency in [Hz] laser1:recorder:channel2:low-pass-filter:cut-off-frequency (real)

Output Filters The output filters allow to limit the rate of change of the output signal to the value set by Slew Rate. PC (only DLC CTL and DL pro based laser systems) PC output filter Enable Enable or disable PC output filter [1: enabled], [0: disabled] laser1:dl:pc:output-filter:slew-rate-enabled (Boolean) Slew Rate Enter slew rate (maximum rate of change) for PC output filter in [V/s] laser1:dl:pc:output-filter:slew-rate (real) CC CC output filter Enable Enable or disable CC output filter [1: enabled], [0: disabled] laser1:dl:cc:output-filter:slew-rate-enabled (boolean) Slew Rate Enter slew rate (maximum rate of change) for CC output filter in [mA/s] laser1:dl:cc:output-filter:slew-rate (real) Analog Remote Control (ARC) PC Analog PC remote control Please refer to section 11.11.1 for an example on how to configure the PC ARC. Enable Enable or disable analog PC remote control [1: enabled], [0: disabled] laser1:dl:pc:external-input:enabled (boolean) Signal Input Select signal input for PC remote control ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:pc:external-input:signal (integer) Factor Enter factor for PC remote control in [V/V] laser1:dl:pc:external-input:factor (real) CC Analog CC remote control Please refer to section 11.11.1 for an example on how to configure the CC ARC. Enable Enable or disable analog CC remote control [1: enabled], [0: disabled] laser1:dl:cc:external-input:enabled (boolean) Signal Input Select signal input for CC remote control ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:cc:external-input:signal (integer) Factor Enter factor for CC remote control in [mA/V] laser1:dl:cc:external-input:factor (real)

TC (not DLC CTL) Analog TC remote control Please refer to section 11.11.1 for an example on how to configure the TC ARC. Enable Enable or disable analog TC remote control [1: enabled], [0: disabled] laser1:dl:tc:external-input:enabled (boolean) Signal Input Select signal input for TC remote control ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:dl:tc:external-input:signal (integer) Factor Enter factor for TC remote control in [K/V] laser1:dl:tc:external-input:factor (real) Motor (only DLC CTL) Analog CTL motor remote control Please refer to section 11.11.2 for an example on how to configure the motor ARC. Enable Enable or disable analog motor remote control [1: enabled], [0: disabled] laser1:ctl:remote-control:enabled (boolean) Signal Input Select signal input for motor remote control ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] laser1:ctl:remote-control:signal (integer) Factor Enter factor for motor remote control in [nm/V] laser1:ctl:remote-control:factor (real) Display Settings Trace Scaling Left/Red Y Minimum Enter Ymin for red curve Reasonable values depend on the selected signal Left/Red Y Maximum Enter Ymax for red curve Reasonable values depend on the selected signal Right/Blue Y Minimum Enter Ymin for blue curve Reasonable values depend on the selected signal Right/Blue Y Maximum Enter Ymax for blue curve Reasonable values depend on the selected signal

Trace Selection NOTE !

A selected signal is displayed not until after a start of a wide scan. Left/Red Signal (available signals depending on system model) Select signal for left/red curve) ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4], ["Out A", 20] ["Out B", 21], ["CC Current", 51], ["CC AIn1", 52], ["CC AIn2", 53] ["TC Set Temp", 56], ["TC Temp", 57], ["PC Voltage", 50], ["SC Output", 101] ["Laser PD", 54], ["External Power", 55], ["PowerLock Input", 102], ["Lock Input", 100] ["Lock-In Output", 30], ["PID 1 Output", 31], ["PID 2 Output", 32] Only with PDH Module ["PDH In 1", 41], ["PDH Error 1", 40], ["PDH In 2", 43], ["PDH Error 2", 42] Only DLC TA pro/-AL ["Amp. Current", 63], ["AMP AIn", 60], ["Seed Power", 61], ["Amp. Power", 62] Only DLC CTL ["CTL Photodiode", 69], ["CTL Set Wavelength", 78], ["CTL Wavelength", 79] Only DLC DL-/TA-SHG/FHG pro ["SHG PC Voltage", 90], ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86] Only DLC DL-/TA-FHG pro ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:recorder:channel1:signal (integer) Right/Blue Signal (available signals depending on system model) Select signal for right/blue curve) ["None", -3], ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4], ["Out A", 20] ["Out B", 21], ["CC Current", 51], ["CC AIn1", 52], ["CC AIn2", 53] ["TC Set Temp", 56], ["TC Temp", 57], ["PC Voltage", 50], ["SC Output", 101] ["Laser PD", 54], ["External Power", 55], ["PowerLock Input", 102], ["Lock Input", 100] ["Lock-In Output", 30], ["PID 1 Output", 31], ["PID 2 Output", 32] Only with PDH Module ["PDH In 1", 41], ["PDH Error 1", 40], ["PDH In 2", 43], ["PDH Error 2", 42] Only DLC TA pro/-AL ["Amp. Current", 63], ["AMP AIn", 60], ["Seed Power", 61], ["Amp. Power", 62] Only DLC CTL ["CTL Photodiode", 69], ["CTL Set Wavelength", 78], ["CTL Wavelength", 79] Only DLC DL-/TA-SHG/FHG pro ["SHG PC Voltage", 90], ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86] Only DLC DL-/TA-FHG pro ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:recorder:channel2:signal (integer)

### 5.4.13 Motor Control Mode (only for Laser Heads with MOTOR pro Option)

The MOTOR pro option for DL pro laser heads or DL pro Master Oscillators of amplified laser heads allows to quickly tune the laser to a new wavelength within its tuning range by moving the internal grating of the DL pro by a motor drive. Please refer to the DL pro laser head manual and the MOTOR pro manual for a detailed description. The motor can tune the wavelength across the tuning range of the integrated laser diode. Please note that the motor drive can move the internal grating of the DL pro into positions, where the laser does not emit light. Please refer to the Production and Quality Control Data Sheet of the connected laser head for its wavelength range. Due to its mechanical nature, the motorized tuning is performed by hopping from one longitudinal mode to the next. It should be used for coarse wavelength selection only. Operation is described in the Motor Control relevant sections of this manual and in the MOTOR pro manual. Fine tuning of the laser wavelength is achieved by a piezo actuator. Its frequency resolution is a few kHz, only limited by the resolution of the high-voltage driver electronics (PC module). The fine-tuning range is limited by the stroke of the piezo to a couple of tens of GHz. Operation is described in the Scan function mode relevant sections of this manual. To access the Motor Control mode relevant operator controls, either press the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 32 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols which appear after tapping. Select to change the display of the touchscreen as well as the assignment of the rotary knobs as needed for setting the most important motor control parameters.

Figure 32

Touchscreen in Motor Control mode (only laser heads with MOTOR pro option)

Depending on whether you use the touchscreen to display a spectrum/signal or not, you can toggle between displaying the signals, the values of the (piezo) scan parameters or the values of the motor control parameters by pressing the Scan/Lock Mode button or by tapping the corresponding symbol (toggle function). Further motor control parameters are set in the context parameter menu (please refer to section 5.4.13.1) which appears on the touchscreen after pressing the Parameter button in Motor Control mode.

Rotary Knobs: NOTE !

All wavelengths in the Motor Control section are internally converted into motor step positions, so the wavelength mainly depends on the stored calibration data. Please refer to section 6.8 (Laser Menu > Optimization Tools > Motor Calibration) and to the MOTOR pro manual for instructions to perform a wavelength calibration.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
NOTE !

Set Wavelength [nm]. Desired target wavelength. Start Wavelength [nm] for a motor scan. As selected in the drop-down menu (see section 4.4.2). Available corner parameters depend on the laser system: Motor Scan Speed [nm/s]. Laser Diode Set Current [mA]. End Wavelength [nm] for a motor scan.

Please note that the motor drive can move the internal grating of the DL pro into positions, where the laser does not emit light. Please refer to the Production and Quality Control Data Sheet of the connected laser head for its wavelength range.

When the Start and End Wavelength values are set, the motor drive is operated by tapping the symbols Play, Pause, and Stop (see Figure 32). A progress bar and a display in the format [min:s] indicate the remaining time of the motor scan (see Figure 32). After the motor scan is finished, the laser returns to the Set Wavelength. NOTE !

In case the laser should remain at the Current Wavelength after the motor scan is finished or stopped, please uncheck the box at the parameter laserX:dl:motor:scan:restore-onend (Parameters window of the TOPAS DLC pro PC-GUI, see section 6.9). With this setting, after the motor scan is finished or stopped, the Current Wavelength becomes the new Set Wavelength.

Play: The Start Wavelength is accessed and the motor scan is initiated with the set Scan Speed. CAUTION ! Checking the Use Tuning Clip boxes for diode laser and amplifier (depending on the connected laser head) in the Laser Config screen (touchscreen user interface, see section 5.3.5) is mandatory before performing a motor scan. Checking the box(es) reduces the laser diode (and amplifier) currents to the Maximum Tuning Currents as noted in the laser head Quality Control and Test Data Sheet to avoid damage to the laser diode (and the amplifier) during a motor scan.

Pause: Motor scan is paused. Tap Play to continue the motor scan.

Stop: Motor scan is stopped and the Set Wavelength is accessed.

5.4.13.1

Motor Control Context Parameter Menu

Motor Scan Settings Scan Shape Enter scan shape ["Triangle", 1], ["Sawtooth", 0] Triangle motor scan shape (default): Return to the Start Wavelength is performed with scan speed. Sawtooth motor scan shape: Return to the Start Wavelength is performed as fast as possible. laser1:dl:motor:scan:shape (integer) Trigger Threshold Enter output trigger wavelength [nm] Trigger output level is high if current wavelength is above, and low if current wavelength is below the threshold wavelength. The trigger output is available at the Dig I/O D-Sub 15 HD connector at the MOTOR pro module (Please refer to the MOTOR pro manual for details). laser1:dl:motor:scan:threshold-trigger:threshold (real)

5.5

SHG/FHG Cavity Scan/Lock Mode (DLC DL-/TA-SHG/FHG pro)

### 5.5.1 SHG/FHG Cavity Selection

DLC DL-/TA-FHG pro: By pressing the SHG/FHG Cavity button (see Figure 33) several times or tapping the symbol aside, you can choose the desired cavity. The front panel controls change accordingly to control the scan and lock. SHG Cavity: The cavity index 2 at the front panel controls symbolizes the SHG cavity for the 2 nd harmonic generation.

FHG Cavity: The cavity index 4 at the front panel controls symbolizes the FHG cavity for the 4 th harmonic generation.

### 5.5.2 Function Modes

Depending on the selected cavity and function mode, the assignment of the rotary knobs (please refer to section 5.5.6) and the display might change. To select the desired function mode, tap the corresponding symbol at the bottom of the touchscreen (please refer to Figure 33). Please refer to the DL-/TA-SHG/ FHG pro manual for details on setting the parameters. Scan: Parameters for the SHG/FHG cavity scan.

ReLock: Parameters for the SHG/FHG cavity ReLock function.

PID Slow, PID Fast, P Analog: Parameters of the PID controllers. DLC DL-/TA-FHG pro: Please note that P Analog is only available with the SHG cavity selected and the laser must be configured for P Analog adjustment. Please refer to the DL-/TA-SHG/FHG pro manual for details. NOTE !

By default, PID Slow is active. To select PID Fast or P Analog, tap PID Slow and select the desired controller.

PDH: Parameters of the PDH lock.

### 5.5.3 Display Modes

The display of the touchscreen changes depending on the selected display mode. To select the display mode, tap the corresponding symbol at the top of the touchscreen. xy: Signals (Y-direction) are plotted against the cavity scan voltage (X-direction). t (Time): Signals (Y-direction) are plotted against time (X-direction).

f (Frequency): The fast Fourier transformation of the time-dependent signal (Y-direction) is plotted against the frequency (X-direction). Trace Scaling: Tap to select the desired trace scaling.

Up to two traces (Left/Red Signal and Right/Blue Signal, axis labelling in the corresponding color) may be displayed on the touchscreen. The input channels of the two signals can be selected in the context parameter menu which appears on the touchscreen after pressing the Parameter button in SHG/FHG Cavity Scan/Lock mode (please refer to Figure 33). Depending on the setting (Input/Auxiliary trace scaling), the graphs are autoscaled in the Y-direction to the full display size or they can be free-scaled by gestures (pinch and spread) on the touchscreen. The graph can also be fixed to its current size. The zero levels in X- and Y-directions are displayed as dashed lines. On each axis, the distance to the zero level is indicated by the offset value and the direction to the zero level is indicated by a small triangle. The other value at the axis indicates the scaling per division.

### 5.5.4 SHG/FHG Cavity Scan Function Mode

By changing the round-trip length of the SHG/FHG cavity periodically, the user can gain important information about the intra-cavity mode, such as cavity finesse, the incoupling efficiency, or the shape of the Error signal. This length change is called a SHG/FHG cavity scan and is performed by applying a triangle voltage to the slow piezo element that is located on one of the cavity mirrors (please refer to the DL-/TASHG/FHG pro manual for details on SHG/FHG cavity scanning).

Figure 33

Touchscreen in SHG Cavity Scan function mode (example DLC DL-/TA-FHG pro)

To access the SHG/FHG Cavity Scan function mode relevant operator controls, either press the SHG/FHG Cavity button to choose the SHG- or FHG cavity, the Scan/Lock Mode button, and select the Scan function mode until display and rotary knob assignment change as shown in Figure 33 or tap the corresponding symbols. Further SHG/FHG cavity scan and lock parameters are set in the context parameter menu (please refer to section 5.5.7) which appears on the touchscreen after pressing the Parameter button in SHG/FHG Cavity Scan/Lock mode. NOTE !

SHG/FHG cavity scanning continues as long as the scan is enabled even if you leave the SHG/FHG Cavity Scan function mode. Enabling/disabling the SHG/FHG cavity scan is done by tapping the symbol at the top of the touchscreen (gray: scan disabled, red: scan enabled) or in the TOPAS DLC pro PC-GUI.

On the touchscreen, the SHG/FHG cavity scan-dependent signal is displayed in the Y-direction. The parameters 2/4 Scan Offset and 2/4 Scan Amplitude are displayed in the bottom-left and bottom-right corners of the display and can be changed by the corresponding rotary knobs. Changes done at the knobs are reflected by the graphical display and changes made with touch gestures on the display are reflected in the numbers in the corners. For example, dragging the display graph right/left in xy display mode changes the SHG/FHG cavity scan offset while pinching the graph in X-direction increases the SHG/FHG cavity scan amplitude.

### 5.5.5 SHG/FHG Cavity Lock Function Modes

The fundamental beam of the Master Oscillator is only coupled into the SHG cavity efficiently if the round-trip length of the cavity is locked to a multiple of the fundamental wavelength. The same holds for the coupling of the SHG beam into the FHG cavity. TOPTICA uses the Pound-Drever-Hall (PDH) technique to perform this length stabilization of the cavity round trip. In order to imprint sidebands onto the laser carrier frequency, either the laser diode current is modulated directly or the fundamental beam passes an electro-optical modulator. For details on SHG/FHG cavity locking, please refer to the DL-/TA-SHG/FHG pro manual.

Figure 34

Touchscreen in SHG Cavity ReLock function mode (example DLC DL-/TA-FHG pro)

Enter the desired function mode for SHG/FHG Cavity locking (please refer to section 5.5.2) by first pressing the SHG/FHG Cavity button to choose the SHG- or FHG cavity, then the Scan/Lock Mode button (or by tapping the corresponding symbols), and select the desired function mode field at the bottom of the touchscreen. The display and rotary knob assignment change as shown in Figure 34. Further SHG/FHG cavity scan and lock parameters are set in the context parameter menu (please refer to section 5.5.7) which appears on the touchscreen after pressing the Parameter button in SHG/FHG Cavity Lock mode. Press the Lock On/Off button to enable/disable the SHG/FHG cavity lock. NOTE !

When the SHG/FHG cavity lock is disabled, scanning is resumed automatically.

### 5.5.6 SHG/FHG Cavity Scan/Lock Mode Rotary Knob Assignments

The functions assigned to the rotary knobs depend on the selected cavity and function mode. The cavity index 2 at the front panel controls symbolizes the SHG cavity for the 2 nd harmonic generation. The cavity index 4 at the front panel controls symbolizes the FHG cavity for the 4 th harmonic generation.

5.5.6.1

Scan Rotary Knobs

Parameter settings for the SHG/FHG Cavity Scan function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.5.6.2

As selected in the drop-down menu (see section 4.4.2). Available corner parameters depend on the laser system: M Scan Offs [V]: Scan offset for the Master Oscillator scan. Amp Curr [mA]: Tapered Amplifier set current. 2/4 Set Temp [°C]: SHG/FHG crystal set temperature. 2/4 Scan Offs [V]: SHG/FHG cavity scan offset. As selected in the drop-down menu (see section 4.4.2). Available corner parameters depend on the laser system: M Set Curr [mA]: Master Oscillator set current, 2/4 Act Temp [°C]: Display of the SHG/FHG crystal temperature. 2/4 Cav. FF Factor [V/V]: SHG/FHG cavity Feed Forward factor 2/4 Scan Amp [Vpp]: Scan Amplitude for the SHG/FHG cavity scan.

ReLock Rotary Knobs

Parameter settings for the SHG/FHG Cavity ReLock function mode.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
5.5.6.3

2/4 Set Level [V]: Reference voltage for the SHG/FHG cavity lock Error signal. 2/4 Hysteresis [V or mW]: Tolerance between the out-of-lock voltage/power level (2/4 Threshold) and the voltage/power level which determines that the laser is in lock again (please refer to the DL-/TA-SHG/FHG pro manual for ReLock configuration). No function. 2/4 Threshold [V or mW]: Lower voltage/power limit of the SHG/FHG cavity ReLock window.

PID Slow/PID Fast Rotary Knobs

Parameter settings for the Proportional-Integral-Differential (PID) controllers PID Slow and PID Fast. NOTE !

- 
- 
- 
- 
By default, PID Slow is active. To select PID Fast, tap PID Slow and select PID Fast.

Top-left: Bottom-left: Top-right: Bottom-right:

2/4 Slow/2/4 Fast P [V/V]: Proportional gain of the selected PID controller. 2/4 Slow/2/4 Fast Gain: Overall gain factor of the selected PID controller. 2/4 Slow/2/4 Fast I [V/V/ms]: Integral gain of the selected PID controller. 2/4 Fast D [V/V x µs]: Differential gain of the PID Fast controller.

5.5.6.4

P Analog Rotary Knobs (only DLC DL-/TA-SHG pro)

Parameter settings for the Proportional controller P Analog. NOTE !

By default, PID Slow is active. To select P Analog, tap PID Slow and select P Analog. Please note that the laser must be configured for P Analog adjustment. Please refer to the DL-/TA-SHG/FHG pro manual for details.

- Top-left:
5.5.6.5

2 Analog P [V/V]: Proportional gain of the P Analog controller.

PDH Rotary Knobs

Parameter settings for the PDH lock.

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
2/4 Set Level [V]: Reference voltage for the SHG/FHG cavity lock Error signal. 2/4 LO Phase [°]: Phase shift of the local oscillator used for demodulation with respect to the applied modulation. no function. 2/4 PDH Gain [V/V]: Gain for adjusting the peak-to-peak amplitude of the SHG/ FHG Error signal.

### 5.5.7 SHG/FHG Cavity Scan/Lock Mode Context Parameter Menu

Additional SHG/FHG cavity scan/lock and display parameters are set in the context parameter menu which appears on the touchscreen after pressing the Parameter button in SHG/FHG Cavity Scan/Lock mode. On the following pages, detailed information about each accessible parameter is provided. NOTE !

The last line of each parameter description shows the path in the parameter menu. These parameters may also be modified by user-specific software. For a detailed description, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

NOTE !

DLC DL-/TA-FHG pro: The FHG Cavity Scan/Lock Mode context parameter menu is equivalent for control of the FHG Stage. Please note that P Analog is not available.

SHG Cavity Scan Enable SHG Cavity Scan Enable or disable SHG cavity scan [1: enabled], [0: disabled] laser1:nlo:shg:scan:enabled (boolean) SHG Cavity Scan Frequency Enter SHG cavity scan frequency Scan frequency in [Hz] laser1:nlo:shg:scan:frequency (real) SHG Cavity Scan Amplitude Enter SHG cavity scan amplitude Scan amplitude in [V] laser1:nlo:shg:scan:amplitude (real) SHG Cavity Scan Offset Enter SHG cavity scan offset Scan offset in [V] laser1:nlo:shg:scan:offset (real) Feed Forward for SHG Cavity SHG Cavity Feed Forward Enable or disable SHG cavity Feed Forward [1: enabled], [0: disabled] laser1:nlo:shg:pc:feedforward-enabled (boolean) SHG Cavity Feed Forward Factor Enter SHG cavity Feed Forward factor SHG cavity Feed Forward factor in [V/V] laser1:nlo:shg:pc:feedforward-factor (real) SHG Lock Settings PID Selection Select PIDs used for SHG cavity locking ["None", 0], ["PID Slow", 1], ["PID Slow + P Analog", 3], ["PID Slow + Fast", 2] ["PID Slow + Fast + P Analog", 4] laser1:nlo:shg:lock:pid-selection (integer)

SHG PID Fast Use I Cut-off Turn I cut-off on or off [1: on], [0: off] laser1:nlo:shg:lock:pid1:gain:i-cutoff-enabled (boolean) I Cut-off Frequency Enter I cut-off frequency. Frequency below which the integral gain of the PID Fast controller is limited. Frequency in [Hz] laser1:nlo:shg:lock:pid1:gain:i-cutoff (real) Cavity PDH Enable Cavity Local Oscillator Enable or disable cavity local oscillator [1: enabled], [0: disabled] laser1:nlo:shg:lock:local-oscillator:enabled (boolean) Cavity Local Oscillator Amplitude Select local oscillator amplitude in [Vpp] [„0.65“, 0], [„0.58“, 2], [„0.52“, 4], [„0.46“, 6],[„0.39“, 9], [„0.33“, 12], [„0.26“, 16], [„0.19“, 21] [„0.13“, 28], [„0.065“, 40], [„0.017“, 64] laser1:nlo:shg:local-oscillator:attenuation-raw (integer) Enable External Local Oscillator Enable or disable external local oscillator [1: enabled], [0: disabled] laser1:nlo:shg:lock:local-oscillator:use-external-oscillator (boolean) Cav. Lock Detection and ReLock Input Channel Select input channel for out-of-lock detection [„Intra-Cavity Signal“,1], [„SHG Power“, 4] laser1:nlo:shg:lock:window:input-channel (integer) Enable ReLock ReLock upon out-of-lock state [1: enabled], [0: disabled] laser1:nlo:shg:lock:relock:enabled (boolean) ReLock Frequency Enter frequency for ReLock scan Frequency in [Hz] laser1:nlo:shg:lock:relock:frequency (real) ReLock Amplitude Enter amplitude for ReLock scan Amplitude in [Vpp] laser1:nlo:shg:lock:relock:amplitude (real) Delay Delay to action after out-of-lock state is detected Enter the delay between out-of-lock detection and the start of a reset/relock. Delay in [s] laser1:nlo:shg:lock:relock:delay (real) Enable SHG Crystal Temperature Enable or disable SHG crystal temperature stabilization [1: enabled], [0: disabled, Tset = 25 °C] laser1:nlo:shg:tc:enabled (boolean)

Display Settings Trace Scaling Left/Red Y Minimum Enter Ymin for red curve Reasonable values depend on the selected signal. Left/Red Y Maximum Enter Ymax for red curve Reasonable values depend on the selected signal. Right/Blue Y Minimum Enter Ymin for of blue curve Reasonable values depend on the selected signal. Right/Blue Y Maximum Enter Ymax for of blue curve Reasonable values depend on the selected signal. Trace Selection Left/Red Signal (available signals depending on system model) Select signal for red curve ["None", -3], ["SHG PC Voltage", 90], ["SHG PID Fast Output", 91] ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86], ["SHG Intra-Cav. Signal", 82] ["SHG Error Signal", 80], ["SHG Cav. Rej. Signal", 81] Only DLC DL-/TA-FHG pro: ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:nlo:shg:scope:channel1:signal (integer) Right/Blue Signal (available signals depending on system model) Select signal for blue curve Select signal for red curve ["None", -3], ["SHG PC Voltage", 90], ["SHG PID Fast Output", 91] ["Seed Power", 85], ["Amp. Power", 84], ["SHG Power", 83] ["Fiber Power", 86], ["SHG Intra-Cav. Signal", 82] ["SHG Error Signal", 80], ["SHG Cav. Rej. Signal", 81] Only DLC DL-/TA-FHG pro: ["FHG PC Voltage", 120], ["FHG Power", 113] laser1:nlo:shg:scope:channel2:signal (integer) Display Refresh Rate Select display refresh rate Frequency in [Hz] ["1 Hz", 1], ["2 Hz", 2], ["3 Hz", 3], ["4 Hz", 4], ["5 Hz", 5], ["10 Hz", 10] laser1:nlo:shg:scope:update-rate (integer) Display Mode Select display mode [“X/Y”, 0], ["Time", 1], ["Frequency", 2] laser1:nlo:shg:scope:variant (integer) Time Time Base Select time base Time in [ms] [“10 µs”, 0.01], [“20 µs”, 0.02], [“50 µs”, 0.05], [“100 µs”, 0.1], [“200 µs”, 0.2] [“500 µs”, 0.5], [“1 ms”, 1], [“2 ms”, 2], [“5 ms”, 5], [“10 ms”, 10], [“20 ms”, 20] [“50 ms”, 50], [“100 ms”, 100], [“200 ms”, 200], [“500 ms”, 500], [“1 s”, 1000] Laser1:nlo:shg:scope:channelx:scope-timescale (real)

Frequency Frequency Base Select frequency base Frequency in [kHz] [“500 Hz”, 0.5], [“1 kHz”, 1], [“2.5 kHz”, 2.5], [“5 kHz”, 5], [“10 kHz”, 10] [“25 kHz”, 25], [“50 kHz”, 50], [“100 kHz”, 100], [“250 kHz”, 250] [“500 kHz”, 500], [“1 MHz”, 1000], [“2.5 MHz”, 2500], [“5 MHz”, 5000] laser1:nlo:shg:scope:channelx:scope-spectrum-range (real)

5.6

Wavelength Control Mode (DLC TOPO)

The wavelength of a TOPO head can be tuned by varying the diode temperature of the DFB pro BFY pump laser or the intracavity crystal position (Motor Position), the intracavity etalon angle (Etalon Servo Position), or the intracavity piezo (PZT) voltage (OPO Slow PZT Voltage). Tuning the crystal position is best for coarse tuning over wide wavelength ranges whereas etalon angle tuning is preferred for moderate wavelength jumps (30 GHz). For fine wavelength accuracy, pump laser thermal tuning has the advantage of large mode-hop-free scans (up to 500 GHz for the idler output of the TOPO head). Piezo voltage tuning is best for applications requiring fast scanning over very small ranges (50 MHz), such as line locking. Detailed information on wavelength selection and operation is provided in the dedicated TOPO head manual. To access the Wavelength Control mode relevant operator controls, either press the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 35 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols that appear after tapping. Select to change the display of the touchscreen as well as the assignment of the rotary knobs as needed for setting the most important wavelength control parameters.

Figure 35

Wavelength Control mode (DLC TOPO)

Rotary Knobs:

- Top-left:
- Bottom-left:
- Top-right:
- Bottom-right:
Etalon Servo Position [servo steps]: The etalon motor moves in 10-step increments, with each increment giving 20 arc-minutes of resolution (range: 4000 - 8000). TC Set Temperature [° C]: DFB pro BFY pump laser temperature. OPO Slow PZT Voltage [V]: Intracavity piezo (PZT) voltage in the range of 0 - 140 V. Motor Position [mm]: Intracavity crystal position with a resolution of 40 nm over a 0 - 17.5 mm range.

NOTE !

Adjustments smaller than 100 nm do not cause any noticeable changes in wavelength or power of the DLC TOPO laser system.

NOTE !

The external fiber amplifier of the DLC TOPO laser system requires 2 - 5 mW of input power. To make sure that the DFB pro BFY pump laser output is inside this range, the Set Current (see section 5.4.7.1) of the DFB pro BFY pump laser should never be changed from the factory setting (see DFB CC Set Current in section 02 of the DLC TOPO Production and Quality Control Data Sheet). Consequently, please use CC Analog Remote Control of the DFB pro BFY current only for locking purposes, and do not use the Feed Forward feature, as this also affects the laser diode current.

5.7

Wavelength Control Mode (DLC TOPO smart)

The wavelength of a TOPO smart laser head can be tuned by varying the laser diode temperature of the DFB master oscillator or the intracavity crystal temperature. Tuning the crystal temperature is best for coarse tuning over wide wavelength ranges. For fine wavelength accuracy, master oscillator laser thermal tuning provides mode-hop-free scans of the idler. Detailed information on wavelength selection and operation is provided in the dedicated TOPO smart laser head manual. To access the Wavelength Control mode relevant operator controls, either press the Scan/Lock Mode button several times until display and rotary knob assignment change as shown in Figure 36 or tap the corresponding symbol. The little white arrow in the symbol indicates that there are further options available that can be selected by tapping one of the corresponding symbols that appear after tapping. Select to change the display of the touchscreen as well as the assignment of the rotary knobs as needed for setting the most important wavelength control parameters.

Figure 36

Wavelength Control mode (DLC TOPO smart)

Rotary Knobs:

- Top-left:
- Top-right:
Master Set Temperature [° C]: Temperature setting of the DFB master oscillator. Crystal Set Temperature [° C]: Temperature setting of the nonlinear crystal.

5.8

Lock On/Off

NOTE !

DLC DL-/TA-SHG/FHG pro: The Lock On/Off button controls the lock of the component which is selected by the Laser 1 or SHG/FHG Cavity button. Laser 1 selected and highlighted: Master Oscillator lock is controlled. SHG/FHG Cavity selected and highlighted: SHG/FHG cavity lock is controlled.

To lock the laser frequency to the wavelength of interest, either a lockpoint candidate must be selected on the signal (see section 5.4.5), or Lock Settings > Lock Without Lockpoint must be enabled in the context parameter menu. For examples on locking, please refer to section 5.4.9 and section 5.4.10. Lock the selected laser (Laser 1 .. 4 buttons, see section 5.11) by tapping the lockpoint candidate (if present) and then pressing the Lock On/Off button or tapping the corresponding symbol. The laser is unlocked by pressing the Lock On/Off button or by tapping the corresponding symbol, again. The Lock On/Off symbol changes corresponding to the locked (red)/unlocked (gray) status. The SHG/FHG cavity lock does not use the lockpoint concept but locks the SHG/FHG PC voltage to a cavity resonance close to the center of the SHG/FHG PC voltage range.

Figure 37

Touchscreen in Scan/Lock mode, laser unlocked (example)

### 5.8.1 Lock On/Off at a DLC pro for Dual- or Quad-Laser-Operation

At a DLC pro for Dual- or Quad-Laser-Operation with Lock option installed, the Lock On/Off symbol is split.

Figure 38

Lock On/Off button with Dual-Laser-Operation (left) or Quad-Laser-Operation (right) and Lock option installed

Lock the selected laser (Laser 1 .. 4 buttons, see section 5.11) by tapping the lockpoint candidate (if present) and then pressing the Lock On/Off button or tapping the corresponding symbol. The laser is unlocked by pressing the Lock On/Off button or by tapping the corresponding symbol, again. The area of the Lock On/Off symbol corresponding to the laser changes according to the locked (red)/unlocked (gray) status.

5.9

Stabilization On/Off

NOTE !

Please refer to sections 5.3.9 and 5.4.6 for detailed information on the power stabilization.

Figure 39

Stabilization On/Off button

Lock the power of the selected laser (Laser 1 .. 4 buttons, see section 5.11) by pressing the Power Stabilization On/Off button or tapping the corresponding symbol (PowerLock). The Power Stabilization On/Off symbol changes its color corresponding to the locked (red)/unlocked (gray) status. Unlock the laser power by pressing the Power Stabilization On/Off button or by tapping the corresponding symbol, again.

### 5.9.1 Stabilization On/Off at a DLC pro for Dual- or Quad-Laser-Operation

At a DLC pro for Dual- or Quad-Laser-Operation, the Stabilization On/Off symbol is split.

Figure 40

Stabilization On/Off symbol at a DLC pro for Dual-Laser-Operation (left) and Quad-LaserOperation (right)

Lock the power of the selected laser (Laser 1 .. 4 push buttons, see section 5.11) by pressing the Power Stabilization On/Off button or tapping the corresponding symbol (PowerLock). The area of the Power Stabilization On/Off symbol corresponding to the laser changes according to the locked (red)/unlocked (gray) status. Unlock the laser power by pressing the Power Stabilization On/Off button or by tapping the corresponding symbol, again.

5.10

SMC Single Mode Control On/Off

NOTE !

Single mode control is only available for DL pro SMC laser heads. Please refer to the SMC manual for details on the single mode control.

Figure 41

SMC Lock On/Off button

When a laser head with SMC single mode control is connected to the DLC pro, the SMC Lock On/Off button is displayed instead of the Power Stabilization On/Off button (see section 5.9). The little white arrow in the symbol indicates that there is also the Power Stabilization functionality available, which can be selected by pressing and holding the SMC Lock On/Off button about 5 seconds, and vice versa. Enable the SMC Lock of the selected laser (Laser 1 .. 4 buttons, see section 5.11) by pressing the SMC Lock On/Off button or tapping the corresponding symbol. The SMC Lock On/Off symbol changes its appearance and color corresponding to the SMC Lock status (red: active/gray: disabled). Disable the SMC Lock by pressing the Lock On/Off button or by tapping the corresponding symbol, again. NOTE !

The SMC single mode control can only be enabled after certain preconditions are met. Please refer to the SMC manual for details. When the single mode control is enabled, Set Voltage and Set Temperature cannot be changed ! Set Current can only be tuned within a limited range which allows the single mode control to operate properly.

Figure 42

SMC Lock disabled (left) and enabled (right)

The parameters for the SMC single mode control are set via the top-left rotary knob (see section 5.4.7.1), in the Scan/Lock mode context parameter menu (see section 5.4.8), and in the parameter menu (laser 1:dl:smc:..., see section 5.14).

### 5.10.1 SMC Lock On/Off at a DLC pro for Dual- or Quad-Laser-Operation

At a DLC pro for Dual- or Quad-Laser-Operation, the SMC Lock On/Off symbol is split.

Figure 43

SMC Lock On/Off symbol at a DLC pro for Dual-Laser-Operation (left) and Quad-Laser-Operation (right)

Enable the SMC Lock of the selected laser (Laser 1 .. 4 buttons, see section 5.11) by pressing the SMC Lock On/Off button or tapping the corresponding symbol. The area of the SMC Lock On/Off symbol corresponding to the laser changes its appearance and color corresponding to the SMC Lock status (red: locked/gray: unlocked. Disable the SMC Lock by pressing the Lock On/Off button or by tapping the corresponding symbol, again.

5.11

Laser Buttons

### 5.11.1 Laser 1

Figure 44

Touchscreen in Scan/Lock mode, Laser 1 selected (example)

After pressing the Laser 1 button or tapping the symbol aside, you can control the laser which is connected to the DLC pro as laser 1. The Laser 1 symbol turns red and the front panel controls change accordingly. To enable laser 1 for laser emission, press the Laser 1 button or tap the symbol aside for one second, until the symbol changes as shown in Figure 45 (right). Now laser emission can be switched on/off by pressing the Emission push button. To disable laser 1 for laser emission, press the Laser 1 button or tap the symbol aside for one second, until the symbol changes as shown in Figure 45 (left). DANGER ! Laser emission is immediately switched on when the laser is enabled by the Laser 1 button and the Emission push button has been toggled to on before. Toggling the Laser 1 button to enabled switches on all laser 1 CC modules.

Figure 45

Laser 1 selected (left) and enabled for laser emission (right)

Figure 46

Laser 1 not selected and not enabled (left) Laser 1 not selected but enabled for laser emission (right)

### 5.11.2 Laser 2 at a DLC pro for Dual- or Quad-Laser-Operation

NOTE !

To use the DLC pro for control of two or up to four lasers (Dual- or Quad-Laser-Operation), an Upgrade for Control of a 2nd or 4 Lasers is required. When the Dual- or Quad-LaserOperation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to sections 11.2 or 11.3 for a step-by-step description on how to upgrade your DLC pro. For installation of the modules, please refer to sections 11.5 and 11.6. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence and the hardware will already be installed.

Figure 47

Touchscreen in Scan/Lock mode, Dual-Laser-Operation, Laser 2 selected (example)

After pressing the Laser 2 button or tapping the symbol aside, you can control the laser which is connected to the DLC pro as laser 2. The Laser 2 symbol turns red and the front panel controls change accordingly. Only laser 1 or laser 2 can be selected at a time.

To enable laser 2 for laser emission, press the Laser 2 button or tap the symbol aside for one second until the symbol changes as shown in Figure 48 (right). Now laser emission can be switched on/off by pressing the Emission push button. To disable laser 2 for laser emission, press the Laser 2 button or tap the symbol aside for one second, until the symbol changes as shown in Figure 48 (left). DANGER ! Laser emission is immediately switched on when the laser is enabled by the Laser 2 button and the Emission push button has been toggled to on before. Toggling the Laser 2 button to enabled switches on all laser 2 CC modules.

Figure 48

Laser 2 selected (left) and enabled for laser emission (right)

Figure 49

Laser 2 not selected and not enabled (left) Laser 2 not selected but enabled for laser emission (middle) Symbol light gray: Laser 2 not connected or no Upgrade for Control of a 2nd Laser (right)

### 5.11.3 Laser 1 to 4 at a DLC pro for Quad-Laser-Operation

NOTE !

To use the DLC pro for control of up to four lasers (Quad-Laser-Operation), an Upgrade for Control of 4 Lasers is required. When the Quad-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.3 for a step-by-step description on how to upgrade your DLC pro. For installation of the modules, please refer to sections 11.5 and 11.6. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence and the hardware will already be installed.

Figure 50

Touchscreen in Scan/Lock mode, Quad-Laser-Operation, Laser 2 selected and additional symbol for selection of Laser 4 displayed. The Laser 1 .. 4 Enabled icon indicates that lasers 2 and 3 are enabled for laser emission (example)

At a DLC pro for Quad-Laser-Operation, the little white arrow in the Laser 1 .. 4 symbols indicates that you can toggle between the lasers by short pressing the Laser 1/3 or Laser 2/4 button or by tapping the symbol aside. Short pressing the Laser 1/3 button toggles between Laser 1 and Laser 3, short pressing the Laser 2/4 button toggles between Laser 2 and Laser 4. After short tapping the Laser 1/3 symbol, an additional symbol for selection of Laser 1/3 appears, after short tapping the Laser 2/4 symbol, an additional symbol for selection of Laser 2/4 appears. DANGER ! Pressing the Laser 1 .. 4 button or tapping the symbol aside for one second enables the respective laser for laser emission. Laser emission is immediately switched on when the laser is enabled by the Laser 1 .. 4 button and the Emission push button has been toggled to on before. Toggling the Laser 1 .. 4 button to enabled switches on all CC modules for the respective laser 1 .. 4.

After selecting the desired laser 1 .. 4 by the respective buttons or symbols aside, you can control the laser which is connected to the DLC pro as laser 1 .. 4. The corresponding Laser 1 .. 4 symbol turns red and the front panel controls change accordingly. Only one of the lasers 1 .. 4 can be selected at a time.

To enable laser 1 .. 4 for laser emission, press the Laser 1 .. 4 button or tap the symbol aside for one second until the symbol changes as shown in Figure 51 (right). Now laser emission can be switched on/off by pressing the Emission push button. To disable laser 1 .. 4 for laser emission, press the Laser 1 .. 4 button or tap the symbol aside for one second, until the symbol changes as shown in Figure 51 (left). DANGER ! Laser emission is immediately switched on when the laser is enabled by the Laser 1 .. 4 button and the Emission push button has been toggled to on before. Toggling the Laser 1 .. 4 button to enabled switches on all CC modules for the respective laser 1 .. 4.

Figure 51

Laser 4 selected (left) and enabled for laser emission (right)

Figure 52

Laser 4 not selected and not enabled (left) Laser 4 not selected but enabled for laser emission (middle)

The Laser 1 .. 4 Enabled icon (see Figure 50) indicates at a glance which of the lasers 1 .. 4 is enabled for laser emission.

Figure 53

Laser 1 .. 4 Enabled icon (example laser 1 and 4 enabled for laser emission)

5.12

SHG/FHG Cavity

Figure 54

Touchscreen in SHG Cavity Scan/Lock mode, SHG Cavity selected (example DLC DL-/TAFHG pro)

DLC DL-/TA-FHG pro: By pressing the SHG/FHG Cavity button several times or tapping the symbol aside, you can choose the desired cavity. The front panel controls change accordingly to control the scan and lock. SHG Cavity

The cavity index 2 at the front panel controls symbolizes the SHG cavity for the 2 nd harmonic generation.

FHG Cavity

The cavity index 4 at the front panel controls symbolizes the FHG cavity for the 4 th harmonic generation.

5.13

Load/Save

Figure 55

Load/Save button

Pressing the Load/Save button or tapping the corresponding symbol allows to perform different tasks:

- Press the Load/Save button once or tap the corresponding symbol once to open the Configuration Manager (please refer to section 5.13.1).
- Press the Load/Save button twice or tap the corresponding symbol twice to quickly store the most
important settings of the parameter menu (please refer to section 5.14) to the flash memory of the DLC pro. Storing the settings is possible on any screen. Tap Back on the Configuration Manager screen (see Figure 56) to return to the previous screen. The stored parameters are immediately active and also loaded upon the next restart of the DLC pro. NOTE !

The function of pressing the Load/Save button twice is equal to Menu > Save Configuration in the TOPAS DLC pro PC-GUI and to the command laser1 .. 4:save.

- Press the Load/Save button on the DLC pro front panel for 5 - 8 seconds to take a screenshot of
the touchscreen. Please refer to section 11.13 for details.

### 5.13.1 Configuration Manager

Figure 56

Configuration Manager

Press the Load/Save button or touch the symbol aside to access the Configuration Manager. Select the desired laser head by pressing the Laser 1 .. 4 button. The Configuration Manager allows to save and load several device parameter configurations, which include laser head operation parameters as well as not laser head specific settings of the DLC pro, e.g., display settings. A configuration file contains the laser head type and its serial number and can only be loaded if this data matches the selected laser head. DANGER ! Before handling configurations, always switch off the laser emission of the connected laser heads via the Emission push button on the DLC pro front panel ! Loading a configuration with the laser emission switched on may result in the direct emission of hazardous laser radiation ! NOTE !

Press the Load/Save button to have the last loaded/saved device parameter configuration resumed at the DLC pro boot procedure.

NOTE !

Servo positions used for the AutoAlign option (motorized mirrors) of the laser head are not stored in the configuration file.

The Configuration Manager screen shows six sections:

- Four device parameter configurations which are stored on the DLC pro (Configuration 1 .. 4).
- A section for loading the factory settings.
- A section (USB Storage, see Figure 57) for selecting configurations from a USB flash drive connected to the USB connector on the DLC pro front panel.
Sections for Device Parameter Configuration 1 .. 4

The four configurations are indicated by a caption (if assigned in the Configuration Manager available in the TOPAS DLC pro menu, see section 6.9), date and time of the last saving, the laser head type and its serial number.

Retrieve&Save

Tapping saves the device parameter configuration for the selected laser head to the DLC pro (Configuration 1 .. 4) or a USB flash drive (USB Storage selected).

Load&Apply

Tapping loads the device parameter configuration. A configuration file contains the laser head type and its serial number and can only be loaded if this data matches the selected laser head (Laser 1 .. 4 button). Otherwise the Load&Apply field is greyed out.

Section for USB Storage

Connect a USB flash drive to the USB connector on the DLC pro front panel and tap Select to open the USB Storage window.

Figure 57

Configuration Manager, USB Storage window The available configurations on the USB flash drive are indicated by the file name, a caption (if assigned in the Configuration Manager available in the TOPAS DLC pro menu, see section 6.9), date and time of the last saving, the laser head type and its serial number.

NOTE !

To be able to save a configuration, the USB flash drive needs a folder "\toptica". Configuration files (*.laserconf) must be located in the folder "\toptica" to be detected. By tapping Retrieve&Save or Load&Apply you can handle the configurations as described above.

Section for Factory Settings Apply NOTE !

Tapping loads the parameter values from the factory settings. Factory settings are certain laser head specific operation parameters, such as laser diode maximum voltages and currents, laser diode polarity, photo diode calibration data and other mostly laser safety related settings. Please note that the factory settings may have been changed formerly by the user, e.g. after an exchange of the laser diode.

5.14

Parameter Menu

NOTE !

For normal operation, set all relevant parameters on the predefined screens and in their context parameter menus. To enable the touchscreen user to change parameters that are not accessible via any predefined screens, review the complete set of DLC pro parameters listed in the parameter menu. For a detailed description on the parameters and associated codes, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Figure 58

Touchscreen showing the parameter menu (example)

Press the Parameter button or tap the corresponding symbol to open the parameter menu on the touchscreen to check and/or change the desired settings.

- The full parameter menu is displayed on the Home screen. A context parameter menus is displayed in Scan/Lock mode. Drag or flick through the list to access more parameters.
- An arrow indicates that further sub-parameters are accessible (see Figure 59). The sub-parameters
are context sensitive; only parameters relevant to the respective DLC pro system appear.

- Move the parameter menu up/down by dragging or flicking.
- Tap a parameter to change it. Depending on the parameter, you can tap switches, select predefined settings or open an editor.
Figure 59

Sub-parameters

For a complete list of the available parameters and their limits, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

# 6 TOPAS DLC pro Graphical User Interface (PC-GUI)

This section describes all controls of the TOPAS DLC pro graphical user interface (PC-GUI) in detail.

## 6.1 System Requirements

System requirements for installation of the TOPAS DLC pro graphical user interface (PC-GUI):

- 
- 
- 
- 
- 
- 
- 
- 
Windows 8, 8.1or 10 operating system TOPAS DLC pro is tested with Windows 10 operating system Min. 1-GHz-Processor Min. 1 GB RAM Min. 100 MB memory available on hard-disk Recommended screen resolution: 1920 x 1200 Recommended setting of Windows Display Scaling: 100 % Depending on the Windows setup, it might be necessary to log in with administrator rights

NOTE !

We recommend operating the DLC pro via Ethernet over using a USB connection due to the higher communication bandwidth. Using a USB to Ethernet adapter on the PC side allows fast communication while having a point-to-point connection between PC and DLC pro – without connecting the DLC pro to the local network or disconnecting the PC from it.

## 6.2 Installation and Start of TOPAS DLC pro

NOTE !

In case releases earlier than TOPAS DLC pro 3.0 are currently installed: Before installing a new release of the TOPAS DLC pro software, please uninstall the current version on your computer. Please follow the procedure described below to install the new software release.

For TOPAS DLC pro installation on your computer, please connect the supplied TOPAS DLC pro USB flash drive and start the installer (path: 1_TOPTICA DLC pro SOFTWARE_x.y.z\ 2_PC-GUI\TOPAS_DLC_pro_x.y.z.exe). The installer will guide you through the installation process.

Figure 60

Installation and license agreement screen?

Start the installation and confirm the license agreement by clicking I Agree.

Figure 61

TOPAS DLC pro folder selection screen

Select the folder where TOPAS DLC pro will be installed. Click Next to continue to the following window. Now all components of TOPAS DLC pro will be installed. In the next window (Figure 61 right) you may choose the name of the program folder which is created in the start menu. Click Install to continue.

Figure 62

Finishing the installation

After the installation is completed, click Finish to close the TOPAS DLC pro installer. Start the TOPAS DLC pro software by clicking the entry in the start menu.

## 6.3 Control of two Lasers (Dual-Laser-Operation)

NOTE !

To use the DLC pro for control of two lasers (Dual-Laser-Operation), an Upgrade for Control of a 2nd Laser is required. When the Dual-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. For installation of the modules, please refer to sections 11.5 and 11.6. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling two laser systems of the type DL pro, DFB pro, DL pro BFY, TA pro, BoosTA pro or two modules in the TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, the second laser is operated in the same way. In the TOPAS DLC pro PC-GUI, indicators and controls for laser 2 are provided in the dashboard (see section 6.5), and in the control windows which are accessed via the menus available from the dashboard. Additional information on the connection and operation of two lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Dual-Laser-Operation upgrade, frequency locking of both lasers is possible.

## 6.4 Control of four Lasers (Quad-Laser-Operation)

NOTE !

To use the DLC pro for control of up to four lasers (Quad-Laser-Operation), an Upgrade for Control of 4 Lasers is required. When the Quad-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. Please refer to section 11.3 for a step-by-step description on how to upgrade your DLC pro. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling up to four laser systems of the type DL pro, DFB pro, DL pro BFY, or up to four DL pro, DFB pro or DL pro BFY modules in the MDL pro or TA pro AL (MTA pro) laser head. In this manual, mainly the operation of one laser is described, all other lasers are operated in the same way. In the TOPAS DLC pro PC-GUI, Indicators and controls for laser 1 .. 4 are provided in the dashboard (see section 6.5), and in the control windows which are accessed via the menus available from the dashboard. Additional information on the connection and operation of three or four lasers is noted in this manual where necessary. With a single Lock option installed (see section 11.20), in combination with the Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

## 6.5 TOPAS DLC pro Dashboard

The TOPAS DLC pro dashboard offers indicators and basic operator controls for the connected laser heads 1 .. 4, and allows access to windows and tabs for setting operation parameters via various menus. The displayed dashboard items depend on the type of the connected laser head, and can be (de-) selected in the dashboard menu (see section 6.7) which appears after a right click on the top row of the dashboard table. Once all operating parameters for a laser head are properly set in the laser menu windows (see section 6.8) and the TOPAS DLC pro menu (see section 6.9), the most important functions can be conveniently operated via the dashboard.

Figure 63

TOPAS DLC pro dashboard and available menus (examples)

Header Menu

Click Menu to open the TOPAS DLC pro menu (for detailed description of the available menu items, please refer to section 6.9).

Help

Click Help > Manual to open a pdf version of this DLC pro manual. Click Help > Shortcuts to open a list of the available shortcuts for TOPAS DLC pro operation (see section 6.10).

Connected DLC pro

The dashboard displays the connected DLC pro, its label (if assigned), and its serial number to the right of the Help icon.

Error Indicator

The red indicator shows that an error has occurred. The error is displayed as a system message in the communication display section in the footer. Clicking on the Error indicator opens a window where system messages are displayed (see section 6.6).

Footer and Communication Display Section System Message

When a malfunction occurs, the system message and the related code are displayed in the footer.

Connection

Displays the connection currently used for communication with the device.

Communication Indicator

Bright green: Dark green:

Communication. No communication.

## 6.6 System Messages Window

The System Messages window opens after clicking on the red Error indicator in the header (see Figure 63).

Figure 64

System Messages window

Current Messages

NOTE !

The window displays current system messages. To confirm a message, check the box and click Apply.

A system message is only deleted, if the cause of the malfunction is resolved.

Message Log

The window displays all system messages from the last boot procedure of the DLC pro. An empty Description at a message indicates that the respective system message is deleted.

Persistent Messages

For TOPTICA service purposes: The window displays all severe system messages, which are not deleted when the DLC pro is switched off.

Export

Click to save the content of the window as a .txt file.

Apply

Confirms the marked (checkbox) current system message.

Close

Closes the System Messages window.

## 6.7 Dashboard Menu

NOTE !

The dashboard menu allows to configure the dashboard and appears after a right-click on the top row of the laser table displayed in the dashboard (see Figure 63). The menu entries depend on the type of the connected laser.

Figure 65

Dashboard menu (example)

Indicators and Controls of the Dashboard

The displayed items depend on the type of the connected laser head, certain items can be (de-)selected in the dashboard menu which appears after a right click on the top row of the dashboard table.

ID

Connected laser head 1 .. 4. The color code of the optional small ribbon (for editing, see section 6.8) helps to distinguish all displayed windows related to the respective laser head 1 .. 4.

Laser Label

Displays a customer-specific name for the respective laser. After a right click on the Laser Label field, a dialog window opens to edit the laser label. Click Set Label to store the laser label.

Product Name

Displays the type and the serial number of the connected laser 1 .. 4.

Health

A green Health indicator shows proper operation of the system, the indicator turns red in case a malfunction has occurred. Usually a red Health indicator leads to a system message in the System Messages window (see section 6.6). Green: System operating properly. Red: Malfunction of laser head or DLC pro laser controller.

Emission

The white indicator corresponds to the Emission Radiation Warning LED on the DLC pro front panel and indicates laser emission of the respective laser.

DANGER ! When the Laser Radiation Emission Warning indicator lights up white, be aware that there is laser emission.

Laser Enabled

To enable the respective laser head for laser emission, click the Laser Enabled button until the symbol turns red. Now laser emission can be switched on/off by pressing the Emission push button on the DLC pro front panel. To disable the respective laser head for laser emission, click the Laser Enabled button until the symbol turns gray.

DANGER ! Laser emission is immediately switched on when the laser is enabled by the Laser Enabled button and the Emission push button on the DLC pro front panel has been toggled to on before. Toggling the Laser Enabled button to enabled switches on all CC modules for the respective laser head.

Scan Enabled

NOTE !

Click Scan Enabled to activate/deactivate the frequency scan of the laser. When the scan is activated, the symbol turns red. Previous setting of the scan related parameters is required, please refer to section 7.2.

Activating the scan is only possible when the laser is not locked.

Lock Enabled

(Only with Lock option installed) Click the Lock Enabled button to lock/unlock the laser to the selected lockpoint candidate. When the laser is locked, the symbol turns red. Previous setting of the lock related parameters is required, please refer to section 7.2.

PowerLock Enabled

Click PowerLock Enabled to enable/disable the laser power stabilization (PowerLock). When the PowerLock is enabled, the symbol turns red. Previous setting of the PowerLock-related parameters is required, please refer to section 7.7.

SHG Cavity Lock Enabled

Previous setting of the SHG cavity lock-related parameters is required, please refer to section 7.4.

FHG Cavity Lock Enabled

Previous setting of the FHG cavity lock-related parameters is required, please refer to section 7.5.

Scopes Checkboxes

NOTE !

(Only displayed with when more than two lasers are connected to the DLC pro).

The DLC pro signal-processing unit features two independent "digital oscilloscopes", each of which is able to record 3 parallel data streams with sampling rates of up to 2.7 MS/s in real-time. These data-acquisition engines or "scope engines" are the backbones of features like Signal Display and Wide Scan Display. If more than two lasers are operated with a DLC pro, the two scope engines must be shared among the lasers, which means only two of the lasers can make use of data-acquisition features at a time. For example, while it is possible to open the Signal Display windows for three or four lasers at a time, only two of them can show measurement trace updates at the same time. The others stay on hold. Please note that the same restrictions apply for respective operation via the touchscreen user interface. Limitations in data stream multiplexing: The data-acquisition engines, mentioned above, get their data from "digital data streams", emitted by hardware modules of the DLC pro, or from laser head electronics connected to the DLC pro via an LVDS cable (as in DLC CTL and DLC DL-/TA-SHG/FHG pro systems). The number of data streams for transmitting multiple data signals in parallel is limited for LVDS and for hardware modules. Some modules and laser heads offer more different signals than parallel data streams are available. Furthermore, some of the data streams will be permanently occupied by data signals required for fundamental internal tasks or power stabilization. As a result not all the available signals can be processed by the data-acquisition engines at the same time. When you try to select the a certain signal to be displayed in the Signal Display or to be recorded in a WideScan you might get a message stating "signal currently unavailable because all data streams are in use (see system summary)". In this case you need to free one of the data streams before being able to select your signal. For example first set both signals of the Signal Display to None and then select you signal, or deselect the signal for the input of the power stabilization. In the System Summary (Menu > Device Configuration Misc Section > Read System Summary) the section "multiplexing channels" will show you how many data streams are available for a certain laser head or module and how they are in use. In case more than two lasers are connected to a DLC pro, the dashboard will offer a column Scopes with checkboxes used to link/unlink a maximum of two lasers with the two scope engines. Only the lasers which have the Scopes box checked, can use the following features: Signal Display updates Lock Point selection

NOTE !

Lock point selection: In order to use the Lock Points tool (see section 7.2.1, available if lock license is installed) for selecting a lock point candidate, a scope engine is required. The PID controllers themselves are independent, though, and once the lock is closed, the scope engine can be unlinked from the laser, without affecting the lock. In case Lock Without Lockpoint is selected (see sections 5.4 and 7.2), no scope engine is required for activating the lock. Lock Wizard execution Wide Scan/Recorder execution Auto PDH execution Auto LIR execution Diagnosis Report generation (requires user level SERVICE) FLOW and SMILE optimization (DLC CTL)

NOTE !

DL-/TA-SHG/FHG pro laser heads: These laser heads have their own signal-processing units integrated into the laser head electronics. The SHG Signal Displays and FHG Signal Displays are independent from the two scope engines discussed here.

## 6.8 Laser Menu

NOTE !

The laser menu allows access to the control windows for the respective laser 1 .. 4 and appears after a right-click on a laser row of the table displayed in the dashboard (see Figure 63). The menu entries depend on the type of the connected laser.

Figure 66

Laser menu (example)

Laser Control

Click to open the Laser Control window for the respective laser 1 .. 4 (see section 7). The tabs displayed in the Laser Control window depend on the connected laser.

Laser Diagnosis

(Only available in user level SERVICE). Click Laser Diagnosis to open the Laser Diagnosis window. Depending on the configuration of the laser system, certain tests to be performed during the diagnosis procedure can be selected. Do not change the factory selection, except when requested by TOPTICA service. Click Generate Diagnosis Report in the Laser Diagnosis window to start the diagnosis procedure. This generates a binary file (*.bin) for TOPTICA service purposes. Depending on the laser head type, the generation of this report includes the monitoring of characteristic curves for laser diodes and amplifier chips, as well as for piezo and servo health. System parameters may be altered during the generation of this report. A dialog window appears to choose the destination to save the generated file. Click Close to exit the Laser Diagnosis window.

NOTE !

During generation of a Diagnosis Report, the LEDs on some DLC pro plug-in modules may light up in red, and the Laser Radiation Emission Warning LEDs on the laser head may be off for a couple of minutes. This does not indicate an error, and does not require action by the user. Laser emission will be restored afterwards.

NOTE !

It is recommended to generate the diagnosis report only in a stable system status, e.g. after all temperatures have settled.

Signal Display

(Not with DL-/TA-SHG/FHG pro laser head) Adds the Signal Displays for laser 1 .. 4 to the screen.

NOTE !

For showing the Lock-relevant functions of the Signal Display, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PCGUI (please refer to section 11.20).

NOTE !

When you display Signal Display and Parameter Trace windows at the same time, you can display one window at full size in the front for better viewing. Do this by picking the window at the title bar and pulling it in the center of the right screen area. The window to be displayed in the front is then selected by buttons at the bottom of the right display area which are labeled accordingly. Each display window may also be moved to any screen position when picked at the title bar.

NOTE !

Limitations in data stream multiplexing: Please note the limitations for transmitting multiple data signals in parallel described in section 6.7, Scopes Checkboxes.

Figure 67

Signal Display showing the Lock Input signal (Input Trace Signal, red) and the Lock-In Output signal (Auxiliary Trace Signal, blue) for Top of Fringe locking and lockpoint candidates (example)

NOTE !

The signals displayed on the Signal Display are simultaneously shown on the touchscreen of the DLC pro.

The Signal Display displays various signals, e.g. for finding resonance frequencies, optimizing scans, locking and for characterizing the laser. Turn the Signal Display on and off with the Signal Display entry in the laser menu. The Signal Display offers three modes of operation: XY, Time and Frequency. In XY mode the signals (Y-direction) are plotted against the scan of the laser (X-direction), in time mode against time. Frequency mode shows a fast Fourier transform of the signal. It is possible to switch between these three modes with the corresponding buttons on the top of Signal Display. A click with the right mouse key on the axis label allows you to select the axis-scale. Two tools are available: Select Zoom and use the mouse wheel to zoom in or out. Another option to zoom in is to hold the left key of the mouse and drag over the desired detail of the graphs from top left to bottom right. Dragging over the graphs from bottom right to top left undoes the last zoom. The display can be shifted right or left by holding the right mouse key. In XY mode, normally a signal is displayed depending on the laser frequency while the laser is scanned. When zooming or moving the displayed spectrum in this mode, the actual scan parameters (scan amplitude and scan offset) are modified. Use the Lock Points Tool for showing and selecting lockpoints, etc. (for details please refer to section 7.2.1). Zooming and shifting the display is performed as described above in the Zoom section. Enable/disable the lock by clicking the Lock Enable button or by double-clicking on the desired lockpoint candidate. The Lock Status (only in XY mode) shows the actual status of the lock. Click the Scope Enable button (only present, if more than two lasers are connected to the DLC pro) to use one of the two available scope engines for signal display updates (for detailed information on the scope engines, please see the Scope checkboxes description in section 6.7). When the laser is locked, the Signal Display shows the Lock Input signal during the last scan before the lock was enabled (default black trace) and the actual Lock Input signal as a point cloud (default red) in red brackets (see Figure 68).

Figure 68

Signal Display when the laser is locked (example)

NOTE !

Due to the enabled lock, the scan is disabled. In XY mode the Lock Input signal now appears as a point cloud because the scan output (X-axis) remains constant and all Y-values are plotted against this constant X-value.

In case one of the used PID controller outputs is equal to the scan output, the X-value does not remain constant, reflecting the action of the PID controller. Depending on the required action of the PID controller to keep the lock stable, the point cloud may leave the displayed X-axis range. In this case a red arrow shows the direction to the point cloud. The red arrow also helps to judge if the laser is still locked. When the laser is out-of-lock, the red arrow will not point into the expected direction.

Figure 69

Red arrows showing the direction to the Lock Input signal point cloud

Right clicking in the graph area allows you to configure the graph appearance (color and thickness of traces, etc.) and to use the Lock Candidate Filter for deselecting unwanted lockpoints. The displayed signal can also be exported as an image. Configure scaling by right-clicking on the axis labels. At the bottom of the Signal Display, you can select the display Refresh Rate as well as the Auxiliary Trace Signal that is displayed on the right Y-Axis. The Input Trace Signal, which is displayed on the left axis, is always the Lock Input signal: you can select it in the Scan & Lock tab (Lock Settings > Lock Input Signal). Click Hold to freeze the display image.

Display Mode XY

Signals (Y-direction) are plotted against the scan of the laser (X-direction).

Time

Signals (Y-direction) are plotted against time (X-direction).

Frequency

Frequency mode shows a fast Fourier transform of the signals.

Tools Zoom

Use the mouse wheel to zoom in or out. Another option to zoom in is to hold the left key of the mouse and drag over the desired area of the graphs from top left to bottom right. Dragging over the graphs from bottom right to top left undoes the last zoom.

Lock Points

Use this tool for showing and selecting lockpoints, etc. (please refer to section 7.2.1). When selected, the Input Trace Signal is fixed to the Lock Input signal.

Lock Enable

Enables/disables the lock.

Lock Status

The Lock Status (only in XY mode) shows the actual status of the lock. Selecting: Lockpoint candidates are displayed. Selected: Lockpoint candidate is selected. Locking: Lock is enabled, lockpoint not reached, yet. Locked: Laser is locked to the selected lockpoint. On Hold: PID outputs are frozen. Resetting: PID output channels are reset to zero. Reset: PID output channels are on zero level. Relocking: A ReLock scan is performed.

NOTE !

When Lock Without Lockpoint in the Scan & Lock tab is checked, Lock Enable and Lock Status are present in every Display Mode.

Scope Enable

Click the Scope Enable button (only present, if more than two lasers are connected to the DLC pro) to use one of the two available scope engines for Signal Display updates (for detailed information on the scope engines, please see the Scope checkboxes description in section 6.7).

Time Base (only Time mode)

The time base for the Signal Display can be adjusted.

Frequency Base (only in Frequency mode)

The frequency base for the Signal Display can be adjusted.

Display Refresh Rate

Select display refresh rate for the Signal Display.

NOTE !

The actual refresh rate may be limited by the Scan Frequency set in the SC Scan Control section of the Laser tab (see section 7.1.1), or the ReLock Frequency set in the ReLock section of the ReLock tab (see section 7.3). Keep that in mind when setting very low Scan Frequency or ReLock Frequency values.

Input Trace Signal

Select input channel for the input trace signal.

Auxiliary Trace Signal

Select input channel for the auxiliary trace signal.

Hold

Freezes the display image when the box is checked.

Autosave

The checkbox Autosave allows to easily store time series of Signal Display measurements. If checked, every single data update of the Signal Display will be exported into a *.csv file on your computer. Signal Display updates can come with a maximum refresh rate of up to 10 Hz, meaning that up to 10 *.csv files would be created per second. The refresh rate can be limited by the Display Refresh Rate selector and furthermore depends on the scan frequency and the required measurement time, which depends on settings like the Display Mode (XY, Time, Frequency) etc. After checking the Autosave box, a window will appear, where you can choose which of the two data traces you want to export. Furthermore you can select the folder on your hard disk the files should be stored in. Filenames will be generated automatically, using the trace signal names and a timestamp. Finally start the automatic export by pressing the Start... button. For stopping the automatic export simply uncheck the Autosave box again.

Master Signal Display

(Only with DL-/TA-SHG/FHG pro laser head) Adds the Signal Display window for the Master Oscillator of the DL-/TA-SHG/FHG pro laser head to the screen (please refer to the Signal Display description above).

SHG Signal Display FHG Signal Display

(Only with DL-/TA-SHG/FHG pro laser head) (Only with DL-/TA-FHG pro laser head) Adds the Signal Display window for the SHG/FHG cavity of the DL-/TASHG/FHG pro laser head to the screen.

NOTE !

Limitations in data stream multiplexing: Please note the limitations for transmitting multiple data signals in parallel described in section 6.7, Scopes Checkboxes.

Figure 70

Example: SHG Signal Display (DLC DL-/TA-SHG pro) showing the SHG Intra-Cavity Signal (yellow trace) and the SHG Error Signal (red Trace)

Please refer to the Signal Display description in section 6.9. Note that the Lock Points tool is not available in the SHG/FHG Signal Display. Lock Enable

Enables/disables the cavity lock.

Lock Status

The Lock Status (only in XY mode) shows the actual status of the cavity lock. Idle: Cavity scan disabled or cavity piezo is scanning. Locking: Cavity lock is enabled, lock not reached, yet. Locked: Cavity is locked.

Left Axis Signal

Select input channel for the Left Axis signal.

Right Axis Signal

Select input channel for the Right Axis signal.

Wide Scan Display

Adds the Wide Scan Display window to the screen.

NOTE !

When you display Wide Scan Display and Parameter Trace windows at the same time, you can display one window at full size in the front for better viewing. Do this by picking the window at the title bar and pulling it in the center of the right screen area. The window to be displayed in the front is then selected by buttons at the bottom of the right display area which are labeled accordingly. Each display window may also be moved to any screen position when picked at the title bar.

NOTE !

Limitations in data stream multiplexing: Please note the limitations for transmitting multiple data signals in parallel described in section 6.7, Scopes Checkboxes.

Figure 71

Wide Scan Display showing a molecular absorption spectrum (left/red curve) and the TC Temperature signal (right/blue curve)

NOTE !

The signals displayed on the Wide Scan Display are simultaneously shown on the touchscreen of the DLC pro. When Scan Shape > Triangle is selected in the Wide Scan section of the Laser tab (see section 7.1.1), do not use the screen display for analysis, as it shows artifacts. The full resolution of all recorded data points can be exported after right clicking in the graph area of the Wide Scan Display.

The Wide Scan Display shows various signals, e.g. for finding resonance frequencies over the entire tuning range of the laser diode. Turn the Wide Scan Display on and off with the Wide Scan Display entry in the laser menu. A click with the right mouse key on the axis label allows you to select the axis-scale. Use the mouse wheel to zoom in or out. Another option to zoom in is to hold the left key of the mouse and drag over the desired detail of the graphs from top left to bottom right. Dragging over the graphs from bottom right to top left undoes the last zoom. The display can be shifted right or left by holding the right mouse key. Normally a signal is displayed depending on the laser frequency while the laser is scanned. The Scan Status shows the actual status of the wide scan. Right clicking in the graph area allows you to configure the graph appearance (color and thickness of traces, etc.). The displayed signal can also be exported as an image. Configure scaling by right-clicking on the axis labels. At the bottom of the Wide Scan Display, you can select the Left/Red Signal (left Y-axis) and the Right/ Blue signal (right Y-axis). NOTE !

A selected signal is displayed not until after a start of a wide scan.

Scan Status

Disabled: Setting Output Channel to start value:

Scan Active: Resetting Output Channel:

Controlled by External Trigger:

Wide scan is disabled.

Wide scan was initiated by the Play button, but has not started, yet. Temperature or wavelength is set to the Start value entered in the Wide Scan section of the Laser tab (see section 7.1.1). Wide scan in progress.

Temperature or wavelength is set to the Set value entered in the Wide Scan section of the Laser tab (see section 7.1.1).

Input Trigger is enabled and wide scan was initiated. The status message remains until the wide scan is stopped.

Scope Enable

Click the Scope Enable button (only present, if more than two lasers are connected to the DLC pro) to use one of the two available scope engines for Wide Scan Display updates (for detailed information on the scope engines, please see the Scope checkboxes description in section 6.7).

Left Trace Signal

Select input channel for the Left Trace signal.

Right Trace Signal

Select input channel for the Right Trace signal.

Autosave

The checkbox Autosave allows to easily store time series of Wide Scan Display measurements (not with Wide Scan set to Repeat). If checked, every single data update of the Wide Scan Display will be exported into a *.csv file on your computer. After checking the Autosave box, a window will appear, where you can choose which of the two data traces you want to export. Furthermore you can select the folder on your hard disk the files should be stored in. Filenames will be generated automatically, using the trace signal names and a timestamp. Finally start the automatic export by pressing the Start... button. For stopping the automatic export simply uncheck the Autosave box again.

Notes on the Functionality of the Wide Scan: The wide scan precisely scans a laser parameter and simultaneously acquires data on two input channels. It enables recording up to 5 million data points per channel in a scan. Depending on the laser type, users can decide to scan one of the following parameters:

- 
- 
- 
- 
Set wavelength or piezo voltage for DLC CTL Laser diode temperature or current for DLC DFB pro or DLC DL pro BFY Piezo voltage or laser diode current for DLC DL pro One of the analog outputs Out A or Out B for any of the above

This scan option also works for lasers that are part of a DLC TA pro/-AL or DLC DL-/TA-SHG/FHG pro system, then the available parameters for scanning are according to the seed lasers. The scan range is limited by the physical boundaries of the chosen parameter to be scanned. E.g. a wide scan of the CTL wavelength is limited by the minimum and the maximum wavelength of the CTL. A wide scan of the temperature of a DFB pro or DL pro BFY is limited by the tuning properties of the respective laser diode and/or the working range of the thermistor. In Wide Scan mode, it is recommended not to change the Set value of the parameter to be scanned (see section 7.1.1) once the scan has started. For slowly changing parameters, like the laser temperature, please be patient while the laser tunes to the start point of the scan. In general, the number of data points recorded will be much bigger than the one displayed on the screen. In order to visualize narrow spectral features, the display actually shows an envelope graph which represents the minimum and maximum values of an interval by a data point each. The envelope is re-calculated whenever the zoom range or the data points change. It is possible to zoom into the recorded data while the scan is still in progress. Use the Full Range button (see section 7.1.1) to return to the full-scale display of the scan. A new scan will always start from the set limits, which may differ from the range displayed on the touchscreen, in particular after a zoom. Once a feature of interest has been found, one may wish to investigate it further, or lock the laser frequency to it. The button Center (see section 7.1.1) changes the Set value of the parameter to be scanned (e.g., the laser diode temperature, CTL wavelength, ...) to the center of the currently zoomed window. Once the change has taken effect, it is possible to switch to Scan/Lock mode (see section 5.4), e.g., for investigating narrow features with a reduced/faster scan or to lock the laser. Alternatively, the button Zoom Range (see section 7.1.1) sets the Start and End values of the wide scan to the left and right borders of the current zoom. The wide scan can then be repeated more slowly and/or with higher resolution. The number of data points to be recorded per channel, depends on selected scan shape, scan amplitude and recorder step size. For example, doing a sawtooth scan with the wavelength of a CTL laser head over a range of 50 nm, while recording with a step size of 0.00001 nm, will result in about 5,000,000 samples per channel. Exporting this data with the PC-GUI will produce a 170 MB "comma-separated-values" file (*.csv), which might be difficult to handle for data visualization software. Equally, the response of the touchscreen can be slower, as the visualization of up to 5 million data points requires quite a bit of computation. If the full number of data points is not required, it is therefore recommended to reduce the scan resolution. The scan resolution is indicated by the parameter laser1:wide-scan:recorder-stepsize (Parameters window, see section 6.9), which can be influenced by:

1.
The Recorder Stepsize Set field (see section 7.1.1) is used to configure the target resolution. Set it to 0 if you need the highest possible resolution or give it a reasonable value of your choice.

2.
The parameter laser1:recorder:sample-count-limit (Parameters window, see section 6.9) is used to configure a maximum number of data points per channel. Use this to limit the amount of data for better touchscreen performance or smaller exported file sizes.

The parameter laser1:wide-scan:recorder-stepsize will be calculated by first trying to achieve the target step size while considering the constraints of the data acquisition hardware and data transfer rates, but eventually increasing the value to reduce the resulting sample count to below the given limit.

While the wide scan of each single laser can record up to 5 million data points per channel during a scan, in a multi-laser setup, memory constraints result in limitations for the overall number of data points. The wide scans of all lasers need to share 100 MB of internal DLC pro memory (Please note that the size of a CSV file is approximately a factor of three higher than the internal memory requirements of the corresponding wide scan run). It is up to the user to distribute the memory among the available wide scans. The wide scan doing the first scan gets all the memory it requests and will keep it until it gets started again or until the user releases its memory. For the next laser's wide scan the user must eventually reduce the sample count such that its memory requirements can be satisfied by the memory left over by the first wide scan. The available memory for the third and fourth laser results correspondingly. The predicted amount of required memory for the next run is indicated for each wide scan in the Memory Size field (see section 7.1.1). Note on Thermal Tuning of a DFB pro or DL pro BFY Laser: The Wide Scan mode offers a very high temperature resolution: 1 bit corresponds to 1.4 x 10-6 K. The actual temperature resolution may differ, due to electronic noise and the properties of the TEC in the diode package. The effective temperature resolution is on the order of 50 µK. The limits of a wide scan are ultimately given by the measurement range of the thermistor inside the laser head, which typically works from 2.2 °C to 51.8 °C. The useable temperature range of a specific DFB pro or DL pro BFY laser depends on the characteristics of the respective diode: When the temperature is tuned, the gain of the semiconductor medium typically shifts about 4 times faster than the grating-defined lasing wavelength. This may cause the diode to jump into a “free-running” (i.e. no longer frequency-stabilized) operation mode at the gain maximum. These operation regimes are excluded by TOPTICA, by restricting the temperature range accordingly.

Optimization Tools > Optimization Progress Monitor (Only with DL-/TA-SHG/FHG pro laser head equipped with the AutoAlign option (motorized mirrors)) Adds the Optimization Progress Monitor window to the screen.

Figure 72

Optimization Progress Monitor window (DLC DL-/TA-SHG/FHG pro with AutoAlign option)

The Optimization Progress Monitor shows the progress of the power optimization procedure which is selected and started in the Optimization/Stabilization tab of the TOPAS DLC pro PC-GUI or in the Optimization/Stabilization sub menu which is available on the touchscreen after pressing the Home button. The optimization progress is displayed in different colors: TA Power SHG Power FHG Power Fiber Power

red blue green white

(only DLC TA-SHG/FHG pro) (only DLC DL-/TA-FHG pro) (only with option FiberMon)

Optimization Tools > Lock Wizard NOTE !

Starts a Lock Wizard session for Top of Fringe locking.

For using the Lock Wizard, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).

The Lock Wizard (only available for the Top of Fringe (Lock-In) lock type) is an interactive tool which helps to set-up a Top of Fringe lock. The tool consists of the Signal Display (see Figure 67) and a series of windows which guide you through the steps described in sections 5.4.10, 7.2.3 and 8.3.2. To ensure a convenient lock set-up, commands are executed automatically and individual parameters are set automatically, for others standard values are specified. Next > /< Back

Buttons to navigate between the different lock instruction steps (windows), where different groups of lock-relevant parameters are specified.

Close

Closes the Lock Wizard session without saving parameters.

Finish

Only available in the last instruction window. Clicking saves the lock settings and closes the Lock Wizard session.

NOTE !

If the Lock Wizard does not complete successfully, or is interrupted, a special configuration, which is stored at the start of the Lock Wizard, is loaded.

Optimization Tools > Motor Calibration (Only with MOTOR pro option) Opens the Motor Calibration window to perform a wavelength calibration of the optional motorized wavelength control MOTOR pro. NOTE !

The laser menu entry Motor Calibration is only available in user level MAINTENANCE and with the HighFinesse wavelength meter software installed.

Figure 73

Motor Calibration window for laser 2 (example)

For a detailed description of the operator controls and performing a wavelength calibration, please refer to the MOTOR pro manual.

Optimization Tools > Bode Plots

Adds a display window for transfer functions of the PID controllers to the screen.

NOTE !

For displaying the Bode Plots, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).

Figure 74

Bode Plots window

The depicted Bode Plots give information about the frequency-dependent transfer functions for the PID controllers of the DLC pro (provided with the lock option). The transfer functions will illustrate the gain settings of the PID controllers (overall, proportional, integral, differential, and cut-off frequencies). The input signals of the transfer functions depend on the lock type. With Side of Fringe selected, the input is the Lock Input Signal while for Top of Fringe, the input is the Lock-In Output Signal, as shown in the TOPAS DLC pro PC-GUI. The output signals of the transfer functions are the outputs of the corresponding PID controllers which are PID 1 and PID 2. Magnitude and phase of these transfer functions are displayed over frequency in the upper and lower graph, respectively. NOTE !

Be aware that parts of the system transfer function, such as piezo elements, will add to the PID controller transfer functions and may act as low-pass filters in the overall feedback loop.

Optimization Tools > Bode Plots Master/SHG/FHG

Figure 75

(Only with DL-/TA-SHG/FHG pro laser head) Adds a display window for transfer functions of the PID controllers to the screen.

Bode Plots window (example DLC DL-/TA-FHG pro)

The depicted Bode Plots give information about the frequency-dependent transfer functions for the PID controllers of the DLC pro (provided with the lock option for the Master Oscillator) and of the SHG/FHG Cavity Lock paths. The transfer functions will illustrate the gain settings of the PID controllers (overall, proportional, integral, differential, and cut-off frequencies). For the Master Oscillator lock - provided with the lock option - , the input signals of the transfer functions depend on the lock type. With Side of Fringe selected, the input is the Lock Input Signal while for Top of Fringe, the input is the Lock-In Output Signal, as shown in the TOPAS DLC pro PC-GUI. For the SHG/FHG cavity lock, the input is the SHG/FHG Error Signal. The output signals of the transfer functions are the outputs of the corresponding PID controllers which are PID 1 and PID 2 for the Master Oscillator lock (Master) and PID Slow and PID Fast for the SHG/FHG cavity lock (SHG/FHG). Magnitude and phase of these transfer functions are displayed over frequency in the upper and lower graph, respectively. NOTE !

Be aware that parts of the system transfer function, such as piezo elements, will add to the PID controller transfer functions and may act as low-pass filters in the overall feedback loop.

NOTE !

While the slow SHG/FHG cavity piezo element has a responsivity of 300 nm per Volt, the fast SHG/FHG cavity piezo element changes the cavity's round-trip length by only 30 nm per Volt. Besides, the voltage of the fast SHG/FHG cavity piezo element passes an additional amplifier with a gain of 2. These factors will add to the magnitude of the corresponding transfer functions.

Edit Laser Label

Click to open a dialog window where a customized name for laser 1 ..4 can be assigned.

Edit Ribbon Color

Click to open a window to customize the optional ribbon color. The small ribbon helps to distinguish all displayed windows related to the respective laser head 1 .. 4.

Laser Config DLC DL pro/DLC DFB pro/DL pro BFY

Figure 76

Laser Config window (DLC DL pro/DLC DFB pro/DLC DL pro BFY)

The Laser Config window allows configuration of the laser heads. Depending on the laser type, some or all of these values can be changed. NOTE !

The values entered in this window are applied immediately after entering. If you want to retain these values even after a reboot of the DLC pro, please click the Save button.

For TOPTICA laser heads please refer to the corresponding Production and Quality Control Data Sheet for the proper operating parameters. CC Current Control Maximum Current Use Tuning Clip

Input Field for maximum current. Parameter: laser1:dl:cc:current-clip Checking the box limits the laser diode current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only).

CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip box in the CC Current Control section is mandatory before performing a motor scan. This avoids damage to the laser diode during a motor scan. Set Current Iset

Input Field for set current.

Maximum Voltage Umax

Input Field for maximum voltage.

Polarity Checkbox

Check when laser diode polarity is positive.

NOTE !

Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

TC Temperature Control Set Temperature Tset Save

Input Field for set temperature. Saves all relevant laser head operating parameters so that they are resumed at the DLC pro boot procedure.

Laser Config DLC TA pro/-AL and Seed Laser + BoosTA pro Combination NOTE !

For a DLC BoosTA pro system, only amplifier operating parameters are available.

Figure 77

Laser Config window (example DLC TA pro)

The Laser Config window allows configuration of the laser head. Depending on the laser type, some or all of these values can be changed. NOTE !

The values entered in this window are applied immediately after entering. If you want to retain these values even after a reboot of the DLC pro, please click the Save button.

For TOPTICA laser heads please refer to the corresponding Production and Quality Control Data Sheet for the proper operating parameters.

CC Current Control Master

Settings for CC Master Oscillator.

Maximum Current

Input Field for maximum current. Parameter: laser1:dl:cc:current-clip

Use Tuning Clip

Checking the box limits the laser diode current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only).

CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip box in the CC Current Control Master section is mandatory before performing a motor scan. This avoids damage to the laser diode during a motor scan. Set Current Iset

Input Field for set current.

Maximum Voltage Umax

Input Field for maximum voltage.

Polarity Checkbox

Check when laser diode polarity is positive.

NOTE !

Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

TC Temperature Control Master Settings for TC Master Oscillator. Set Temperature Tset CC Current Control Amplifier

Input Field for set temperature. Settings for CC Tapered Amplifier.

Maximum Current

Input Field for maximum current. Parameter: laser1:amp:cc:current-clip

Use Tuning Clip

Checking the box limits the amplifier current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only).

CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip box in the CC Current Control Amplifier section is mandatory before performing a motor scan. This avoids damage to the amplifier during a motor scan. Set Current Iset

Input Field for set current.

Maximum Voltage Umax

Input Field for maximum voltage.

TC Temperature Control Amplifier Set Temperature Tset Save

Settings for TC Tapered Amplifier. Input Field for set temperature. Saves all relevant laser head operating parameters so that they are resumed at the DLC pro boot procedure.

## 6.9 TOPAS DLC pro Menu

NOTE !

The TOPAS DLC pro menu allows access to general DLC pro control windows and appears after a click on the Menu button displayed in the dashboard. The menu entries depend on the system configuration.

Figure 78

TOPAS DLC pro menu (example)

> Menu > Connect

Establishes a connection to the device selected in the Connection Settings window.

> Menu > Connection Settings

Figure 79

Connection Settings window

TCP/IP

NOTE !

The Connection Settings window opens for configuring the connection settings.

When selected, all devices connected via TCP/IP to the local network are listed in the display area of the Connection Settings Window. After selecting a device, its connection properties (IP address, Command Port and Monitoring Port) are displayed in the respective fields. It is possible to alternatively enter the hostname of the device in the IP address field. This hostname remains, also in case the DHCP server assigns a new IP address to the device. The factory default hostname is the serial number of the DLC pro in the form: DLC_PRO_XXXXXX. An individual hostname can be assigned in the Parameters window of the TOPAS DLC pro PC-GUI by changing the text in the parameter net-conf:hostname (SERVICE user level required).

Serial

Select Serial Port for establishing a serial connection to a device.

Serial Port

Select serial port to which the DLC pro is connected.

Baudrate

Not relevant, setting is ignored by software.

Settings

Not relevant, setting is ignored by software.

Test Connection

Establishes a test connection to the selected device and then closes. When the connection test was successful, a pop-up window displays details on the selected device and the DLC pro plays an acoustic signal. In other cases, a system message appears.

Connect on Startup

When checked, the connection saved by clicking OK is automatically established at the next software start.

Search

Starts a new search for devices connected via TCP/IP.

OK

Saves the settings and closes the window. To establish a connection with these settings, select Menu > Connect

Cancel

Discards changes and closes the window.

> Menu > Disconnect

Closes the connection to the device.

> Menu > Device Configuration NOTE !

The Device Configuration window opens.

Please note that, depending on the connected laser head, some tabs of the Device Configuration menu may not be available.

> Menu > Device Configuration User Level Section

Figure 80

Device Configuration window User Level section

Set User Level

Section for changing the user level.

Current User Level

Displays current user level.

Current Auto-Login

Displays current setting for Auto-Login.

User Level

Select user level.

NOTE !

Changing the user level only affects operation via TOPAS DLC pro PC-GUI. For touchscreen operation the USER level is fixed. READ ONLY: TOPAS DLC pro is set for only displaying the laser operation, all PC-GUI controls are disabled. USER: Setting for daily DLC pro operation. MAINTENANCE: User level for operations needed to maintain the laser (according to the laser safety standard). SERVICE: User level for operations that may change the laser safety classification such as changing the maximum operating current of the laser (service operation according to the laser safety standard). INTERNAL: For internal TOPTICA use only.

NOTE !

If a password for the USER level is introduced (see section 4.9.1), for changing to the MAINTENANCE level this password plus the MAINTENANCE password must be entered as a combined but single password. The SERVICE password remains unchanged.

DANGER ! The user levels MAINTENANCE and SERVICE may only be accessed by authorized and CAUTION ! specially-trained service personnel. Customers entering the MAINTENANCE or SERVICE level need to be aware that wrong parameter values may harm and destroy laser diodes and warranty may be voided. The INTERNAL level is not for customers use.

NOTE !

The user level required for changing a certain parameter is noted in the parameter description in the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro. The user level nomenclatures in the Remote Command Reference and in this manual correspond as follows: 4 > READ-ONLY 3 > USER 2 > MAINTENANCE 1 > SERVICE 0 > INTERNAL

Password

NOTE !

Input field for entering the password required for the respective user level. READ ONLY: No password required. USER: No password required. Please refer to section 4.9.1 for introducing a password for the USER level. MAINTENANCE: For password please refer to the Production and Quality Control Data Sheet. See note below. SERVICE: For password please refer to the Production and Quality Control Data Sheet.

If a password for the USER level is introduced, for changing to the MAINTENANCE level this password plus the MAINTENANCE password must be entered as a combined but single password. The SERVICE password remains unchanged.

Save as Auto-Login Checkbox

When checked, the entered password is saved for Auto-Login.

OK

Clicking changes the user level.

Close

Closes the window.

> Menu > Device Configuration Network Section

Figure 81

Device Configuration window Network section

NOTE !

To activate the new network settings while the DLC pro is connected via TCP/IP, please click Apply Settings and select No in the following confirmation dialog window. Disconnect the TOPAS DLC pro PC-GUI and switch off and on the DLC pro by the ON/OFF switch on the rear panel. After switching off, please wait for at least 10 seconds before switching the DLC pro on again. Then open Menu > Connection Settings, double click the DLC pro with its new IP address and click Menu > Connect. When changing network settings while the DLC pro is connected via TCP/IP, do not restart the DLCpro's network adapter by clicking Apply Settings and confirming the following dialog window with Yes. Restarting the network adapter while using it will cause an undefined state of the adapter. Changing the settings and restarting the adapter works properly if you are connected via USB.

Current Settings IP-Address

Shows the currently active IP address of the connected device.

Netmask

Shows the currently active subnet mask of the connected device.

MAC-Address

Shows the hardware/MAC address of the connected device´s network adapter.

DHCP enabled

Indicates whether the device is configured for automatic IP configuration by a DHCP server.

Use DHCP

Changes the device’s network adapter configuration for automatic setup by a DHCP server. After selecting this option, the IP address and netmask will not yet have changed to the new values. In order to use the DHCP mechanism, use the Apply Settings button and confirm the following dialog window with Yes or reboot the system.

Manual Configuration

Changes the device’s network adapter configuration to a static IP configuration. Provide the desired IP address and netmask in the IP address and Netmask field, respectively. After doing this, the IP address and netmask will not yet have changed to the new values. In order to use the new address, click the Apply Settings button and confirm the following dialog window with Yes or reboot the DLC pro.

IP-Address

Input field for the IP address if you want to use the Manual Configuration button for setting up a fixed IP address. Please enter an IPv4 address in the format “xxx.xxx.xxx.xxx”, (e.g., "192.168.1.1").

Netmask

Input field for the subnet mask if you want to use the Manual Configuration button for setting up a fixed IP address. Please enter an IPv4 netmask in the format “xxx.xxx.xxx.xxx”, (e.g., "255.255.255.0").

Apply Settings

Restarts the network adapter, making use of the new network configuration. Please note that you might lose your current TCP/IP connection if you click the Apply Settings button and confirm the following dialog window with Yes. Please see NOTE ! above.

Close

Closes the window.

> Menu > Device Configuration Misc Section

Figure 82

Device Configuration window Misc section

Serial Number

Displays the serial number of the connected device.

Label

Displays the individual name with which the connected device is identified in the local network.

Label Input Field

Input field for entering an individual name for the currently connected device. The number of characters is limited to 15.

Set Label

Saves the individual name as a label.

NOTE !

The label is displayed in the header and in the device list in the Connection Settings window (see Figure 79) !

Read System Summary

Displays a detailed summary of the DLC pro and the connected laser head.

Generate Service Report

Generates a binary file (*.bin) for TOPTICA service purposes. A dialog window appears to choose the destination to save the generated file. Click Cancel to stop the process.

NOTE !

Do not change settings within the TOPAS DLC pro PC-GUI or the DLC pro front panel while the Service Report is being generated.

Run Service Script

Functionality to run a service script provided by TOPTICA.

Close

Closes the window.

> Menu > Device Configuration Firmware Update Section NOTE !

For a step-by-step description of a firmware update via TOPAS DLC pro, please refer to section 11.18.2.

Figure 83

Device Configuration window Firmware Update section

Firmware Information

Displays information about the current firmware version and status.

Show Log

Displays a log file of the firmware installer.

Show Installation History

Displays the history of the installed firmware versions.

Next >

Opens the Archives window where firmware files to be installed can be added.

Figure 84

Firmware Update Archives window

Add Archive(s)

Adds firmware files to the Archives window.

Remove

Deletes firmware files from the list in the Archives window.

Back

Closes the Archives window.

Install

Saves the selected firmware file to the DLC pro.

NOTE !

Close

Please reboot the DLC pro to finish installation of the new firmware version.

Closes the Device Configuration window.

> Menu > Device Configuration License Manager Section NOTE !

For an example of a step-by-step description of the installation of a new option via TOPAS DLC pro please refer to section 11.20.

Figure 85

Device Configuration window License Manager section

A window shows details on options already installed on the DLC pro. Install New Option

Opens the License Key window. Please insert the license key provided by TOPTICA and click OK to install the new option on the connected DLC pro.

Close

Closes the Device Configuration window.

> Menu > Save Configuration

NOTE !

Saves the most important settings of the Parameters window (e.g., settings for Scan/Lock mode, laser current and temperature settings).

The function of Menu > Save Configuration is equal to pressing the Load/Save button on the DLC pro front panel twice and to executing the command laser1 .. 4:save.

> Menu > Configuration Manager

Figure 86

The Configuration Manager window opens.

Configuration Manager window

The Configuration Manager allows to save and load several device parameter configurations, which include laser head operation parameters as well as not laser head specific settings of the DLC pro, e.g., display settings. A configuration file contains the laser head type and its serial number and can only be loaded if this data matches the selected laser head. The Configuration Manager window shows the connected laser heads and a list of all available configuration files on the DLC pro, a USB flash drive at the USB connector at the DLC pro front panel or stored on the control computer. DANGER ! Before handling configurations, always switch off the laser emission of the connected laser heads via the Emission push button on the DLC pro front panel ! Loading a configuration with the laser emission switched on may result in the direct emission of hazardous laser radiation ! NOTE !

Click Menu > Save Configuration to have the last loaded/saved device parameter configuration resumed at the DLC pro boot procedure.

NOTE !

Servo positions used for the AutoAlign option (motorized mirrors) of the laser head are not stored in the configuration file.

Select connected Laser Head

Select the laser head for which the device parameter configuration should be handled.

Keep applied/retrieved configuration after reboot

When the box is checked, the last applied/retrieved configuration is used after the next boot procedure of the DLC pro.

Configurations

Lists all available device parameter configurations on the DLC pro, the selected Local directory on the control computer, and a USB flash drive connected to the USB connector at the DLC pro front panel. Click on the configuration to select it. The last used configuration is marked in gray.

Show only configurations for selected Laser Head

When the box is checked, only device parameter configurations which match the selected laser head are displayed.

Load

Clicking loads the selected device parameter configuration. A configuration file contains the laser head type and its serial number and can only be loaded if this data matches the selected laser head (Select connected Laser Head).

NOTE !

To be able to save a configuration, the USB flash drive needs a folder "\toptica". Configuration files (*.laserconf) must be located in the folder "\toptica" to be detected.

Save

Clicking saves the selected device parameter configuration for the selected laser head to the DLC pro, to the selected Local directory on the control computer, or a USB flash drive.

Save as ...

Clicking opens a dialog window to enter a caption of the device parameter configuration. Click OK to confirm and open a dialog window to select a configuration file or to create a new file. Click Save to export the device parameter configuration for the selected laser head to the chosen Local directory on the control computer.

Local directory

Select the directory on the control computer where to load/save configurations from/to.

Factory Settings Apply NOTE !

Clicking loads the parameter values from the factory settings. Factory settings are certain laser head specific operation parameters, such as laser diode maximum voltages and currents, laser diode polarity, photo diode calibration data and other mostly laser safety related settings. Please note that the factory settings may have been changed formerly by the user, e.g. after an exchange of the laser diode.

Retrieve & Store

Close

Allows to handle the factory settings for the selected laser head (Select connected Laser Head).

User level MAINTENANCE required, otherwise not present (for changing the user level, please refer to section 6.9). Clicking reads out the parameter values in the factory settings and stores them into the EEPROM of the laser head. Closes the Configuration Manager window.

> Menu > Parameter Trace

Adds the Parameter Trace window to the screen.

NOTE !

When you display Signal Display and Parameter Trace windows at the same time, you can display one window at full size in the front for better viewing. Do this by picking the window at the title bar and pulling it in the center of the right screen area. The window to be displayed in the front is then selected by buttons at the bottom of the right display area which are labeled accordingly. Each display window may also be moved to any screen position when picked at the title bar.

Figure 87

Parameter Trace window

The Parameter Trace window displays user selectable parameters over time. You can turn this window on and off with the Parameter Trace entry in the TOPAS DLC pro menu. Please note that the minimum sample interval is 0.5 seconds. Select a parameter from the list in the center window below the display screen and click < or > to display it and to select whether the corresponding axis labelling is shown on the left or the right. Click the right mouse key in the display screen, to access several useful functions such as customizing the display setup or exporting data. Click the right mouse key on the axis label to select the axis scale (yaxis) or the displayed time range (x-axis). NOTE !

Please make sure that there is no automatic clock change of the control computer during a running measurement !

> Menu > IO

Figure 88

Adds the IO (Input/Output) window to the screen.

IO window (example)

The IO window allows to configure the voltages applied to the Out A and Out B BNC-connectors on the DLC pro front panel (see Figure 5), as well as configuration of the digital outputs at the MC+ module (see section 10.2.3). It is possible to control the DC voltage level and to route certain DLC pro internal signals to the BNC outputs, e.g. for monitoring on an external oscilloscope. The signals available for monitoring depend on the laser head type in use. You can think of Out A (and Out B) as an "adder", summing up a constant DC value and data from a "Monitoring Signal" to generate a resulting data stream which is then translated into a voltage, and finally getting applied to the BNC-connector. For translating the signal into a voltage, you must specify an Operating Point and a Monitoring Factor. The Operating Point, with the physical unit of the signal to be monitored, gets substracted from the signal, before it gets multiplied with the given Monitoring Factor in order to generate the voltage to be added to the output. NOTE !

In case you did configure Out A or B as the output channel for the scan generator on the Laser tab or one of the PID regulators on the Scan&Lock tab, the outputs of these components will be added to the resulting data stream as well.

Out A/Out B

Sections to configure the output applied to the Out A and Out B BNC-connectors on the DLC pro front panel (see Figure 5). Click Enable to activate the voltage output at the respective BNCconnector. When the output is disabled, the output voltage is 0 V.

Set Voltage

NOTE !

In case Out A/B is selected as the Scan Output channel (e.g. in the Laser tab), changes of the Scan Offset will immediately change the Set Voltage.

Actual Voltage

NOTE !

Input field for a DC offset voltage applied to the output BNC-connector.

Display of the actual voltage applied to the output BNC-connector. The displayed voltage is internally calculated by the DLC pro.

In case Out A/B is selected as the signal output at any other point of the TOPAS DLC pro PC-GUI or a context parameter menu of the touchscreen user interface, this also affects the Actual Voltage value.

Click the triangle below to access advanced setting options. Linked Laser

Only available with Dual- or Quad-Laser Operation. Choose the desired laser for Source Signal selection.

Signal Monitor

Click Enable to output signals which are fed to the DLC pro from connected devices.

Source Signal

Available signals are dependent on the Linked Laser head. Select signal type to be output at the BNC-connector.

Operating Point

Enter the operating point, at which you want the Source Signal to be monitored. The operating point will be translated to 0 V when adding the Source Signal to the output channel. The available value range depends on the Source Signal and its internal representation in the data processing unit.

Monitoring Factor

Enter a factor to be multiplied with the difference between Source Signal and Operating Point. The resulting voltage is added to the Set Voltage and applied to the output BNC-connector. This can be useful to scale-down signals so that the output range of - 4 V .. + 4 V is met. The available value range depends on the Source Signal and its internal representation in the data processing unit.

NOTE !

We recommend to enable the Signal Monitors only when required. When configuring the Signal Monitors, always make sure that the settings suit the experimental setup and that the selected Linked Laser does not interfere with selections in other tabs ! This is especially important when external devices are connected to the Out A/ Out B BNC-connectors.

Digital Output X

Sections to configure the digital outputs at the MC+ module (see section 10.2.3).

Mode

Depending on the selected mode, the voltage level at the Digital Output X is driven by different features of the DLC pro. Some modes only work if the corresponding license is installed.

Scan Sync Trigger mode

A square form (duty cycle 1:1) trigger signal synchronous to the scan ramp generating the laser frequency scan for the Linked Laser 1 .. 4 is available as a digital signal.

Linked Laser

The parameter must be set to 1 .. 4 for linking the respective Digital Output to the desired laser 1 .. 4.

Phase Shift

The phase shift between internal scan generator and output signal can be set by this parameter.

Invert

Select if the digital output logic should be inverted.

Lock OK mode

Only with Lock option license installed. TTL output signal indicating whether the Linked Laser 1 .. 4 is locked AND whether the measured signal is within the defined window. This signal may be used for fast lock/unlock detection to stop data acquisition when laser 1 .. 4 falls out-of-lock.

Linked Laser

The parameter must be set to 1 .. 4 for linking the respective Digital Output to the desired laser 1 .. 4.

Invert

Select if the digital output logic should be inverted.

WideScan Output Trigger mode

Trigger signal at the trigger threshold of a wide scan. (please refer to sections 5.4.12 and 7.1.1).

Linked Laser

The parameter must be set to 1 .. 4 for linking the respective Digital Output to the desired laser 1 .. 4.

Output Threshold

Output trigger threshold in [mA, V, K, nm]. Trigger output level is high if current value is above Output Threshold and low otherwise.

Invert

Select if the digital output logic should be inverted.

Manual Control mode

Manual control of the digital output.

Set Value

Check box to enable high digital signal at the output.

Invert

Select if the digital output logic should be inverted.

> Menu > Parameters

Adds the Parameters window to the screen.

NOTE !

For normal operation, all relevant parameters are set in the relevant sections of the TOPAS DLC pro PC-GUI. To enable the user to change parameters that are not accessible via any predefined screens, review the complete set of the DLC pro parameters in the Parameters window. For a detailed description of the parameters and associated codes, please refer to the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

Figure 89

Parameters window (example)

A complete list of the accessible parameters is displayed in the Parameters window (parameter tree). The parameters are sorted according to functional units. Some parameters can be set directly in the tree after clicking on the value, others are display only.

Along with the parameters a number of commands are accessible in the Parameters window. They are displayed in orange and after clicking them, a button appears which allows to execute the command. An example for such a command is the command laser1:save which stores the most important settings in the Parameters window to the flash memory of the DLC pro in order to operate the laser with those settings after the next boot procedure of the DLC pro. Please note that some of the commands require a certain user level and are not visible if they cannot be executed. To save the most important settings in the Parameters window to the flash memory of the DLC pro, select Menu > Save Configuration or execute the command laser1:save. NOTE !

The function of Menu > Save Configuration is equal to pressing the Load/Save button on the DLC pro front panel twice and to executing the command laser1 .. 4:save.

> Menu > Service

(Only available in user level SERVICE) For TOPTICA internal use only.

> Menu > FALC > Control

(Only with FALC pro module connected) Adds the FALC Control window to the screen.

NOTE !

For operation of up to two FALC pro modules, System Software 5.9.1 or higher and Firmware 2.2.0 or higher are required. For operation of up to four FALC pro modules, System Software 6.2.0 or higher and Firmware 3.1.0 or higher are required. For DLC pro units labelled with #BG-002900, the MC+ module must be of hardware version 1V09 or higher.

NOTE !

To show and use the FALC Control window, a FALC pro module must be connected to your DLC pro. When the FALC pro module is acquired, TOPTICA also provides relevant software to update your DLC pro. Please refer to the FALC pro manual for detailed information on connecting the FALC pro module and configurating the CAN bus connection. If purchased along with the DLC pro, the software is already installed. However, the CAN bus connection must be configured according to the individual setup for FALC pro single use, or FALC pro use in a CAN link chain (see FALC pro manual for detailed information).

NOTE !

To use the FALC pro module together with the DLC pro Lock option, a Lock option license is required. For DLC pro systems purchased without the DLC pro Lock option, a 30-day trial license is provided on the USB flash drive with the DLC pro software. Please refer to section 11.20 for activating the license key. The FALC pro module itself can be used without Lock option license. Please refer to the FALC pro manual for detailed information.

Figure 90

FALC Control window (example with four FALC pro modules)

The FALC Control window allows to configure the regulator of the FALC pro module and is only available with a FALC pro module connected to your DLC pro. The FALC Control window does not depend on which front panel is mounted to the FALC pro module. Please refer to the FALC pro manual for detailed information on the module.

Input Gain

Specify the input gain factor of the input signal. Available values are 1 and 5.

Offset

Compensates an offset of the input signal in [V].

Link Settings Path Selection

Only with DLC pro Lock option. Specify the branch(es) that are controlled by the DLC pro Lock option.

Main Enable

Activates/deactivates the main circuit branch.

Enable Checkboxes

Check the respective box to enable the filter element in the main circuit branch.

I1

Specify the left corner frequency of the I1-integrating filter element.

I2

Specify the left corner frequency of the I2-integrating filter element.

I3

Specify the left corner frequency of the I3-integrating filter element.

D1

Specify the left corner frequency of the D1- differentiating filter element.

D2

Specify the left corner frequency of the D2- differentiating filter element.

Gain

Output gain value [dB] of the main circuit branch.

Unlim Enable

Activates/deactivates the Unlim integrator branch.

Hold

Enables/Disables the update of the Unlim integrator output value. If enabled, the output value is frozen to the value in the moment the hold status is initiated.

Input Offset

Compensates an offset between the input of the Unlim integrator and the FALC pro internal error signal in [mV].

Output Range

Maximum absolute voltage [V] of the Unlimited integrator output signal.

Slew Rate

Specify the slew rate setting of the Unlim integrator [1 .. 12].

Gain

Indication of the resulting integrator gain [V/V/s] that is specified by the Output Range and the Slew Rate.

Sign Positive

Checkbox to select the sign (behavior) of the Unlim integrator. Checked: Output signal is in phase with the Error Output of the FALC pro module. Unchecked: Output signal is inverted with respect to the Error Output.

> Menu > PFD > Control

(Only with PFD pro module connected) Adds the PFD Control window to the screen.

NOTE !

For operation of up to four PFD pro modules, System Software 6.3.1 or higher and Firmware 3.3.0 or higher are required. For DLC pro units labelled with #BG-002900, the MC+ module must be of hardware version 1V09 or higher.

NOTE !

To show and use the PFD Control window, a PFD pro module must be connected to your DLC pro. When the PFD pro module is acquired, TOPTICA also provides relevant software to update your DLC pro. Please refer to the DLC pro manual for detailed information about the laser driver electronics. If purchased along with the DLC pro, the software is already installed. However, the CAN bus connection must be configured according to the individual setup for PFD pro single use, or PFD pro use in a CAN link chain (see PFD pro manual for detailed information).

NOTE !

To utilize the HF path of the PFD pro, a license is required. When the PFD pro HF is acquired, the USB flash drive with the license key is part of the delivery content. The license is unlimited in time but linked to the individual hardware of the PFD pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).

Figure 91

PFD Control window of the TOPAS DLC pro PC-GUI (example with two PFD pro modules)

The PFD Control window allows to configure the operation parameters of each PFD pro module and is only available with a PFD pro module connected to your DLC pro. The operation parameters which are displayed in the PFD Control window depend on the individual selections in the window. Please refer to the PFD pro manual for detailed information on the module. NOTE !

For detailed information on the PFD pro module and its connectors, please refer to the PFD pro manual.

Input Configuration

RF Path

This section allows to configure the major signal paths. The displayed parameters depend on the individual selections in the PFD Control window. LF LF-TF

HF Reference Path

Internal External

Select LF in case the beat signal frequency of your experiment is between 5 MHz .. 200 MHz. Select LF-TF in case the beat signal frequency of your experiment is between 5 MHz .. 95 MHz. A tunable bandpass filter is used. (Center Frequency below). Select HF in case the beat signal frequency of your experiment is between 200 MHz .. 10 GHz. Select Internal to use the internal frequency synthesizer as reference signal for the phase comparison. (only with RF Path LF or HF selected). Select External to use an external signal (Ref connector) as reference signal for the phase comparison. The frequency of the reference signal can be calculated by: Reference frequency = Ref Divider/RF Divider x Center Frequency.

Clock Source

Displays whether the internal frequency synthesizer uses the internal reference clock, or the externally applied 10 MHz clock signal.

10 MHz Locked

The green indicator shows that the externally applied 10 MHz clock signal is used.

LF/LF-TF/HF Path

High Frequency Divider

NOTE !

The displayed parameters depend on individual selections in the PFD Control window. (only with RF Path HF selected). Checkbox to enable the high frequency divider necessary for optimum signal processing if the required beat frequency of the experiment is > 8 GHz.

For lowest phase noise set the value as low as possible.

Automatic Gain

(only with RF Path LF or LF-TF selected). Click Enable to activate the automatic gain control loop. The gain is automatically controlled in a way so that the Phase Detector Level is 0 dBm. This is useful in case the input signal (RF LF connector) is fluctuating significantly.

Manual Gain

(only with RF Path LF or LF-TF selected and Automatic Gain disabled). Set the gain factor for the input signal (RF LF connector) so that the Phase Detector Level is around 0 dBm.

Phase Detector Level

(only with RF Path LF or LF-TF selected). Displays the level of the input signal (RF LF connector) after amplification by automatic or manual gain control.

RF Divider

NOTE !

Set the division value for the required beat frequency of the experiment to match the divided internal reference signal (Ref Divider) for the phase comparison (Frequency Plan section). When RF Path HF is selected, the step size of the RF Divider value is 2, with the High Frequency Divider additionally enabled, the step size is 4. For lowest phase noise set the value as low as possible.

Ref Divider

Set the division value for the internal reference signal to match the divided required beat frequency of the experiment (RF Divider).

Frequency Plan

(only with Reference Path Internal selected). This section allows to configure the properties of the required beat frequency (RF HF and RF LF connector of the PFD pro module) for the phase comparison. The displayed parameters depend on individual selections in the PFD Control window.

Mode

Pull-down menu to select the Frequency Plan modes. For detailed description of the modes, please refer to the PFD pro manual. (only with RF Path LF-TF selected). Tunable Filter The tunable bandpass filter is activated. (Center Frequency below). (only with RF Path LF or HF selected). Adjustable Select Adjustable in case a constant Center Frequency is desired. Scan Select Scan in case an internally generated triangular scan around the Center Frequency is desired. Scan Frequency and Frequency Amplitude can be set.

NOTE !

A trigger signal synchronous to the scan is available at the Dig I/O connector of the PFD pro module (please refer to the PFD pro manual for the digital in- and outputs). Scan External Select Scan External in case an external trigger signal is applied to Digital Input 0 (Dig I/O connector of the PFD pro module). The linear scan ramp around the Center Frequency is executed according to the state of the digital line: 0: decreasing frequency 1: increasing frequency). Frequency Slope and Frequency Amplitude can be set. Hopping External Select Hopping External in case up to two external trigger signals (applied to Digital Input 0 and 1, Dig I/O connector of the PFD pro module)) should initiate the hopping between up to four frequencies (Frequency 1 .. Frequency 4). Feed Forward Offset and Feed Forward Factor can be set.

Center Frequency

(not with Mode Hopping External selected). Set the Center Frequency, i.e the required beat frequency for the experiment. This value is equal to the filter frequency for the tunable bandpass filter which is activated in Mode Tunable Filter.

Scan Frequency

(only with Mode Scan selected). Set the frequency of the internally generated triangular scan.

Frequency Slope

(only with Mode Scan External selected). Set the slope of the externally triggered scan ramp.

Frequency Amplitude

(only with Mode Scan or Scan External selected). Set the peak-to-peak amplitude of the externally triggered scan cycle.

Frequency 1 .. 4

(only with Mode Hopping External selected). Up to four target frequencies (Frequency 1 .. 4) can be chosen, allowing the required beat frequency to jump between them based on external digital trigger signals. Dig I/O-connector of the PFD pro module Dig. Inp. 0

Dig.Inp. 1

Frequency 1

0 (low)

0 (low)

Frequency 2

1 (high)

0 (low)

Frequency 3

0 (low)

1 (high)

Frequency 4

1 (high)

1 (high)

Feed Forward Offset

(only with Mode Hopping External selected). The PFD pro allows to generate a voltage signal equivalent to (Frequency 1 .. 4 - Feed Forward Offset) x Feed Forward Factor. This voltage is applied to the Aux 2 connector of the PFD pro module.

Feed Forward Factor

(only with Mode Hopping External selected). Scaling factor for the feed forward voltage signal in relation to frequency difference Frequency 1 .. 4 - Feed Forward Offset.

NOTE !

For convenient changing of adjustable values, place the mouse pointer on the input field and change the value with the mouse wheel.

> Menu > FALC > Bode Plots

(Only with FALC pro module connected) Adds a display window for transfer functions of the FALC pro PID controllers to the screen. Please refer to the description of Laser Menu > Optimization Tools > Bode Plots (see section 6.8) for details.

> Menu > PDH

(Only with PDH module) Adds the PDH window to the screen.

NOTE !

To show and use the PDH window, a PDH module must be installed at your DLC pro. When the PDH module is acquired, TOPTICA also provides relevant software to update your DLC pro. Please refer to section 11.4 for a step-by-step description on how to install the PDH module. If purchased along with the DLC pro, the PDH module and the software is already installed.

NOTE !

To use the PDH module for Top of Fringe PDH locking (Scan & Lock tab, see section 7.2.3), a Lock option license is required. The PDH module itself can be used without Lock option license. The Error signals are applied to the SMB-connectors of the PDH module (rear side of the DLC pro) and can be used together with an external controller.

Figure 92

PDH window (example with two PDH modules)

The PDH window allows to configure the PDH module and is only available with a PDH module installed at your DLC pro.

PDH 1/PDH 2

In case of two PDH modules installed: PDH 1 is related to the PDH module installed furthest to the left (DLC pro rear view), PDH 2 is related to the PDH module installed further to the right.

Channel 1

Settings for channel 1 of the PDH module.

Enable

Enable or disable PDH modulation and demodulation signal generation.

Frequency

Select PDH modulation frequency.

Amplitude

Enter PDH modulation amplitude.

Click the triangle below to access advanced setting options. Max. Input Level

Select the maximum RF input level expected at the in 1 connector of the PDH module.

-10 dBm:
Signal level valid up to -10 dBm 0 dBm: Signal level valid up to 0 dBm +10 dBm: Signal level valid up to +10 dBm

Lock Level

Set level for the DLC pro internal PID controller used for the Top of Fringe PDH lock type.

Phase

Enter the phase difference between PDH modulation and demodulation signal.

AutoPDH

Starts an algorithm which finds the optimum phase between the photo diode signal and the local oscillator.

LO Output

Enable or disable output of the LO signal instead of the error signal at the err/lo 1 connector of the PDH module.

LO Amplitude

Enter the LO Amplitude.

NOTE !

Channel 2

When LO Output is enabled, the LO Amplitude can be set as desired. This may affect the error signal generated by the PDH module. If you wish to output the demodulation signal and ensure optimum error signal quality at the same time, set LO Amplitude to 8.8 dBm.

Settings for channel 2 of the PDH module. Please refer to the descriptions of Channel 1 for information.

> Menu > Communication

Figure 93

Adds the Communication window to the screen.

Communication window

Communication Window

Shows details on the communication between TOPAS DLC pro and the DLC pro.

Hold

Freezes the display of the communication. Click Hold again to continue the display.

Show Monitoring Line/ Show Command Line

Toggles between displaying the communication on the monitoring line or on the command line.

> Menu > About

The About window opens, which provides information about the manufacturer, contact details, software version, etc.

> Menu > Exit

Closes the TOPAS DLC pro software without saving the most important parameters set in the Parameters window.

NOTE !

To store the configuration set in the Parameters window, please use Menu > Save Configuration.

## 6.10 TOPAS DLC pro Operation via Shortcuts

Some shortcuts allow for convenient operation of the running TOPAS DLC pro PC-GUI.

- Double-clicking a laser row in the dashboard opens the Laser Control window for the respective
laser 1 .. 4, and all laser related windows which have been previously opened.

- Double-clicking the colored ribbon (in the dashboard or in a window) allows to customize the
optional ribbon color.

- CTRL + SHIFT D displays the TOPAS DLC pro dashboard in the foreground.
- CTRL + SHIFT A displays all windows of the TOPAS DLC pro PC-GUI which have been opened previously.
- F1 .. F4 displays all windows related to laser 1 .. 4 which have been previously opened.
- CTRL + F1 .. F4 opens the Laser Control window related to laser 1 .. 4.
- CTRL + 1 .. 4 opens the Signal Display window related to laser 1 .. 4.
- CTRL + SHIFT L opens the FALC Control window (only with FALC pro module connected).
- CTRL + SHIFT H opens the PDH window (only with PDH module installed).
- CTRL + SHIFT F opens the PFD Control window (only with PFD pro module installed).
- CTRL + SHIFT P opens the Parameters window.
- CTRL + SHIFT T opens the Parameter Trace window.
- CTRL + SHIFT I opens the IO window.
# 7 Laser Control Window in the TOPAS DLC pro Graphical User Interface

7

Laser Control Window in the TOPAS DLC pro Graphical User Interface

## 7.1 Laser Tabs

### 7.1.1 DLC pro for Laser Head DL pro

Figure 94

Laser tab (DLC DL pro)

CC Current Control Enable

Activates/deactivates the Current Control.

Set Current

Input field for set current Iset.

Actual Current

Display field for actual current Iact. The actual current is measured with low accuracy for monitoring purposes and fault detection.

NOTE !

The Actual Current differs from the Set Current due to the Feed Forward and offsets added by PIDs.

Maximum Current NOTE !

Input field for maximum current Imax.

Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

Use Tuning Clip

Checking the box limits the laser diode current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only).

CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip boxes for diode laser and amplifier (depending on the connected laser head) in the CC section(s) of the Laser tab (for amplifier see also section 7.1.7) is mandatory before performing a motor scan. This avoids damage to the laser diode and amplifier during a motor scan. Click the triangle in the CC Section to access advanced setting options for the Feed Forward and Analog Remote Control of the laser frequency. Feed Forward Enable

Activates/deactivates the Feed Forward, i.e. a change of the laser diode current proportional to the change of the piezo voltage due to the scan.

Feed Forward Factor

Scaling parameter of the Feed Forward in mA/V. (for DL pro SMC laser heads alternatively in V/mA, according to the selected Feed Forward Direction, see section 7.1.3).

Analog Remote Control Enable Activates/deactivates the Analog Remote Control. Please refer to section 11.11.1 for an example on how to configure the CC Analog Remote Control. ARC Signal Input

Specify the BNC connector for the external remote control voltage.

ARC Factor

Specify the conversion factor for converting the remote control voltage [V] into a CC output offset [mA].

TC Temperature Control Enable

Activates/deactivates the Temperature Control.

Set Temperature

Input field for set temperature Tset.

Actual Temperature

Display field for actual temperature Tact.

Click the triangle in the TC Section to access advanced setting options for the Analog Remote Control of the laser frequency. Analog Remote Control Enable Activates/deactivates the Analog Remote Control. Please refer to section 11.11.1 for an example on how to configure the TC Analog Remote Control. ARC Signal Input

Specify the BNC connector for the external remote control voltage.

ARC Factor

Specify the conversion factor for converting the remote control voltage [V] into a TC output offset [K].

PC Piezo Control Enable

Activates/deactivates the Piezo Control.

Set Voltage

Input field for a DC offset voltage which is applied to the piezo.

NOTE !

When the SC Scan Output (see below) is directed to PC Voltage, the value is identical to SC Scan Offset.

Actual Voltage

Display Field for internally measured voltage which is currently applied to the piezo. The actual piezo voltage is measured with low accuracy for monitoring and fault detection.

Click the triangle in the PC section to access advanced setting options. Slew Rate Enable

Enable/Disable slew rate limiting feature. It allows to limit the rate of change of the output signal to the value set by Slew Rate

Slew Rate

Set slew rate (maximum rate of change) of PC output.

Analog Remote Control Enable Activates/deactivates the Analog Remote Control. Please refer to section 11.11.1 for an example on how to configure the CC Analog Remote Control. ARC Signal Input

Specify the BNC connector for the external remote control voltage.

ARC Factor

Specify the conversion factor for converting the remote control voltage [V] into a PC output offset [V].

Pressure Compensation Enable Enable/Disable the air pressure compensation to improve the long term stability of the laser frequency. Air Pressure

Shows averaged air pressure.

Factor

Factor for linear pressure compensation.

NOTE !

Please refer to section 11.12 for further information on the pressure compensation.

Compensation Voltage

Shows pressure compensation voltage.

SC Scan Control NOTE !

For displaying a signal depending on the laser scan on the screen of your PC, please use the Signal Display in the laser menu (see section 6.8).

Enable NOTE !

Activates/deactivates the frequency scan of the laser. Activating the scan is only possible when the laser is not locked. Please note that the Scan Offset is applied to the piezo even if the SC is disabled.

Scan Amplitude

Peak-to-peak amplitude. The unit is dependent on the Scan Output.

Scan Offset

DC signal level. The unit is dependent on the Scan Output.

Click the triangle below to access advanced setting options. Scan Output

Select output channel to which the generated signal is directed. PC Voltage: Scan signal is directed to the Piezo Control module and the piezo voltage is scanned. CC Current: Scan signal is directed to the Current Control module and the laser current is scanned. Out A: Scan signal is directed to the Out A BNC-connector on the DLC pro front panel. Out B: Scan signal is directed to the Out B BNC-connector on the DLC pro front panel.

Scan Frequency

Set repetition frequency of the chosen waveform in Hz.

Scan Shape

Select type of the generated waveform (sine or triangle). Default setting is triangle.

Wide Scan X-Axis Signal

NOTE !

Select X-axis signal for the Wide Scan Display (see section 6.8). The X-axis signal is the parameter to be scanned. Available signals depend on the laser head type.

When Analog Remote Control (ARC) for the selected X-Axis signal is enabled in the corresponding sections of the Laser tab, the ramp of the wide scan is superimposed by the ARC signal. This may lead to distorted visualization at Wide Scan Display.

Set <value>

Set value [mA, V, °C, nm] of the parameter to be scanned.

Actual <value>

Actual value [mA, V, °C, nm] of the parameter to be scanned when wide scan is running.

Start <value>

Start value [mA, V, °C, nm] of the parameter to be scanned.

End <value>

End value [mA, V, °C, nm] of the parameter to be scanned.

Buttons

Center: Click to set the Set value (e.g., the laser diode temperature) to the center value of the actual detail of the Wide Scan Display (Xaxis). The display of Actual value will change accordingly. Zoom Range: Select to set the Start and End value (e.g., the laser diode temperature) to the outer values of the actual detail of the Wide Scan Display (X-axis). The display of Start and End value will change accordingly. Full Range: Click to scale the Wide Scan Display so that the entire wide scan from Start value to End value is displayed.

Play: Wide scan is initiated with the set Scan Speed. After the wide scan is finished, the laser returns to the Set value. NOTE !

In case the laser should remain at the Actual value after the wide scan is finished or stopped, please uncheck the box at the parameter laserX:wide-scan:restore-on-end (Parameters window of the TOPAS DLC pro PC-GUI, see section 6.9). With this setting, after the wide scan is finished or stopped, the Actual value becomes the new Set value.

Play Trigger: The icon in the Play button indicates that the wide scan is initiated by a input trigger signal and not by tapping the Play button (Trigger Input enabled). After tapping the Play Trigger symbol, the Start <value> of the parameter to be scanned is accessed. The wide scan then is initiated with the set Scan Speed when a trigger signal is applied to the selected trigger Input Channel. When the trigger signal is removed, the wide scan continues until the End <value> is reached. Tap the Stop symbol to discontinue the wide scan. Stop: Wide scan is stopped and the Set value is accessed.

Repeat: Wide scan is continuously repeated within the set values. The Scan Shape for a repeated wide scan can be selected in the respective pop-up menu. Progress Bar

Displays the progress of the wide scan and the remaining time.

Scan Speed

Enter wide scan speed in [mA/s, V/s, K/s, nm/s].

NOTE !

A high Scan Speed together with a small laser1:wide-scan:recorder-stepsize-set (Parameters window, see section 6.9) leads to a higher laser1:recorder:sampling-rate. At a sampling-rate above 100 kHz, dropouts during recording may occur.

Scan Shape

Select scan shape (triangle or sawtooth) for a repeated wide scan. Default setting is Triangle. Sawtooth: Return to the start value is performed as fast as possible. Triangle: Return to the start value is performed with Scan Speed.

Recorder Stepsize Set

Enter set value for recorder stepsize in [mA], [V], [K], [nm].

Memory Size

Displays actual value of required memory size for the next wide scan run in Bytes.

Input Trigger Enable Input Trigger

Enable input trigger. The wide scan is initiated by an external trigger signal applied to Digital Input 2 or 3 of the Digital I/O connector on the MC+ module (see section 11.10.4).

NOTE !

Quad-Laser-Operation: The Digital Inputs 2 and 3 are linked to both, the lock hold function and the wide scan input trigger (see section 10.2.3). If that is not desired, the lock hold function can be deactivated via the parameter laserX:dl:lock:di-hold-enabled (parameter menu of the touchscreen (please refer to section 5.14) or Parameters window of the TOPAS DLC pro PC-GUI (please refer to section 6.9).

NOTE !

The Trigger Output Channels (Digital Outputs, see section 10.2.3) can be configured for wide scan trigger in the IO window of the TOPAS DLC pro PC-GUI (see section 6.9). Configuration is also possible in the parameter menu (touchscreen, see section 5.14): The parameter io:digital-outX:mode must be set to 2, the Trigger Output Channels (Digital Outputs) must be linked to laser 1 .. 4 by setting the parameter io:digital-outX:linked-laser to 1 .. 4.

Input Channel

7.1.1.1

Select input channel (pin of the Digital I/O connector on the MC+ module, see section 11.10.4) for input trigger.

Synchronized Scanning of Lasers

At a DLC pro for Dual- or Quad-Laser-Operation (see section 1.3) the scan of all connected lasers can be synchronized. The settings for the synchronization can be performed in the Parameters window of the TOPAS DLC pro PC-GUI (see section 6.9) or via software commands (see section 11.14). laser-common:scan:sync-laser1 .. 4 laser-common:scan:frequency laser-common:scan:sync laser-common:scan:save

Select the lasers to be synchronized. Enter the common scan frequency. When the command is executed, the scan generators of all selected lasers are set to the common scan frequency. Save the scan-synchronization settings to be used after the next DLC pro boot procedure.

When the scan is enabled by clicking Enable in the SC Scan Control section of the Laser tab, the scans of the selected lasers then are started simultaneously and the lasers are scanned with the same frequency, and with zero relative phase-shift.

### 7.1.2 DLC pro for Laser Head DL pro F with Intra-Cavity EOM

Figure 95

Laser tab (DLC DL pro F with intra-cavity EOM)

As an option, an intra-cavity EOM can be integrated into the resonator of a DL pro laser head (DL pro F). The voltage of the slow electrode of the intra-cavity EOM is controlled via one channel of a PC module. The operation and control of the respective laser head is unchanged and control for the slow electrode of the intra-cavity EOM is added in the EOM section of the Laser tab. For description of the operator controls, please refer to the Laser tab of the DL pro (see section 7.1.1). Specific information on operation of the DL pro with intra-cavity EOM are noted below. CAUTION ! Please refer to the DL/TA/DL-/TA-SHG pro F manual for details about how to connect and power up/down the laser head correctly.

EOM Enable

Activates/deactivates the EOM slow control.

Set Voltage

Input field for a DC offset voltage which is applied to the slow electrode of the EOM.

Actual Voltage

Display Field for internally measured voltage which is currently applied to the slow electrode of the EOM. The actual EOM voltage is measured with low accuracy for monitoring and fault detection.

Click the triangle in the EOM section to access advanced setting options. Analog Remote Control Enable Activates/deactivates the Analog Remote Control. Please refer to section 11.11.1 for an example on how to configure the EOM Analog Remote Control. ARC Signal Input

Specify the BNC connector for the external remote control voltage.

ARC Factor

Specify the conversion factor for converting the remote control voltage [V] into a PC output offset [V] for the intra-cavity EOM.

SC Scan Control Click the triangle to access advanced setting options. Scan Output

Select output channel to which the generated signal is directed. EOM Voltage Slow: Scan signal is directed to the Piezo Control module for the intra-cavity EOM and the voltage applied to the slow electrode of the intracavity EOM is scanned.

### 7.1.3 DLC pro for Laser Head DL pro SMC with Single Mode Control

Figure 96

Laser tab (DLC DL pro SMC with single mode control)

As an option, the DL pro laser head can be equipped with the SMC single mode control to ensure the highest possible single mode stability at the desired operating point. The operation and control of the respective laser head is unchanged and control for the single mode control is added in the SMC - Single Mode Control section of the Laser tab. Additionally, for DL pro SMC laser heads, the Feed Forward Direction can be selected in the CC - Current Control section. For description of the operator controls, please refer to the Laser tab of the DL pro (see section 7.1.1). Specific information on operation of the DL pro with SMC single mode control are noted below. NOTE !

Please refer to the SMC manual for details about the single mode control, and how to connect the laser head correctly.

SMC-Single Mode Control Enable

Activates/deactivates the SMC single mode control.

NOTE !

The single mode control can only be enabled after certain preconditions are met. Please refer to the SMC manual for details. When the single mode control is enabled, PC Set Voltage and TC Set Temperature cannot be changed ! CC Set Current can only be tuned within a limited range which allows the single mode control to operate properly.

Status

Displays the status of the SMC single mode control. Please refer to the SMC manual for a list and a detailed description of the status messages.

SMC Bandwidth

Drop-down menu to choose the bandwidth of the single mode controller. Please refer to the SMC manual for details.

Reset

Clicking the button resets the single mode control, and initiates a new SMC Lock close to the previous PC Set Voltage. Please refer to the SMC manual for details.

CC-Current Control Feed Forward Direction

Drop-down menu to select the feed forward direction. PC → CC: The laser diode current is changed proportionally to the change of the piezo voltage due to the scan (according to the set Feed Forward Factor in mA/V). CC → PC: The piezo voltage is changed proportionally to the change of the laser diode current due to the scan (according to the set Feed Forward Factor in V/mA).

### 7.1.4 DLC pro for Laser Head DL pro with MOTOR pro Option

Figure 97

Laser tab (DLC DL pro with MOTOR pro option)

NOTE !

For MOTOR pro module operation, DLC pro System Software 5.12.0 or higher and DLC pro Firmware 2.6.0 or higher are required. For DLC pro units labelled with #BG-002900, the MC+ module must be of hardware version 1V09 or higher.

The MOTOR pro option for DL pro laser heads or DL pro Master Oscillators of amplified laser heads allows to quickly tune the laser to a new wavelength within its tuning range by moving the internal grating of the DL pro by a motor drive. Please refer to the DL pro laser head manual and the MOTOR pro manual for detailed description. The operation and control of the laser head with MOTOR pro option is unchanged and control for the motor drive is added in the Motor Control section of the Laser tab. For description of the operator controls, please refer to the Laser tab of the DL pro (see section 7.1.1). Specific information on operation of the DL pro with MOTOR pro option are noted below. Motor Control NOTE !

All wavelengths in the Motor Control section are internally converted into motor step positions, so the wavelength accuracy mainly depends on the stored calibration data. Please refer to section 6.8 (Laser Menu > Optimization Tools > Motor Calibration) and to the MOTOR pro manual for instructions to perform a wavelength calibration.

Set Wavelength

Set desired target wavelength.

Actual Wavelength

Displays actual wavelength as calculated from the current motor position.

Start Wavelength

Start wavelength for a motor scan.

End Wavelength

End wavelength for a motor scan.

NOTE !

Please note that the motor drive can move the internal grating of the DL pro into positions, where the laser does not emit light. Please refer to the Production and Quality Control Data Sheet of the connected laser head for its wavelength range.

Inaccuracy

Displays the expected deviation of the Actual Wavelength from a measured wavelength, due to mechanical tolerances and other influences.

Buttons Play: The Start Wavelength is accessed and the motor scan is initiated with the set Scan Speed. After the scan is finished, the laser returns to the Set Wavelength. CAUTION ! Checking the Use Tuning Clip boxes for diode laser and amplifier (depending on the connected laser head) in the CC section(s) of the Laser tab (see sections 7.1.1 and 7.1.7) is mandatory before performing a motor scan. Checking the box(es) reduces the laser diode (and amplifier) currents to the Maximum Tuning Currents as noted in the laser head Quality Control and Test Data Sheet to avoid damage to the laser diode (and the amplifier) during a motor scan. NOTE !

In case the laser should remain at the Actual Wavelength after the motor scan is finished or stopped, please uncheck the box at the parameter laserX:dl:motor:scan:restore-on-end (Parameters window of the TOPAS DLC pro PC-GUI, see section 6.9). With this setting, after the motor scan is finished or stopped, the Actual Wavelength becomes the new Set Wavelength.

Pause: Motor scan is paused. Tap Play to continue the motor scan.

Stop: Motor scan is stopped and the Set Wavelength is accessed.

Progress Bar

Displays the progress of the Motor scan and the remaining time.

Scan Speed

Enter Motor scan speed in [nm/s].

Scan Shape

Select scan shape (triangle or sawtooth) for a repeated Motor scan. Default setting is Triangle. Sawtooth: Return to the Start Wavelength is performed as fast as possible. Triangle: Return to the Start Wavelength is performed with Scan Speed.

Trigger Threshold

Enter output trigger wavelength [nm]. Trigger output level is high if Actual Wavelength is above threshold wavelength, and low if Actual Wavelength is below threshold wavelength. The trigger output is available at the Dig I/O D-Sub 15 HD connector at the MOTOR pro module (please refer to the MOTOR pro module for details).

### 7.1.5 DLC pro for DFB pro/DL pro BFY

Figure 98

Laser tab (DLC DFB pro/DLC DL pro BFY)

NOTE !

The DLC DFB pro/DLC DL pro BFY Laser tab is present if a DFB pro/DL pro BFY laser head or a laser system with a DFB pro Master Oscillator is connected to the DLC pro.

The Laser tab comprises the operator controls for the DFB pro/DL pro BFY laser and the wide scan. As the DFB pro/DL pro BFY laser is operated like a DL pro laser head, please refer to section 7.1.1 for description of the basic CC-, TC, SC and Wide Scan operator controls. All DFB pro/DL pro BFY specific operator controls are described below.

CC Current Control Feed Forward Factor

Scaling parameter of the Feed Forward in mA/K.

SC Scan Control Scan Output

TC Set Temperature For DFB pro or DL pro BFY laser heads, PC Voltage is not available as output channel. When TC Set Temperature is selected, the scan signal is directed to the Temperature Control module and the laser diode temperature is scanned.

### 7.1.6 DLC pro for Laser Head CTL

Figure 99

Laser tab (DLC CTL)

The Laser tab comprises the operator controls for the laser and the Motor Control section. As the laser is operated like a DL pro laser head, please refer to section 7.1.1 for description of the basic CC-, PC, SC and Wide Scan operator controls. All CTL specific operator controls are described below.

Motor Control Set Wavelength

Input field for set wavelength.

Actual Wavelength

Display field for actual wavelength.

SMILE Enable

Enable the Single Mode Intelligent Loop Engine. For details please refer to the CTL manual.

µ-Steps

When enabled the scan motor is able to perform so-called microsteps (< 1 pm) while scanning. By default, these microsteps are enabled, but are automatically disabled for fast scans.

Analog Remote Control Enable Activates/deactivates the Motor Analog Remote Control. Please refer to section 11.11.2 for an example on how to configure the Motor Analog Remote Control. Input

Specify the BNC connector for the external remote control voltage.

Factor

Specify the input sensitivity factor for converting the remote control voltage [V] into a wavelength [nm].

### 7.1.7 DLC pro for Laser Head TA pro

Figure 100 Laser tab (DLC TA pro)

The Laser tab comprises the operator controls for the TA pro Master Oscillator and the Tapered Amplifier. As the Master Oscillator is operated like a DL pro laser head, please refer to section 7.1.1 for description of the Master Oscillator operator controls. The Tapered Amplifier operator controls are described below. CC Current Control Tapered Amplifier Enable

Activates/deactivates the Current Control.

Set Current

Input field for set current Iset.

Actual Current

Display field for actual current Iact.

NOTE !

The Actual Current differs from the Set Current due to the Amplifier Feed Forward.

Maximum Current

Input field for maximum current Imax.

Use Tuning Clip

Checking the box limits the amplifier current to the Maximum Tuning Current as noted in the laser head Quality Control and Test Data Sheet. In case this Maximum Tuning Current is lower than the entry in the Maximum Current field, this field changes to Maximum Tuning Current (display only).

CAUTION ! Laser heads with MOTOR pro option: Checking the Use Tuning Clip box in the CC-Amplifier Current Control section is mandatory before performing a motor scan. This avoids damage to the amplifier during a motor scan. Feed Forward Enable

Activates/deactivates the Amplifier Feed Forward, i.e. a change of the Tapered Amplifier current proportional to the change of the Master Oscillator piezo voltage due to the its scan.

Feed Forward Factor

Scaling parameter of the Amplifier Feed Forward in mA/V.

NOTE !

Analog Remote Control (ARC) is also available for CC-Amplifier. Please refer to section 11.11.1 for an example on how to configure the CC Analog Remote Control.

TC Temperature Control Tapered Amplifier Enable

Activates/deactivates the Temperature Control.

Set Temperature

Input field for set temperature Tset.

Actual Temperature

Display field for actual temperature Tact.

Power Limits Actual Seed Power

Display field for actual seed power.

Actual Output Power

Display field for actual output power at laser beam aperture of the TA pro.

Min. Seed Power

Input field for setting the minimum seed power.

Max. Seed Power

Input field for setting the maximum seed power.

Min. Output Power

Input field for setting the minimum output power at laser beam aperture of the TA pro.

Max. Output Power

Input field for setting the maximum output power at laser beam aperture of the TA pro.

### 7.1.8 DLC pro for Laser Head TA pro F with Intra-Cavity EOM

Figure 101 Laser tab (DLC TA pro F with intra-cavity EOM for the Master Oscillator)

As an option, an intra-cavity EOM can be integrated into the resonator of the DL pro Master Oscillator in the TA pro laser head (TA pro F). The voltage of the slow electrode of the intra-cavity EOM is controlled via one channel of a PC module. The operation and control of the respective laser head is unchanged and control for the slow electrode of the intra-cavity EOM is added in the EOM section of the Laser tab. The TA pro Laser tab comprises the operator controls for the Master Oscillator and the Tapered Amplifier. As the Master Oscillator is operated like a DL pro laser head, please refer to section 7.1.1 for description of the Master Oscillator operator controls, and to section 7.1.2 for description of the intra-cavity specific operator controls. The Tapered Amplifier operator controls are described in section 7.1.7. CAUTION ! Please refer to the DL/TA pro F manual for details about how to connect and power up/ down the laser head correctly.

### 7.1.9 DLC pro for TA pro AL

Figure 102 Laser tab (DLC TA pro AL, example one laser unit in TA pro configuration)

The Laser tab comprises the operator controls for the TA pro AL Master Oscillator (only DL pro and TA pro configuration) and the Tapered Amplifier (only TA pro and BoosTA pro configuration). As the Master Oscillator is operated like a DL pro or DFB pro laser head, please refer to section 7.1.1 or section 7.1.5 for description of the Master Oscillator operator controls. The Tapered Amplifier operator controls are described in section 7.1.7.

### 7.1.10 DLC pro for Seed Laser + BoosTA pro Combinations

Figure 103 Laser tab seed laser + BoosTA pro combination (example DL pro seed laser)

In addition to a DL pro, DFB pro or CTL as seed laser head, a BoosTA pro tapered amplifier can be connected to the DLC pro, if at least one CC-5000 module is installed in the DLC pro laser driver electronics. In this seed laser + BoosTA pro combination, the operation and control of the respective seed laser head (Master Oscillator) is unchanged, and controls for the BoosTA pro are added in the Laser tab. For description of the operator controls, please refer to the Laser tab of the respective seed laser, and the Laser tab of the TA pro. Specific informations on seed laser + BoosTA pro combination are noted below. NOTE !

DLC BoosTA pro: In case only a BoosTA pro laser head without a seed laser is connected to the DLC pro, only the BoosTA pro relevant operator controls are displayed.

Please refer to the BoosTA pro manual for details about how to connect and power up/down the laser heads correctly. CC Current Control Tapered Amplifier Feed Forward Enable

Activates/deactivates the Amplifier Feed Forward, i.e. a change of the Tapered Amplifier current proportional to the change of the seed laser piezo voltage due to the its scan.

NOTE !

CTL seed laser + BoosTA pro combination: Do not use the amplifier feed forward as there is no power fluctuation to be compensated while scanning.

NOTE !

Analog Remote Control (ARC) is also available for CC-Amplifier. Please refer to section 11.11.1 for an example on how to configure the CC Analog Remote Control.

Power Limits Actual Seed Power

Display field for actual seed power. Please refer to the BoosTA pro manual for information on installation and calibration of the seed power photo diode.

Actual Output Power

Display field for actual output power at laser beam aperture of the TA pro. Please refer to the BoosTA pro manual for information on installation and calibration of the amplified output power photo diode.

### 7.1.11 DLC pro for Laser Head DL-/TA-SHG/FHG pro

Figure 104 Laser tab (DLC TA-SHG/FHG pro, example DLC TA-FHG pro)

The Laser tab comprises the operator controls for the Master Oscillator and the Tapered Amplifier of the DL-/TA-SHG/FHG pro. Please refer to section 7.1.7 for description of the Master Oscillator and Tapered Amplifier operator controls, and to section 7.1.1 for description of the Wide Scan operator controls.

### 7.1.12 DLC pro for TOPO smart Laser Head

Figure 105 Laser tab (DLC TOPO smart laser head)

The Laser tab comprises the operator controls for the TOPO smart master oscillator, the tapered amplifier, and the OPO cavity. As the master oscillator is operated like a DFB pro laser head, please refer to section 7.1.5 for description of the master oscillator operator controls. As the tapered amplifier is operated like a TA pro amplifier, please refer to section 7.1.7 for description of the tapered amplifier operator controls. The OPO cavity operator controls are described below. TC Temperature Control Crystal Enable

Activates/deactivates the temperature control.

Set Temperature

Input field for set temperature Tset.

Actual Temperature

Display field for actual temperature Tact.

TC Temperature Control Cavity Enable

Activates/deactivates the temperature control.

Set Temperature

Input field for set temperature Tset.

Actual Temperature

Display field for actual temperature Tact.

7.2

Scan & Lock Tab

NOTE !

To show and use the Scan & Lock tab, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence is already installed. Otherwise a 30-day trail licence is provided on the USB flash drive in the Options Folder. Dual- or Quad-Laser-Operation: With a single Lock option installed, in combination with the Dual- or Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

Figure 106 Scan & Lock tab (example DLC DL pro)

SC - Scan Control

For a full description, please refer to SC Scan Control in section 7.1.1.

Lock Settings Enable

Locks/unlocks the laser to the selected lockpoint candidate.

Hold

Freezes the PID controller(s) output at the current value. When deselected by clicking again, the PID controller(s) continue to regulate starting with the value prior to the selection of Hold.

Lock Input Signal

Selection of the lock input signal. Chose the signal the DLC pro should be using to lock the laser. Fine In 1/Fine In 2 BNC connector on DLC pro front panel. Fast In 3/Fast In 4 BNC connector on DLC pro front panel. PDH In 1/PDH In 2 Only with PDH module. SMB-connectors on PDH module panel.

Lock Type

Selection whether to lock to an edge or to an extremum of the input signal. Top of Fringe: LIR Lock to an extremum (requires modulation). Side of Fringe: Lock to an edge (slope). Top of Fringe PDH: Only with PDH module. PDH Lock to an extremum (requires modulation).

NOTE !

Lock Type Top of Fringe: Top of fringe locking is only possible without a FALC pro module (i.e., None) selected as FALC Selection. Lock Type Top of Fringe PDH: If the PDH photo diode is DC-coupled, the Lock Input Signal can be derived by selecting PDH In 1/PDH In 2 from the SMB-connectors on the PDH module.

Error Signal

Only when Top of Fringe PDH as Lock Type and Fine In/Fast In as Lock Input Signal is selected. Selection of the error signal generated by the PDH module. PDH Error 1 Error signal at err/lo 1 connector of the PDH module. PDH Error 2 Error signal at err/lo 2 connector of the PDH module.

Lock Without Lockpoint

Check box to select the Lock mode without lockpoint candidates. The lock is triggered in the middle of a rising scan ramp (equivalent to Scan Offset).

PID Selection

Selects the PID controllers for stabilizing the laser. Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage. None PID 1 PID 2 PID 1+2

FALC Selection

NOTE !

Only when a FALC pro module is connected, and Top of Fringe as Lock Type is NOT selected. Selects the FALC pro module used for that is used for the fast control loop. None FALC 1 FALC 2 FALC 3 FALC 4

The DLC pro supports up to four FALC pro modules in a CAN link chain.

Set Level

Only when Side of Fringe as Lock Type is selected. Set lock level voltage for Side of Fringe lockpoint candidates.

Compensation Offset

Only when Side of Fringe as Lock Type is selected and FALC pro module is connected. Set compensation offset voltage for Side of Fringe lockpoint candidates.

Laser

NOTE !

Parameters of the laser which can be modified for scanning and locking. The Laser parameters correspond to the respective parameters in the Laser tab.

CC Set Current

Input field for set current Iset.

PC Set Voltage

Input field for a DC offset voltage which is applied to the piezo. Not available for DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator.

TC Set Temperature

Input field for set temperature Tset.

SMC-Single Mode Control

The SMC-Single Mode Control section is only displayed in case a laser head with single mode control is connected to the DLC pro. For a full description, please refer to section 7.1.3 and to the SMC manual.

PID 1/PID 2

Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage.

Gain

Overall gain factor of the selected PID controller.

P

Proportional gain of the selected PID controller.

I

Integral gain of the selected PID controller.

D

Differential gain of the selected PID controller.

Access advanced setting options by clicking the triangle below. Output Channel

Output channel that is controlled by the PID. PC Voltage: The PID controls the piezo voltage. TC Set Temperature: (only DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator) For DFB pro or DL pro BFY laser heads, PC Voltage is not available as output channel. When TC Set Temperature is selected, the scan signal is directed to the Temperature Control module and the laser diode temperature is scanned. CC Current: The PID controls the laser current. Out A: PID output signal is directed to the Out A BNC-connector on the DLC pro front panel. Out B: PID output signal is directed to the Out B BNC-connector on the DLC pro front panel. EOM Voltage Slow (only laser systems with intra-cavity EOM): The PID controls the voltage applied to the slow electrode of the intra-cavity EOM.

Sign Positive

Checkbox to select positive polarity of the PID output in respect to the selected SC Scan Output. When selected, an increased PID controller output acts in the same direction as an increase of the Lock Input Signal.

Use I-cut-off (PID 1 only)

Activated by the checkbox. Frequency in Hz below which the integral gain of the PID controller is limited. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

Use Limit

Checkbox to define the symmetric maximum value which the PID controller can add or subtract to/from the offset of the piezo voltage or the laser current, depending on the selected PID Output Channel. Enter the maximum current, voltage or temperature in mA, V or °C into the Input Field.

Enable PID

Checkbox to enable/disable the PID controller.

Lock-In

Parameters for the Error signal generation required for the Top of Fringe lock type.

NOTE !

The Lock-In parameters are only displayed if Top of Fringe is selected as Lock Type in the Lock Settings section.

Enable

Enables/disables the Error signal generation.

Frequency

Modulation frequency in Hz. A good starting value for a modulation using the laser current is 20000 Hz.

Amplitude

Modulation amplitude (pp: peak-to-peak); the unit depends on the selected Lock-In Output Channel: PC Voltage: [V pp] CC Current: [mA pp]

Access advanced setting options by clicking the triangle below. Output Channel

Signal output to which the modulated signal is applied. PC Voltage: Modulated signal is applied to the piezo voltage. TC Set Temperature: (only DLC DFB pro/DLC DL pro BFY and laser systems with DFB pro Master Oscillator) For DFB pro or DL pro BFY laser heads, PC Voltage is not available as output channel. When TC Set Temperature is selected, the scan signal is directed to the Temperature Control module and the laser diode temperature is scanned. CC Current: Modulated signal is applied to the laser current. Out A: Modulated signal is directed to the Out A BNC-connector on the DLC pro front panel. Out B: Modulated signal is directed to the Out B BNC-connector on the DLC pro front panel.

Lock Level

Offset (normally set to zero) for the PID controller used for the Top of Fringe lock type to compensate for spurious DC signals originated by the demodulation of the modulated input signal (in most cases due to an amplitude modulation component).

Phase

Relative phase (in °) between modulation and demodulation. Optimize the parameter (used for the Top of Fringe lock type) to get the Error signal as a derivative of the input signal. We suggest to turn-off the autoscaling of the signal during optimization.

AutoLIR

Clicking automatically determines and sets the Phase to get the Error signal as a derivative of the input signal.

P/N Tolerance

If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by adjusting the P/N Tolerance correctly for the signal and signal-to-noise ratio used.

### 7.2.1 Using the Lock Points Tool of the Signal Display for Locking

NOTE !

For showing the Lock-relevant functions of the Signal Display, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PCGUI (please refer to section 11.20).

The Lock Points Tool in the Signal Display is used for showing and selecting lockpoints. The procedures for Side of Fringe and Top of Fringe locking with the PC-GUI is described in sections 7.2.2 and 7.2.3.

Figure 107 Lock Points tool of the Signal Display

For detailed information on the Signal Display, please refer to section 6.9.

- To specify the input signal to use for locking, select Lock Input Signal in the Lock Settings section of
the Scan&Lock tab.

- With the Lock Points tool selected, the Input Trace Signal is fixed to Lock Input.
- To get the Error signal that is required for Top of Fringe locking, select Auxiliary Trace Signal > LockIn Output. The laser is actually locked to the Lock-In Output signal.
- To display the lockpoint candidates, click Lock Points. Depending on the selected lock type (Side
of fringe or Top of Fringe) the arrow inside the lockpoint candidate clearly shows its identity (see

Figure 108.

Figure 108 Identification of lockpoint candidate

- To deselect unwanted lockpoint candidates for a clearer view, use the Lock Candidate Filter: A
right click in the graph area opens a menu. Select Lock Candidate Filter and configure the settings so that unwanted lockpoint candidates are not displayed.

- To lock the laser, select a lockpoint candidate and click Lock Enable on the Signal Display or click
Enable in the Lock Settings section of the Scan&Lock tab. The lock can also be enabled by double-clicking on the desired lockpoint candidate.

- To unlock the laser, click Lock Enable on the Signal Display or click Enable in the Lock Settings section of the Scan&Lock tab. The lock can also be disabled by double-clicking somewhere in the
Signal Display screen area.

- The Lock Status shows the actual status of the lock (please refer to section 6.9).
- To freeze the screen display, check the Hold checkbox.
### 7.2.2 Side of Fringe Locking with TOPAS DLC pro PC-GUI

NOTE !

For showing the Lock-relevant functions of the Signal Display, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PCGUI (please refer to section 11.20).

Prerequisites:

- Experimental setup connected to the DLC pro (for details, see section 8.1):
- Control computer connected to the DLC pro (for details please refer to section 4.5.1).
- TOPAS DLC pro (PC-GUI) installed and started (for details please refer to section 6.2).
- Lock option license key activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).
- Lock Input signal connected to Fine In or Fast In (BNC-connectors on DLC pro front panel).
- Laser head connected to the DLC pro as described in section 4.5.3.
Figure 109 Signal Display showing the Lock Input signal (red) and lockpoint candidates for Side of Fringe

locking.

1.
Add the Signal Display to the screen (Laser Menu > Signal Display) and select the XY display mode. Click on the axis labels with the right mouse key and select Autoscale.

2.
Select the Scan&Lock tab (Laser Menu > Laser Control > Scan&Lock tab).

3.
Select the input channel of the Lock Input signal: Lock Settings > Lock Input Signal. Choose the Lock Input signal to be shown on the Signal Display as a red trace (Input Trace Signal).

4.
Select the Side of Fringe lock type: Lock Settings > Lock Type > Side of Fringe.

5.
Select the PID controller(s) for regulating the lockpoint: Lock Settings > PID Selection. Ensure that each PID output is configured correctly.

NOTE !

Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

6.
Move and zoom the Lock Input signal and adjust the laser current (Laser > CC Set Current) until the desired lockpoint in the spectrum is clearly visible on the Signal Display.

7.
Click Lock Points on the Signal Display to display the lockpoint candidates.

8.
Set the desired lock level voltage in one of the following ways:

- Specify the Set Level in the Lock Settings section.
- Click to the desired voltage on the Signal Display.
- Move the horizontal gray line on the Signal Display to the desired voltage.
NOTE !

9.
The current lock voltage level is displayed as a gray line on the Signal Display. Lockpoint candidates are displayed where the Lock Input signal crosses the lock voltage level line.

Locking with lockpoint candidates: Select the lockpoint by clicking the desired lockpoint candidate. For a clearer display, unwanted lockpoint candidates can be deselected either using the Lock Candidate Filter (right-click in the graph area) or in the Parameters window (laser 1 > dl > lock > candidate filter > positive-edge/negative-edge). Locking without lockpoint candidates: Check the box Lock Without Lockpoint in the Lock Settings section of the Scan & Lock tab. Move the spectrum on the Signal Display in x-direction so that the desired region to trigger the lock is located in the center.

10.
Click Lock Enable on the Signal Display or click Enable in the Lock Settings section. Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. The Lock Status shows the actual status of the lock (please refer to section 6.9). Locking without lockpoint candidates: The laser scans to the center of the spectrum (Scan Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on. The Lock Status shows the actual status of the lock (please refer to section 6.9).

11.
Adjust the PID Gain settings and the advanced settings of the PID controller(s) to optimize the lock: PID 1, PID 2. Please refer to section 9.3 for information on PID controller configuration and to section 7.2 for information on PID controller setting options.

### 7.2.3 Top of Fringe (Lock-In/PDH) Locking with TOPAS DLC pro PC-GUI

NOTE !

For showing the Lock-relevant functions of the Signal Display, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PCGUI (please refer to section 11.20). Only Top of Fringe (Lock-In): The Lock Wizard in the TOPAS DLC pro PC-GUI (Laser Menu > Optimization Tools > Lock Wizard, see section 6.8) is an interactive tool which helps to setup a Top of Fringe lock.

NOTE !

If your DLC pro is equipped with a PDH module (see section 10.2.11), you can also perform a Top of Fringe PDH lock, instead of the Lock-In procedure described in this section. In this case connect your experimental setup as shown in section 8.3.3 and follow the instructions below for Lock-In accordingly. Settings for the PDH module are performed in the PDH window (see section 6.9). For an application example of a Top of Fringe PDH lock with high-finesse cavity, please refer to section 8.2.

NOTE !

It is possible to route the Lock-In Error signal to the Out A/B BNC connectors on the DLC pro front panel. Please use the Parameters window to set the following parameters: io:out-a/b:external-input:signal = 30, io:out-a/b:external-input:factor = 1.0, and io:out-a/b:external-input:enabled = #t Choose io:out-a/b:linked-laser = 1 .. 4 to select the Lock-In Error signal of laser 1 .. 4. By routing the Lock-In Error signal to analog outputs, the signal resolution may be reduced. Please use the parameters io:out-a:external-input:factor or io:out-b:external-input:factor, respectively, in order to increase signal-to-noise.

Prerequisites:

- Experimental setup connected to the DLC pro (for details, see sections 8.3.2 or 8.3.3):
- Control computer connected to the DLC pro (for details please refer to section 4.5.1).
- TOPAS DLC pro (PC-GUI) installed and started (for details please refer to section 6.2).
- Lock option license key activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20).
- Only Lock-In: Lock Input signal connected to Fine In or Fast In (BNC connectors on DLC pro front
panel).

- Only PDH Lock: Lock Input signal connected to in 1 or in 2 (SMB connectors on PDH module
panel).

- Laser head connected to the DLC pro as described in section 4.5.3.
Figure 110 Signal Display showing lockpoint candidates for Top of Fringe locking

1.
Add the Signal Display to the screen (Laser Menu > Signal Display) and select the XY display mode. Click on the axis labels with the right mouse key and select Autoscale.

2.
Select the Scan&Lock tab (Laser Menu > Laser Control > Scan&Lock tab).

3.
Select the input channel of the Lock Input signal: Lock Settings > Lock Input Signal depending on the desired Lock Type and the experimental setup. Choose the Lock Input signal to be shown on the Signal Display as a red trace (Input Trace Signal).

4.
Select the Top of Fringe lock type: Lock Settings > Lock Type > Top of Fringe or Top of Fringe PDH.

5.
Select the PID controller(s) for regulating the lockpoint: Lock Settings > PID Selection. Ensure that each PID output is configured correctly.

NOTE !

Typically, PID 1 handles the high frequencies by controlling the laser current. PID 2 is responsible for the lower frequencies by controlling the piezo voltage. If PID 1 is used in parallel with PID 2 in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

6.
Move and zoom the Lock Input signal and adjust the laser current (Laser > CC Set Current) until the desired lockpoint in the spectrum is clearly visible on the Signal Display.

7.
Click Lock Points on the Signal Display to display the lockpoint candidates.

8.
If necessary, switch on the Lock-In Error signal generation (Lock-In, Enable) and display the modulated/demodulated Error signal on the Signal Display: Auxiliary Trace Signal > Lock-In Output.

9.
10.
11.
Select the signal output to which the Error signal modulation is applied: Lock-In > Output Channel. In case of Lock Settings > Lock Type > Top of Fringe PDH the Error signal modulation is always applied to the out 1/2 SMB-connectors at the PDH module. Adjust the modulation frequency, modulation amplitude, lock level, and phase of the Error signal: Lock-In > Frequency, Amplitude, Lock Level, Phase. Modify the demodulation phase (Lock-In > Phase) until the Error signal matches the derivative of the Lock Input signal and the Error signal runs in the correct direction through the signal extremum to which you want to lock:

- Lockpoint is in signal valley: rising flank of the Error signal (default color: blue).
- Lockpoint is on signal peak: falling flank of the Error signal (default color: blue).
This optimization may be eased by disabling auto scaling. Locking with lockpoint candidates: Select a lockpoint by clicking the desired lockpoint candidate. For a clearer display, unwanted lockpoint candidates can be deselected either using the Lock Candidate Filter (right-click in the graph area) or in the Parameters window (laser 1 > dl > lock > candidate filter > top/bottom).

NOTE !

If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by setting the Peak/Noise Tolerance in the Lock Candidate Filter of the Signal Display (Parameters window: laser 1 > lock > candidate-filter > peak-noise-tolerance) correctly for the signal and signal to noise ratio used. This parameter is 0 for automatic detection, and automatic detection does not always work perfectly. The parameter should be set to a value that is larger than the peak-to-peak noise and smaller than the peaks that the laser should be locked to. For a convenient parameter optimization it is recommended to use the TOPAS DLC pro PC-GUI where the parameter can be changed while the signal is displayed.

Locking without lockpoint candidates: Check the box Lock Without Lockpoint in the Lock Settings section of the Scan & Lock tab. Move the spectrum on the Signal Display in x-direction so that the desired region to trigger the lock is located in the center.

12.
Click Lock Enable on the Signal Display or click Enable in the Lock Settings section. Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops and the PID controller(s) switch on. The Lock Status shows the actual status of the lock (please refer to section 6.9). Locking without lockpoint candidates: The laser scans to the center of the spectrum (Scan Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on. The Lock Status shows the actual status of the lock (please refer to section 6.9).

NOTE !

13.
The laser is actually locked to the Lock-In Error signal (0 V of the Lock-In Output signal). The Lock-In Error signal is the input signal for the PID controller(s).

Adjust the PID gain settings and the advanced settings of the PID controller(s) to optimize the lock: PID 1, PID 2. Please refer to section 9.3 for information on PID controller configuration and to section 7.2 for information on PID controller setting options.

7.3

ReLock Tab

NOTE !

To show and use the ReLock tab, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to 11.20).

Figure 111 ReLock tab

Lock Detection

This tab allows to set the parameters for the out-of-lock detection.

Enable

Enables/disables the Out-of-lock detection.

Input Signal

Select input signal for the ReLock window (Window Input signal).

Level High

Upper voltage limit of the ReLock window.

Level Low

Lower voltage limit of the ReLock window.

Hysteresis

Tolerance between the out-of-lock voltage levels (Level High or Level Low) and the voltage levels which determine that the laser is in lock again (see section 5.4.11).

Delay

Time between detection of the out-of-lock state and initialization of a reset/relock procedure.

Out-of-Lock Action

Behavior of the PID controllers after the out-of-lock state was detected and the Delay time has passed. Enable Reset:Check box to enable reset of all selected PID controllers.

ReLock Enable

Enables/disables the ReLock scan.

Amplitude

ReLock scan amplitude. The unit depends on the selected Output Channel.

Frequency

ReLock scan frequency in [Hz].

Output Channel

Select Output channel of the ReLock scan. PC Voltage: Piezo voltage. TC Set Temperature (only DLC DFB pro/DLC DL pro BFY and systems with DFB pro Master Oscillator): For DFB pro or DL pro BFY laser heads, PC Voltage is not available as output channel. When TC Set Temperature is selected, the scan signal is directed to the Temperature Control module and the laser diode temperature is scanned. CC Current: Laser current. Out A: ReLock output signal is directed to the Out A BNC-connector on the DLC pro front panel. Out B: ReLock output signal is directed to the Out B BNC-connector on the DLC pro front panel.

### 7.3.1 ReLock Configuration with TOPAS DLC pro PC-GUI

Prerequisites:

- The laser is ready to be locked (please refer to sections 7.2.2, 7.2.3).
- Signal Display added to the screen (Laser Menu > Signal Display).
- A separate signal for out-of-lock detection (Window Input signal) is connected to Fine In or Fast In
(BNC-connectors on DLC pro front panel).

1.
Select the ReLock tab (Laser Menu > Laser Control > ReLock tab) and select the XY display mode in the Signal Display.

2.
Select the channel for the Lock Detection Input signal: Lock Detection > Input Signal. Display the Lock Detection Input signal on the Signal Display: Auxiliary Trace Signal.

3.
Define the limits of the ReLock window for out-of-lock detection: Lock Detection > Level High, Level Low, Hysteresis (please refer to section 5.4.11).

4.
Define the delay between out-of-lock detection and reset/relock scan activation: Lock Detection > Delay.

5.
Enable/disable the PID controller(s) reset: Out-of Lock-Action Enable Reset checkbox. The speed of the reset is dependent on the Slew Rate settings of the selected PID output channels.

6.
Enable/disable the ReLock scan: ReLock > Enable. Define amplitude, frequency, and output channel of the ReLock scan: ReLock > Amplitude, Frequency, Output Channel.

7.
Enable/disable the out-of-lock detection: Lock Detection > Enable.

NOTE !

In case the ReLock Frequency is lower than the Scan Frequency set in the SC Scan Control section of the Laser tab (see section 7.1.1), the XY display mode of the Signal Display does not show a whole ReLock scan period. Use the Time display mode for proper display.

7.4

SHG Tab (DLC DL-/TA-SHG pro)

Figure 112 SHG tab (DLC DL-/TA-SHG pro)

Cavity Scan Settings

SHG cavity scan settings.

Enable

Enables/disables the SHG cavity scan.

Scan Amplitude

Peak-to-peak scan amplitude in [Vpp].

Scan Offset

DC signal level in [V].

Click the triangle below to access advanced setting options. Scan Frequency

Set repetition frequency in Hz.

TC Crystal

Settings for the SHG crystal temperature controller. Please note that the temperature gradient is limited to avoid damage of the crystal.

Enable

Activates/deactivates the crystal Temperature Control. When TC Crystal is disabled, the crystal temperature is regulated to 25 °C.

Set Temperature

Input field for set temperature Tset.

Actual Temperature

Display field for actual temperature Tact.

Cavity ReLock Enable

Enables/disables the SHG ReLock.

Click the triangle below to access advanced setting options. Settings

This tab allows to set the SHG ReLock parameters.

Input Signal

Select input signal for the ReLock window (Window Input signal). SHG Intra-Cavity Signal: Circulating fundamental power inside the SHG cavity. Threshold and Hysteresis are given in [V]. SHG Power: Harmonic output power of the SHG cavity. Threshold and Hysteresis are given in [mW].

Amplitude

ReLock scan amplitude in [Vpp].

Frequency

ReLock scan frequency in [Hz].

Lock Detection

This tab allows to set the parameters for the out-of-lock detection.

Threshold

Lower voltage/power limit of the ReLock window.

Hysteresis

Tolerance between the out-of-lock voltage/power level (Threshold) and the voltage/power level which determines that the laser is in lock again (please refer to the DL-/TA-SHG/FHG pro manual for ReLock configuration) Note that for the SHG cavity lock the Level High of the ReLock window does not need to be adjusted by the user.

Delay

Time between detection of the out-of-lock state and initialization of a reset/relock procedure.

Master

NOTE !

Parameters of the Master Oscillator which can be modified without the need to switch to the Laser tab. The Master parameters correspond to the respective parameters in the Laser tab.

CC Set Current

Input field for set current Iset of the Master Oscillator in [mA].

PC Set Voltage

Input field for a DC offset voltage which is applied to the piezo of the Master Oscillator in [V].

Lock Settings Enable

Locks/unlocks the SHG cavity to a cavity resonance which is close to the central cavity piezo position (approx. 70 V piezo voltage).

General PID Selection

NOTE !

Selects the PID controllers for stabilizing the SHG cavity. Typically, PID Slow is responsible for the lower frequencies by controlling the slow cavity piezo. PID Fast handles the higher frequencies by controlling the fast cavity piezo. P Analog is used to lock the Master Oscillator frequency onto the cavity length via the modulation input of the Master Oscillator.

Please note that the laser must be configured for P Analog adjustment. Please refer to the DL-/TA-SHG/FHG pro manual for details. None PID Slow PID Slow + Fast PID Slow + P Analog PID Slow + Fast + P Analog

Set Level

Set lock level voltage for the SHG cavity lock Error signal.

Click the triangle below to access advanced setting options. PDH Photo Diode Gain

Gain of the Pound-Drever Hall photo diode in [V/V].

Cavity Feed Forward Enable Activates/deactivates the SHG cavity Feed Forward, i.e. the slow cavity piezo voltage follows the Master Oscillator piezo voltage to support faster scan speeds in locked operation. Cavity Feed Forward Factor Scaling parameter of the SHG cavity Feed Forward in [V/V]. Local Oscillator Enable

Enables/disables the local oscillator of the SHG cavity lock. The local oscillator operates at a frequency of 25 MHz.

Amplitude

Local oscillator amplitude in [Vpp].

Phase

Relative phase between modulation and demodulation in [°]. Optimize the parameter to get the Error signal as a derivative of the input signal. We suggest to turn off autoscaling of the signal during optimization.

AutoPDH

Starts an algorithm which finds the optimum phase between the photo diode signal and the local oscillator.

PID Slow/PID Fast

PID controllers as selected in PID Selection.

Gain

Overall gain factor of the PID controller.

P

Proportional gain of the PID controller in [V/V].

I

Integral gain of the PID controller in [V/V/ms].

D (PID Fast only)

Differential gain of the PID controller in [V/V x µs].

Use I-cut-off (PID Fast only)

Activated by the checkbox. Frequency in Hz below which the integral gain of the PID controller is limited. If PID Fast is used in parallel with PID Slow in a control system, I-cutoff prevents that the two PID loops accumulate offsets in different directions.

P Analog

As selected in PID Selection. P Analog is used to lock the Master Oscillator frequency onto the cavity length via the modulation input of the Master Oscillator.

NOTE !

Please note that the laser must be configured for P Analog adjustment. Please refer to the DL-/TA-SHG/FHG pro manual for details.

P

Proportional gain of the analog feedback path to the Master Oscillator in [V/V].

7.5

FHG Tab (DLC DL-/TA-FHG pro)

Figure 113 FHG tab (DLC DL-/TA-FHG pro)

The FHG tab for control of the FHG Stage is equivalent to the SHG tab which is described in section 7.4. Please note that P Analog is not available.

7.6

OPO Tab (DLC TOPO)

Figure 114 OPO tab (DLC TOPO)

TC Crystal

Settings for the TOPO crystal temperature controller. Please note that the temperature gradient is limited (1 K/min) to avoid damage of the crystal.

Enable

Activates/deactivates the crystal Temperature Control. When enabled, the crystal temperature is regulated to the Set Temperature. When disabled, the crystal temperature is regulated to the idling temperature of 35 °C.

Set Temperature

Input field for the crystal set temperature.

Actual Temperature

Display field for actual crystal temperature.

TC Cavity

Settings for the TOPO cavity Temperature Control.

Enable

Activates/deactivates the cavity Temperature Control. When enabled, the cavity temperature is regulated to the Set Temperature.

Set Temperature

Input field for cavity set temperature.

Actual Temperature

Display field for actual cavity temperature.

Wavelength Control Motor Position

NOTE !

Settings for TOPO output wavelength control. Intracavity crystal position with a resolution of 40 nm over a 0 - 17.5 mm range.

Adjustments smaller than 100 nm do not cause any noticeable changes in wavelength or power of the DLC TOPO laser system.

Etalon Servo Position

The etalon motor moves in 10-step increments, with each increment giving 20 arc-minutes of resolution (range: 4000 - 8000).

OPO Slow PZT Voltage

Intracavity piezo (PZT) voltage in the range of 0 - 140 V.

TC Set Temperature

Input field for DFB pro BFY pump laser temperature.

NOTE !

The external fiber amplifier of the DLC TOPO laser system requires 2 - 5 mW of input power. To make sure that the DFB pro BFY pump laser output is inside this range, the CC Set Current in the Laser tab should never be changed from the factory setting (see DFB CC Set Current in section 02 of the DLC TOPO Production and Quality Control Data Sheet). Consequently, please use CC Analog Remote Control of the DFB pro BFY current only for locking purposes, and do not use the Feed Forward feature, as this also affects the laser diode current.

System Powers Pump Power

Display of the pump power measured by the power monitoring unit inside the TOPO head.

Depleted Pump Power

Display of the depleted pump power measured by the power monitoring unit inside the TOPO head.

Signal Power

Display of the signal power measured by the power monitoring unit inside the TOPO head.

NOTE !

For details on the power monitoring units and the required alignment and calibration procedures, please refer to the TOPO head manual.

7.7

Optimization/Stabilization Tab

NOTE !

For details of the power stabilization, please refer to section 5.4.6.

### 7.7.1 DLC pro for Laser Head DL pro

Figure 115 Stabilization tab (DLC DL pro)

The Stabilization tab comprises the operator controls for the DL pro power stabilization. Please refer to section 7.7.5 for a description of the basic operator controls. The specific operator controls for stabilization on External Power are described below. For an example on how to configure an external power stabilization, please refer to section 5.4.6.1 and follow the instructions accordingly.

Power Stabilization

Settings for the laser power stabilization.

Enable

Enables/Disables the laser power stabilization (PowerLock). The indicator shows the status of the PowerLock. Dark green: PowerLock disabled. Yellow:

- PowerLock enabled, but power is not stabilized,
locking procedure is in progress.

- Actual Current not sufficient for reaching the
desired power Set Level. Light green: PowerLock enabled and power is stabilized.

Input Signal

Selects which monitor photo diode is used for the power stabilization. External Power: External photo diode connected to one of the four DLC pro front panel BNC-connectors Fine/ Fast In.

External Physical Channel

Select the BNC-connector on the DLC pro front panel for connection of the external photo diode.

Photo Diode Value

Displays the photo diode voltage applied to the External Physical Channel [V].

External Power Calibration Factor

Enter the calibration factor for the external power.

External Power Calibration Offset

Enter the calibration offset for the external power.

Set Level

Set lock level power for the power stabilization in [mW].

Actual Level

Displays the current power of the selected Input Signal.

Gain

Overall gain factor of the power stabilization PID controller.

P

Proportional gain of the power stabilization PID controller in [mA/mW].

I

Integral gain of the power stabilization PID controller in [mA/mW/ms].

D

Differential gain of the power stabilization PID controller in [mA/mW x µs].

Hold Output Current on Unlock If checked, the current of the component used for the power stabilization will stay at its present value when the power stabilization is disabled. If not checked, the current is set to the value before the power stabilization was enabled. Stabilization Detection

Settings for a detection when the power stabilization is suspended.

Enable

Enables/disables the power stabilization detection

Level

Power limit below which the power stabilization is suspended.

Hysteresis

Tolerance between Level and the actual laser power level above which the power stabilization is resumed.

### 7.7.2 DLC pro for Laser Head TA pro

Figure 116 Stabilization tab (DLC TA pro)

The Stabilization tab comprises the operator controls for the TA pro power stabilization. Please refer to section 7.7.5 for a description of the operator controls.

### 7.7.3 DLC pro for Laser Head TA pro AL

Figure 117 Stabilization tab (DLC TA pro AL, example one laser unit in TA pro configuration)

The Optimization/Stabilization tab comprises the operator controls for the TA pro AL optimization and power stabilization routines.

Power Optimization

This section allows to start various procedures for power optimization. Please note that, depending on the individual TA pro AL configuration, some optimization features may be not available. The process of the selected optimization procedure can be displayed on the Optimization Progress Monitor which is available in the laser menu.

Probe Power

Only available with DLC TA pro AL laser in DL pro and TA pro configuration. Clicking starts the optimization procedure for the probe laser beam power.

Amp. Power

Only available with DLC TA pro AL laser in TA pro and BoosTA pro configuration. Clicking starts the optimization procedure for the Tapered Amplifier power.

Fiber Power

Only available with DLC TA pro AL laser in TA pro and BoosTA pro configuration. Clicking starts the optimization procedure for the fiber output power.

Advanced Checkbox

When selected, a combination of optimization algorithms is performed. For details, please refer to the TA pro AL manual.

All Stages

Clicking starts the available optimization procedures in a preset sequence:

1. Probe Power optimization
2. Amp. Power optimization
3. Fiber Power optimization
Status

Text and indicator provide additional information about the algorithm state.

Abort

Stops a running optimization process.

Power Stabilization

Settings for the laser power stabilization.

Enable

Enables/Disables the laser power stabilization (PowerLock). The indicator shows the status of the PowerLock. Dark green: PowerLock disabled. Yellow:

- PowerLock enabled, but power is not stabilized,
locking procedure is in progress.

- Actual Current not sufficient for reaching the
desired power Set Level. Light green: PowerLock enabled and power is stabilized.

Input Signal

Selects which monitor photo diode is used for the power stabilization. The available selection is dependent on the TA pro AL configuration. DL pro configuration External Power: External photo diode connected to one of the four DLC pro front panel BNC-connectors Fine/Fast In. Laser diode current is controlled. TA pro/BoosTA pro configuration External Power: External photo diode connected to one of the four DLC pro front panel BNC-connectors Fine/Fast In. Amplifier current is controlled. Amp. Power: TA output photo diode is used for stabilization. Amplifier current is controlled.

External Physical Channel

Select the BNC-connector on the DLC pro front panel for connection of the external photo diode.

Photo Diode Value

Displays the photo diode voltage applied to the External Physical Channel [V].

External Power Calibration Factor

Enter the calibration factor for the external power.

External Power Calibration Offset

Enter the calibration offset for the external power.

Set Level

Set lock level power for the power stabilization in [mW].

Actual Level

Displays the current power of the selected Input Signal.

Gain

Overall gain factor of the power stabilization PID controller.

P

Proportional gain of the power stabilization PID controller in [mA/mW].

I

Integral gain of the power stabilization PID controller in [mA/mW/ms].

D

Differential gain of the power stabilization PID controller in [mA/mW x µs].

Hold Output Current on Unlock If checked, the current of the component used for the power stabilization will stay at its present value when the power stabilization is disabled. If not checked, the current is set to the value before the power stabilization was enabled. Stabilization Detection

Settings for a detection when the power stabilization is suspended.

Enable

Enables/disables the power stabilization detection

Level

Power limit below which the power stabilization is suspended.

Hysteresis

Tolerance between Level and the actual laser power level above which the power stabilization is resumed.

### 7.7.4 DLC pro for Laser Head CTL

Figure 118 Optimization tab (DLC CTL)

The Optimization/Stabilization tab comprises the operator controls for the CTL power stabilization and the optimization routines. Please refer to section 7.7.5 for a description of the basic power stabilization operator controls. The CTL specific power stabilization and optimization operator controls are described below.

Power Stabilization

Selects which monitor photo diode is used for the power stabilization.

Enable

Enables/Disables the laser power stabilization (PowerLock). The indicator shows the status of the PowerLock. Dark green: PowerLock disabled. Yellow:

- PowerLock enabled, but power is not stabilized,
locking procedure is in progress.

- Actual Current not sufficient for reaching the
desired power Set Level. Light green: PowerLock enabled and power is stabilized.

Input Signal

CTL Power

Feed Forward

Enable/disable the power stabilization Feed Forward. When enabled, the piezo voltage is changed proportional to a laser diode current change. This results in a higher wavelength stability when the Feed Forward Factor is set properly.

Feed Forward Factor

Enter the power stabilization Feed Forward factor. To set the Feed Forward Factor, couple the laser beam into a wavelength meter. Set the Feed Forward Factor so that a wavelength change during a change of the power stabilization Set Level is minimized. Reasonable values are 0 .. 1 V/mA.

CTL output power.

CTL Optimization SMILE

Clicking SMILE initiates an optimization of SMILE parameters (takes about 1 minute). For details please refer to the CTL manual.

FLOW

Clicking FLOW minimizes the lasing threshold for a number of different wavelengths (takes about 5 minutes). After FLOW has completed successfully, the optimization of SMILE parameters is automatically performed. For details please refer to the CTL manual.

Abort

Click Abort to stop the optimization. The previous SMILE/FLOW parameter values are resumed.

Progress Bar

The progress bar indicates the status of the optimization.

NOTE !

An error message appears, if SMILE or FLOW optimization is not possible. Potential reasons are active power stabilization, an active motor scan, or enabled ARC for the motor.

### 7.7.5 DLC pro for Laser Head DL-/TA-SHG/FHG pro

Figure 119 Optimization/Stabilization tab (example DLC DL-/TA-FHG pro)

The Optimization/Stabilization tab allows access to various optimization and stabilization procedures. The Optimization tab is only available with the AutoAlign option (motorized mirrors). The Stabilization tab is only available with TA-SHG/FHG pro laser systems as the Tapered Amplifier power is used for stabilization.

Power Optimization

Only with AutoAlign option. This section allows to start various procedures for power optimization. Please note that, depending on the individual DLC DL-/TA-SHG/FHG pro set-up, some optimization features may be not available. The process of the selected optimization procedure can be displayed on the Optimization Progress Monitor which is available in the laser menu.

Amp Power

Clicking starts the optimization procedure for the amplifier power (only DLC TA-SHG/FHG pro).

SHG Power

Clicking starts the optimization procedure for the SHG power.

Advanced Checkbox

FHG Power Fiber Power

The advanced option allows a more sophisticated algorithm which may achieve higher SHG power levels. only DLC DL-/TA-FHG pro Clicking starts the optimization procedure for the FHG power. Clicking starts the optimization procedure for the fiber power (available only with option FiberMon).

All Stages

Clicking starts the available optimization procedures in a preset sequence:

1. TA Power optimization
(only DLC TA-SHG/FHG pro)

2. SHG Power optimization (SHG Advanced algorithm if selected)
3. FHG Power optimization (only DLC DL-/TA-FHG pro)
4. Fiber Power optimization (only with option FiberMon)
Status

Text and indicator provide additional information about the algorithm state.

Abort

Stops a running optimization process.

Power Stabilization

Settings for the laser power stabilization.

Enable

Enables/Disables the laser power stabilization (PowerLock). The indicator shows the status of the PowerLock. Dark green: PowerLock disabled. Yellow:

- PowerLock enabled, but power is not stabilized,
locking procedure is in progress.

- Actual Current not sufficient for reaching the
desired power Set Level. Light green: PowerLock enabled and power is stabilized.

Input Signal

Selects which monitor photo diode is used for the power stabilization. External Power: External photo diode connected to one of the four DLC pro front panel BNC-connectors Fine/ Fast In. Please refer to section 7.7.1 for input channel selection and calibration options. Amp. Power: TA output photo diode. SHG Power: SHG output photo diode. FHG Power: FHG output photo diode (only DLC TA-FHG pro). Fiber Power: Fiber monitor photo diode (only with option FiberMon).

Set Level

Set lock level power for the power stabilization in [mW].

Actual Level

Displays the current power of the selected Input Signal.

Gain

Overall gain factor of the power stabilization PID controller.

P

Proportional gain of the power stabilization PID controller in [mA/mW].

I

Integral gain of the power stabilization PID controller in [mA/mW/ms].

D

Differential gain of the power stabilization PID controller in [mA/mW x µs].

Hold Output Current on Unlock If checked, the current of the component used for the power stabilization will stay at its present value when the power stabilization is disabled. If not checked, the current is set to the value before the power stabilization was enabled. Stabilization Detection

Settings for a detection when the power stabilization is suspended.

Enable

Enables/disables the power stabilization detection

Level

Power limit below which the power stabilization is suspended.

Hysteresis

Tolerance between Level and the actual laser power level above which the power stabilization is resumed.

# 8 Application Examples

NOTE !

To utilize the DLC pro Lock function modes, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence is already installed. Otherwise a 30-day trail licence is provided on the USB flash drive in the Options Folder. Dual- or Quad-Laser-Operation: With a single Lock option installed, in combination with the Dual- or Quad-Laser-Operation upgrade, frequency locking of all lasers is possible.

NOTE !

The application examples below describe step-by-step the operation via the touchscreen interface. All examples can also be performed using the TOPAS DLC pro PC-GUI.

There are numerous different schemes to stabilize the frequency of lasers (e.g., to atomic or molecular resonances as well as cavities). The Lock function modes of the DLC pro are designed to cover a large range of locking scenarios. This section describes step-by-step how to perform some of the most common schemes with the DLC pro. NOTE !

This section assumes that the user has some basic knowledge of the laser system and the electronics involved. For further information, see the laser head manual and the respective sections of the DLC pro manual.

## 8.1 General System Setup

The general setup to stabilize the frequency of lasers via the DLC pro is shown in Figure 120. All locking schemes are based on a spectroscopic or cavity signal (Lock Input signal) provided by the experimental setup which serves as a reference. The Scan/Lock mode of the DLC pro supplies the scan functionality to find resonances and potential lockpoints. It is also capable of utilizing the scan response as the Error signal and provides the controllers for the feedback loops. Moreover, the DLC pro can generate an Error signal by means of a frequency modulation/demodulation technique called Lock-In or Pound-DreverHall. Furthermore, the touchscreen and the TOPAS DLC pro PC-GUI support both user-friendly and intuitive access to all lock parameters. The integrated frequency analysis (Frequency display mode) allows you to optimize the controllers for advanced applications. This section introduces the common setup with a DLC DL pro laser system for different lock scenarios.

Figure 120 Typical setup for a frequency lock of a TOPTICA diode laser head via the DLC pro

The signal from a photo diode is fed into one of the Input BNC-connectors on the DLC pro front panel. The two PID controllers act on the grating piezo via the PC module and on the laser diode current via the CC module.

Initial Setup: CAUTION ! Make sure that the laser current is switched off while installing the experimental setup. Ensure proper (personal) grounding while handling the laser head (e.g., when connecting cables).

1.
Make sure that the laser head is properly connected to the TC, CC, and PC modules on the rear panel of the DLC pro. In the application examples, a DL pro extended-cavity diode laser (ECDL) is assumed. The same setup can work equally well with the DL 100 and can be translated to other diode based laser systems like the Tapered Amplifier (DLC TA pro), the Continuously Tunable Laser (DLC CTL), and the frequency-converting laser systems (DLC DL-/TA-SHG/FHG pro). The corresponding connections of the DL 100 laser head are labeled as follows: DL pro

DL 100

Comment

mod DC

curr. mod.

DC-coupled current feedback is used for the fast feedback in addition to the slow feedback to the piezo.

bias-t

AC-coupled fast current feedback can optionally be used for feedback or modulation at high frequencies in the MHz range or to apply the modulation frequency independently from the current feedback.

mod AC

2.
The output of the photo detector is connected to one of the Fine/Fast In BNC-connectors on the DLC pro front panel. Using the Fine connectors is recommended. For the BNC-connector specifications, please refer to section 4.3.

CAUTION ! On the Home screen, tap Laser Config and check the maximum current setting Imax of the CC module to prevent damage to the laser diode. DANGER ! Do not look into the laser beam as the output can exceed the limits for class 1 specified by US laws 21 CFR 1040.10 and 2 CFR 1040.11 and the Laser Safety Standards EN 608251:2014+A11:2021, IEC 60825-1:2014. Take precautions to eliminate exposure to a direct or reflected beam.

3.
Switch on the laser by pressing the Emission button. After a few minutes, the laser will stabilize thermally. Switch to Scan/Lock mode and select the Scan function mode. You can adjust the laser frequency to the desired resonance using several methods with increasing precision:

- Coarse tuning in the 0.1 nm range is usually only required for the initial setup and can be achieved
by modifying the angle of the grating with the fine-thread screw (please refer to the laser head manual).

- Adjust the Set Current Iset (and if necessary the Set Temperature Tset) at the rotary knobs to tune the
frequency and achieve single mode operation of the laser.

- The built-in piezo allows mode hop-free scanning of the laser over several 10 GHz. The DLC pro
generates the scan signal that drives the piezo using the PC module as a high-voltage amplifier. The output is the sum of the Scan Amplitude and the Scan Offset.

4.
Adjust the settings for the scan signal generation via the rotary knobs and touch gestures or in the context parameter menu after pressing the Parameter button in Scan/Lock mode: Parameter

Description

Value to set toa

Scan > Scan Shape

Shape of the scan ramp

Triangle

Scan > Scan Frequency

Frequency of full scan (back and forth)

10 Hz

Scan Amplitude (Rotary Knob)

Scan amplitude peak-peak

10 Vb

Scan Offset (Rotary Knob)

Scan offset

dependent on the laser

Scan > Scan Output

Output to which the scan signal is added

<PC Voltage>

Feed Forward > Feed Forward Factor

Current ramp applied to the laser diode

- 1 mA/V
a. b.

Table 1

The numerical values are guidelines and depend on the individual setup. The scan amplitude can be enlarged or reduced to correspond to the application.

DLC pro scan control settings

Obtain the maximum scan range of the DLC pro in the following way:

5.
Set Scan Offset to 69.5 V.

6.
Set Scan Amplitude to 141 V. The scan control can now access the full output range (-1 .. +140 V).

7.
You can analyze all the relevant signals via the touchscreen. However, the Digital I/O Connector of the MC+ module provides a digital trigger output (TTL-compatible) that can be used for monitoring signals on an external oscilloscope (for details please refer to section 10.2.3).

Now, all the hardware is set up, and the laser system can be completely controlled by the DLC pro.

## 8.2 PDH Lock with Cavity

### 8.2.1 Utilizing the DLC pro Lock Option

This section describes the laser frequency stabilization to a cavity.

Figure 121 Experimental setup for Top of Fringe Lock with cavity, PDH module in the DLC pro and an

external PID controller to increase the bandwidth of the control loop, e.g. when the laser linewidth should be narrowed, or to increase the lock stability. NOTE !

If you want to use the Lock Points Tool for showing and selecting lockpoints, etc. (for details please refer to section 7.2.1), a DC-coupled photo diode 1 must be used, or photo diode 2 must be connected as shown in Figure 121.

To lock the laser frequency to an extremum of the cavity signal, a zero-crossing slope is generated using frequency modulation and demodulation. PDH (Pound-Drever-Hall) lock uses a modulation frequency larger than the characteristic resonance width to obtain the derivative of the absorption signal by demodulation.

1.
Press the Scan/Lock Mode button to switch to Scan/Lock mode. Tap the xy symbol at the top of the touchscreen to switch to xy display mode. Select Display Settings > Trace Selection > Input Trace Signal > Lock Input Signal.

Tap the Lockpoint symbol at the bottom of the touchscreen to choose the Lockpoint function mode.

2.
Select the input channel for the photo diode signal that is connected to the PDH module of the DLC pro (parameter menu, Lock Settings > Lock Input Signal > PDH In 1 in the example). From the Lock Input Signal, the PDH Error signal is generated, which is used as the input for all selected PID controllers.

3.
In the parameter menu, select Lock Settings > Lock Type > Top of Fringe PDH.

Figure 122 Lockpoint function mode: Lockpoint candidates for Top of Fringe PDH Lock type (example)

4.
Select both PID controllers for frequency stabilization (parameter menu, Lock Settings > PID Selection > PID 1+2).

5.
Zoom and drag the Lock Input signal and adjust the laser current (Set Current rotary knob) until the desired lockpoint in the spectrum is clearly visible on the display.

NOTE !

6.
If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by adjusting the P/N Tolerance at the bottom right rotary knob. This parameter is 0 for automatic detection, and automatic detection does not always work perfectly. The parameter should be set to a value that is larger than the peak-to-peak noise and smaller than the peaks that the laser should be locked to.

Switch to the PDH Ch 1 Lock function mode by selecting the PDH Ch 1 symbol. Select the PDH Error 1 signal to be displayed as the Auxiliary trace in blue (parameter menu, Display Settings > Trace Selection > PDH Error 1).

7.
Adjust the blue PDH Error 1 signal until it looks similar to the example shown in Figure 123. Use the rotary knobs and the parameter menu (PDH) to configure the PDH lock parameters. Parameter

Description

Reasonable setting

PDH Modulation Frequency

User-selected modulation/demodulation frequency.

25 [MHz]

PDH Modulation Amplitude

Amplitude of the PDH modulation.

Depending on experimental setup [dBm] (*)

PDH Demodulation Phase

Phase difference between modulation and demodulation.

0 … 360 [°] (to be adjusted, **)

* The PDH modulation amplitude is a tradeoff between the desired PDH Error 1 signal strength and
the power in the side bands. The larger the amplitude, the larger the PDH Error 1 signal. However, the side bands will be stronger.

** The PDH Error 1 signal resembles the derivative of the input signal (i.e., positive Error signal on
positive signal slope). The phase between the modulation and the reference signal must be adjusted to obtain a large error signal with steep slopes and zero crossings at the maxima of the spectral signal.

Figure 123 Display of the cavity spectrum (Lock Input Signal, red) with the corresponding

PDH Error 1 signal (blue). Note: The phase of the PDH Error 1 signal is chosen to resemble the derivative of the input signal. 7.1.

Choosing the correct sign for the PID 1/2 controllers in the DLC pro: Please refer to section 9.3.

7.2.

Choosing the correct sign for the external PID controller: Increase the P-contribution until the slope of the PDH Error 1 signal at the selected lockpoint gets significantly shallower/broader. If the slope gets steeper/narrower, the sign of the external PID controller must be inverted. Set the P-contribution to zero again.

8.
Determine the level of the PDH Error 1 signal at the selected lockpoint. Enter this value as Lock Level (top-right rotary knob).

9.
Switch to Lockpoint function mode. Locking with lockpoint candidates: Select the lockpoint by tapping on the Lockpoint Candidate (see Figure 132). For a clearer display, unwanted lockpoint candidates can be deselected in the context parameter menu (Lock Settings > Peak/Trough Lock Candidates). Locking without lockpoint candidates: Enable Lock Settings > Lock Without Lockpoint in the context parameter menu. Move the spectrum on the touchscreen in x-direction so that the desired region to trigger the lock is located in the center.

10.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. Locking without lockpoint candidates: The laser scans to the center of the spectrum (Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on.

11.
Select the PID 1 or PID 2 function mode by selecting the PID symbols. Adjust the PID Gain settings with the rotary knobs. Please refer to section 9.1 for information on PID controller configuration.

12.
To avoid destabilization of the laser by driving it very far from the lockpoint, especially during initial setup and optimization, you can limit the PID output relative to the initial offset (used when activating the lock) of the output channel (parameter menu, PID 1/PID 2 > Use Limit). Set the symmetric limit for the PID output (parameter menu, PID 1/PID 2 > Limit). Reasonable choices in the example are: Configured to feedback on the CC-500/CC-700 module: PID 1 > Limit: 1 mA Configured to feedback on the PC module: PID 2 > Limit: Depending on the environmental conditions affecting the experimental setup. Optimization of the external PID controller: Adjust the PID gain settings to further decrease the peak-to-peak amplitude of the PDH Error 1 signal. Please follow the instructions in section 9.1 correspondingly.

13.
We recommend to use the ReLock feature (see section 5.4.11) to improve the convenience of operation during optimization of the various control loops and to increase the long term robustness of the experimental setup.

To turn the lock off, press the Lock On/Off button or tap the corresponding symbol (see section 5.8). The PID controllers switch OFF, and the scan starts. NOTE !

When the lock is switched off, the output value of the PID controller(s) is set to 0.

8.2.2

Optimized for Fast Feedback with FALC pro utilizing the DLC pro Lock Option

As an application example, the wiring for a complete DLC pro laser system being locked to a cavity in a closed loop configuration is shown in Figure 124. Please refer to the FALC pro manual for a detailed description of the locking procedure.

Figure 124 Experimental setup for Top of Fringe Lock with cavity, PDH module in the DLC pro and an

external PID controller with integrated mixer (FALC pro with front panel including mixer)

### 8.2.3 Optimized for Fast Feedback with mFALC 110

Some experiments require an extended control bandwidth in order to achieve high suppression of noise components. The setup in Figure 125 shows a solution that uses the PDH module in the DLC pro as generator for high quality modulation and demodulation signals. The external PID controller with integrated mixer (mFALC 110 in a DLC ext rack) opens up the possibility to design a control loop with short signal paths and highest possible bandwidth. NOTE !

For using the setup shown in Figure 125, no DLC pro Lock option license is required.

Figure 125 Experimental setup for Top of Fringe Lock with cavity, PDH module in the DLC pro and an

external PID controller with integrated mixer (mFALC 110 in a DLC ext rack) Basic operation principle:

- The PDH module supplies the signal that is used to apply a frequency modulation to the laser.
- The demodulation signal from the PDH module and the photodiode signal are fed to the mixer
integrated in the mFALC 110 module in order to generate a PDH error signal.

- A high-speed control signal of the mFALC 110 module (Main output) is used to control the laser
current via the Mod DC input at the laser head.

- A low-speed control signal exits the DLC ext via the DA 2 output and is fed into the Fine 1 input of
the DLC pro to control the piezo voltage via the Analog Remote Control (ARC) mechanism.

## 8.3 Doppler-Free Saturation Spectroscopy

This section describes the laser frequency stabilization to an atomic transition by Doppler-free saturation spectroscopy of Rb after realizing the initial setup described in section 8.1. Figure 126 shows the experimental setup.

Figure 126 Experimental setup for Doppler-free saturation spectroscopy

Once the Doppler-free saturation spectroscopy setup is adjusted and the laser is tuned to the appropriate transition, the photo detector signal can be optimized by scanning the laser frequency across the desired resonance. NOTE !

1.
In this application example, application-specific settings are configured via the DLC pro touchscreen. For configuration via TOPAS DLC pro graphical user interface (PC-GUI), please refer to section 7.2.

To scan the laser frequency with the piezo, use the touchscreen of the DLC pro in Scan/Lock mode (refer to section 5.4). Switch to Scan function mode by pressing the Scan/Lock Mode button or by tapping the corresponding symbol and further by selecting the Scan function mode. Enable the scan by tapping the symbol at the top of the touchscreen (gray: scan disabled, red: scan enabled). In the parameter menu, select Scan > Scan Output > PC Voltage, Scan > Scan Shape > Triangle and set Scan > Scan Frequency to 10 Hz. Set Scan Amplitude in the order of 10 Volts. Depending on the laser diode, this corresponds to several GHz of frequency tuning.

2.
Adjust the spectroscopy signal by zooming and dragging the display graph on the touchscreen. The signal expected after the adjustment will look similar to the one shown in Figure 127.

Figure 127 Absorption signal of a Doppler-free Rb spectroscopy

Once the laser scans across the feature of the absorption line to which the laser should be locked, the following locking schemes can be implemented using the Scan/Lock mode of the DLC pro:

- Side of Fringe locking locks the laser to a slope of the absorption line (see section 8.3.1).
- Top of Fringe locking uses frequency modulation/demodulation to lock the laser to a maximum or
minimum of the absorption line (see section 8.3.2).

### 8.3.1 Side of Fringe Locking

To lock the laser to the slope of a Doppler-free absorption line, use the Scan/Lock mode of the DLC pro. NOTE !

General step-by-step procedures for Side of Fringe locking are provided in sections 5.4.9. and 7.2.2. Section 8.3.1 provides additional application-specific information for parameter configuration.

1.
Press the Scan/Lock Mode button to switch to Scan/Lock mode. Select the xy symbol at the top of the touchscreen to switch to xy display mode. Select Display Settings > Trace Selection > Input Trace Signal > Lock Input Signal. Select the Lockpoint symbol at the bottom of the touchscreen to choose the Lockpoint function mode.

2.
Select the input channel for the photo diode signal that is connected to the DLC pro (parameter menu, Lock Settings > Lock Input Signal > Fine In 1 in the example). The selected input channel is used as the input for all selected PID controllers.

3.
In the parameter menu, select Lock Settings > Lock Type > Side of Fringe.

Figure 128 Lockpoint function mode; lock voltage level and lockpoint candidates for Side of Fringe locking (example)

4.
Select both PID controller(s) for stabilizing to the lockpoint (parameter menu, Lock Settings > PID Selection > PID 1+2).

5.
Zoom and drag the Lock Input signal and adjust the laser current (Set Current rotary knob) until the desired lockpoint in the spectrum is clearly visible on the display.

NOTE !

The selected lock voltage level is displayed as a red line. Lockpoint candidates are displayed where the Lock Input signal crosses the lock voltage level line.

In our example, the 85Rb D2 transitions at 780 nm are used (Figure 129), and the desired lockpoint is shown.

Figure 129 Rb transitions at 780 nm. Lockpoint selected

6.
Configure the PID 1 controller to handle the high-frequency feedback by controlling the laser current via the modulation option in the laser head (parameter menu, PID 1 > Output Channel > CC). Configure the PID 2 controller to handle the large range, low-frequency feedback by controlling the piezo voltage (parameter menu, PID 2 > Output Channel > PC).

7.
To prevent the PID controllers from mutual interaction by accumulating offsets in opposite directions, an “I cut-off“ frequency can be defined for the PID 1 controller (parameter menu, PID 1 > Use I cut-off). The “I cut-off“ frequency defines the corner frequency below which the integral gain of the controller is limited. A reasonable choice is in the order of 100 Hz (parameter menu, PID 1 > I cut-off frequency).

8.
To avoid destabilization of the laser by driving it very far from the lockpoint, especially during initial setup and optimization, you can limit the PID output relative to the initial offset (used when activating the lock) of the output channel (parameter menu, PID 1/PID 2 > Use Limit). Set the symmetric limit for the PID output (parameter menu, PID 1/PID 2 > Limit). Reasonable choices in the example are: PID 1 > Limit: 1 mA PID 2 > Limit: 3 V

9.
Set the desired lock level voltage by turning the Lock Level rotary knob. Lockpoint candidates are displayed where the Lock Input signal crosses the lock voltage level line. Before enabling the lock for the first time, please set the Gain, P, I and D parameters of both PIDs to reasonable values. If unsure about reasonable parameters, start with PID 2 by setting PID 1 gain to zero. Optimize PID values for PID 2 as described in section 9.1, then add PID 1 by increasing its gain and PID values.

10.
Locking with lockpoint candidates: Select the lockpoint by tapping on the Lockpoint Candidate. For a clearer display, unwanted lockpoint candidates can be deselected in the context parameter menu (Lock Settings > Positive-Edge/Negative-Edge Lock Candidates). Locking without lockpoint candidates: Enable Lock Settings > Lock Without Lockpoint in the context parameter menu. Move the spectrum on the touchscreen in x-direction so that the desired region to trigger the lock is located in the center.

11.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. Locking without lockpoint candidates: The laser scans to the center of the spectrum (Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on.

Figure 130 Side of Fringe lock display after the lock is engaged

12.
Set the values of the gain parameters for the PID controllers with the rotary knobs (see section 5.4.7.4). Their settings depend on the slope of the Error signal and the actuator response. In most cases, the low-frequency feedback of PID 2 is sufficient to achieve a first lock. We advise starting with conservative (small) gain settings. To find the correct settings for the sign of each PID controller, please refer to section 9.3. Once locking is accomplished, the PID gain parameters can be optimized (see section 9.1).

To turn the lock off, press the Lock On/Off button or tap the corresponding symbol (see section 5.8). The PID controllers switch OFF, and the scan starts. NOTE !

When the lock is switched off, the output value of the PID controller(s) is set to 0.

General Hints on Parameter Optimization: To obtain a “good“ lock, it is necessary to optimize the gain settings of the PID controllers to values which do not lead to oscillations of the error signal (see section 9.1 for details). As PID 2 is only responsible for the low-frequency components, this controller can be left at moderate gains. The performance of the lock is predominantly determined by the settings of PID 1 that is connected to the fast actuator. To improve the lock performance, increase the gain of the I, P, and D parts of the PID in an iterative manner, to values well below the point at which the control loop starts to oscillate. The general strategy for optimizing the P, I and D parameters is described in section 9.1. A helpful tool for the optimization process is the Frequency display mode (see Figure 131 and section 5.4.2). Figure 131 shows the result of the Fourier transformation of the sampled time signal. In our example, select Lock Settings > Lock Input signal > Fine In 1. Chose the frequency scale according to the bandwidths of the experiment. Typical bandwidths of the gratings are in the range of a few kHz while the CC500/CC-700 output has a bandwidth of up to 30 kHz. In most cases, the DC component of the frequency signal is quite dominant. In order to better resolve the peaks in the frequency spectrum, set the display trace scaling to appropriate amplitude values.

Figure 131 Frequency display of a photo diode signal.

In this example, the frequency analysis clearly shows the onset of an oscillation at about 20 kHz due to high gain settings.

### 8.3.2 Top of Fringe Locking (Lock-In)

To lock the laser frequency to an extremum of the Doppler-free absorption signal, a zero-crossing slope is generated using frequency modulation and demodulation. Lock-In uses a modulation frequency smaller than the characteristic resonance width to obtain the derivative of the absorption signal by demodulation. NOTE !

The general step-by-step procedures for Top of Fringe locking are provided in sections 5.4.10. and 7.2.3. This section provides additional application-specific information for the parameter configuration. Only Top of Fringe (Lock-In): The Lock Wizard in the TOPAS DLC pro PC-GUI (Laser Menu > Optimization Tools > Lock Wizard, see section 6.8) is an interactive tool which helps to setup a Top of Fringe lock.

NOTE !

It is possible to route the Lock-In Error signal to the Out A/B BNC connectors on the DLC pro front panel. Please refer to section 7.2.3 for details. By routing the Lock-In Error signal to analog outputs, the signal resolution may be reduced. Please use the parameters io:out-a:external-input:factor or io:out-b:external-input:factor, respectively, in order to increase signal-to-noise.

1.
Press the Scan/Lock Mode button to switch to Scan/Lock mode. Tap the xy symbol at the top of the touchscreen to switch to xy display mode. Select Display Settings > Trace Selection > Input Trace Signal > Lock Input Signal. Tap the Lockpoint symbol at the bottom of the touchscreen to choose the Lockpoint function mode.

2.
Select the input channel for the photo diode signal that is connected to the DLC pro (parameter menu, Lock Settings > Lock Input Signal > Fine In 1 in the example). From the Lock Input Signal, the Lock-In Output signal (error signal) is generated, which is used as the input for all selected PID controllers.

3.
In the parameter menu, select Lock Settings > Lock Type > Top of Fringe.

Figure 132 Lockpoint function mode: Lockpoint candidates for Top of Fringe Lock type (example)

4.
Select both PID controllers for frequency stabilization (parameter menu, Lock Settings > PID Selection > PID 1+2).

5.
Zoom and drag the Lock Input signal and adjust the laser current (Set Current rotary knob) until the desired lockpoint in the spectrum is clearly visible on the display.

NOTE !

If the lockpoints at the extrema are not properly detected automatically, this behavior can be improved by adjusting the P/N Tolerance at the bottom right rotary knob. This parameter is 0 for automatic detection, and automatic detection does not always work perfectly. The parameter should be set to a value that is larger than the peak-to-peak noise and smaller than the peaks that the laser should be locked to.

6.
Switch to the LIR Lock function mode by selecting the LIR symbol. Select the Lock-In Output signal (Error signal) to be displayed as the Auxiliary trace in blue (parameter menu, Display Settings > Trace Selection > Lock-In Output).

7.
Adjust the blue Lock-In Output signal until the Error signal matches the derivative of the red Lock Input signal. Use the rotary knobs and the parameter menu (Lock-In) to configure the Lock-In parameters. Parameter

Description

Reasonable setting

Lock-In Modulation Frequency

User-selected modulation/demodulation frequency, depending on the output channel.

CC output channel: 20000 [Hz]

Lock-In Modulation Amplitude

Amplitude of the Lock-In modulation.

0.05 [mApp] (*)

Lock-In Demodulation Phase

Phase difference between modulation and demodulation.

0 … 360 [°] (to be adjusted, **)

Output Channel

Output to which the modulation is added.

CC: laser diode current

* The Lock-In modulation amplitude is a tradeoff between the desired lock-in signal strength and
the allowed frequency modulation of the laser. The larger the amplitude, the larger the lock-in signal. However, the linewidth of the laser increases at the same time.

** The Lock-In Out signal is the derivative of the input signal (i.e., positive Error signal on positive signal slope). The phase between the modulation and the reference signal must be adjusted to
obtain a large error signal with steep slopes and zero crossings at the maxima of the spectral signal.

Figure 133 Display of the Doppler-free Rb spectrum (red) with the corresponding

Lock-In Output signal (blue). Note: The phase of the Lock-In Output signal is chosen to be the derivative of the absorption signal.

8.
Switch to Lockpoint function mode. Locking with lockpoint candidates: Select the lockpoint by tapping on the Lockpoint Candidate (see Figure 132). For a clearer display, unwanted lockpoint candidates can be deselected in the context parameter menu (Lock Settings > Peak/Trough Lock Candidates). Locking without lockpoint candidates: Enable Lock Settings > Lock Without Lockpoint in the context parameter menu. Move the spectrum on the touchscreen in x-direction so that the desired region to trigger the lock is located in the center.

9.
Press the Lock On/Off button or tap the corresponding symbol (see section 5.8). Locking with lockpoint candidates: The laser scans to the selected lockpoint. When the scan reaches the lockpoint, the scan stops, and the PID controller(s) switch on. Locking without lockpoint candidates: The laser scans to the center of the spectrum (Offset). When the scan reaches this point, the scan stops, and the PID controller(s) switch on.

10.
Select the PID 1 or PID 2 function mode by selecting the PID symbols. Adjust the PID Gain settings with the rotary knobs. Please refer to section 9.1 for information on PID controller configuration.

NOTE !

11.
The laser is actually locked to the Lock-In Output signal. The Lock-In Output signal is the input signal for the PID controller(s).

To avoid destabilization of the laser by driving it very far from the lockpoint, especially during initial setup and optimization, you can limit the PID output relative to the initial offset (used when activating the lock) of the output channel (parameter menu, PID 1/PID 2 > Use Limit). Set the symmetric limit for the PID output (parameter menu, PID 1/PID 2 > Limit). Reasonable choices in the example are: Configured to feedback on the CC-500/CC-700 module: PID 1 > Limit: 1 mA Configured to feedback on the PC module: PID 2 > Limit: 3 V

To turn the lock off, press the Lock On/Off button or tap the corresponding symbol (see section 5.8). The PID controllers switch OFF, and the scan starts. NOTE !

When the lock is switched off, the output value of the PID controller(s) is set to 0.

### 8.3.3 Top of Fringe Locking (PDH)

To lock the laser frequency to an extremum of the Doppler-free absorption signal, a zero-crossing slope is generated using frequency modulation and demodulation. A FM spectroscopy lock with the PDH module uses a modulation frequency larger than the characteristic resonance width to obtain the derivative of the absorption signal by demodulation.

Figure 134 Experimental setup for Doppler-free saturation spectroscopy using the PDH module

If your DLC pro is equipped with a PDH module (see section 10.2.11), you can also use the PDH Ch1/ PDH Ch2 function modes for Top of Fringe locking, instead of the LIR function mode described in section 8.3.2. In this case connect your experimental setup as shown in Figure 134 and follow the relevant instructions in section 8.2 accordingly.

# 9 Notes on Feedback Control Loops with DLC pro

NOTE !

To utilize the DLC pro Lock function modes, a Lock option license is required. When a Lock option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. The license key must be activated via the TOPAS DLC pro PC-GUI (please refer to section 11.20). If purchased along with the DLC pro, the licence is already installed. Otherwise a 30-day trail licence is provided on the USB flash drive in the Options Folder.

## 9.1 Controller Parameter Adjustment and Optimization

To obtain a good lock, it is necessary to optimize the gain settings of the PID controllers. Once a suitable Lock-In Output signal (Error signal) is at hand, the feedback loop (see Figure 135) can be closed and optimized. The general working principle of the Proportional-Integral-Differential (PID) controller is to minimize the deviation of a physical measure (Process Variable) from a selected Set Value by modifying the actuator drive (Manipulated Variable) accordingly. The output of the controller is a weighted sum of the integral (I), proportional (P), and differential (D) paths scaled by the overall gain. The digital PIDs in the DLC pro allow for a precise and reproducible control of the gain settings.

Figure 135 PID controller feedback loop

The three contributions differ in their frequency dependence:

1.
The integral (I) part is given by the time integral of the Error signal. Therefore, its gain increases to lower frequencies, and it is responsible for the compensation of (dc) offset changes. The residual deviation of the error signal from zero, or respectively the difference between the physical measure and the set value (see (P) part) is also eliminated. The integral (I) part is also one of the parameters used to optimize the lock dynamics, i.e. the response to perturbances at different frequencies.

2.
The proportional (P) part has a flat frequency response and is limited by the bandwidth of the control loop. A larger proportional gain (P) reduces the deviation from the set value and is limited by the onset of oscillations. The residual error which would remain with (P) operation only, can be compensated by setting the integral (I) part of the PID controller.

3.
The differential (D) part reacts to sudden changes in order to reduce deviations (e.g., an over shoot in the transient response). Its frequency response increases with frequency and is limited to higher frequencies by the bandwidth of the control loop. Since it provides a phase lead, the differential (D) part can help to improve the phase response at higher frequencies, which in turn allows to increase the gain on the I and P parts before inducing oscillations. Note, that due to the highbandwidth transient response, the differential part is also particularly prone to amplification of noise.

Before adjusting the parameters of the PID controllers, select the correct phase and polarity of the PID controller with respect to the scan output. Positive polarity means that an increased PID controller output results in an increase of the Lock Input signal (bottom-left rotary knob with Scan/Lock screen and PID1/ PID2 function mode selected, Scan/Lock mode parameter menu, PID 1/PID 2 > Sign Positive, or PC-GUI Scan & Lock tab, PID 1/PID 2 groups). To start, select a low input gain and set all contributions (P, I, D) to zero. Now, increase the integral part until the system locks1. Generally speaking, the quality of the lock will now improve with increasing gain of the controller until the feedback loop starts to oscillate. This is the case when the feedback loop reaches a gain of 1 at a 180° phase shift. Therefore, the usable bandwidth of many actuators (e.g., piezos) is limited by their characteristic frequencies. In any case, phase shifts due to finite bandwidths and signal propagation times in the control loop lead to phase lags which increase with frequency. The appearance of oscillations can be observed in the display of the Error signal. The frequency analysis (Frequency display mode) may be better suited because it is often more sensitive and directly shows the resonance peak. It is usually helpful to drive the system into oscillation and note the characteristic frequencies for reference. A simple parameter adjustment is obtained by an iterative process:

1.
Set the integral (I) gain to a non-zero value (all others to zero) and increase the overall gain until the system locks.

2.
Alternate between increasing the proportional (P) gain and the integral (I) gain each until the feedback loop starts to oscillate, then reduce the gains until the oscillation definitely stops. Standard optimization procedures set the proportional (P) gain to about 0.6 of the value where oscillations start.

3.
Increase the integral (I) gain until the feedback loop starts to oscillate, then increase the differential (D) gain until the oscillation stops. Proceed iteratively Increasing both gains until the oscillation cannot be stopped by further increase of the differential (D) gain. At that point, reduce both gains until the oscillation definitely stops.2

NOTE !

1.
2.
The optimized parameters depend on the slope of the error signal at the current lockpoint and the actuator response. Therefore, there is usually a trade-off between a good locking result and a reasonable robustness against external disturbance. Higher gains will lead to the smallest error signal and narrow linewidth. However, the system can react too strongly when larger disturbances occur, and, due to the reaction, fall out of the lock. Lower gain settings relax the feedback control loop and can ensure longer locking times.

If the system does not lock, check the polarity by trying the opposite Sign Positive polarity setting. Alternatively, there are several methods for estimating PID controller parameters which mostly originate from slow (temperature type) controller applications. The Ziegler–Nichols method gives rule of thumb values derived from the proportional gain P, osc where an oscillation of frequency νosc starts: P = 0.6 x P,osc ; I = 2 P,osc / ν osc; D = (P,osc x νosc)/ 8

## 9.2 Signal Limitations in Analyzing the Locking Performance

NOTE !

To analyze the performance of a lock based on a frequency modulation technique, we recommend using the demodulated signal (Lock-In Out) to observe residual excursions in the display as well as using the frequency analysis tools (Frequency display mode).

As common to any digital signal sampling, the DLC pro shows effects of aliasing. When the sampled signals have frequency components faster than half the sampling rate, they will be folded into the frequency band from zero to this Nyquist frequency. The sampling rate of the DLC pro is automatically set to make full use of the number of acquired points. Therefore, in the Scan/Lock mode display, the sampling rate is given by the number of points per trace (1024) divided by the time range chosen. According to the Nyquist theorem, the sampling rate in the frequency analysis (FFT) is set to twice the selected maximum frequency. Because of aliasing effects, the X/Y, time, and frequency display of DLC pro can show signals that are actually at other frequencies. This effect is well known from digital oscilloscopes. In general, signals appear at the difference frequency between their original frequency and the sampling frequency (or its harmonics). In the X/Y and Time display mode, this can appear as fast oscillations or noise, but also as slow variations or "breathing" of signal amplitudes if the frequency difference is small. In case of the DLC pro, there is an additional effect to be observed for sampling rates well below the Nyquist frequency. Due to the complete synchrony of the sampling with the applied modulation, the undersampled signal can show up as a (noisy) line at a finite offset that varies from shot to shot. Note that this is not an indication of the performance of the lock, but merely an artifact of the input signal sampling including the applied modulation. This explains why we recommend using the demodulated signal for analysis.

## 9.3 Identification of Signal Polarity and Slope

To support the lock features, the DLC pro takes a consistent approach to the definition of the signal polarity of each PID controller. The polarity of a PID controller is used to match the action of the corresponding output to the direction of the scan. Select the polarity in such a way that an increased controller output acts in the same direction as an increase of the SC scan output. If the output of the PID controller is identical to the SC scan output, the polarity is positive. Otherwise, the polarity has to be determined for the particular actuator used. For example, if the laser is scanned via the PC module and PC is selected as the output channel of PID 2, the PID 2 polarity is trivially positive. In general, the polarity of the controller output for any actuator can be determined by comparing the signals of the regular SC scan output with the signal observed while scanning the PID controller output. To determine the directionality of the resulting effect, look at a characteristic part of the error signal (e.g., close to the lockpoint), or use a wavelength meter reading, if available. A general method to verify the correct polarity is to compare the signals during the scan with the PID controller switched on and off while using just the proportional part. To do so:

- Select the appropriate PID controller (PID 1 or PID 2; not PID 1+2) in the Scan/Lock mode parameter menu (Lock Settings > PID Selection)
- Select the xy display mode.
- Select the Lock function mode/Side of Fringe and enable the Lockpoint display (Scan/Lock mode
parameter menu, Lock Settings > Lock Type).

- Set the lockpoint candidate to a rising signal slope. If Lock Without Lockpoint is enabled, a rising
signal slope is chosen as default.

- Select the xy display mode and adjust the Time Base according to the Scan Frequency (Time Base
[s] = 1/ 2 * Scan Frequency [Hz]) (Display Settings > Time).

- Set the integrator and differentiator parts of the PID controller to zero.
- Set the proportional part and the overall gain of the PID controller to some non-zero value such as
10. (PID 1 or PID 2 Lock Function mode, rotary knobs).
- Enable the PID controller (Scan/Lock mode parameter menu, Enable PID in the respective PID
controller settings) while scanning across the region of interest in the spectrum.

- Increase the proportional part and/or overall gain of the PID controller until you see a significant
distortion of the signal.

- Disable the PID controller.
To check the observed effect, you can compare with the cases of the other polarity as well as with the PID controller being switched off. The cases of Side of Fringe locking and locking to a Lamb dip of a saturated absorption signal are illustrated in Figure 136 and Figure 137.

Figure 136 Polarity of the PID controller for Side of Fringe lock.

The graph shows the characteristic distortions of the error signal of a Side of Fringe lock for different polarities. The displayed example is a zoom into the saturated absorption spectrum of Rb. The undistorted signal (solid black) is given for reference. When the correct polarity is selected, the rising slopes are shallower/broader than the unlocked slope. Rising slopes that are steeper/narrower than the unlocked slope indicate an incorrect polarity.

Figure 137 Polarity of the PID controller using frequency modulation

The graph shows the characteristic distortions of the error signal as well as the saturated absorption signal of a Top of Fringe lock for different polarities. The undistorted signal (solid black) is given for reference. For the correct polarity (dashed red), the slope of the error signal at the peak is shallower while the peak itself is broader (see boxed part of the graph). In contrast, the slope is steeper and the peak narrower for the incorrect polarity (dotted green). If the polarity is correct (incorrect), a resonance should become wider (narrower) as compared to the case of the controller being inactive. The slope of the error signal, e.g. in frequency modulation, should become flatter (steeper) when the polarity is correct (incorrect).

# 10 DLC pro Hardware Description

## 10.1 DLC pro Front Panel

The DLC pro front panel allows direct and quick control by the user and provides access to most of the available functionality. The main control element is the projected capacitive touchscreen (PCT) with 17.8 cm (7") diagonal size and 800 x 480 pixels. Eight push buttons are located left and right of the touchscreen. Some operator controls are designed to be context-sensitive, so their function is determined by the firmware and accordingly displayed on the touchscreen. The push buttons are mainly used for navigation and to select frequently-used functions or functions that need to be performed "blindly" (e.g., while looking at the experiment). Rotary knobs are located at each corner of the touchscreen. They are used (context-sensitive) for adjusting operating parameters, such as laser diode current, operating temperature, piezo voltage for wavelength tuning and many more. For a detailed description of the front panel operator controls, please refer to section 4.

### 10.1.1 I/O Board

The I/O board is part of the front panel and provides four analog inputs and two analog outputs that are accessible as BNC-connectors at the DLC pro front panel. The board comprises analog input/output amplifiers and A/D D/A converters for each input and output as well as an FPGA unit and a reference power supply unit. Input signals applied to the fine BNC-connectors are directed to a precise 24-bit A/D converter whereas input signals which are applied to the fast BNC-connectors are directed to a 16-bit A/D converters for fast signal processing. Output signals are generated by a dual 16-bit D/A converter. All control commands for the A/D D/A converters and the communication with the MC board in the MC+ module are implemented in the FPGA unit.

Figure 138 I/O Board schematic overview

## 10.2 Modules on the DLC pro Rear Panel

NOTE !

Please note that for every type of module the mounting position must be chosen correctly. Please refer to section 11.6 for information.

### 10.2.1 PS+ Module

Figure 139 Panel of the PS+ module

1

ON/OFF Switch

3

Mains Connector

2

Fuse Cartridge

4

Output Connector

NOTE !

5

Ground Pin

Item 4 is not present at PS modules.

1

ON/OFF Switch

Switch for mains supply ON/OFF. NOTE !

2

Fuse Cartridge

After switching off, please wait for at least 10 seconds before switching the DLC pro on again.

DANGER ! Before exchanging a fuse, make sure to switch off and disconnect the device from the mains supply ! The mains supply is protected by a 250 V~, 4 A T (slow blow) fuse 5 x 20 mm, which are accessible after removing the fuse cartridge. For exchanging the fuse please refer to section 11.8.1.

3

Mains Connector

Connector for the supplied mains cable.

4

Output Connector

- LEMO 2B.304 connector
Power output connector for supply of TOPTICA laser heads. Not intended for general use. For pin assignment and power values, please refer to section 11.10.6. NOTE !

5

Ground Pin

The Output Connector is not present at PS modules.

Pin for installation of a ground connection to external devices.

### 10.2.2 PS HP Module

Figure 140 Panel of the PS HP module

1

External Power Adaptor Connector

3

ON/OFF Switch

2

Output Connector

4

Ground Pin

1

External Power Adaptor Connector

Input connector for power supply by the delivered external power adaptor.

2

Output Connector

- LEMO 2B.304 connector
Power output connector for supply of TOPTICA laser heads. Not intended for general use. For pin assignment and power values, please refer to section 11.10.6. NOTE !

The Output Connector is not present at PS modules.

3

ON/OFF Switch

Switching off the PS HP at the ON/OFF switch, only sets the power supply to standby. Disconnect the mains cable to the external power adaptor to completely shut down the DLC pro. NOTE ! After switching off, please wait for at least 10 seconds before switching the DLC pro on again.

5

Ground Pin

Pin for installation of a ground connection to external devices.

Please refer to Figure 141 for connecting a DLC pro with PS HP module to mains via the supplied external power adaptor and mains cable. DANGER ! Before connecting/disconnecting the mains cable or the power adaptor connector, CAUTION ! always switch off the DLC pro at the ON/OFF switch of the PS HP module.

Figure 141 Mains connection of DLC pro with PS HP module. The external power adaptor is delivered by

TOPTICA.

### 10.2.3 MC+ Module

The MC+ module is the control center of the DLC pro. It comprises a module with an ARM microcontroller and an FPGA unit for various control purposes and communication with other plug-in modules. Several peripheral connectors as well as digital inputs and outputs are also available. All other plug-in modules and the touchscreen on the DLC pro front panel are connected to the MC+ module via the backplane. The MC+ module offers various interfaces (USB, two Ethernet connectors, an RS232 interface, and an LVDS socket). The LVDS connector is used for digital high-speed communication, e.g., with a CTL laser head. All other plug-in modules and the touchscreen on the DLC pro front panel are connected to the MC+ module via the backplane.

Figure 142 Block diagram of the MC+ module

Figure 143 Panel of the MC+ module

1

Status LED A

5

External Interlock Connector

8

LVDS Connector

2

Status LED B

6

Digital I/O Connector

9

RS 232/CAN Connector

3

Audio Out

7

Ethernet 1 Connector

10 Ethernet 2 Connector

4

USB Connector

NOTE !

Items 8, 9, and 10 are not present at MC modules.

1

Status LED A

Dark Orange: Off:

2

Status LED B

Please see description of Status LED A for information.

3

Audio Out

- 3.5 mm Audio
Stereo Jack

not yet implemented.

Not initialized. Ready

4

USB Connector

Micro USB 2.0 connector (host/slave, USB on-the-go) can be used for remote control of the DLC pro by a computer. When connected to a computer, the DLC pro appears as a USB-connected serial interface. For details on setting up the USB connection, please refer to section 11.21. NOTE !

A micro USB 2.0 cable with connector type B must be used. We recommend operating the DLC pro via Ethernet over using a USB connection due to the higher communication bandwidth. Using a USB to Ethernet adapter on the PC side allows fast communication while having a point-to-point connection between PC and DLC pro – without connecting the DLC pro to the local network or disconnecting the PC from it.

5

External Interlock Connector

- Phoenix
MC 0.5/2-G-2.5 connector

Connector for installation of an external interlock circuit to switch off the laser (e.g., using a door switch). The type of the interlock plug is Phoenix FK-MC 0.5/2-ST-2.5. The interlock plug supplied with the DLC pro should only be used for first adjustment purposes. For details on the external interlock circuit, please refer to section 2.3.1.

6

Digital I/O Connector

- D-Sub 15 HD male
connector

Connector for multi-purpose digital inputs and outputs. A breakout cable (article number K DLC/Digital I/O) is available from TOPTICA for convenient access to all 8 digital lines. Digital Input 0

1 (high)Lock function for laser 1 is on hold (pause). 0 (low) Lock function for laser 1 is continued.

Only Dual-Laser-Operation: Digital Input 1 1 (high)Lock function for laser 2 is on hold (pause). 0 (low) Lock function for laser 2 is continued. Digital Input 2 or 3 Input trigger for initiating a wide scan. Only Quad-Laser-Operation: NOTE ! The Digital Inputs 2 and 3 are linked to both, the lock hold function and the wide scan input trigger. If that is not desired, the lock hold function can be deactivated via the parameter laserX:dl:lock:di-hold-enabled (parameter menu of the touchscreen (please refer to section 5.14) or Parameters window of the TOPAS DLC pro PC-GUI (please refer to section 6.9). Digital Input 1

1 (high)Lock function for laser 2 is on hold (pause). 0 (low) Lock function for laser 2 is continued.

Digital Input 2

1 (high)Lock function for laser 3 is on hold (pause). 0 (low) Lock function for laser 3 is continued. Input trigger for initiating a wide scan.

Digital Input 3

1 (high)Lock function for laser 4 is on hold (pause). 0 (low) Lock function for laser 4 is continued. Input trigger for initiating a wide scan.

Specifications Digital Inputs: Input resistance 10 kΩ TTL level high > 2.0 V TTL level low < 0.8 V

6

Digital I/O Connector

- D-Sub 15 HD male
connector

Each of the four Digital Outputs 0 .. 3 can be linked to one desired laser 1 .. 4 and be operated in different modes. The linked laser and the modes can be selected in the IO window (see section 6.9).

(continued)

Specifications Digital Outputs: high: min. 4 V at 10 kΩ load low: max. 0.4 V at 10 kΩ load For pin assignment of the D-Sub 15 HD connector, please refer to section 11.10.4.

7

Ethernet 1 Connector

Ethernet connector for remote control of the DLC pro via TCP/IP.

8

LVDS Connector

Connector for high-speed digital communication with supported TOPTICA laser heads. CAUTION ! Connection to other devices may damage the DLC pro laser driver electronics. NOTE !

9

RS 232/CAN Connector

- D-Sub 9
connector

10 Ethernet 2 Connector

Digital communication connection. NOTE !

The RS232/CAN Connector is not present at MC modules.

Ethernet connector RJ45. DLC DL-/TA-SHG/FHG pro: Connection between DLC pro and DL-/TASHG/FHG pro laser head. NOTE !

The LVDS Connector is not present at MC modules.

The Ethernet 2 Connector is not present at MC modules.

### 10.2.4 CC-500/CC-700 Module

The CC-500/CC-700 module is a digitally controllable, low-noise current source for diode lasers. Its most important features are:

- CC-500: Two available channels (245 mA each) that can be combined to one channel (490 mA).
- CC-700: Two available channels (350 mA each) that can be combined to one channel (700 mA).
- Support for laser diodes with either positive or negative polarity.
Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC-500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

- Monitoring of the voltage applied to the laser diode.
- High current/voltage or loose connection detection to prevent damage to the laser diode.
- Two available differential analog SMB inputs on each CC-500/CC-700.
- Power supply for the laser head modulation circuit.
- Built-in temperature sensors for overheat detection.
The CC-500/CC-700 shows superior short-term and temperature stability of the laser diode current and fits into an M-Slot of the DLC pro.

Figure 144 Block diagram of the CC-500 module (similar for CC-700)

Figure 145 Panel of the CC-500 module (similar for CC-700)

1

Status LED Channel 1

4

Channel 1 Current Connector

2

Status LED Channel 2

5

Channel 2 Current Connector

3

Channel 1 ain (Analog Input)

6

Channel 2 ain (Analog Input)

NOTE !

Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

1

Status LED Channel 1

Red: Green: Green flashing:

2

Status LED Channel 2

Please see description of Status LED 1 for information.

3

Channel 1 ain

- SMB connector
Multi-purpose measurement input, - 4 V .. + 4 V, input resistance 1 MΩ.

4

Channel 1 Current Connector

- D-Sub 9 connector
Connector for channel 1 current. For pin assignment of the D-Sub 9 connector, please refer to section 11.10.1. NOTE !

5

Channel 2 Current Connector

- D-Sub 9 connector
Channel 2 ain

- SMB connector
When the CC-500/CC-700 is set to a current output of 1 x 490 mA, resp. 1 x 700 mA (see section 10.2.4.1), only Channel 1 is active.

Connector for channel 2 current. For pin assignment of the D-Sub 9 connector, please refer to section 11.10.1. NOTE !

6

Error: LD overcurrent, LD overvoltage, Power not OK. Output active. Disabled, waiting.

Channel 2 is deactivated when the CC-500/CC-700 is set to a current output of 1 x 490 mA, resp. 1 x 700 mA (see section 10.2.4.1).

Multi-purpose measurement input, - 4 V .. + 4 V, input resistance 1 MΩ. DLC TA pro/-AL: Used for monitoring the seed power (please refer to the TA pro or TA pro AL laser head manual).

10.2.4.1

Changing the CC-500/CC-700 Current Output (Service Operation)

DANGER ! The CC-500/CC-700 module must be removed from the DLC pro for changing between the current output options. Switch off the DLC pro, disconnect it from the mains supply, and follow the instructions noted in section 11.5 to remove and install the plug-in module.

Figure 146 Switch on the CC-500/CC-700 pcb to change the current output

The current output of the CC-500/CC-700 module is set by a switch on the pcb. Switch ON CC-500: Max. Current Output 1 x 490 mA on Channel 1 (Factory Setting) CC-700: Max. Current Output 1 x 700 mA on Channel 1 (Factory Setting) Switch OFF CC-500: Max. Current Output 2 x 245 mA on Channel 1 and 2 (Factory Setting for customer specific DLC MDL pro configurations) CC-700: Max. Current Output 2 x 350 mA on Channel 1 and 2 (Factory Setting for customer specific DLC MDL pro configurations)

### 10.2.5 CC-500 SMC Module

NOTE !

In this manual, generally the term CC-500 is used for both, the CC-500 and the CC500 SMC modules. CC-500 SMC specific information is added where required.

The CC-500 SMC module is a digitally controllable, low-noise current source for diode lasers, which additional control electronics and connectors for the single mode control (SMC). For detailed description of the single mode control, please refer to the SMC manual. The basic features and interfaces of the CC-500 SMC module are described in section 10.2.4. Single mode control related details are described in this section.

Figure 147 Panel of the CC-500 SMC module

1

Channel 1 SAFE

2

Channel 2 SAFE

1

Channel 1 SAFE

- Mini D-Sub 15-connector
Connector for signal transfer and supply to the SMC detection unit in the laser head. NOTE !

2

Channel 2 SAFE

- Mini D-Sub 15-connector
Connector for signal transfer and supply to the SMC detection unit in the laser head. NOTE !

Channel 1 SAFE must be connected to the SAFE connector of the laser head which is connected to the Channel 1 Current connector of the same CC-500 SMC module.

Channel 2 SAFE must be connected to the SAFE connector of the laser head which is connected to the Channel 2 Current connector of the same CC-500 SMC module.

### 10.2.6 CC-5000 Module

The CC-5000 module is a digitally controllable, low-noise current source for high-power diode lasers and amplifiers. Its most important features are:

- 
- 
- 
- 
- 
- 
Support for negative laser diodes (anode grounded). Monitoring of the voltage applied to the laser diode. High current/voltage or loose connection detection to prevent damage to the laser diode. Differential analog SMB input. Power supply for the laser head modulation circuit. Built-in temperature sensors for overheat detection.

Modulation and stabilization sources within DLC pro can be directed to the CC-5000 module - with little limitations:

- Above a Set Current of 500 mA, current modulation can be applied with slew rates up to
500 Ampere per second. Limitations are a -3 dB bandwidth of 70 Hz and a constant delay of 2 ms.

- Below a Set Current of 500 mA, current slew rates of more than 50 Ampere per second will cause a
distorted waveform. The CC-5000 shows low noise properties and allows high stability of the laser diode or amplifier current. It fits into an S-Slot of the DLC pro. CAUTION ! Do not interchange the CC-5000 and the TC Module as this leads to malfunction. Observe the mounting instructions noted in section 11.6. NOTE !

In Dual-Laser configurations, limitations of tapered amplifier currents may occur when using a CC-HP module together with a CC-5000 or a second CC-HP module and at least one current setting > 5000 mA. In this case, both lasers can be operated at their maximum rating separately. Firmware could limit one or both tapered amplifier currents in case of simultaneous operation, depending on the DLC pro configuration.

Figure 148 Block diagram of the CC-5000 module

Figure 149 Panel of the CC-5000 module

1

Status LED A

3

Current Connector

2

Status LED B

4

Ain (Analog Input)

1

Status LED A

Red: Green: Green flashing:

2

Status LED B

Not active.

3

Current Connector

- D-Sub 15 connector
Connector for output current. For pin assignment of the D-Sub 15 connector, please refer to section 11.10.2.

4

Ain

- SMB connector
Multi-purpose measurement input, - 4 V .. + 4 V, input resistance 1 MΩ. DLC TA pro/-AL: Used for monitoring the amplified output power (please refer to the TA pro or TA pro AL laser head manual).

Error: LD overcurrent, LD overvoltage, Power not OK. Output active. Disabled, waiting.

10.2.6.1

Combination of two CC-5000 Modules for up to 10 A

Two CC-5000 modules can be combined to deliver currents up to 10 A. In this case, the two modules are connected internally, one of the current connectors is sealed and the accessible current connector of is used to supply the combined current. NOTE !

If the DLC pro is using the PS or PS+ module, the maximum current is limited to 7 A by the power supply module as well as the heat generated within the DLC pro. If the DLC pro is powered with a PS HP module up to 10 A are possible. Please refer to the laser head manuals for the required cooling.

NOTE !

For installation of a combination of two CC-5000 modules, please refer to section 11.5.2.

The most important features are:

- 
- 
- 
- 
- 
- 
Support for negative laser diodes (anode grounded). Monitoring of the voltage applied to the laser diode. High current/voltage or loose connection detection to prevent damage to the laser diode. Differential analog SMB input. Power supply for the laser head modulation circuit. Built-in temperature sensors for overheat detection.

The combination of two CC-5000 modules shows low noise properties and allows high stability of the laser diode current and is available factory installed together with Article SUR TA / HP. If you wish your DLC pro laser driver electronics to be upgraded (Article UPGR TA / HP), please contact TOPTICA Photonics SE.

Figure 150 Block diagram of the combination of two CC-5000 modules

Figure 151 Panel of the combination of two CC-5000 modules

1

Status LED A (left CC-5000)

4

Ain (Analog Input left CC-5000)

2

Status LED B (left CC-5000)

5

Status LED B (right CC-5000)

3

Current Connector

6

Status LED A (right CC-5000)

7

Ain (Analog Input right CC-5000)

CAUTION ! The DLC pro software is designed to support the Current Connector (3). Do not use the covered connector and the ain SMB connector of the right CC-5000 !

1

Status LED A (left CC-5000)

Red: Green: Green flashing:

Error: LD overcurrent, LD overvoltage, Power not OK. Output active. Disabled, waiting.

2

Status LED B (left CC-5000)

Not active.

3

Current Connector

- D-Sub 15 connector
Connector for current connection. For pin assignment of the D-Sub 15 connector, please refer to section 11.10.2.

4

Ain (left CC-5000)

- SMB connector
Multi-purpose measurement input, - 4 V .. + 4 V, input resistance 1 MΩ. DLC TA pro/-AL: Used for monitoring the amplified output power (please refer to the TA pro or TA pro AL laser head manual).

5

Status LED B (right CC-5000)

Not active.

6

Status LED A (right CC-5000)

Red: Green: Green flashing:

7

Ain (right CC-5000)

- SMB connector
Do not use.

Error: LD overcurrent, LD overvoltage, Power not OK. Output active. Disabled, waiting.

### 10.2.7 CC-HP Module

The CC-HP module is a digitally controllable, low-noise current source for high-power diode lasers and amplifiers. Its most important features are:

- Support for negative laser diodes (anode grounded) and positive laser diodes (cathode
grounded).

- Extended current range of up to 10000 mA.
- Monitoring of the voltage applied to the laser diode.
- High current/voltage or loose connection detection to prevent damage to the laser diode.
- Differential analog SMB input.
- Power supply for the laser head modulation circuit.
- Built-in temperature sensors for overheat detection.
Modulation and stabilization sources within DLC pro can be directed to the CC-HP module - with little limitations:

- Above a Set Current of 500 mA, current modulation can be applied with slew rates up to
500 Ampere per second. Limitations are a -3 dB bandwidth of 70 Hz and a constant delay of 2 ms.

- Below a Set Current of 500 mA, current slew rates of more than 50 Ampere per second will cause a
distorted waveform. The CC-HP shows low noise properties and allows high stability of the laser diode or amplifier current. It fits into an S-Slot of the DLC pro. CAUTION ! Do not interchange the CC-HP and the TC Module as this leads to malfunction. Observe the mounting instructions noted in section 11.6. NOTE !

In Dual-Laser configurations, limitations of tapered amplifier currents may occur when using a CC-HP module together with a CC-5000 or a second CC-HP module and at least one current setting > 5000 mA. In this case, both lasers can be operated at their maximum rating separately. Firmware could limit one or both tapered amplifier currents in case of simultaneous operation, depending on the DLC pro configuration.

NOTE !

If the DLC pro is using the PS or PS+ module, the maximum current is limited to 7 A by the power supply module as well as the heat generated within the DLC pro. If the DLC pro is powered with a PS HP module up to 10 A are possible.

Figure 152 Panel of the CC-HP module

1

Status LED a

3

Current Connector

2

Status LED b

4

Ain (Analog Input)

1

Status LED A

Red: Green: Green flashing:

2

Status LED B

Not active.

3

Current Connector

- D-Sub 15 connector
Connector for output current. For pin assignment of the D-Sub 15 connector, please refer to section 11.10.2.

4

Ain

- SMB connector
Multi-purpose measurement input, - 4 V .. + 4 V, input resistance 1 MΩ. DLC TA pro/-AL: Used for monitoring the amplified output power (please refer to the TA pro or TA pro AL laser head manual).

Error: LD overcurrent, LD overvoltage, Power not OK. Output active. Disabled, waiting.

### 10.2.8 TC Module

The TC module is designed for driving peltier elements (TEC) that are regulated depending on the signal of a negative temperature coefficient resistor (NTC). The NTC measures the temperature inside the connected laser head and, depending on the configured operating parameters, the TEC controls the temperature. The TC module comprises power stages, measurement functions, and digital regulators to perform this task. In the basic set up, two absolutely independent regulators are available. The block diagram below shows the setup and the most important elements. Communication between the TC module and the MC+ module is carried out via the internal digital bus which comprises fast serial interfaces (LVDS) and hardware control lines. The core of the TC module is an FPGA with a microcontroller. Together, they contain the interface for communication with the MC+ module and the digital software regulators. The relevant TC parameters (PID settings, limits etc.) can be set via touchscreen, PC-GUI or software commands.

Figure 153 Block diagram of the TC module

Figure 154 Panel of TC module

1

Status LED Channel 1

3

TEC 1 Connector

2

Status LED Channel 2

4

TEC 2 Connector

1

Status LED Channel 1

Red: Error: Power Driver Problem, NTC missing or TEC not OK. Off: No head connection (TEC and NTC missing). Green: Output active, settled. Green flashing: Disabled, waiting. Orange: Output active, regulating. Orange flashing: Output active, regulating, saturated;

2

Status LED Channel 2

Please see description of Status LED 1 for information.

3

TEC 1 Connector

- D-Sub 15
connector

Connector for TEC 1 temperature control connection. For pin assignment of the D-Sub 15 connector, please refer to section 11.10.3.

4

TEC 2 Connector

- D-Sub 15
connector

Connector for TEC 2 temperature control connection. For pin assignment of the D-Sub 15 connector, please refer to section 11.10.3.

### 10.2.9 PC Module (PC 2-1)

The PC 2-1 module applies an analog voltage to a piezo element inside the laser head, which allows to tune the wavelength. The digital circuit area comprises D/A and A/D converters and an FPGA. The analog circuit area features its own reference voltage source and various high-quality operational amplifiers. The digital input signal that is applied internally via the backplane is converted to an analog voltage. The following discrete and fully analog high-voltage amplifier provides the piezo control voltage. This unipolar voltage signal, typically -1 V .. +140 V with max. 25 mA, allows to generate frequencies up to 1000 Hz at a piezo capacity of typically 1µF. For typical TOPTICA laser heads, the scan amplitude corresponds to a wavelength tuning of several 10 GHz.

Figure 155 Block Diagram of the PC 2-1 module

Figure 156 Panel of the PC 2-1 module

1

Status LED Channel 1

2

1

Status LED Channel 1

Red: Green: Green flashing:

2

Status LED Channel 2

Not active.

3

Piezo Connector

- LEMO 0S.302 -connector
Analog voltage output for piezo control. Voltage range: - 1 V .. + 140 V. For pin assignment, please refer to section 11.10.5. NOTE !

Status LED Channel 2

3

Piezo Connector

HV not OK. Output active. Disabled, waiting.

The piezo voltage output is short-circuit proof. When the power of the piezo driver channel is not sufficient to realize proper modulation of the piezo together with its connected mechanics, this is detected and a warning message (xxx: piezo driver current fault) is displayed. This message disappears 2 s after normal piezo modulation is resumed.

### 10.2.10 PC Module (PC 2-2)

The two channel PC 2-2 module applies analog voltages to piezo elements inside the laser head, which allow to tune the wavelength. The digital circuit area comprises D/A and A/D converters and an FPGA. The analog circuit area features its own reference voltage source and various high-quality operational amplifiers. The digital input signals that are applied internally via the backplane are converted to analog voltages. The following discrete and fully analog high-voltage amplifiers provide the piezo control voltages. These unipolar voltage signals, typically -1 V .. +140 V with max. 25 mA, allow to generate frequencies up to 1000 Hz at a piezo capacity of typically 1µF. For typical TOPTICA laser heads, the scan amplitude corresponds to a wavelength tuning of several 10 GHz.

Figure 157 Block Diagram of the PC 2-2 module

Figure 158 Panel of the PC 2-2 module

1

Status LED Channel 1

3

Piezo Connector 1

2

Status LED Channel 2

4

Piezo Connector 2

1

Status LED Channel 1

Red: Green: Green flashing:

2

Status LED Channel 2

Please see description of Status LED 1 for information.

3

Piezo Connector 1

- LEMO 0S.302 -connector
Analog voltage output for piezo control. Voltage range: - 1 V .. + 140 V. For pin assignment, please refer to section 11.10.5. NOTE !

4

Piezo Connector 2

- LEMO 0S.302 -connector
The piezo voltage output is short-circuit proof. When the power of the piezo driver channel is not sufficient to realize proper modulation of the piezo together with its connected mechanics, this is detected and a warning message (xxx: piezo driver current fault) is displayed. This message disappears 2 s after normal piezo modulation is resumed.

Analog voltage output for piezo control. Voltage range: - 1 V .. + 140 V. For pin assignment, please refer to section 11.10.5. NOTE !

HV not OK. Output active. Disabled, waiting.

The piezo voltage output is short-circuit proof. When the power of the piezo driver channel is not sufficient to realize proper modulation of the piezo together with its connected mechanics, this is detected and a warning message (xxx: piezo driver current fault) is displayed. This message disappears 2 s after normal piezo modulation is resumed.

### 10.2.11 PDH Module

NOTE !

When the PDH module is acquired, TOPTICA also provides relevant software to update your DLC pro. Please refer to section 11.4 for a step-by-step description on how to install the PDH module. If purchased along with the DLC pro, the PDH module and the software is already installed.

NOTE !

To use the PDH module for Top of Fringe PDH locking (see sections 5.4.10 and 7.2.3), a Lock option license is required. The PDH module itself can be used without Lock option license. The Error signals are applied to the SMB-connectors of the PDH module and can be used together with an external controller.

Figure 159 Block diagram of the PDH module (only channel 1 shown)

Figure 160 Panel of the PDH module

1

Status LED Channel 1

4

Input 1

7

Input 2

2

Status LED Channel 2

5

Output 1

8

Output 2

3

Error/Local Oscillator 1

6

Error/Local Oscillator 2

1

Status LED Channel 1

Red: Green: Green flashing:

2

Status LED Channel 2

Please see description of Status LED 1 for information.

3

Error/Local Oscillator 1

- SMB-connector
Err 1:

Lo 1:

NOTE !

PDH module error. Modulation enabled. Modulation disabled.

Pound-Drever-Hall error signal output for channel 1. The analog error signal of the PDH module is superimposed by the sum frequency of the modulation and demodulation signal. For viewing the error output on an oscilloscope, an external lowpass filter is recommended. Demodulation signal output for channel 1. LO Output can be enabled in the PDH window (see section 6.9) or via touchscreen (context parameter menu with Scan/Lock screen selected, see section 5.4.8) When LO Output is enabled, the LO Amplitude can be set as desired. This may affect the error signal generated by the PDH module. If you wish to output the demodulation signal and ensure optimum error signal quality at the same time, set LO Amplitude to 8.8 dBm.

4

Input 1

- SMB-connector
Channel 1 input for connection of a photo diode monitoring the spectrum of the respective cavity or atomic transition. The Maximum Input Level can be adapted in the PDH window (see section 6.9) or via touchscreen (context parameter menu with Scan/Lock screen selected, see section 5.4.8).

5

Output 1

- SMB-connector
Channel 1 output for the modulation signal applied to the laser diode current or EOM for generating the Pound-Drever-Hall error signal. The signal Amplitude can be set in the PDH window (see section 6.9) or via touchscreen (context parameter menu with Scan/Lock screen selected, see section 5.4.8).

6

Error/Local Oscillator 2

- SMB-connector
Err 2: Lo 2:

Pound-Drever-Hall error signal output for channel 2. Demodulation signal output for channel 2.

Please see description of Error/Local Oscillator 1 for information. 7

Input 2

- SMB-connector
Channel 2 input for connection of a photo diode. Please see description of Input 1 for information.

8

Output 2

- SMB-connector
Channel 2 output for the modulation signal. Please see description of Output 1 for information.

### 10.2.12 SI Module

NOTE !

All DLC pro from serial number 50000 on are equipped with the SI module.

When the DLC pro is integrated in a customer specific system, it may be difficult to operate the Emission push button on the DLC pro front panel, e.g. after an interlock (see section 2.3.1), or to check the Laser Radiation Emission Warning LEDs on DLC pro and the connected laser head(s). The SI (System Integrator) module offers the possibility to switch the parameter emission-button-enabled (which is equal to operating the Emission push button) remotely and to connect external Laser Radiation Emission Warning LEDs. DANGER ! Service Operation. For removing the cover to get access to the Laser Class 4 or Laser Class 3B remote control functionality, tools are required to perform the respective procedure at the DLC pro SI module. All operations, which require tools to be used, are declared as service operations. Service operations require additional knowledge and may only be carried out by specially trained personnel. Before carrying out service operations, switch off the DLC pro and disconnect it from the mains supply. DANGER ! When the label and the cover are removed to get access to the Laser Class 4 or Laser Class 3B remote control functionality (Service Operation), the system consisting of the DLC pro and all connected laser heads no longer complies with the International Laser Safety Standards EN 60825-1:2014+A11:2021, IEC 60825-1:2014.

Figure 161 Block diagram of the SI module

Figure 162 Panel of the SI module

1

Laser Class 4

3

Emission Contacts

2

Laser Class 3B

4

Ext. Emission Control

1

Laser Class 4

- SMB-connector
For Class 4 laser systems, TOPTICA provides a SMB-connector behind a cover for manual remote control of the parameter emission-buttonenabled via a positive or negative TTL slope. For details, please refer to section 10.2.12.1. DANGER ! When the label and the cover are removed to get access to the SMB-connector (Service Operation), the system consisting of the DLC pro and all connected laser heads no longer complies with the International Laser Safety Standards EN 608251:2014+A11:2021, IEC 60825-1:2014. Positive TTL Slope (0 V → 5 V): emission-button-enabled #t. Negative TTL Slope (5 V → 0 V): emission-button-enabled #f.

2

Laser Class 3B

- Switch
For Class 3B laser systems, TOPTICA provides a switch behind a cover for enabling remote control of the parameter emission-button-enabled via software commands. For details, please refer to section 10.2.12.2. DANGER ! When the label and the cover are removed to get access to the switch (Service Operation), the system consisting of the DLC pro and all connected laser heads no longer complies with the International Laser Safety Standards EN 608251:2014+A11:2021, IEC 60825-1:2014. Switch in Position 0: (Factory setting) Switch in Position 1:

3

Emission Contacts

- Phoenix-connector
DFK-MC 1,5/6-GF3,81

Connector block for connecting circuits for external Laser Radiation Emission Warning LEDs (external voltage supply required). For details, please refer to section 10.2.12.3. Each of the external circuits is fused by a 1 A slow blow fuse 5 x 20 mm. For exchanging the fuse, please refer to section 10.2.12.4. Maximum values of the external circuit:

30 VDC, 1 A 50 VAC, 1 A

Emission State #f:

Contact between pins 1 + 3, no contact between pins 2 + 3. Contact between pins 2 + 3, no contact between pins 1 + 3.

Emission State #t:

NOTE ! 4

Ext. Emission Control

- SMB-connector
Toggling the parameter emission-button-enabled #t/f via software command not possible. Toggling the parameter emission-button-enabled #t/f via software command possible.

not used

Redundancy at pins 4 - 6 (analog to pins 1 - 3).

10.2.12.1 Activating Class 4 Laser Remote Emission Control (Service Operation) Remove the label and remove the metal cover (2 screws). Apply a TTL slope 0 .. 5 V to the SMB-connector (+ 0 .. 5 V to the inner connector, GND to the outer connector) to switch the parameter emission-button-enabled #t/f. Positive TTL Slope (0 V → 5 V): emission-button-enabled #t. Negative TTL Slope (5 V → 0 V): emission-button-enabled #f. A constant voltage applied has no effect on switching.

10.2.12.2 Activating Class 3B Laser Remote Emission Control (Service Operation) Remove the label and remove the metal cover (2 screws). Set switch to position 1 to enable the remote control of the parameter emission-button-enabled via software commands.

10.2.12.3 Connections at the Emission Contacts Connector The Emission Contacts connector allows to connect two circuits (pins 1 .. 3, and pins 4 .. 6) for external Laser Radiation Emission Warning LEDs. The external circuits are closed/opened by relays inside the SI module, depending on the Emission State being #f or #t. Maximum values of the external circuit:

30 VDC, 1 A 50 VAC, 1 A

The voltage supply is connected to pin 4 (first circuit) and pin 1 (second circuit). The circuits are closed, by e.g. a LED with a series resistor or a bulb connected to pins 2 or 3 (second circuit) or pins 5 or 6 (first circuit). Please see Figure 163 for an example.

Figure 163 Schematic circuit example (first circuit)

Plug for connection: Cable Nominal Cross Section:

Phoenix MC 1,5/6-STF-3,81 1.5mm2

10.2.12.4 Exchanging the Fuses inside the SI Module (Service Operation) DANGER ! Before removing a plug-in module, the DLC pro must be switched off and disconnected CAUTION ! from the mains supply. Do not remove plug-in modules unless absolutely necessary as the procedure is strenuous to the hardware. Each of the external circuits is fused by a 1 A slow blow fuse 5 x 20 mm. For exchanging the fuse, the SI module must be removed from the DLC pro (please follow the instructions noted in section 11.5 accordingly).

Figure 164 Location of the fuses inside the SI module

Check the fuses and exchange if necessary. Fuse type is 1 A slow blow, 5 x 20 mm. Mount the SI module to the DLC pro again.

# 11 Appendix

## 11.1 Specifications of the DLC pro

### 11.1.1 General and Environmental Conditions

General and Environmental Specifications Voltage Requirements

100 .. 240 V~, 50/60 Hz (Wide Range Input)

Power Requirements

max. 250 W

Weight

8.0 kg (Mainframe with MC+, CC, PC, TC module)

Size (H x W x D)

154 mm x 450 mm x 348 mm

Overvoltage Category

II

Applicable Pollution Degree

2, indoor use only

Operating Temperature

5 °C .. 40 °C, non-condensing

Transport Temperature

0 .. 40° C, non-condensing

Storage Temperature

0 .. 40° C, non-condensing

Operating Altitude

up to 2000 m

Relative Humidity

non-condensing

### 11.1.2 System Components and Performance

Mainframe Specifications Operator Controls

1 touchscreen, 10 push-buttons, 4 rotary knobs, 1 key switch

Display size and resolution

7 inch diagonal, 800 x 480 pixels, 262k colors

LCD type

TFT, transmissive, anti-glare

Touchscreen

projected capacitive (PCT) with multi-touch capability

I/O port connectors

6 BNC, 1 USB type A

I/O port types

4 Analog Inputs, 2 Analog Outputs, 1 USB 2.0 host

Input Range (all Inputs)

-4 V .. +4 V
Input Impedance (all Inputs)

10 kΩ

Max. Input GND Voltage above PE

-4 V .. +4 V
ADC Resolution (Inputs 1, 2) and Bandwidth

24 bits, 200 kHz analog bandwidth

ADC Resolution (Inputs 3, 4) and Bandwidth

16 bits, 200 kHz analog bandwidth

DAC Resolution (Outputs A, B) and Bandwidth

16 bits, 200 kHz analog bandwidth

Output Range (Outputs A, B)

-4 V .. +4 V (no load), during startup temporarily -4 V
Output Impedance (Outputs A, B)

50 Ω, min. load 200 Ω to prevent overload

# of M-Slots (PC, CC-500, ...)

4

# of S-Slots (TC, CC-5000, ...)

2-4

Current Controller CC-500/CC-500 SMC Laser Current Connectors

D-Sub, 9-pin female (1 Connector for each Channel)

ADC Input Connectors

SMB (1 Connector for each Channel)

Max. Laser Current

2 x 245 mA or 1 x 490 mA (selectable via switch on CC pcb) Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC-500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

Min. Laser Current

0.5 mA

Laser Current Polarity

selectable via software

Max. Output Voltages

7 V @ 360 mA, 5 V @ 490 mA

Current Noise Density

280 pA/sqrt (Hz) @ 1 kHz

Low Freq. Current Noise (0.1 Hz .. 10 Hz)

< 50 nA p-p

Smallest Current Step

16 nA (enhanced resolution ON)

Absolute Accuracy

+/1 mA (without offset calibration)

Modulation Bandwidth

DC to 15 kHz .. 30 kHz (depending on laser diode)

Achievable Power Stabilization Bandwidth

DLC DL pro, DLC DFB pro, DLC DL pro BFY: 10 kHz, DLC CTL: 4 kHz

Temperature Coefficient of Laser Current

< 3 ppm/K typ.*

Long Term Stability of Laser Current

< 100 ppm/sqrt (khrs)*

ADC Input Range

-4 V .. + 4 V
Input Impedance

10 kΩ

ADC Resolution

16 bits

Max. Input GND Voltage above PE

-8 V .. + 8 V
*
after >1 hr warm-up period

Current Controller CC-700 Laser Current Connectors

D-Sub, 9-pin female (1 Connector for each Channel)

ADC Input Connectors

SMB (1 Connector for each Channel)

Max. Laser Current

2 x 350 mA or 1 x 700 mA (selectable via switch on CC pcb) Maximum Current settings for laser diodes with negative polarity: The total maximum current for negative-polarity laser diodes is limited by the internal power supply of DLC pro. The power supply provides 650 mA current in total, which can be distributed over all CC-500/CC-700 modules driving the negative-polarity diodes of all laser heads connected to one DLC pro. The Maximum Current for each negative-polarity laser diode must be set in a way, that the sum of maximum currents does not exceed 650 mA.

Min. Laser Current

0.5 mA

Laser Current Polarity

selectable via software

Max. Output Voltages

7 V @ 510 mA, 5 V @ 700 mA

Current Noise Density

400 pA/sqrt (Hz) @ 1 kHz

Low Freq. Current Noise (0.1 Hz .. 10 Hz)

< 70 nA p-p

Smallest Current Step

23 nA (enhanced resolution ON)

Absolute Accuracy

+/1 mA (without offset calibration)

Modulation Bandwidth

DC to 15 kHz .. 30 kHz (depending on laser diode)

Achievable Power Stabilization Bandwidth

DLC DL pro, DLC DFB pro, DLC DL pro BFY: 10 kHz, DLC CTL: 4 kHz

Temperature Coefficient of Laser Current

< 3 ppm/K typ.*

Long Term Stability of Laser Current

< 100 ppm/sqrt (khrs)*

ADC Input Range

-4 V .. + 4 V
Input Impedance

10 kΩ

ADC Resolution

16 bits

Max. Input GND Voltage above PE

-8 V .. + 8 V
*
after >1 hr warm-up period

Current Controller CC-5000 Laser Current Connector

D-Sub, 15-pin female

ADC Input Connector

SMB

Max. Laser Current

5000 mA

Min. Laser Current

5 mA

Laser Current Polarity

negative (anode grounded)

Output Voltage

0.85 V .. 4 V

Maximum Laser Voltage @ Max. Current + 2 m Cable

0.85 V .. 3.5 V

Current Noise Density

120 nA/sqrt (Hz)

Low Freq. Current Noise (0.1 Hz .. 10 Hz)

10 µA p-p

Smallest Current Step

5 µA

Absolute Accuracy

max. 0.1 % dev. from setpoint

Modulation Bandwidth

100 Hz

Achievable Power Stabilization Bandwidth

DLC TA pro/-AL: 4 kHz, DLC SHG pro, DLC FHG pro: 1 kHz

Temperature Coefficient of Laser Current

10 ppm/K typ.*

ADC Input Range

-4 V .. + 4 V
Input Impedance

10 kΩ

ADC Resolution

16 bits

Max. Input GND Voltage above PE

-8 V .. + 8 V
*
after >1 hr constant current

Current Controller combination of two CC-5000 Laser Current Connector

D-Sub, 15-pin female

ADC Input Connectors

2 x SMB

Max. Laser Current

10000 mA with PS HP module 7000 mA with PS or PS+ module

Min. Laser Current

10 mA

Laser Current Polarity

negative (anode grounded)

Output Voltage

0.85 V .. 4 V

Maximum Laser Voltage @ Max. Current + 2 m Cable

0.85 V .. 3.2 V

Current Noise Density

200 nA/sqrt (Hz)

Low Freq. Current Noise (0.1 Hz .. 10 Hz)

20 µA p-p

Smallest Current Step

10 µA

Absolute Accuracy

max. 0.1 % dev. from setpoint

Modulation Bandwidth

100 Hz

Achievable Power Stabilization Bandwidth

DLC TA pro/-AL: 4 kHz, DLC SHG pro, DLC FHG pro: 1 kHz

Temperature Coefficient of Laser Current

10 ppm/K typ.*

ADC Input Range

-4 V .. + 4 V
Input Impedance

10 kΩ

ADC Resolution

16 bits

Max. Input GND Voltage above PE

-8 V .. + 8
*
after >1 hr constant current

Current Controller CC-HP Laser Current Connector

D-Sub, 15-pin female

ADC Input Connector

SMB

Max. Laser Current

10000 mA with PS HP module 7000 mA with PS+ module

Min. Laser Current

100 mA

Laser Current Polarity

negative (anode grounded), positive (cathode grounded)

Output Voltage

0.85 V .. 4 V

Maximum Laser Voltage @ Max. Current + 2 m Cable

0.85 V .. 3.5 V

Current Noise Density

120 nA/sqrt (Hz)

Low Freq. Current Noise (0.1 Hz .. 10 Hz)

10 µA p-p

Smallest Current Step

10 µA

Absolute Accuracy

max. 1 % dev. from setpoint

Modulation Bandwidth

100 Hz

Achievable Power Stabilization Bandwidth

DLC TA pro/-AL: 4 kHz, DLC SHG pro, DLC FHG pro: 1 kHz

Temperature Coefficient of Laser Current

20 ppm/K typ.*

ADC Input Range

-4 V .. + 4 V
Input Impedance

10 kΩ

ADC Resolution

16 bits

Max. Input GND Voltage above PE

-8 V .. + 8 V
*
NOTE !

after >1 hr constant current

In Dual-Laser configurations, limitations of tapered amplifier currents may occur when using a CC-HP module together with a CC-5000 or a second CC-HP module and at least one current setting > 5000 mA. In this case, both lasers can be operated at their maximum rating separately. Firmware could limit one or both tapered amplifier currents in case of simultaneous operation, depending on the DLC pro configuration.

Temperature Controller TC TEC Current Connectors

2 D-Sub, 15-pin male (1 Connector for each Ch)

Max. TEC Current

2 x 3 Amps

Act. Temperature Noise (100 µHz .. 1 Hz)

< 300 µK p-p

Smallest Set Temperature Step

50 µK

Absolute Accuracy of Actual Temperature

+/1 °C (typ., dep. on NTC)

Repeatability of Actual Temperature

< 0.001 K*

NTC Value @ Room Temperature

10 kΩ

Temperature Coeff. of Actual Temperature

< 140 ppm K/K* (TEC temperature change divided by ambient temperature change)

Temp. Control Loop Bandwidth

30 Hz

* after > 1 hr warm-up period
Piezo Controller PC 2-1 Piezo Voltage Connector

Lemo Series 0S.302

Piezo Voltage Range

-1 V .. +140 V
Max. Piezo Current (Charge/Decharge)

25 mA

Amplifier Output Impedance

50 Ω

Voltage Noise Density

140 nV/sqrt (Hz) @ 1 kHz

Smallest Piezo Voltage Step

9.5 µV

Load Capacitance Range

0 .. ∞ µF

Small Signal Bandwidth

3 kHz at Cload = 0

Temperature Coefficient of Piezo Voltage

< 5 mV/K

Piezo Controller PC 2-2 (specifications per channel) Piezo Voltage Connector

Lemo Series 0S.302

Piezo Voltage Range

-1 V .. +140 V
Max. Piezo Current (Charge/Decharge)

25 mA

Amplifier Output Impedance

50 Ω

Voltage Noise Density

140 nV/sqrt (Hz) @ 1 kHz

Smallest Piezo Voltage Step

9.5 µV

Load Capacitance Range

0 .. ∞ µF

Small Signal Bandwidth

3 kHz at Cload = 0

Temperature Coefficient of Piezo Voltage

< 5 mV/K

Main Controller MC+ I/O Connectors

2 x ETH, Digital I/O, LVDS, RS 232/CAN (currently not supported), Interlock, USB, Audio Out

CPU

ARM Cortex-A8 CPU with graphics acceleration

Operating System

Linux

ETH Connector

RJ-45 for 10BASE-T/100BASE-TX

Digital I/O Connector

HD-Sub, 15-pin male, a breakout cable (article number K DLC/ Digital I/O) is available from TOPTICA for convenient access to all 8 digital lines.

Digital I/O Configuration

4 Inputs, 4 Outputs, TTL-compatible

Input Impedance of Digital Input

10 kΩ

High Level Input Voltage

> 2.0 V (maximum voltage 5.5 V)

Low Level Input Voltage

ca. 4.9 V @ no load, ca. 2.3 V @ I = -32mA; Imax = -32 mA

Output Impedance of Digital Output

50 Ω

High Level Output Voltage

ca. 4.9 V @ no load, ca. 2.3 V @ I = -32mA; Imax = -32 mA

Low Level Output Voltage

ca. 0.1 V @ no load, ca. 2.05 V @ I = 32mA; Imax = 32 mA

USB Connector

Micro-USB type B for USB 2.0 on-the-go

Audio Out Connector

3.5 mm Audio Stereo Jack

Audio Output Level (Full Scale)

1.0 V rms

Audio Output Power

40 mW max. @ 16 Ω, 30 mW max. @ 32 Ω

Stereo Codec

Texas Instruments TLV320AIC23B

NOTE !

See section 11.5.1 for exchange of a MC+ module.

Pound-Drever-Hall PDH module (specifications per channel) Input/Output Connectors

3 x SMB per channel

Modulation Output 1/2 Waveform

Sine

Level

- 49.2 dBm .. 13.8 dBm (2.2 mV .. 3.1 V peak-to-peak voltage)
Step Size

0.5 dB

Frequency

5 MHz or 25 MHz, switchable

Output Impedance

50 Ω

Input Range Mod./Demod. Step

- 10 dBm, 0 dBm, + 10 dBm (max. input level)
Relative

Phase

1.3° (5 MHz), 6.5° (25 MHz)

Adjustable Phase Range

0 .. 360°

<PDH in> ADC resolution

14 bit

<PDH error> ADC resolution

16 bit

Error Signal Bandwidth (digital)

1.5 MHz (- 3 dB)

Input Impedance

50 Ω

Error Output 1/2 Range

±1.5 V

Output Impedance

50 Ω

Bandwidth

50 MHz (-3 dB)

Group delay

20 ns

LO Output 1/2 Level

- 20.7 dBm .. 10.8 dBm (58 mV .. 2.2 V peak-to-peak voltage)
Step Size

0.5 dBm

Output Impedance

50 Ω

Common Mode Input/Output Range of Connectors

Err/LO: +/-1 V Out: +/- 10 V In: +/- 10 V

All Outputs Short-Circuit Proof

Yes

Power Supply Module PS+ Mains Input

100 .. 240 V~, 50/60 Hz (Wide Range Input)

Fuse

250 V, 4 A T (slow blow) fuse 5 x 20 mm

Max. Power Consumption

250 W

Typ. Power Consumption (examples)

approx. 40 W (DLC pro is switched on, CTL laser emission is off), 45 W (CTL laser emission is on)

Power Supply Module PS HP Mains Input to External Power Adaptor

100 .. 240 V~, 50/60 Hz (Wide Range Input)

Fuse

2 x 10 A T (slow blow) fuse, 5 x 20 mm on PS HP pcb

Max. Power Consumption

280 W

Typ. Power Consumption (examples)

approx. 42 W (DLC pro is switched on, CTL laser emission is off), 47 W (CTL laser emission is on) approx. 55 W (DLC pro is switched on, TA-SHG pro laser emission is off), 95 W (TA-SHG pro laser emission is on)

System Integrator Module SI Fuses for Emission Contacts Circuits

1 A slow blow fuse 5 x 20 mm

Maximum values of the Emission Contacts Circuits:

30 VDC, 1 A 50 VAC, 1 A

## 11.2 Upgrade for Control of a 2nd Laser (Service Operation)

NOTE !

To use the DLC pro for control of two lasers (Dual-Laser-Operation), an upgrade is required. When the Dual-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling two laser systems of the type DL pro, DFB pro, DL pro BFY, TA pro, BoosTA pro or two modules in the TA pro AL (MTA pro) laser head. If an Upgrade for Control of a 2nd Laser is purchased to upgrade an existing DLC pro, plug-in modules must be installed, software must be updated and a software license needs to be activated. Please follow the instructions below to upgrade your DLC pro.

1.
Switch off the ON/OFF switch on the DLC pro rear panel and disconnect the DLC pro from the mains supply.

2.
Install the required plug-in modules (see Figure 172 as an example). Please follow the instructions noted in section 11.5 accordingly and observe the mounting positions which are noted in section 11.6.

3.
Perform a DLC pro system software update (see section 11.19) to ensure that all modules have the same system software version.

NOTE !

4.
Install TOPAS DLC pro (PC-GUI) as described in section 6.2.

NOTE !

5.
For Dual-Laser-Operation, System Software 5.5.0 or higher and Firmware 1.7.0 or higher are required.

For Dual-Laser-Operation, TOPAS DLC pro 1.7.0 or higher is required.

Activate the license key for Upgrade for Control of a 2nd Laser as described in section 11.20.

### 11.2.1 Rules for TC, CC, and PC Module Connection (Dual-Laser-Operation)

The Digital Laser Controller DLC pro is capable of controlling two laser systems of the type DL pro, DFB pro, DL pro BFY, TA pro, BoosTA pro or two modules in the TA pro AL (MTA pro) laser head. When connecting the cables between the laser heads and the TC, CC, and PC modules of the DLC pro, please follow the general rules in the order noted below:

- 1. TC modules connections:
The DLC pro identifies laser 1/laser 2 by the order of TC module TEC channels to which a diode laser or Master Oscillator (for amplified laser systems) is connected, counting from the left to the right, up to down (see example in Figure 165).

- 2. CC-500/CC-700 modules connections:
Start with connecting a diode laser or Master Oscillator which consumes > 245 mA to the ch 1 current connector of the CC-500 module inserted in M-Slot 1. In this case (> 245 mA) the ch 2 current connector of this CC-500 module cannot be used, connect the next diode laser or Master Oscillator to the ch 1 current connector of the CC-500 module inserted, e.g. in M-Slot 2. If the first diode laser or Master Oscillator consumes < 245 mA, you can use the ch 2 current connector of the CC-500 module inserted in M-Slot 1 for the second one, if this consumes also < 245 mA. For changing the CC-500 current output from one-channel operation to two-channel operation, please refer to section 10.2.4.1. The same rules apply for an installed CC-700 module with the difference that a single current channel can deliver < 350 mA in two-channel operation and < 700 mA in one-channel operation.

- 3. PC modules connections:
PC module connections are also counted from the left to the right, up to down (for PC 2-2 modules). Start with the first piezo voltage connector and connect according to the temperature control connections in step 1.

- CC-5000/CC-HP modules connections:
Connect the tapered amplifiers of the connected laser heads as required from the left to the right to the CC-5000/CC-HP modules installed in S-Slots 1 and 2.

- CC-HP modules connections for XP tapered amplifiers:
Connect the XP tapered amplifier (Amp CC 1 .. Amp CC 4) of the connected laser head as required from left to right to two CC-HP modules, and two channels of the designated CC-700 module. Please refer to the laser head manual for details. NOTE !

In Dual-Laser configurations, limitations of tapered amplifier currents may occur when using a CC-HP module together with a CC-5000 or a second CC-HP module and at least one current setting > 5000 mA. In this case, both lasers can be operated at their maximum rating separately. Firmware could limit one or both tapered amplifier currents in case of simultaneous operation, depending on the DLC pro configuration.

11.2.1.1

Connection Example DLC pro with two MTA TA pro Modules in TA pro AL (MTA pro)

Figure 165 Connection example: DLC pro with two MTA TA pro modules in a TA pro AL (MTA pro), connected as laser 1 and laser 2.

In this example both MTA TA pro Master Oscillator consume > 245 mA, so the ch 2 current connector of both CC-500 modules cannot be used.

11.2.1.2

Connection Example DLC pro with TA pro and DL pro

Figure 166 Connection example: DLC pro with TA pro laser head connected as laser 1 and DL pro laser

head connected as laser 2. In this example both, the TA pro Master Oscillator and the DL pro consume > 245 mA, so the ch 2 current connector of both CC-500 modules cannot be used.

11.2.1.3

Connection Example DLC pro with CTL and BoosTA pro

Figure 167 Connection example: DLC pro with a combination of CTL laser head and BoosTA pro laser

head connected as laser 1 NOTE !

In case you want to operate CTL and BoosTA pro as separate lasers, then connect the BoosTA pro temperature control to the tec 1 connector of the TC module, and the CTL temperature control to the tec 2 connector. The DLC pro then detects separate lasers, and the BoosTA pro is operated as laser 1, the CTL as laser 2.

11.3

Upgrade for Control of four Lasers (Service Operation)

NOTE !

To use the DLC pro for control of up to four lasers (Quad-Laser-Operation), an upgrade is required. When the Quad-Laser-Operation upgrade is acquired, TOPTICA provides a license key via e-mail or USB flash drive and additional hardware, such as modules and cables. The license is unlimited in time but linked to the individual hardware of the DLC pro and cannot be used for other devices. If purchased along with the DLC pro, the licence and the hardware will already be installed.

The Digital Laser Controller DLC pro is capable of controlling up to four laser systems of the type DL pro, DFB pro, DL pro BFY, or up to four DL pro, DFB pro or DL pro BFY modules in the MDL pro or TA pro AL (MTA pro) laser head. If an Upgrade for Control of 4 Lasers is purchased to upgrade an existing DLC pro, plug-in modules must be installed, software must be updated and a software license needs to be activated. Please follow the instructions below to upgrade your DLC pro.

1.
Switch off the ON/OFF switch on the DLC pro rear panel and disconnect the DLC pro from the mains supply.

2.
Install the required plug-in modules (see Figure 173 as an example). Please follow the instructions noted in section 11.5 accordingly and observe the mounting positions which are noted in section 11.6.

3.
Perform a DLC pro system software update (see section 11.19) to ensure that all modules have the same system software version.

NOTE !

4.
Install TOPAS DLC pro (PC-GUI) as described in section 6.2.

NOTE !

5.
For Quad-Laser-Operation, System Software 6.1.0 or higher and Firmware 3.1.0 or higher are required.

For Quad-Laser-Operation, TOPAS DLC pro 3.1.0 or higher is required.

Activate the license key for Upgrade for Control of 4 Lasers as described in section 11.20.

### 11.3.1 Rules for TC, CC, and PC Module Connection (Quad-Laser-Operation)

The Digital Laser Controller DLC pro is capable of controlling up to four laser systems of the type DL pro, DFB pro, DL pro BFY, or up to four DL pro, DFB pro or DL pro BFY modules in the MDL pro or TA pro AL (MTA pro) laser head. When connecting the cables between the laser heads and the TC, CC, and PC modules of the DLC pro, please follow the general rules in the order noted below:

- 1. TC modules connections:
The DLC pro identifies laser 1 .. 4 by the order of TC module TEC channels to which a diode laser or Master Oscillator (for amplified laser systems) is connected, counting from the left to the right, up to down.

- 2. CC-500/CC-700 modules connections:
Start with connecting a diode laser or Master Oscillator which consumes > 245 mA to the ch 1 current connector of the CC-500 module inserted in M-Slot 1. In this case (> 245 mA) the ch 2 current connector of this CC-500 module cannot be used, connect the next diode laser or Master Oscillator to the ch 1 current connector of the CC-500 module inserted, e.g. in M-Slot 2. If the first diode laser or Master Oscillator consumes < 245 mA, you can use the ch 2 current connector of the CC-500 module inserted in M-Slot 1 for the second one, if this consumes also < 245 mA. Connect all the other lasers using the same logic. For changing the CC-500 current output from one-channel operation to two-channel operation, please refer to section 10.2.4.1. The same rules apply for an installed CC-700 module with the difference that a single current channel can deliver < 350 mA in two-channel operation and < 700 mA in one-channel operation.

- 3. PC modules connections:
PC module connections are also counted from the left to the right, up to down (for PC 2-2 modules). Start with the first piezo voltage connector and connect according to the temperature control connections in step 1.

## 11.4 Installation of a PDH Module (Service Operation)

NOTE !

When the PDH module is acquired, TOPTICA also provides relevant software to update your DLC pro. If purchased along with the DLC pro, the PDH module and the software is already installed.

If PDH module is purchased to upgrade an existing DLC pro, the PDH module must be installed and software must be updated. Please follow the instructions below to upgrade your DLC pro.

1.
Switch off the ON/OFF switch on the DLC pro rear panel and disconnect the DLC pro from the mains supply.

2.
Install the PDH module. Please follow the instructions noted in section 11.5 accordingly and observe the mounting position which is noted in section 11.6.

3.
Perform a DLC pro system software update (see section 11.19) to ensure that all modules have the same system software version.

NOTE !

4.
For PDH module operation, System Software 5.6.0 or higher and Firmware 1.8.0 or higher are required.

Install TOPAS DLC pro (PC-GUI) as described in section 6.2.

## 11.5 Changing Plug-In Modules (Service Operation)

DANGER ! Before removing a plug-in module, the DLC pro must be switched off and disconnected CAUTION ! from the mains supply. Do not remove plug-in modules unless absolutely necessary as the procedure is strenuous to the hardware. For changing a plug-in module (except MC+), follow the steps below:

1.
Switch off the ON/OFF switch on the DLC pro rear panel and disconnect the DLC pro from the mains supply.

2.
Unscrew the two/four fixing screws at the top and the bottom of the respective module.

3.
Carefully remove the module, either by pulling at two (if possible diagonal) fixing screws or better by pulling at a properly fixed D-Sub plug.

CAUTION ! When changing a PS module (all versions), disconnect the ground cable from the old module before pulling out the module completely. Reconnect the ground cable to the new module.

4.
Insert the new plug-in module and fix it with the two/four screws.

5.
Perform a DLC pro system software update (see section 11.19) to ensure that all modules have the same system software version.

### 11.5.1 Exchange of a MC+ Module

For exchanging a MC+ module, follow the steps below:

1.
Switch off the ON/OFF switch on the DLC pro rear panel and disconnect the DLC pro from the mains supply.

2.
Unscrew the four fixing screws at the top and the bottom of the MC+ module.

3.
Carefully remove the original MC+ module, by pulling at the lever at the panel.

4.
Insert the new MC+ module and fix it with the four screws.

5.
Perform a DLC pro system software update (see section 11.19) to ensure that all modules have the same system software version.

6.
Perform a TOPAS DLC pro software update (see section 11.17).

7.
Load the factory settings of the laser system (see section 4.12) so that the actual settings are used after a restart of the DLC pro.

8.
In case you had a Lock option please install the original Lock option on the DLC pro again (see section 11.20).

### 11.5.2 Mounting a Combination of two CC-5000 Modules

NOTE !

Operating the combination of two CC-5000 modules (see section 10.2.6.1) is only possible in a DLC pro which is equipped with a MC+ module. If necessary, the MC+ module is supplied together with the set of two CC-5000 modules. Please refer to section 11.5.1 for installation.

For installation of the combination of two CC-5000 modules, please follow the steps below:

Figure 168 Removing DLC pro cover panel

1.
Loosen 4 x screws (1) and remove 2 x cover panels (2).

Figure 169 Connecting the two CC-5000 modules

2.
Connect the two CC-5000 modules via the supplied cable (3). Fold cable (3) as shown in Figure 169, right.

Figure 170 Mounting the CC-5000 modules at the DLC pro and covering the D-Sub-15 connector

3.
Place the PCBs of both CC-5000 modules in the guide rails of the DLC pro and slide-in completely. Fix the CC-5000 modules each with 2 x screws (1).

4.
Cover the D-Sub-15 connector of the right CC-5000 module with the cover (3) and fix it with 2 x screws (4).

## 11.6 Arrangement of Plug-In Modules

DANGER ! Before changing a plug-in module, the DLC pro must be switched off and disconnected from the mains supply. When installing plug-in modules in the DLC pro, observe the following notes: You can insert different plug-in modules on the rear panel of the DLC pro in certain slots. Please note that the slots and the plug-in modules have different widths (see the figures and tables in this section).

### 11.6.1 Arrangement Example for one Laser

Figure 171 Different slot widths at the rear of the DLC pro Laser Control Electronics (example DLC DL pro)

Plug-In Module

Width (Horizontal Pitch)

Mounting Position

SI Module

8 HP

Ext-Slot

PS+/PS HP Module

14 HP

P-Slot

TC Module

4 HP

S-Slot 3

TC Module for Tapered Amplifier with DLC TA-SHG/FHG pro and FHG crystal with DLC DL-/TA-FHG pro

4 HP

S-Slot 4

TC Module for TOPO crystal and cavity with DLC TOPO

4 HP

S-Slot 2

MC+ Module

8 HP

L-Slot

CC-500/CC-700 Module

7 HP

M-Slot 1

CC-5000/CC-HP Module

4 HP

S-Slot 2

Combination of two CC-5000 Modules

2 x 4 HP

S-Slot 1 + 2 For mounting instructions, please see section 11.5.2.

PC Module

7 HP

M-Slot 2

PC Modules DLC CTL

7 HP

PC 2-2 in M-Slot 2 PC 2-1 in M-Slot 3

PC Modules DL-/TA-SHG/FHG pro

7 HP

PC 2-2 Master Osc. and SHG Cav. in M-Slot 2 PC 2-1 FHG Cav. in M-Slot 3

PDH Module

7 HP

M-Slot 4

CAUTION ! When your DLC pro is equipped with a CC-5000 Module, do not interchange the CC-5000 and the TC Module as this will lead to malfunction. Observe the mounting positions in the table above.

### 11.6.2 Arrangement Example for Dual-Laser-Operation

Figure 172 Different slot widths at the rear of the DLC pro Laser Control Electronics (example DLC DL pro

upgraded for Dual-Laser-Operation with CC-500 module in M-Slot 3 and PC 2-1 module in MSlot 4).

Plug-In Module

Width (Horizontal Pitch)

Mounting Position

SI Module

8 HP

Ext-Slot

PS+/PS HP Module

14 HP

P-Slot

TC Module

4 HP

S-Slot 3

TC Module (upgraded for DualLaser-Operation)

4 HP

S-Slot 4

MC+ Module

8 HP

L-Slot

CC-500/CC-700 Module

7 HP

M-Slot 1

CC-500 Module (upgraded for Dual-Laser-Operation with diode current > 245 mA per channel) CC-700 Module (upgraded for Dual-Laser-Operation with diode current > 350 mA per channel)

7 HP

M-Slot 3

CC-5000/CC-HP Module

4 HP

S-Slot 2

CC-5000/CC-HP Module (upgraded for Dual-Laser-Operation)

4 HP

S-Slot 1

PC Module PC 2-2 Module (upgraded for Dual-Laser-Operation, if PDH Module is used)

7 HP

M-Slot 2

Plug-In Module

Width (Horizontal Pitch)

Mounting Position

PC 2-1 Modules (upgraded for Dual-Laser-Operation, if no PDH Module is used)

7 HP

M-Slot 2 M-Slot 4

PC Modules DLC CTL

7 HP

PC 2-2 in M-Slot 2 PC 2-1 in M-Slot 3

PDH Module

7 HP

M-Slot 4

CAUTION ! When your DLC pro is equipped with a CC-5000 Module, do not interchange the CC-5000 and the TC Module as this will lead to malfunction. Observe the mounting positions in the table above. NOTE !

In Dual-Laser configurations, limitations of tapered amplifier currents may occur when using a CC-HP module together with a CC-5000 or a second CC-HP module and at least one current setting > 5000 mA. In this case, both lasers can be operated at their maximum rating separately. Firmware could limit one or both tapered amplifier currents in case of simultaneous operation, depending on the DLC pro configuration.

### 11.6.3 Arrangement Example for Quad-Laser-Operation

Figure 173 Different slot widths at the rear of the DLC pro Laser Control Electronics (example DLC DL pro

upgraded for Quad-Laser-Operation of four DL pro laser heads with CC-500 module in MSlot 3 and PC 2-2 modules in M-Slot 2 and 4).

Plug-In Module

Width (Horizontal Pitch)

Mounting Position

SI Module

8 HP

Ext-Slot

PS+/PS HP Module

14 HP

P-Slot

TC Module

4 HP

S-Slot 3

TC Module (upgraded for QuadLaser-Operation)

4 HP

S-Slot 4

MC+ Module

8 HP

L-Slot

CC-500/CC-700 Module

7 HP

M-Slot 1

CC-500 Module (upgraded for Quad-Laser-Operation with diode current < 245 mA per channel) CC-700 Module (upgraded for Dual-Laser-Operation with diode current > 350 mA per channel)

7 HP

M-Slot 3

PC 2-2 Module (upgraded for Quad-Laser-Operation)

7 HP

M-Slot 2

PC 2-2 Module (upgraded for Quad-Laser-Operation)

7 HP

M-Slot 4

NOTE !

The arrangement of plug-in modules for Quad-Laser-Operation is dependent on the connected laser heads (e.g., DL pro, DFB pro or DL pro BFY), the required laser diode current, or whether a PDH Module is used or not.

## 11.7 DLC pro for Rack Integration

The DLC pro can be installed in the TOPTICA T-RACK or a third-party 19“ rack. Please refer to section 11.7.1 in this manual for preparation, and the T-RACK manual for installation and operation of the DLC pro in a T-RACK or in a third-party rack. Specifications are only guaranteed when the DLC pro is installed in the TOPTICA T-RACK. NOTE !

Optical performance specification of TOPTICA Laser Rack Systems is only guaranteed, if the T-RACK exclusively integrates TOPTICA building blocks.

### 11.7.1 Exchanging the DLC pro Front Handles (Service Operation)

DANGER ! Before opening the housing, the DLC pro must be switched off and disconnected from the mains supply. For installation in the TOPTICA T-RACK or a third-party 19“ rack the DLC pro must be equipped with the appropriate front handles. Please follow the instructions below:

Figure 174 Removing the DLC pro top cover

1.
Remove 4 x screws (1) and lift DLC pro top cover (2) upwards. Please note that the top cover (2) is clipped into rails at 6 points (The clips are similar to the ones of the base plate illustrated in Figure 175). These connections must be unclipped when lifting the top cover (2) upwards.

Figure 175 Lifting the DLC pro from the base plate

2.
Release the clips between DLC pro and base plate (3) at both sides and lift the DLC pro from the base plate (3) as shown in Figure 175. Please note that the base plate (3) is also clipped into rails at 6 points. These connections must also be unclipped when lifting the DLC pro from the base plate (3).

Figure 176 Exchanging the DLC pro front handles

3.
Remove 4 x screws (4) and both front handles (5). Mount 2 x T-RACK front handles (6) with 4 x screws (4).

Figure 177 Placing the DLC pro on the base plate

4.
Place the DLC pro in correct orientation (see Figure 177) on the base plate (3) so that the six clips of the base plate (3) are aligned with the rails of the DLC pro (see Figure 177). Carefully press together DLC pro and base plate (3). A clicking indicates that a clip is properly engaged.

CAUTION ! The clips can easily be damaged. Check whether the base plate (3) is properly aligned to the DLC pro front- and rear panel after mounting.

Figure 178 Placing the top cover on the DLC pro

5.
Place the top cover (2) on the DLC pro so that the six clips of the top cover (2) are aligned with the rails of the DLC pro (The clips and rails are similar to the ones of the base plate illustrated in Figure 177). Carefully press together top cover (2) and DLC pro. A clicking indicates that a clip is properly engaged.

CAUTION ! The clips can easily be damaged. Check whether the top cover (2) is properly aligned to the DLC pro front- and rear panel after mounting. Before mounting the top cover, please make sure that there is no material or tools left inside the DLC pro housing. Fix top cover with 4 x screws (1).

## 11.8 Maintenance

### 11.8.1 Fuse Replacement (PS+ Module)

DANGER ! Before exchanging the fuse, make sure to switch off and disconnect the device from the mains supply ! The connector block contains a cartridge with a fuse and is located on the rear panel of the DLC pro (see Figure 6).

Figure 179 Fuse at the DLC pro connector block

To replace the fuse, open the connector block cover and pull out the fuse cartridge as shown in Figure

179. Use only a 250 V~, 4 A T (slow blow) fuse 5 x 20 mm.
### 11.8.2 Cleaning

DANGER ! Before cleaning, the DLC pro must be switched off and disconnected from the mains supply. Clean the outside of the DLC pro Laser Control Electronics, the front panel, and the panels of the plug-in modules with a cloth slightly moistened with a mild detergent solvent. Then dry with a clean cloth. Do not clean the inside of the DLC pro. CAUTION ! If any materials or liquids get into the DLC pro during cleaning, contact TOPTICA. Never use strong solvents such as thinners, benzine, acidic- or alkaline solvents, spray-type cleaners or abrasive cleaners as they may destroy the surface.

## 11.9 Battery Recycling

NOTE !

Batteries inside ! The return and disposal of batteries must be complied with and practised in accordance with the current applicable legal requirements and local regulations.

## 11.10 Pin Assignment of the DLC pro Connectors

### 11.10.1 CC-500/CC-700 Module Current Connectors

Figure 180 Pin assignment of the current connector (D-Sub-9 female)

Pin Assignment for Diode Laser Connection: Pin 1 Supply voltage + 6.5 V for modulation circuit/short circuit relay Pin 2 Cathode of internal LD photodiode Pin 3 Laser diode ground Pin 4 Anode of internal LD photodiode Pin 5 Supply voltage - 6.5 V for modulation circuit/short circuit relay Pin 6 Measurement of laser diode voltage (GND) Pin 7 Laser diode cathode for anode grounded laser diodes Pin 8 Laser diode anode for cathode grounded laser diodes Pin 9 Measurement of laser diode voltage Shield Earth ground Pin Assignment for XP Tapered Amplifier Connection: Pin 1 Supply Voltage + 6 V Pin 2 Reserved Pin 3 XP Tapered Amplifier Ground Pin 4 Reserved Pin 5 Supply Voltage - 6 V Pin 6 Measurement of XP Tapered Amplifier Voltage (GND) Pin 7 XP Tapered Amplifier Cathode for anode grounded amplifiers Pin 8 XP Tapered Amplifier Anode for cathode grounded amplifiers Pin 9 Measurement of XP Tapered Amplifier Voltage Shield Earth Ground

### 11.10.2 CC-5000/CC-HP Module Current Connector

Figure 181 Pin assignment of the current connector (D-Sub-15 female)

Pin 1 Pin 2 Pin 3 Pin 4 Pin 5 Pin 6 Pin 7 Pin 8 Pin 9 Pin 10 Pin 11 Pin 12 Pin 13 Pin 14 Pin 15 Shield

Supply voltage + 6.5 V for modulation circuit/short circuit relay Laser diode ground Laser diode ground Laser diode ground Laser diode cathode for anode grounded laser diodes Laser diode cathode for anode grounded laser diodes Measurement of laser diode voltage (GND) Supply voltage - 6 V for modulation circuit/short circuit relay Laser diode ground Laser diode ground Laser diode ground Laser diode cathode for anode grounded laser diodes Laser diode cathode for anode grounded laser diodes Laser diode cathode for anode grounded laser diodes Measurement of laser diode voltage Earth ground

### 11.10.3 TC Module TEC Connectors

Figure 182 Pin assignment of the temperature control connectors (D-Sub15 male)

Pin 1 Pin 2 Pin 3 Pin 4 Pin 5 Pin 6 Pin 7 Pin 8 Pin 9 Pin 10 Pin 11 Pin 12 Pin 13 Pin 14 Pin 15 Shield

Supply for digital electronics + 3.3 V Serial clock signal I2C Thermo-electric element A Thermo-electric element B Thermo-electric element A + Thermistor A Thermistor B Ground for analog electronics Ground for digital electronics Serial data signal I2C Thermo-electric element A Thermo-electric element B + Thermo-electric element A + Thermistor A + Thermistor B + Earth ground

### 11.10.4 MC+ Module Digital I/O Connector

Figure 183 Pin assignment of the Digital I/O connector (D-Sub15 HD male)

NOTE !

Pin 1 Pin 2 Pin 3 Pin 4 Pin 5 Pin 6 Pin 7 Pin 8 Pin 9 Pin 10 Pin 11 Pin 12 Pin 13 Pin 14 Pin 15 Shield

A breakout cable (article number K DLC/Digital I/O) is available from TOPTICA for convenient access to all 8 digital lines.

Digital output 3 Digital output 2 Digital output 1 Digital output 0 Ground Ground Ground Ground not connected Ground Ground Digital input 3 Digital input 2 Digital input 1 Digital input 0 Earth ground

### 11.10.5 PC Module LEMO Connector

Figure 184 LEMO 0S.302 connector on the PC module

### 11.10.6 PS+ and PS HP LEMO Connector

Figure 185 LEMO 2B.304 connector on the PS+ module

Pin 1 Pin 2 Pin 3 Pin 4

5 V/4 A GND +15 V/1 A

- 15 V/ 0.2 A
## 11.11 Analog Remote Control of the Laser Frequency

To support customers who lock or control the laser by proprietary signals or locking schemes, the DLC pro can control the laser frequency via an external voltage connected to a BNC-connector on the DLC pro front panel. Using Analog Remote Control, configurable offsets are applied to the CC, PC or TC output of the DLC pro. With CTL laser heads, an additional voltage can be used to control the motor position for coarse wavelength tuning. The DLC pro converts the external voltage into an offset for the CC, PC or TC output. In this way the output values set in the DLC pro are modified by these output offsets. Thus, the CC, PC or TC output of the DLC pro can be controlled by the Analog Remote Control. Prerequisites:

- Experimental setup connected to the DLC pro (for details, see section 8.1).
- External voltage connected to the Fine In or Fast In BNC-connectors on the DLC pro front panel
(for details on the connectors, please refer to section 4.3).

- Laser head connected to the DLC pro as described in section 4.5.3.
- For configuration via PC-GUI: TOPAS DLC pro installed as described in section 6.2.
### 11.11.1 Analog Remote Control Configuration for CC/PC/TC/EOM

Configuration via touchscreen:

1.
On the DLC pro front panel, press the Scan/Lock Mode button or tap the corresponding symbol to access the Scan/Lock mode or the Wide Scan mode.

2.
Press the Parameter button or tap the corresponding symbol to access the context parameter menu.

3 a.

Select Analog Remote Control > CC in the context parameter menu to configure a CC output offset. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Factor Specify the conversion factor for converting the external voltage [V] into a CC output offset [mA]. Example: External voltage: Factor: CC output offset:

3V 2 6 mA

3 b.

Select Analog Remote Control > PC in the context parameter menu to configure a PC output offset. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Factor Specify the conversion factor for converting the external voltage [V] into a PC output offset [V]. Example: External voltage: Factor: PC output offset:

3 c.

2V

-3.5
-7 V
Select Analog Remote Control > TC in the context parameter menu to configure a TC output offset. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Factor Specify the conversion factor for converting the external voltage [V] into a TC output offset [K]. Example: External voltage: Factor: TC output offset:

3 d.

2V

-4
-8 K
Select Analog Remote Control > EOM in the context parameter menu to configure a PC output offset for the intra-cavity EOM. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Factor Specify the conversion factor for converting the external voltage [V] into a PC output offset [V] applied to the slow electrode of the intra-cavity EOM. Example: External voltage: Factor: PC output offset for intra-cavity EOM):

2V

-3.5
-7 V
Configuration via TOPAS DLC pro PC-GUI:

1.
Select the Laser tab in the TOPAS PC-GUI (Laser Menu > Laser Control > Laser tab).

2 a.

To configure a CC output offset, click on the triangle in the CC section. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] ARC Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] ARC Factor Specify the conversion factor for converting the external voltage [V] into a CC output offset [mA]. Example: External voltage: ARC Factor: CC output offset:

2 b.

3V 2 6 mA

To configure a PC output offset, click on the triangle in the PC section. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] ARC Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] ARC Factor Specify the conversion factor for converting the external voltage [V] into a PC output offset [V]. Example: External voltage: ARC Factor: PC output offset:

2V

-3.5
-7 V
2 c.

To configure a TC output offset, click on the triangle in the TC section. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] ARC Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] ARC Factor Specify the conversion factor for converting the external voltage [V] into a TC output offset [K]. Example: External voltage: ARC Factor: TC output offset:

2 d.

2V

-4
-8 K
To configure a PC output offset for the intra-cavity EOM, click on the triangle in the EOM section. Enable Enable or disable control via external voltage. [1: enabled], [0: disabled] ARC Signal Input Specify the BNC connector for the external voltage. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] ARC Factor Specify the conversion factor for converting the external voltage [V] into a PC output offset [V] applied to the slow electrode of the intra-cavity EOM. Example: External voltage: ARC Factor: PC output offset for intra-cavity EOM):

2V

-3.5
-7 V
### 11.11.2 Analog Remote Control Configuration for Motor Scan (only DLC CTL)

Configuration via touchscreen:

1.
On the DLC pro front panel, press the Scan/Lock Mode button several times or select the symbol to access the Wide Scan mode.

2.
Press the Parameter button or tap the corresponding symbol to access the context parameter menu.

3.
Select Analog Remote Control > Motor in the context parameter menu to configure the analog motor remote control. Enable Enable analog motor remote control. [1: enabled], [0: disabled]. Signal Input Select signal input for analog motor remote control. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] Factor Enter input sensitivity factor for analog motor remote control in [nm/V]. Example: Please configure the Motor ARC first, then enable the Analog Remote Control. Set Wavelength: External voltage: Factor: New Wavelength:

960 nm

-2V
2.5 nm/V 955 nm

If the external voltage jumps to - 1 V, the laser scans to 957.5 nm at the maximum speed.

Configuration via TOPAS DLC pro PC-GUI: To configure the Motor Analog Remote Control, click on the triangle in the Motor Control section. Analog Remote Control Enable Enable analog motor remote control. [1: enabled], [0: disabled]. ARC Signal Input Select signal input for analog motor remote control. ["Fine In 1", 0], ["Fine In 2", 1], ["Fast In 3", 2], ["Fast In 4", 4] ARC Factor Enter input sensitivity factor for analog motor remote control in [nm/V]. Example: Please configure the Motor ARC first, then enable the Analog Remote Control. Set Wavelength: External voltage: ARC Factor: New Wavelength:

960 nm

-2V
2.5 nm/V 955 nm

If the external voltage jumps to - 1 V, the laser scans to 957.5 nm at the maximum speed.

## 11.12 Air Pressure Compensation

In extended-cavity diode lasers (ECDLs), part of the cavity contains air. With changing air pressure, the index of refraction of air changes, and with that, the optical length of the air-filled part of the cavity changes. This causes a drift of the laser frequency. Also, in the resonator, the residual reflectivity of the laser diode facet forms an etalon inside the laser cavity. In some ECDLs, the optical length of this etalon needs to be synchronized with the overall length of the cavity to ensure proper single mode operation without mode-hops. With release 1.6.0, TOPTICA introduces a pressure compensation feature that measures the ambient pressure and compensates pressure changes by adjusting the piezo voltage, thereby adjusting the mechanical cavity length in order to keep the optical cavity length constant. The correction is applied to the piezo voltage only and no feed forward is given to the laser diode current. This leaves the internal resonator (the laser diode itself) unaltered while the length change of the external resonator due to the air pressure change is compensated for. This procedure compensates the described effect to first order which is sufficient to eliminate mode-hops and to considerably reduce drift under nearly all practical circumstances.

- In the TOPAS DLC pro PC-GUI interface, the controls for the pressure compensation are located in
the PC section of the Laser tab (please refer to section 7). The user can set the compensation Factor and Enable/Disable the compensation. The Compensation Voltage, that is currently added to the piezo voltage, and the actual Air Pressure are displayed for reference.

- In the touchscreen user interface, the pressure compensation controls can be found on the
Parameter Menu screen (please refer to section 5.14).

- For remote control, the pressure compensation parameters are accessible via:
laser1:dl:pressure-compensation:xxx. The compensation Factor depends on the extended-cavity resonator type:

Laser Head

DL pro or Laser System with DL pro Master Oscillator

Resonator Type Compensation Factor

CTL

A

B

C

D

E

F

n.a.

-0.165
-0.228
-0.102
-0.083
-0.038
-0.355
-0.368
From 2017 on, the resonator type of DL pro and TA pro laser heads is documented in section 05 and section 1.3, respectively, of the Production and Quality Control Data Sheet which is shipped along with the laser head. For older models and for DL-/TA-SHG/FHG pro laser systems, please contact TOPTICA Service for support to set the compensation Factor.

## 11.13 Screenshot Function for Touchscreen

The screenshot function allows to store screenshots of the actual touchscreen display on a USB flash drive. To take a screenshot, please perform the steps as described below:

1.
Insert a USB flash drive in the USB connector on the DLC pro front panel.

2.
Press the Load/Save button on the DLC pro front panel for 5 - 8 seconds. A beep indicates that a screenshot has been taken.

3.
The screenshot is stored on the USB flash drive as a file named dlcpro-<date>-<time>.png.

## 11.14 Parameter List/Software Command List

The complete parameter tree of the DLC pro is described in detail in the Remote Command Reference for TCP/IP and USB. This document is available as a pdf file in the Documentations folder on the software USB flash drive supplied with the DLC pro.

## 11.15 Internal Handling and Storage of Operation Parameters

The operating parameters of the laser head are stored to be available after the DLC pro is switched on. In the following, the data handling is described.

- After the boot procedure of the DLC pro, the operating parameters for the connected laser head
are set to the same values as at the time of the last save.

- To save operating parameters and make them available for the next restart, either press the Load/
Save button on the DLC pro front panel twice, click Menu > Save Configuration or use the save command in the Parameters window in the PC-GUI.

- To return to the saved operating parameters, use the load command in the Parameters window in
the PC-GUI.

- In addition to the set of operating parameters managed in the way described above, another set
of operating parameters is available, called factory settings. They serve as a safe backup. To return to these values, use the restore command followed by the apply command in the Parameters window in the PC-GUI. Use the save command (or similar, see above) to ensure the DLC pro is set to these values after the next boot procedure.

- In rare cases, e.g., exchange of the laser diode, the factory settings need to be changed. To do
so, use the retrieve-now command followed by the store command in the Parameters window in the PC-GUI. Please note that the store command overwrites the factory settings parameters set by TOPTICA as documented in the Production and Quality Control Data Sheet. A warning message must be acknowledged. Use the save command (or similar, see above) to ensure the DLC pro is set to these values after the next boot procedure. An overview of the data flow controlled by the discussed commands is shown in Figure 186. In case of an amplified laser system, the parameters of the Master Oscillator (dl) and the Amplifier (amp) are treated separately.

Figure 186 Internal handling and storage of operating parameters

Summary of the commands to handle the operating parameters in the Parameters window of the PCGUI: NOTE !

[save], [load] and [apply] are accessible in the user level USER, for all other commands discussed here the user level MAINTENANCE is required (for changing the user level, please refer to section 6.9).

laser1:save

laser1:load laser1:xxxx:store

laser1:xxxx:restore laser1:xxxx:factory-settings:apply laser1:xxxx:factory-settings:retrieve-now

Saves the currently used operating parameters. The DLC pro laser system will reboot with these settings. Pressing the Load/Save button on the DLC pro front panel twice is has the same result. The previously saved [laser1:save] operating parameters are resumed. Stores the factory settings parameters to the laser head, use only e.g., after an exchange of the laser diode. Please note that this overwrites the factory settings parameters set by TOPTICA as documented in the Production and Quality Control Data Sheet. A warning message must be acknowledged. Restores the factory settings parameters to the values stored in the laser head [laser1:xxxx:store]. Loads and applies the factory settings parameters as currently used operating parameters. Writes the currently used operating parameters into the factory settings.

## 11.16 System Messages

In case a malfunction occurs, the related system message and its code are displayed in the footer of the TOPAS DLC pro PC-GUI screen, and the red error indicator in the header lights up. The system message is also displayed in the window which appears after clicking on the error indicator in the header (see section 6.6). On the touchscreen, the system message is displayed in the bottom right area. Tapping the bell symbol opens the system messages window where all current system messages are displayed. The system messages window is also accessible from the Home screen. In case a safety-related issue leads to a condition where the laser cannot be switched on or has been switched off automatically, the Laser Radiation Emission Warning LED on the DLC pro front panel lights up red.

## 11.17 TOPAS DLC pro Software Update

Before installing a new release of the TOPAS DLC pro software, please uninstall the current version on your computer. Please follow the procedure described in section 6.2 to install the new software release.

## 11.18 DLC pro Firmware Update

NOTE !

When a DLC pro firmware update is performed, all connected devices (e.g. laser heads, FALC pro module, PFD pro module) are also updated.

NOTE !

The software controlling the DLC pro hardware is divided into two main components: System software and firmware. They can be updated independently (for a system software update, please refer to section 11.19) and have different release cycles.

The firmware provides all the DLC pro specific functionality and is the part of the software that you as a user communicate with. The firmware itself consists of several individual components. It includes the code for all the programmable DLC pro hardware (FPGAs - "field programmable gate arrays"), the graphical user interface for the DLC pro touchscreen, and the device-control software as the main control center. The file (*.fw) for updating the DLC pro firmware is provided for download on the TOPTICA website. www.toptica.com > Company > Downloads > Software > DLC pro Software Update Please note that certain laser heads require additional firmware files to be updated together with the file (*.fw) for updating the DLC pro. Laser Head

Additional Firmware Update File

DL-/TA-SHG/FHG pro

nlo-system-update.fw

TOPO

nlo-system-update.fw

The additional files (*.fw) for updating the laser heads are also provided for download on the TOPTICA website. www.toptica.com > Company > Downloads > Software > DLC pro Software Update TOPTICA announces new versions by an email newsletter. You may subscribe by sending an email to dlcpro@toptica.com with subject “subscribe”. NOTE !

With the shipment of the DLC pro, TOPTICA provides a USB flash drive containing the current system software and firmware versions, the DLC pro USB driver, and the TOPAS DLC pro PC-GUI.

NOTE !

In some cases, an update of the system software is required prior to a firmware update. If this is the case, the firmware update is aborted and the DLC pro will start with the previously installed firmware. Please refer to section 11.19 for instructions on the system software update.

### 11.18.1 Firmware Update via USB Flash Drive

Prerequisites:

- DLC pro switched off at the ON/OFF switch on the rear panel.
NOTE !

The firmware update starts automatically after a system software update (please refer to section 11.19).

NOTE !

Firmware updates can also be performed via the TOPAS DLC pro PC-GUI (please refer to section 11.18.2).

1.
Create a directory \toptica on a FAT formatted USB flash drive. Copy the required firmware update file(s) (see section 11.18) to the \toptica directory on the USB flash drive.

2.
Plug the USB flash drive into the USB connector on the DLC pro front panel (please refer to section 4.1).

3.
Switch on the DLC pro at the ON/OFF switch on the rear panel. The Firmware Installer automatically starts the firmware update.

Figure 187 Touchscreen display during firmware installation

4.
When the firmware update is complete, the following screen will appear:

Figure 188 Touchscreen display when firmware installation is completed

4.
Switch off the DLC pro and remove the USB flash drive. Then switch on the DLC pro again. After switching off, please wait for at least 10 seconds before switching the DLC pro on again. The DLC pro starts and operates with the new firmware installed.

### 11.18.2 Firmware Update via TOPAS DLC pro PC-GUI

CAUTION ! While a firmware update is performed, please switch off the emission of all connected lasers. Prerequisites:

- DLC pro connected to a computer with TOPAS DLC pro PC-GUI (please refer to section 6.9) via
TCP/IP.

- Required firmware update file(s) (see section 11.18) downloaded and stored on the PC.
1.
In the PC-GUI, select Menu > Device Configuration > Firmware Update. The Firmware Information window displays details of the currently-installed firmware.

Figure 189 Device Configuration window, section Firmware Update

2.
Click Next > to open the Upload Firmware Archives window.

Figure 190 Upload Firmware Archives window

3.
Click Add Archive(s) and browse to the location of the downloaded firmware file(s). Select the required firmware file(s).

Figure 191 Firmware file selected

4.
Click Install.

5.
When the Restart System window prompts, click OK and switch off the DLC pro at the ON/OFF switch on the rear panel.

Figure 192 Restart System window

6.
Switch on the DLC pro at the ON/OFF switch on the rear panel. The Firmware Installer automatically starts the firmware update.

Figure 193 Touchscreen display during firmware installation

When the firmware update is complete, the following screen appears on the touchscreen:

Figure 194 Touchscreen display when firmware installation is completed

7.
Switch off the DLC pro. Wait for at least 10 seconds and switch on the DLC pro again. The DLC pro starts and operates with the new firmware installed.

## 11.19 DLC pro System Software Update

NOTE !

The software controlling the DLC pro hardware is divided into two main components: System software and firmware. They can be updated independently (for a firmware update, please refer to section 11.18) and have different release cycles.

The system software provides very fundamental functionality. It comprises the operating system as well as services and software libraries necessary for basic features like hardware access, graphics display, networking, USB support, firmware updates, and others. The file for updating the DLC pro system software is provided for download on the TOPTICA website: www.toptica.com > Company > Downloads > Software > DLC pro Software Update File name: dlcpro-system-software.img Do not rename the system software file.

NOTE !

With the shipment of the DLC pro, TOPTICA provides a USB flash drive that contains the current system software and firmware versions, the DLC pro USB driver, and the TOPAS DLC pro PC-GUI. Do not rename the system software file.

NOTE !

A firmware update (please refer to section 11.18) is required after each system software update. The firmware update starts automatically after the system software update.

Prerequisites:

- DLC pro switched off at the ON/OFF switch on the rear panel.
1.
Create a directory \toptica on a FAT formatted USB flash drive. Copy the system software update file and the corresponding firmware update file (*.fw) to the \toptica directory on the USB flash drive.

2.
Plug the USB flash drive into the USB connector on the DLC pro front panel (please refer to section 4.1).

3.
Switch on the DLC pro and press the Parameter button on the DLC pro front panel until the Preparing system software update message is displayed on the touchscreen. The system software update starts automatically, and the following screen is displayed:

Figure 195 Touchscreen display during system software update

4.
When the system software update is complete, the Firmware Installer automatically starts the firmware update (please refer to section 11.18).

Figure 196 Touchscreen display during firmware installation

5.
When the firmware update is complete, the following screen will appear:

Figure 197

6.
Touchscreen display when firmware installation is completed

Switch off the DLC pro and remove the USB flash drive. Then switch on the DLC pro again. After switching off, please wait for at least 10 seconds before switching the DLC pro on again. The DLC pro starts and operates with the new system software.

## 11.20 Activating Option Licenses

To utilize some DLC pro functions or features, separate option licenses are required. When a option license is acquired, TOPTICA provides an option license key via e-mail or USB flash drive. The license key must be activated via the TOPAS DLC pro PC-GUI. If purchased along with the DLC pro, the licence is already installed. Prerequisites:

- TOPAS DLC pro PC-GUI connected to DLC pro.
- Option license key provided by TOPTICA.
1.
In the PC-GUI, select Menu > Device Configuration > License Manager. A window shows the option licenses that are already installed on the DLC pro.

Figure 198 Device Configuration section License Manager

2.
Click Install New Option. The License Key window opens.

Figure 199 License Key window

3.
Copy the License key information from the email or the USB flash drive to the PC clipboard. Example for a License key:

--- License key: --hFviuU+D23LXeip21ll7ho6RYsKUGr5j8bT+MuULxq+jL3S3zRhJ8lopgc106YjQo5sOCi6o
tTuTwOVwc62RhcuXyKIkyh3WBp9+GhZYXiFN/oHsEjiKvmOxGfmBUpLPGEOCMHeaiM0pDwUc G2Xpgnkz6vJKpdtH4twx7tAyR8vKZgE1xle7UUATNekcvML/6pqy3hc+ShV3eQBvsCvasO5J AQn+ceFNAGmatuZBS7smbBHkDnPx1uhV1vJ8eaNGZTLpR54JgKkULr/wnGglt+QtepicFcBs poq3gpthjrigCesYYIdPgCBPjEhEeeX29W2dRX7RuBlg4PpfKFl9PjCMuu0jDXpruRexmL+b B7w= The license key information is the code written below --- License key: ---.

4.
Paste the license key information into the License Key window and click OK. When the Option installed message is displayed, click OK. The License Manager window lists option type and license validity of the newly-installed license.

Figure 200 License Manager with Lock option and Quad-Laser-Operation upgrade installed (example)

5.
Click Close to exit the window.

6.
Close the TOPAS DLC pro PC-GUI and switch off the DLC pro. Wait for at least 10 seconds and switch on the DLC pro again. Run the TOPAS DLC pro PC-GUI. The DLC pro will now operate with the new option.

## 11.21 DLC pro Control via USB Connection

NOTE !

We recommend operating the DLC pro via Ethernet over using a USB connection due to the higher communication bandwidth. Using a USB to Ethernet adapter on the PC side allows fast communication while having a point-to-point connection between PC and DLC pro – without connecting the DLC pro to the local network or disconnecting the PC from it.

NOTE !

For DLC pro control via USB, the control computer must be connected to the USB connector at the MC+ module (rear panel, please refer to section 10.2.3) via a micro USB 2.0 cable with connector type B. The USB connector at the front panel of the DLC pro is not intended for controlling the DLC pro but for performing a firmware or system software update as described in sections 11.18 or 11.19.

### 11.21.1 USB Driver Installation

If the DLC pro is to be controlled by a computer via USB connection, the TOPAS DLC pro software requires a specific USB driver. Together with the shipment of the DLC pro, TOPTICA provides a USB flash drive that contains the current system software and firmware versions, the DLC pro USB driver files, and the TOPAS DLC pro PC-GUI. USB driver files:

dlcpro-usb-serial.inf dlcpro-usb-serial.cat

(Setup Information) (Security Catalog)

USB driver files updates are provided on the TOPTICA website as part of the DLC pro software package: www.toptica.com > Company > Downloads > Software > DLC pro Software Update Prerequisites:

- Computer login with administrator privileges.
- Both DLC pro USB driver files copied to the computer, or
USB flash drive with both DLC pro USB driver files connected to the computer.

1.
Make sure that the DLC pro is switched on but not connected to the control computer via USB.

2.
On the computer, browse to the directory that contains the DLC pro USB driver files, right-click dlcpro-usb-serial.inf (Setup Information), and click Install.

3.
Windows 8: At the confirmation dialog window, select the option to install the driver. Windows 10: Please confirm all security warning dialogs to install the driver. The USB driver is installed.

4.
Connect the control computer to the micro USB connector of the MC+ module on the DLC pro rear panel (please refer to section 10.2.3). Use a USB connection cable (micro USB 2.0 cable with connector type B). Wait until the new hardware is detected.

5.
Start the TOPAS DLC pro PC-GUI and configure it for operation via USB connection as described in section 11.21.2.

### 11.21.2 Configuring TOPAS DLC pro for Operation via USB Connection

To control the DLC pro with a computer via USB connection, the TOPAS DLC pro PC-GUI must be configured accordingly. Prerequisites:

- 
- 
- 
- 
DLC pro and computer connected via USB connection. TOPAS DLC pro PC-GUI installed on the computer as described in section 6.2. DLC pro USB driver installed on the computer as described in section 11.21.1. DLC pro and computer switched on.

1.
Start the TOPAS DLC pro PC-GUI on the computer.

2.
Click Menu > Connection Settings.

3.
Switch the Connection Settings to Serial and select the Serial Port according to the DLC pro USB driver installation. For DLC pro systems the Baudrate is fixed.

4.
Click OK to save the settings.

11.22

License and Copyright Information associated with Third Party Software

The DLC pro device incorporates third-party software. The license and copyright information associated with this software is available on the Information screen. The DLC pro device contains software which, according to GNU General Public License Version 2 respectively 3, is subjected to disclosure. TOPTICA Photonics SE offers on request an entire copy of the corresponding machine-readable source code at cost price. The DLC pro device contains software covered by the GNU Lesser General Public License. Upon request, TOPTICA Photonics SE offers to grant the rights resulting from this license. This offer is valid during a 3-years-period beginning at the purchase date. Please address your request to TOPTICA Photonics SE, Head of Development, Lochhamer Schlag 19, 82166 Graefelfing, Germany.

## 11.23 Declarations of CE Conformity

### 11.23.1 DLC DL pro and DLC DFB pro

### 11.23.2 DLC DL pro BFY

### 11.23.3 DLC TA pro

### 11.23.4 DLC TA pro AL

### 11.23.5 DLC MTA pro

### 11.23.6 DLC BoosTA pro/Seed Laser + BoosTA pro Combination

### 11.23.7 DLC CTL

### 11.23.8 DLC MSHG pro

### 11.23.9 DLC DL-/TA-SHG pro

### 11.23.10 DLC DL-/TA-FHG pro

### 11.23.11 DLC TOPO

### 11.23.12 DLC TOPO smart

## 11.24 DLC pro Main Dimensions

Figure 201 DLC pro main dimensions

## 11.25 EU Legislation for Electrical and Electronic Equipment (EEE)

Companies selling electrical and electronic goods in the European Union must conform to the EU legislation for electrical and electronic equipment (EEE), which includes the Waste Electrical and Electronic Equipment Directive (WEEE). Assigned duties affect product design of the equipment, disposal of used appliances as well as organizational responsibilities, i.e. product registration. There are different requirements for household WEEE and that which is sold business to business (B2B). All equipment TOPTICA Photonics SE handles is classed as B2B. TOPTICA is registered at the Competent Authority (Stiftung Elektro-Altgeräte Register EAR) under No. DE70442884. At end-of life return your product back to TOPTICA. TOPTICA will dispose used equipment in such a manner as to meet all relevant local, country and EU requirements and guideline. To return products please mark them clearly with "used device". Contact TOPTICA prior to shipping and send them to the following address: TOPTICA Photonics SE Lochhamer Schlag 19 D-82166 Graefelfing

The crossed out wheeIed dust bin symbol indicates that products must be collected and disposed of separately from household waste. TOPTICA reminds all end users of WEEE that you are responsible for deleting personal data on the waste equipment to be disposed of.

## 11.26 Guarantee and Service

As a first step toward obtaining technical support, please contact your local distributor or visit the support pages on our web site: https://www.toptica.com/support/. In case you wish to return a product for diagnosis and/or repair, please contact us prior to sending it so we can issue a Return Material Authorization (RMA) number for you. You can always contact TOPTICA service on the Internet by

- Email: service@toptica.com
- Web form: service.toptica.com
The service department at our headquarters in Munich can be reached by phone

- Tel: +49 89 85837150
For up-to-date phone numbers and addresses of our regional offices please refer to our web site: www.toptica.com/contact-us/
