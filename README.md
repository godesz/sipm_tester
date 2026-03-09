# sipm_tester
LumenPnP modified to test SiPMs in their tray, Pogo pins with diode testing. Pad recognison.


cd backend
python -m venv venv 
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd frontend
npm i
npm run dev



enable_A_psu,0


set_module,0,0,0,k,0,0,0,0    OFF
set_module,0,0,0,k,1,30,30,30   BAL
set_module,0,0,0,k,2,30,30,30    JOBB
set_module,0,0,0,k,3,30,30,30   BOTH

get_cooler_state,0
get_cooler_state,0  //reused for contact check!!!! use cooler_1_state(first param) //0x00->short 0x01->OK 0x02->not_valid 0x03->open 0xFF->i2c bus error
get_cooler_state,0,OK*3,1,0,0.000,0.000,0.00,0.00,0.00,0.00*


M906-tal le lehet kérni
https://marlinfw.org/docs/gcode/M906.html

X driver current: 800
Y driver current: 1000
Y2 driver current: 1000
Z driver current: 800
I driver current: 200
J driver current: 200
ok

setelni:
M906 Z2

M906 T1 E10
T mint tool


Disable steppers
https://marlinfw.org/docs/gcode/M018.html
Disable all steppers immediately
M18

Disable Z and E steppers immediately
M18 Z E

Set the stepper inactivity timeout to 1 minute
M18 S60

Disable the stepper inactivity timeout
M18 S0

Steps/mm: 400
Current: 200mA
Feedrate: 500 mm/min
Z=0 → top (endstop), Z+ → down toward SiPM
M92 Z400, to set the steps to 400.
M906 Z200 to  lower the current
Feedrate is 500


TODO:

startup motor áram control
acc lefokozás

Z beforrasztása
kábelek kiszedése, pneum

tray rugós rögzítés

