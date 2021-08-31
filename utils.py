from subprocess import check_output
from xml.etree.ElementTree import fromstring
from ipaddress import IPv4Interface, IPv6Interface

# from https://stackoverflow.com/a/45729633/7394961

def getNics() :

    cmd = 'wmic.exe nicconfig where "IPEnabled  = True" get ipaddress,MACAddress,IPSubnet,DNSHostName,Caption,DefaultIPGateway /format:rawxml'
    xml_text = check_output(cmd, creationflags=8)
    xml_root = fromstring(xml_text)

    nics = []
    keyslookup = {
        'DNSHostName' : 'hostname',
        'IPAddress' : 'ip',
        'IPSubnet' : '_mask',
        'Caption' : 'hardware',
        'MACAddress' : 'mac',
        'DefaultIPGateway' : 'gateway',
    }

    for nic in xml_root.findall("./RESULTS/CIM/INSTANCE") :
        # parse and store nic info
        n = {
            'hostname':'',
            'ip':[],
            '_mask':[],
            'hardware':'',
            'mac':'',
            'gateway':[],
        }
        for prop in nic :
            name = keyslookup[prop.attrib['NAME']]
            if prop.tag == 'PROPERTY':
                if len(prop):
                    for v in prop:
                        n[name] = v.text
            elif prop.tag == 'PROPERTY.ARRAY':
                for v in prop.findall("./VALUE.ARRAY/VALUE") :
                    n[name].append(v.text)
        nics.append(n)

        # creates python ipaddress objects from ips and masks
        for i in range(len(n['ip'])) :
            arg = '%s/%s'%(n['ip'][i],n['_mask'][i])
            if ':' in n['ip'][i] : n['ip'][i] = IPv6Interface(arg)
            else : n['ip'][i] = IPv4Interface(arg)
        del n['_mask']

    return nics



def getIpv4AddressWithAdapter():
    nics = getNics()
    # tempDict:dict[str:str] = {}
    tempList:list[NetworkAdapter] = []
    for nic in nics :
        adapterName = nic['hardware'] 
        ipv4 = str(nic['ip'][0].ip)
        # tempDict[adapterName] = ip
        tempList.append(NetworkAdapter(adapeterName=adapterName,ip=ipv4))
    return tempList


class NetworkAdapter():
    def __init__(self,adapeterName,ip):
        self.adapterName = adapeterName
        self.ip = ip
    
    def getIp(self)->str:
        return self.ip
    
    def getAdapterName(self)->str:
        return self.adapterName
    
    def __str__(self) -> str:
        return "{adapter} {ip}".format(adapter = self.adapterName,ip=self.ip)
    
    def __repr__(self)->str:
        return "{adapter} {ip}".format(adapter = self.adapterName,ip=self.ip)




import re

tcpUrlPattern =  '(?:tcp.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

def getPort(url):
    m = re.search(tcpUrlPattern,url)
    return int(m.group('port'))


def getHost(url):
    m = re.search(tcpUrlPattern,url)
    return m.group('host')

if __name__ == '__main__':
    print(getIpv4AddressWithAdapter())
