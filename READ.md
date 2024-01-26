This project is to help with managing and setting up a very simple wireguard VPN. 


This command generates and new wireguard network with 2 peers
``` python
new_wgNetwork(2, endPoint="10.0.0.234:51820", serverDir="./server-conf/", peerDir="./peer-conf/", serverFileName="wg-test.conf")
```

This command parses an existing network and appends a new peer to it
``` python
append_newPeer_to_existing_wgNetwork("./server-conf/wg-test.conf", endPoint="10.0.0.234:51820", serverDir="./server-conf/", peerDir="./peer-conf/")
```

This is to help make it easier to add new peers in the future when I forget how to use wireguard.
