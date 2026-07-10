import asyncio
import warnings
warnings.filterwarnings('ignore', message="The 'pysnmp-lextudio' package is deprecated")
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

OID_SYSNAME = '1.3.6.1.2.1.1.5.0'
OID_SYSDESCR = '1.3.6.1.2.1.1.1.0'
OID_CLIENTES_2G = '1.3.6.1.4.1.41112.1.4.1.1.4'
OID_CLIENTES_5G = '1.3.6.1.4.1.41112.1.4.2.1.4'

async def _check_one(ip, comunidade):
    online = False
    nome = ''
    modelo = ''
    clientes_2g = 0
    clientes_5g = 0
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(comunidade),
            UdpTransportTarget((ip, 161), timeout=3, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(OID_SYSNAME)),
            ObjectType(ObjectIdentity(OID_SYSDESCR)),
            ObjectType(ObjectIdentity(OID_CLIENTES_2G)),
            ObjectType(ObjectIdentity(OID_CLIENTES_5G))
        )
        if not errorIndication and not errorStatus:
            online = True
            for name, val in varBinds:
                oid = str(name)
                if oid == OID_SYSNAME:
                    nome = str(val)
                elif oid == OID_SYSDESCR:
                    modelo = str(val)
                elif oid == OID_CLIENTES_2G:
                    clientes_2g = int(val)
                elif oid == OID_CLIENTES_5G:
                    clientes_5g = int(val)
    except:
        pass
    return online, nome, modelo, clientes_2g, clientes_5g

def verificar_wifi_snmp(dispositivos):
    async def check_all():
        return await asyncio.gather(
            *[_check_one(d['ip'], d['comunidade_snmp']) for d in dispositivos]
        )
    return asyncio.run(check_all())
