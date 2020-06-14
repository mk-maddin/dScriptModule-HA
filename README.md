[dScriptModule Custom Component](https://github.com/mk-maddin/dScriptModule-HA) for homeassistant

# What This Is:

This is a custom component to allow control of [Devantech Robot-Electronics dScript](https://www.robot-electronics.co.uk/products/dscript.html) devices in [Homeassistant](https://home-assistant.io) using the [custom dScriptRoomControl firmware](https://github.com/mk-maddin/dScriptRoomControl) which is available in private repository only.
The [dScriptModule python module](https://github.com/mk-maddin/dScriptModule-PyPi) is necessary for this.

# What It Does:

Allows for control of dScript boards (by Robot-Electronics / Devantech Ltd.) via home assistant with the following features:

- automatic discover of conneted lights / switches / covers
- light on/off
- switch on/off
- covers
  - up / down
  - set to specific level
- automatic update

# Installation and Configuration

## Installation
Download the repository and save the "dScriptModule" folder into your home assistant custom_components directory.

## Configuration
Once the files are downloaded, you’ll need to **update your config** to include the following under the **`dScriptModule` domain**:

```yaml
dScriptModule:
  server:
    enabled: True
#   protocol: binaryaes
#   aes_key: "This MUST be 32 characters long."

```

This will automatically detect the boards available in your network as soon as they are online.
(Ever board where you have entered the dScriptServer IP within its configuration will contact the server in regular intervalls and on every state/configuration change).

Alternatively you can define dScriptBoards manually via their IP Address by entering the following under the **`dScriptModule` domain**:

```yaml
dScriptModule:
  devices:
    - host: 192.168.13.120
#     protocol: binaryaes
#     aes_key: "This MUST be 32 characters long."
```

# License

[Apache-2.0](LICENSE). By providing a contribution, you agree the contribution is licensed under Apache-2.0. This is required for Home Assistant contributions.
