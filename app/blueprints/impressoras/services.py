import asyncio
import warnings
warnings.filterwarnings('ignore', message="The 'pysnmp-lextudio' package is deprecated")
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def _check_one(ip, comunidade):
    online = False
    modelo = ''
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(comunidade),
            UdpTransportTarget((ip, 161), timeout=3, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        )
        if not errorIndication and not errorStatus:
            online = True
            for name, val in varBinds:
                modelo = str(val)
    except:
        pass
    return online, modelo

def verificar_impressoras_snmp(impressoras):
    async def check_all():
        return await asyncio.gather(
            *[_check_one(prt['ip'], prt['comunidade_snmp']) for prt in impressoras]
        )
    return asyncio.run(check_all())
