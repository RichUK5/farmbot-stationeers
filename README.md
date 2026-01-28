# Farmbot-Stationeers

Farmbot Stationeers is a discord bot for managing a Stationeers server. It utilises pycord for discord interaction. It is developed and tested on Ubuntu 24.04, but should be easy to adapt to other operating systems that utilise systemd.

## Features:
- Service management with systemd, including example systemd service files.
- Automatic updating of the code (checks to see if anyone is currently on the server first).
- Executing some in-game commands and returning output to Discord.
- Savegame upload and management (Can stop the server and switch between different savegames).
- A JSON configuration file that can store basic user data, and provide a link between ingame users and discord users.
- A basic permissions system to control who can run which discord command. It supports a range of 0-15, where 0 is no permissions and 15 is full admin.

## Installation:
- Create a linux service user for `stationeers`.
- Create a linux service user for `farmbot-stationeers`, adding to the `stationeers` group (required for updating to work).
- Use steamcmd to install stationeers to `/opt/stationeers`, ensuring that the `stationeers` user and group are the owners.
- Download the repository to `/opt/` (so the full path will be `/opt/farmbot-stationeers/`), ensuring that the `farmbot-stationeers` user and group are the owners.
- Create your python venv (`farmbot-stationeers-env` is the recommended name, as this is already part of the `.gitignore` file).
- Install requirements as per `requirements.txt`.
- Use the `config.example.json` file to create `config.json` with your settings. (`/opt/farmbot-stationeers/config.json`)
- Use the `stationeers.example.service` file to install stationeers as a service within systemd (`/etc/systemd/system/stationeers.service`).
- Use the `farmbot-stationeers.example.service` file to install farmbot-stationeers as a service within systemd (`/etc/systemd/system/farmbot-stationeers.service`)
- Use the `stationeers.sudoers.example` file to allow `farmbot-stationeers` service permissions via sudo. (`/etc/sudoers.d/stationeers`)
- Use the `update.example.py` file to create an `update.py` file. This is executed as part of systemd starting the service. (Default `/opt/stationeers/update.py`)
- Reload daemons in systemd to read the new files (`systemctl daemon-reload`)

## Use:
This is not an exhaustive list of all commands, but a few base features:
- Adjusting a user's permission level
  - Once a user has registered, use `/setfarmbotuserpermissionlevel`

## Possible future features:
- Mod management
- Switching between Stationeers update channels (stable / experimental)
- Uploading and activiating a new save:
  - Run `/uploadnewstationeerssave` and provide the ZIP file.
  - Run `/activatestationeersstashedsave` to load the save. This will stop the server, re-arrange the save files, and start the server again.
- Enabling automatic updates:
  - Run `/enableupdatenotifications` in a channel that you want the update notifications to be posted in.
  - Run `/enableautomaticupdates`.