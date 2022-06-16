import json,configparser
from pathlib import Path
from proxmoxer import ProxmoxAPI


def getHost(host,cfg):
    proxmox = ProxmoxAPI(
        host, verify_ssl=False,
        user= cfg.get(host,'user'),
        token_name= cfg.get(host,'token_name'),
        token_value= cfg.get(host,'token_value')
    )
    r = {}
    for node in proxmox.nodes.get():
        n = json.loads(json.dumps(node))
        r['Proxmox Name'] = n["node"]
        r['Status'] = n["status"]
        r['VMs'] = []
        for vm in proxmox.nodes(n["node"]).qemu.get():
            #print ("{0}. {1} => {2}".format(vm["vmid"], vm["name"], vm["status"]))
            r['VMs'].append(dict({'VM id':vm["vmid"], 'VM name': vm["name"],'VM stato': vm["status"]}))
        return r

def main(config_file):
    l = []
    file = Path(Path.cwd() / CONFIG_DIR / PRODUCTION_FILE)
    cfg = getConfig(config_file= config_file)
    
    for host in cfg.sections():
        l.append(getHost(host,cfg))
    with open(file, 'w') as f:
        json.dump(l, f)
    pass

def appConfig():
    file = Path(Path.cwd() / 'app-config.ini')
    if(not file.exists() or not file.is_file()):
        file.touch(exist_ok = False)
        cfg = configparser.ConfigParser()
        cfg.optionxform = lambda option: option
        cfg.read(file)
        cfg.set('DEFAULT','CONFIG_DIR','personal_data')
        cfg.set('DEFAULT','ERROR_DIR','personal_data/err')
        cfg.set('DEFAULT','LOG_DIR','personal_data/log')
        cfg.set('DEFAULT','ROTATION_LOG','2')
        with open(file, 'w') as f:
            cfg.write(f)

    cfg = configparser.ConfigParser()
    cfg.read(file)
    return cfg
pass

def getConfig(config_file = 'config.ini'):
    file = Path(Path.cwd() / CONFIG_DIR / config_file)
    if(not file.exists() or not file.is_file()):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch(exist_ok = False)
    cfg = configparser.ConfigParser()
    cfg.read(file)
    return cfg
pass

#TODO backup
#TODO LOG e ERR

if __name__ == "__main__":
    appcfg = appConfig()
    CONFIG_DIR = appcfg.get('DEFAULT','CONFIG_DIR',fallback='personal_data')
    ERROR_DIR = appcfg.get('DEFAULT','ERROR_DIR',fallback='personal_data/err')
    LOG_DIR = appcfg.get('DEFAULT','LOG_DIR',fallback='personal_data/log')
    ROTATION_LOG = appcfg.get('DEFAULT','ROTATION_LOG',fallback='7')
    PROXMON_INI = appcfg.get('DEFAULT','PROXMOX_LIST',fallback='config.ini')
    PRODUCTION_FILE = appcfg.get('DEFAULT','PRODUCTION_FILE',fallback='list-server.json')
    main(PROXMON_INI)