% for i in node.interfaces:  
/sbin/ifconfig ${i.id} ${i.ip_address} netmask ${i.subnet.netmask} broadcast ${i.subnet.broadcast} up
echo 1 > /proc/sys/net/ipv4/conf/${i.id}/proxy_arp
% endfor                
route del default
twistd -y /STRIP/STRIPmain.py
