import subprocess

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

if __name__ == "__main__":
  config_path = './server-conf/wg0.conf'  # Replace with your actual file path
  parsed_config = parse_wireguard_config(config_path)

  print_config(parsed_config)

  private = new_private_key()
  print(private)
  public = gen_public_key(private)
  print(public)

  print(gen_public_key(parsed_config["Interface"]["PrivateKey"]))

