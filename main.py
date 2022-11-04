import json,configparser
from string import Template
from pathlib import Path
from proxmoxer import ProxmoxAPI
from proxmoxer import ResourceException

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.
    """

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def inviaMail(errori):
    s = smtplib.SMTP(
        host= appcfg.get('sendMail','MAIL_HOST',fallback = 'localhost'),
        port= appcfg.get('sendMail','MAIL_PORT',fallback = 25))
    if  int(appcfg.get('sendMail','MAIL_USESSL',fallback = 0)):
        s.starttls()
        s.login(
            appcfg.get('sendMail','MAIL_USERNAME'),
            appcfg.get('sendMail','MAIL_PASSWD')
        )

    msg = MIMEMultipart()       # create a message
    message= "\n"
    # add in the actual person name to the message template
    for e in errori:
        if (e['type'] == 'VM'):
            message += message_template_vm.substitute(**e)
            message += "\n"
        else :
            mapping ={'address':e['Address'], 'name':e['Internal Name'], 'status':e['Status']} 
            message += message_template_server.substitute(**mapping)
            message += "\n"

    # setup the parameters of the message
    msg['From'] = appcfg.get('sendMail','MAIL_FROM')
    msg['To'] = appcfg.get('sendMail','MAIL_TO')
    msg['Subject'] = "Errori VM CLOUD "
    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    filename = PRODUCTION_FILE 
    f = open(Path(Path.cwd() / CONFIG_DIR / PRODUCTION_FILE))
    attachment = MIMEText(f.read())
    f.close
    attachment.add_header('Content-Disposition','attachment', filename=filename)
    msg.attach(attachment)

    # send the message via the server set up earlier.
    try:
        s.send_message(msg)
    except Exception as exx:
        print(exx)
    finally:
        del msg
        s.quit()
    pass

def getHost(host,cfg):
    vmtoskip = cfg.get('DEFAULT','vm-to-skip',fallback=[])
    r = {}
    r['Address'] = host
    r['Internal Name'] = cfg.get(host,'INTERNAL_NAME', fallback='non presente')
    skip = cfg.get(host,'SKIP', fallback='0')
    if(skip == '1'):
        r['SKIP'] = 'Controllo disabilitato'
        return r
    #TODO controllo eccezioni
    try:    
        proxmox = ProxmoxAPI(
            host, verify_ssl=False,
            user= cfg.get(host,'user'),
            token_name= cfg.get(host,'token_name'),
            token_value= cfg.get(host,'token_value')
        )
    except ResourceException as err:
        print(err)
        r['Status'] = 'ERRORE'
        r['type'] = 'SERVER'
        return r
    try:
        nodes = proxmox.nodes.get()
    except:
        r['Status'] = 'ERRORE Host non Connesso'
        r['type'] = 'SERVER'
        errori.append(r)
        return r

    for node in nodes:
        n = json.loads(json.dumps(node))
        r['Proxmox Name'] = n["node"]
        r['Status'] = n["status"]
        r['VMs'] = []
        for vm in proxmox.nodes(n["node"]).qemu.get():
            r['VMs'].append(dict({'VM id':vm["vmid"], 'VM name': vm["name"],'VM stato': vm["status"]}))
            if(vm["status"] != 'running' and str(vm["vmid"]) not in vmtoskip):
                errori.append(dict({'id':vm["vmid"], 'name': vm["name"],'stato': vm["status"],'cloud':r['Internal Name'],'type':'VM'}))
    return r

def main(config_file):
    l = []
    file = Path(Path.cwd() / CONFIG_DIR / PRODUCTION_FILE)
    cfg = getConfig(config_file= config_file)
    for host in cfg.sections():
        l.append(getHost(host,cfg))
    with open(file, 'w') as f:
        json.dump(l, f, indent=2, sort_keys=True)
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


if __name__ == "__main__":
    errori = []
    appcfg = appConfig()
    CONFIG_DIR = appcfg.get('DEFAULT','CONFIG_DIR',fallback='personal_data')
    ERROR_DIR = appcfg.get('DEFAULT','ERROR_DIR',fallback='personal_data/err')
    LOG_DIR = appcfg.get('DEFAULT','LOG_DIR',fallback='personal_data/log')
    ROTATION_LOG = appcfg.get('DEFAULT','ROTATION_LOG',fallback='7')
    PROXMON_INI = appcfg.get('DEFAULT','PROXMOX_LIST',fallback='config.ini')
    PRODUCTION_FILE = appcfg.get('DEFAULT','PRODUCTION_FILE',fallback='list-server.json')
    dict_list = main(PROXMON_INI)
    message_template_vm = read_template(Path(Path.cwd() / CONFIG_DIR / 'txterror-vm.txt'))
    message_template_server = read_template(Path(Path.cwd() / CONFIG_DIR / 'txterror-server.txt'))

    if int(appcfg.get('sendMail','ENABLE',fallback = 0) and len(errori)):
        try:
            inviaMail(errori)
        except:
            print("Connessione assente")
    print (errori)
