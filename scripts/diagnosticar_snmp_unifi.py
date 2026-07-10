import asyncio, warnings, sys
warnings.filterwarnings('ignore')
from pysnmp.hlapi.asyncio import getCmd, nextCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def testar(ip, comunidade):
    print(f"=== Teste SNMP em {ip} comunidade={comunidade} ===\n")

    async def get(oid):
        err, _, _, vb = await getCmd(SnmpEngine(), CommunityData(comunidade), UdpTransportTarget((ip, 161), timeout=3, retries=1), ContextData(), ObjectType(ObjectIdentity(oid)))
        if not err and vb:
            return str(vb[0][1])
        return f"ERRO: {err}"

    async def walk(base_oid):
        results = []
        try:
            async for err, _, _, vb in nextCmd(SnmpEngine(), CommunityData(comunidade), UdpTransportTarget((ip, 161), timeout=3, retries=1), ContextData(), ObjectType(ObjectIdentity(base_oid)), lexicographicMode=True):
                if err: break
                for o, v in vb:
                    results.append((str(o), str(v)))
        except:
            pass
        return results

    # 1. sysName / sysDescr
    print("--- 1. Dados basicos ---")
    for oid, nome in [('1.3.6.1.2.1.1.5.0', 'sysName'), ('1.3.6.1.2.1.1.1.0', 'sysDescr')]:
        r = await get(oid)
        print(f"  {nome} ({oid}): {r}")

    # 2. VAP NumStations
    print("\n--- 2. unifiVapNumStations (1.3.6.1.4.1.41112.1.6.1.2.1.8) ---")
    r = await walk('1.3.6.1.4.1.41112.1.6.1.2.1.8')
    if r:
        for o, v in r: print(f"  {o} = {v}")
    else:
        print("  (vazio ou sem resposta)")

    # 3. VAP Radio
    print("\n--- 3. unifiVapRadio (1.3.6.1.4.1.41112.1.6.1.2.1.9) ---")
    r = await walk('1.3.6.1.4.1.41112.1.6.1.2.1.9')
    if r:
        for o, v in r: print(f"  {o} = {v}")
    else:
        print("  (vazio ou sem resposta)")

    # 4. Tenta arvore unifiRadioTable tb
    print("\n--- 4. unifiRadioTable (1.3.6.1.4.1.41112.1.6.1.1) ---")
    r = await walk('1.3.6.1.4.1.41112.1.6.1.1')
    if r:
        for o, v in r: print(f"  {o} = {v}")
    else:
        print("  (vazio ou sem resposta)")

    # 5. Toda a arvore Ubiquiti
    print("\n--- 5. Arvore completa 1.3.6.1.4.1.41112 ---")
    r = await walk('1.3.6.1.4.1.41112')
    if r:
        for o, v in r[:20]: print(f"  {o} = {v}")
        if len(r) > 20: print(f"  ... e mais {len(r)-20} OIDs")
    else:
        print("  (vazio - SNMP pode estar desabilitado)")

ip = sys.argv[1]
comunidade = sys.argv[2] if len(sys.argv) > 2 else 'public'
asyncio.run(testar(ip, comunidade))
