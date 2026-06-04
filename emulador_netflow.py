import socket
import struct
import time
import random

# Configuración hacia tu contenedor Telegraf
COLLECTOR_IP = "127.0.0.1"
COLLECTOR_PORT = 2055

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def generar_flujo_netflow():
    # 1. CABECERA NetFlow v5 (24 bytes)
    version = 5
    count = 1 # Enviamos 1 registro por paquete
    sys_uptime = int(time.monotonic() * 1000)
    unix_secs = int(time.time())
    unix_nsecs = 0
    flow_sequence = random.randint(1, 1000)
    engine_type = 0
    engine_id = 0
    sampling_interval = 0

    # Empaquetado binario de la cabecera (! = Network Big-Endian)
    header = struct.pack('!HHIIIIBBH', version, count, sys_uptime, unix_secs, 
                         unix_nsecs, flow_sequence, engine_type, engine_id, sampling_interval)

    # 2. REGISTRO DE DATOS (48 bytes)
    # Simulamos IPs aleatorias de una red local a internet
    ip_origen = f"192.168.1.{random.randint(10, 50)}"
    ip_destino = f"8.8.8.{random.randint(8, 10)}"
    
    srcaddr = struct.unpack("!I", socket.inet_aton(ip_origen))[0]
    dstaddr = struct.unpack("!I", socket.inet_aton(ip_destino))[0]
    nexthop = 0
    snmp_in = 1
    snmp_out = 2
    dPkts = random.randint(5, 500)             # Paquetes simulados
    dOctets = dPkts * random.randint(64, 1500) # Bytes simulados
    first = sys_uptime - 1000
    last = sys_uptime
    srcport = random.randint(1024, 65535)      # Puerto origen aleatorio
    dstport = 443                              # Puerto destino (HTTPS)
    pad1 = 0
    tcp_flags = 27                             # Banderas TCP (SYN, ACK)
    prot = 6                                   # Protocolo TCP
    tos = 0
    src_as = 0
    dst_as = 0
    src_mask = 0
    dst_mask = 0
    pad2 = 0

    # Empaquetado binario del registro
    record = struct.pack('!IIIHHIIIIHHBBBBHHBBH',
        srcaddr, dstaddr, nexthop, snmp_in, snmp_out, dPkts, dOctets,
        first, last, srcport, dstport, pad1, tcp_flags, prot, tos,
        src_as, dst_as, src_mask, dst_mask, pad2
    )

    # Unir cabecera + registro y enviar por UDP
    packet = header + record
    sock.sendto(packet, (COLLECTOR_IP, COLLECTOR_PORT))
    print(f"[+] Flujo inyectado: {dPkts} paquetes / {dOctets} bytes | Origen: {ip_origen}:{srcport} -> Destino: {ip_destino}:{dstport}")

if __name__ == "__main__":
    print("=== Emulador de Tráfico NetFlow v5 (Software Libre) ===")
    print(f"Inyectando tráfico a Telegraf en {COLLECTOR_IP}:{COLLECTOR_PORT}...")
    try:
        while True:
            generar_flujo_netflow()
            # Inyecta un flujo aleatorio cada 1 segundo
            time.sleep(1) 
    except KeyboardInterrupt:
        print("\nEmulación detenida exitosamente.")
