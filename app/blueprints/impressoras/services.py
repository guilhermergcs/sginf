import asyncio
import warnings
warnings.filterwarnings('ignore', message="The.*pysnmp-lextudio.*deprecated")
from pysnmp.hlapi.asyncio import get_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def _check_one(ip, comunidade):
    online = False
    modelo = ''
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
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
    except Exception:
        pass
    return online, modelo

def verificar_impressoras_snmp(impressoras):
    async def check_all():
        return await asyncio.gather(
            *[_check_one(prt['ip'], prt['comunidade_snmp']) for prt in impressoras]
        )
    return asyncio.run(check_all())
