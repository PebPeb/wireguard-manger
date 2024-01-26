import subprocess
import ipaddress
import re


WG_IPv4NETWORK = '10.0.0.0/24'


def parse_wireguard_config(file_path):
  config = {
    'Interface': {},
    'Peers': []
  }

  with open(file_path, 'r') as file:
    current_section = None

    devices = []
    current_device = []
    first_found = True
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
        current_section = line[1:-1]
        current_device.append(line)
        continue
      if not first_found:                                 # Wait until first device found
        current_device.append(line)
    devices.append(current_device)                        # Add trailing Device to list

    for x in devices:
      if x[0] == "[Interface]":
        config["Interface"].update(parse_device(x))
      elif x[0] == "[Peer]":
        config["Peers"].append(parse_device(x))
      else:
        print("WARNING Invalid device \"" + x[1] + "\". Skipping device.")

  return config

def parse_device(device):
  config = {}
  for x in device[1:]:      # Skip the first value
    config.update(__parse_key_pair(x))
  return config

def __parse_key_pair(text):
  try:
    key, value = map(str.strip, text.split('=', 1))
    return {key: value}
  except:
    print("WARNING Unable to parse \"" + text + "\" not a valid key pair. Skipping line.")
    return None



def print_config(config):

  print("Interface:")
  for key, value in config["Interface"].items():
      print(f"  {key}: {value}")
  print()

  for peer in config['Peers']:
      print("Peer:")
      for key, value in peer.items():
          print(f"  {key}: {value}")
      print()



def new_private_key():
  return subprocess.run(['wg', 'genkey'], capture_output=True, text=True, check=True).stdout.strip()

def gen_public_key(PrivateKey):
  return subprocess.run(['wg', 'pubkey'], input=PrivateKey, capture_output=True, text=True, check=True).stdout.strip()

def add_peer(config):
  # Collecting all the IPs used in the conf so far
  taken_IPs = [re.sub(r'/\d+$', '', config["Interface"]["Address"])]
  for x in config["Peers"]:
    taken_IPs.append(re.sub(r'/\d+$', '',x["AllowedIPs"]))

  # Select new IP 

  subnet = ipaddress.IPv4Network(WG_IPv4NETWORK) # This is currently hardcoded
  available_ips = [str(ip) for ip in subnet.hosts() if str(ip) not in taken_IPs]

  print(subnet)
  if available_ips:
    selected_ip = available_ips[0]
    print("Selected next available IP address:", selected_ip)
  else:
    print("No available IP addresses in the subnet.")
    exit(-1)
  
  private_key = new_private_key()


class wgConfig:
  def __init__(self, configFile=None) -> None:
    self.peers = []
    self.interface = None
    if configFile != None:
      self.parseConf(configFile)

  def parseConf(self, configFile):
    config = []

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
      print(devices)
      for x in devices:
        if x[0] == "[Interface]":
          self.interface = None
          # config["Interface"].update(parse_device(x))
        elif x[0] == "[Peer]":
          peertmp = self.parse_device(x)
          self.peers.append(peer(re.sub(r'/\d+$', '', peertmp["AllowedIPs"]), 
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

class wgDevice:
  def __init__(self, ip, subnet, privateKey=None, publicKey=None, description=None, name=None, port="5180"):
    self.privateKey = privateKey if privateKey or publicKey else new_private_key()
    self.publicKey = publicKey if publicKey else gen_public_key(self.privateKey)
    self.ip = ip
    self.subnet = subnet
    self.description = description if description else ""
    self.name = name if name else "peer_" + self.ip.replace(".", "_")

  def __str__(self) -> str:
    x = "Name = " + self.name + "\n"
    x = x + "Description = " + self.description + "\n"
    return x

class peer(wgDevice):
  def __init__(self, ip, subnet, privateKey=None, publicKey=None, description=None, name=None, port="5180"):
    super().__init__(ip, subnet, privateKey, publicKey, description, name, port)

  def __str__(self) -> str:
    x = "[Peer]\n"
    x = x + super().__str__()
    x = x + "PublicKey = " + self.publicKey + "\n"
    x = x + "AllowedIPs = " + self.ip + "/32\n"               # Currently the subnet mask is hard coded
    return x

class interface(wgDevice):
  def __init__(self, ip, subnet, privateKey=None, publicKey=None, description=None, name=None, port="5180"):
    super().__init__(ip, subnet, privateKey, publicKey, description, name, port)

  def __str__(self) -> str:
    x = "[Interface]\n"
    x = x + super().__str__()
    x = x + "Address = " + self.ip + "/24\n"                  # Currently the subnet mask is hard coded
    x = x + "ListenPort = " + self.port + "\n"              
    return x



if __name__ == "__main__":
  config_path = './server-conf/wg0-example.conf'  # Replace with your actual file path
  parsed_config = parse_wireguard_config(config_path)

  print_config(parsed_config)

  private = new_private_key()
  print(private)
  public = gen_public_key(private)
  print(public)

  print(gen_public_key(parsed_config["Interface"]["PrivateKey"]))
  add_peer(parsed_config)


  test_peer = peer("10.9.9.3", "255.255.255.0")

  print(test_peer)

  n = wgConfig(config_path)
  for x in n.peers:
    print(x)