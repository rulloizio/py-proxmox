# py-proxmox
An API wrapper to proxmox VE


###Install 
pip install -r requirements.txt

on first launch script create an "app-config.ini" with default variables for application: 
- a CONFIG_DIR: relative path to directory with all app production's file
- an ERROR_DIR: relative path to directory with all errors logs files
- a LOG_DIR: relative path to directory with all logs files
- a ROTATION_LOG: day's number to exclude from error and log rotation
- a PROXMOX_LIST file name with proxmox serer configurazion

Using header.txt, body.txt, footer.txt with class string.Template we can crate a message to send by email
