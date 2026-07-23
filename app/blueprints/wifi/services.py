import asyncio
import warnings
warnings.filterwarnings('ignore', message="The.*pysnmp-lextudio.*deprecated")
from pysnmp.hlapi.asyncio import get_cmd, walk_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

OID_SYSNAME = '1.3.6.1.2.1.1.5.0'
OID_SYSDESCR = '1.3.6.1.2.1.1.1.0'
OID_VAP_NUMSTATIONS = '1.3.6.1.4.1.41112.1.6.1.2.1.8'
OID_VAP_RADIO = '1.3.6.1.4.1.41112.1.6.1.2.1.9'

async def _check_one(ip, comunidade):
    online = False
    nome = ''
    modelo = ''
    clientes_2g = 0
    clientes_5g = 0
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(comunidade),
            UdpTransportTarget((ip, 161), timeout=3, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(OID_SYSNAME)),
            ObjectType(ObjectIdentity(OID_SYSDESCR))
        )
        if not errorIndication and not errorStatus:
            online = True
            for name, val in varBinds:
                oid = str(name)
                if oid == OID_SYSNAME:
                    nome = str(val)
                elif oid == OID_SYSDESCR:
                    modelo = str(val)
    except Exception:
        pass

    if not online:
        return online, nome, modelo, clientes_2g, clientes_5g

    try:
        stations = {}
        async for errorIndication, errorStatus, errorIndex, varBinds in walk_cmd(
            SnmpEngine(),
            CommunityData(comunidade),
            UdpTransportTarget((ip, 161), timeout=3, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(OID_VAP_NUMSTATIONS)),
            ObjectType(ObjectIdentity(OID_VAP_RADIO))
        ):
            if errorIndication or errorStatus:
                break
            for name, val in varBinds:
                oid = str(name)
                oid_parts = oid.split('.')
                idx = oid_parts[-1]
                base = '.'.join(oid_parts[:-1])
                if base == OID_VAP_NUMSTATIONS:
                    stations[idx] = {'count': int(val), 'band': None}
                elif base == OID_VAP_RADIO:
                    if idx in stations:
                        stations[idx]['band'] = str(val)

        for idx, data in stations.items():
            c = data['count']
            band = data['band']
            if band == 'na':
                clientes_5g += c
            elif band == 'ng':
                clientes_2g += c
            elif '5' in str(band or ''):
                clientes_5g += c
            elif '2' in str(band or ''):
                clientes_2g += c
            else:
                clientes_2g += c
    except Exception:
        pass

    return online, nome, modelo, clientes_2g, clientes_5g

def verificar_wifi_snmp(dispositivos):
    async def check_all():
        return await asyncio.gather(
            *[_check_one(d['ip'], d['comunidade_snmp']) for d in dispositivos]
        )
    return asyncio.run(check_all())
