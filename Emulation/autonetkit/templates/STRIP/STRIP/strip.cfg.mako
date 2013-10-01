[server]
port=1234
identity=${node.label}
keyfiles=/STRIP/keys
announcementDelay=30
WaitForMoreRequestsDelay=10
WaitForResponsesDelay=20

[neighbours]
hosts=${node.strip.nbrIPs}
targets=${node.strip.nbrNames}
distances=${node.strip.nbrDists}

[logging]
logfile=/hosthome/test/${node.label}.log
fibfile=/hosthome/test/${node.label}.fib
measurementfile=/hosthome/test/${node.label}.msm