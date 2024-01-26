import subprocess
import ipaddress
import re


WG_IPv4NETWORK = '10.0.0.0/24'


def main():
  config_path = './server-conf/wg0-example.conf'  # Replace with your actual file path

  # n = wgNetwork(config_path)
  # n.peerConf(n.add_newPeer())

  # n.serverConf()

  new_wgNetwork(4)
  


class wgNetwork:
  def __init__(self, configFile=None) -> None:
    self.peers = []
    self.host = None

    self.peerDir = ""

    if configFile != None:
      self.parseConf(configFile)

  def parseConf(self, configFile):
    devices = []
    current_device = []
    first_found = True
    with open(configFile, 'r') as file:
      for line in file:
        line = line.strip()

        if not line or line.startswith('#'):                # Ignore Comments
          continue
        if line.startswith('[') and line.endswith(']'):     # Find Device
          if not first_found:                               # After found start Adding new finished Devices
            devices.append(current_device)
            current_device = []
          else:                                             # Can't add first Device because does not have lines yet
            first_found = False
          current_device.append(line)
          continue
        if not first_found:                                 # Wait until first device found
          current_device.append(line)
      devices.append(current_device)                        # Add trailing Device to list

      for x in devices:
        if x[0] == "[Interface]":
          hosttmp = self.parse_device(x)
          self.host = wgDevice(re.sub(r'/\d+$', '', hosttmp["Address"]), 
                            ipaddress.IPv4Network(hosttmp["Address"], strict=False).netmask,
                            privateKey=hosttmp["PrivateKey"],
                            port=hosttmp["ListenPort"])
          # config["Interface"].update(parse_device(x))
        elif x[0] == "[Peer]":
          peertmp = self.parse_device(x)
          self.peers.append(wgDevice(re.sub(r'/\d+$', '', peertmp["AllowedIPs"]), 
                            ipaddress.IPv4Network(peertmp["AllowedIPs"], strict=False).netmask,
                            publicKey=peertmp["PublicKey"]))

        else:
          print("WARNING Invalid device \"" + x[1] + "\". Skipping device.")
  
  def parse_device(self, device):
    config = {}
    for x in device[1:]:      # Skip the first value
      config.update(self.__parse_key_pair(x))
    return config

  def __parse_key_pair(self, text):
    try:
      key, value = map(str.strip, text.split('=', 1))
      return {key: value}
    except:
      print("WARNING Unable to parse \"" + text + "\" not a valid key pair. Skipping line.")
      return None

  def add_newPeer(self):
    newPeer = self.newPeer()
    self.peers.append(newPeer)
    return newPeer
  
  def newPeer(self):
    # Collecting all the IPs used in the conf so far
    taken_IPs = []
    if self.host != None:
      taken_IPs = [self.host.ip]
    for x in self.peers:
      taken_IPs.append(x.ip)

    # Select new IP 
    subnet = ipaddress.IPv4Network(WG_IPv4NETWORK) # This is currently hardcoded
    available_ips = [str(ip) for ip in subnet.hosts() if str(ip) not in taken_IPs]

    if available_ips:
      peerIP = available_ips[0]
      # print("Selected next available IP address:", selected_ip)
    else:
      print("No available IP addresses in the subnet.")
      exit(-1)
    
    peerPrivateKey = gen_publicKey()
    peerPublicKey = gen_privateKey(peerPrivateKey)

    newPeer = wgDevice(peerIP, "255.255.255.0", 
           privateKey=peerPrivateKey,
           publicKey=peerPublicKey)
    return newPeer  


  # Expects to receive a wgDevice object
  # Directory to write the config file to
  def peerConf(self, wgObj, writeTo=None):
    x = wgObj('interface') + "\n"
    x += self.host('peer')
    if writeTo != None:
      try:
        with open(writeTo, 'w') as file:
          file.write(x)
      except:
        print("Failed to write to: \"" + writeTo + "\"")
    else:
      try:
        with open(self.peerDir + wgObj.name + ".conf", 'w') as file:
          file.write(x)
      except:
        print("Failed to write to: \"" + self.peerDir + wgObj.name + ".conf" + "\"")
      
    return x

  def serverConf(self, writeTo=None):
    x = self.host('interface') + "\n"
    for y in self.peers:
      x += y('peer') + "\n"
    
    if writeTo != None:
      try:
        with open(writeTo, 'w') as file:
          file.write(x)
      except:
        print("Failed to write to: \"" + writeTo + "\"")
    else:
      try:
        with open(self.peerDir + self.host.name + ".conf", 'w') as file:
          file.write(x)
      except:
        print("Failed to write to: \"" + self.peerDir + self.host.name + ".conf" + "\"")
      
    return x
    


class wgDevice:
  def __init__(self, ip, subnet, privateKey=None, publicKey=None, description=None, name=None, port="5180"):
    self.privateKey = privateKey if privateKey or publicKey else gen_publicKey()
    self.publicKey = publicKey if publicKey else gen_privateKey(self.privateKey)
    self.ip = ip
    self.subnet = subnet
    self.description = description if description else ""
    self.name = name if name else "peer_" + self.ip.replace(".", "_")
    self.port = port

  def __str__(self, format_type='default') -> str:
      if format_type == 'peer' and hasattr(self, 'publicKey'):
          # [Peer] format
          x = "[Peer]\n"
          x += self.__str__()
          x += "PublicKey = " + self.publicKey + "\n"
          x += "AllowedIPs = " + self.ip + "/32\n"
      elif format_type == 'interface' and hasattr(self, 'privateKey'):
          # [Interface] format
          x = "[Interface]\n"
          x += self.__str__()
          x += "PrivateKey = " + self.privateKey + "\n"
          x += "Address = " + self.ip + "/24\n"
          x += "ListenPort = " + str(self.port) + "\n"
      else:
          # Default format
          x = "Name = " + self.name + "\n"
          x += "Description = " + self.description + "\n"

      return x

  def __call__(self, format_type='default') -> str:
      return self.__str__(format_type)


def gen_publicKey():
  return subprocess.run(['wg', 'genkey'], capture_output=True, text=True, check=True).stdout.strip()

def gen_privateKey(PrivateKey):
  return subprocess.run(['wg', 'pubkey'], input=PrivateKey, capture_output=True, text=True, check=True).stdout.strip()




def new_wgNetwork(numPeers=1):
  wgVar = wgNetwork()
  wgVar.host = wgVar.newPeer()
  for i in range(numPeers):
    wgVar.add_newPeer()
  
  wgVar.serverConf()
  for x in wgVar.peers:
    wgVar.peerConf(x)

  return wgVar




if __name__ == "__main__":
  main()

