this is a set of configuration files that doesn't need the emulation environment. 
You can run all three routers on one pc as programs. Great for getting to know the code and debugging.
They communicate over different ports, so no need to set up network interfaces. 

To run the distance-vector protocol:
python PVmain.py lab/testy/r0.cfg
and in separate consoles:
python PVmain.py lab/testy/r1.cfg
python PVmain.py lab/testy/r2.cfg

For the STRIP protocol:
replace PCmain.py with STRIPmain.py