# RPCS3 iOS port

Experimental PS3 emulator, port of RPCS3

## Installation
- Download `ipa` file from [GitHub releases](https://github.com/XITRIX/RPCS3-iOS-Releases/releases)
- Sideload using AltStore/SideStore
- Open StikDebug and Assign "universal.js" script for RPCS3 app 
- Run RPCS3 from StikDebug

## Usage
- Launch the app using StikDebug
- Press "Start" button
- Install PS3 Firmware selecting `UPDATE.PUP` file (not included)
- Install dumped game and run it

## Features
- Native iOS UI
- Installation of pkg, iso, zip and unpacked folders
- Game Patch manager
- Automatic game updater
- Per-game settings
- Multiple controllers support
- RPCN support (PSN online servers)
- Game trophies screen
- Save data manager
- Per-game settings presets
- RPCS3 compatibility database sync

## Minimal device requirements
- iOS 26+
- 8 GB of RAM

Tested on iPhone 15 Pro Max and iPad Pro M4

## Some tests from developer

### iPhone 15 Pro Max:

- ✅ Tekken 6 - Playable
- ✅ WRC FIA World Rally Championship - Playable
- ✅ Minecraft: Playstation 3 Edition (only v1.0) - Playable
- ✅ Naruto Shippuden: Ultimate Ninja STORM Revolution - Playable
- ❌ Colin McRae Dirt 2 - Non playable, device is too weak to run it
- ❌ God Of War 3 - Non playable, device is too weak to run it
- ❌ Grand Theft Auto V - Non playable, device is too weak to run it

### iPad Pro M4:

- ✅ Tekken 6 - Playable
- ✅ WRC FIA World Rally Championship - Playable
- ✅ Colin McRae Dirt 2 - Playable
- ✅ Infamous - Playable
- ✅ God Of War 3 - Playable 
- ☑️ Grand Theft Auto IV - Running, low FPS 
- ✅ Grand Theft Auto V - Playable, screen flickering from RPCS3 core


## Credits
- [RPCS3](https://github.com/rpcs3/rpcs3) - Emulator's Core
- [ARMSX3](https://github.com/ARMSX2/ARMSX3/) - ARM64 CPU optimizations
- [StikDebug](https://github.com/StikDebug/StikDebug) - For making JIT 26 possible
- [UTM](https://github.com/utmapp/UTM), [Amethyst](https://github.com/AngelAuraMC/Amethyst-iOS), MeloNX - For JIT implementation samples
- Everyone involved into iOS emulation scene
- Special thanks to MeloNX community helping me to test games