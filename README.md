# sipm_tester
LumenPnP modified to test SiPMs in their tray, Pogo pins with diode testing. Pad recognison.


cd backend
venv\Scripts\activate
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