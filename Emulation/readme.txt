To test STRIP we emulated a network using netkit. (http://wiki.netkit.org/index.php/Main_Page)
Netkit emulates routers with lightweight virtual machines which can be connected via virtual links.
To simplify the configuration process we modified 'autonetkit' (http://www.autonetkit.org/). A tool to 
automatically generate all required configuration for netkit from a network description in grapheme.

To be able to run STRIP in netkit you have to modify the virtual image it uses to run the routers. You need 
to add python and the required libraries by following the instructions on the netkit wiki. You might also need
to assign more memory to the virtual machines. 
Also copy the implementation of STRIP into the /STRIP/ folder in the vital image filesystem.

You should now be able to run the netkit labs in the 'labs' folder.
e.g. for the abilene network:
cd /labs/abilene
lstart