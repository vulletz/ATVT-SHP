#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulador de red heterogénea para prototipo de telemetría.

Objetivo:
- Simular tráfico de red en una facultad con varios edificios.
- Representar equipos de distintos fabricantes: Cisco, TP-Link, Ubiquiti,
  Steren, Huawei y Netgear.
- Normalizar la información en una tabla común en ClickHouse.
- Permitir visualización en Grafana por edificio, piso, IP, hostname,
  fabricante, aplicación y estado.

No genera NetFlow binario real. Genera eventos normalizados equivalentes
para validar la arquitectura de observabilidad del prototipo.
"""

import argparse
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

CLICKHOUSE_HOST = "127.0.0.1"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "telegraf"
CLICKHOUSE_PASSWORD = "admin123"

DATABASE = "telemetria"
TABLE = "trafico_red"


# ==========================================================
# MODELO DE RED
# ==========================================================

EDIFICIOS = {
    "A": {
        "subred": "192.168.10",
        "pisos": [1, 2, 3],
        "descripcion": "Edificio A - Aulas y oficinas administrativas",
    },
    "B": {
        "subred": "192.168.20",
        "pisos": [1, 2, 3],
        "descripcion": "Edificio B - Laboratorios",
    },
    "C": {
        "subred": "192.168.30",
        "pisos": [1, 2],
        "descripcion": "Edificio C - Posgrado y docentes",
    },
    "D": {
        "subred": "192.168.40",
        "pisos": [1, 2],
        "descripcion": "Edificio D - Servicios generales",
    },
    "ADMIN": {
        "subred": "192.168.50",
        "pisos": [1],
        "descripcion": "Área administrativa",
    },
    "LAB": {
        "subred": "192.168.60",
        "pisos": [1, 2],
        "descripcion": "Laboratorios especializados",
    },
}


FABRICANTES = {
    "Cisco": {
        "modelos": ["Catalyst 2960", "Catalyst 3560", "ISR 4331"],
        "tipos": ["Switch Core", "Switch Distribución", "Router"],
        "detalle_telemetria": "alto",
        "protocolos": ["SNMPv3", "NetFlow/IPFIX"],
        "confiabilidad": 0.98,
    },
    "Huawei": {
        "modelos": ["S5720", "AR1220", "S5735"],
        "tipos": ["Switch Distribución", "Router"],
        "detalle_telemetria": "alto",
        "protocolos": ["SNMPv3", "NetStream/IPFIX"],
        "confiabilidad": 0.97,
    },
    "Ubiquiti": {
        "modelos": ["UniFi AP AC Pro", "UniFi Switch 24", "EdgeRouter X"],
        "tipos": ["Access Point", "Switch Acceso", "Router"],
        "detalle_telemetria": "medio",
        "protocolos": ["SNMP", "API/Controller"],
        "confiabilidad": 0.95,
    },
    "TP-Link": {
        "modelos": ["TL-SG1024", "Archer C6", "EAP225"],
        "tipos": ["Switch Acceso", "Router SOHO", "Access Point"],
        "detalle_telemetria": "medio",
        "protocolos": ["SNMP básico", "Web UI"],
        "confiabilidad": 0.92,
    },
    "Netgear": {
        "modelos": ["GS724T", "JGS524E", "Nighthawk R7000"],
        "tipos": ["Switch Acceso", "Router SOHO"],
        "detalle_telemetria": "medio",
        "protocolos": ["SNMP básico"],
        "confiabilidad": 0.93,
    },
    "Steren": {
        "modelos": ["COM-860", "COM-818", "Repetidor WiFi"],
        "tipos": ["Extensor WiFi", "Router SOHO"],
        "detalle_telemetria": "bajo",
        "protocolos": ["ICMP", "Web UI básica"],
        "confiabilidad": 0.85,
    },
}


APLICACIONES = [
    {
        "nombre": "Plataforma Educativa",
        "destinos": ["148.224.10.10", "148.224.10.11"],
        "puerto": 443,
        "protocolo": "TCP",
        "criticidad": "alta",
        "peso": 18,
    },
    {
        "nombre": "Videoconferencia",
        "destinos": ["172.217.14.110", "142.250.72.14"],
        "puerto": 443,
        "protocolo": "UDP",
        "criticidad": "alta",
        "peso": 14,
    },
    {
        "nombre": "YouTube",
        "destinos": ["142.250.72.206", "172.217.14.238"],
        "puerto": 443,
        "protocolo": "TCP",
        "criticidad": "media",
        "peso": 12,
    },
    {
        "nombre": "Correo Institucional",
        "destinos": ["142.251.35.109", "142.250.190.77"],
        "puerto": 993,
        "protocolo": "TCP",
        "criticidad": "alta",
        "peso": 10,
    },
    {
        "nombre": "DNS",
        "destinos": ["8.8.8.8", "1.1.1.1"],
        "puerto": 53,
        "protocolo": "UDP",
        "criticidad": "alta",
        "peso": 8,
    },
    {
        "nombre": "Actualizaciones",
        "destinos": ["20.189.173.1", "13.107.246.45"],
        "puerto": 443,
        "protocolo": "TCP",
        "criticidad": "media",
        "peso": 7,
    },
    {
        "nombre": "Redes Sociales",
        "destinos": ["157.240.6.35", "31.13.94.35"],
        "puerto": 443,
        "protocolo": "TCP",
        "criticidad": "baja",
        "peso": 8,
    },
    {
        "nombre": "Descarga Masiva",
        "destinos": ["151.101.1.140", "185.199.108.133"],
        "puerto": 443,
        "protocolo": "TCP",
        "criticidad": "baja",
        "peso": 4,
    },
]


ESTADOS = ["UP", "DEGRADADO", "SATURADO", "CAIDO"]


# ==========================================================
# UTILIDADES CLICKHOUSE
# ==========================================================

def clickhouse_url(query=None):
    base = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"

    params = {
        "user": CLICKHOUSE_USER,
        "password": CLICKHOUSE_PASSWORD,
    }

    if query is not None:
        params["query"] = query

    return base + "?" + urllib.parse.urlencode(params)

def ejecutar_clickhouse(query):
    data = query.encode("utf-8")
    req = urllib.request.Request(
        url=clickhouse_url(),
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")

def crear_tabla():
    ejecutar_clickhouse(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

    query = f"""
    CREATE TABLE IF NOT EXISTS {DATABASE}.{TABLE}
    (
        timestamp DateTime,
        fabricante String,
        modelo String,
        tipo_dispositivo String,
        protocolo_telemetria String,
        nivel_detalle String,

        edificio String,
        piso UInt8,
        hostname String,
        ip_dispositivo IPv4,
        mac String,

        ip_origen IPv4,
        ip_destino IPv4,
        puerto_destino UInt16,
        protocolo String,
        aplicacion String,
        criticidad String,

        bytes UInt64,
        paquetes UInt64,
        latencia_ms Float32,
        perdida_pct Float32,
        errores UInt32,

        estado String,
        severidad String,
        descripcion_evento String
    )
    ENGINE = MergeTree
    ORDER BY (timestamp, edificio, hostname, aplicacion)
    """
    ejecutar_clickhouse(query)


def insertar_eventos(eventos):
    if not eventos:
        return

    query = f"INSERT INTO {DATABASE}.{TABLE} FORMAT JSONEachRow"
    payload = "\n".join(json.dumps(e, ensure_ascii=False) for e in eventos)

    req = urllib.request.Request(
        url=clickhouse_url(query),
        data=payload.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()

    except urllib.error.HTTPError as e:
        print("\n[!] ClickHouse rechazó el INSERT")
        print(f"[!] Código HTTP: {e.code}")
        print("[!] Respuesta de ClickHouse:")
        print(e.read().decode("utf-8", errors="replace"))
        print("\n[!] Primer evento que se intentó insertar:")
        print(json.dumps(eventos[0], indent=2, ensure_ascii=False))
        raise

# ==========================================================
# GENERACIÓN DE INVENTARIO
# ==========================================================

def generar_mac(indice):
    return f"02:00:00:{(indice // 65536) % 256:02x}:{(indice // 256) % 256:02x}:{indice % 256:02x}"


def generar_inventario():
    inventario = []
    indice = 1

    for edificio, info in EDIFICIOS.items():
        subred = info["subred"]

        # Equipos de infraestructura por edificio
        for piso in info["pisos"]:
            for _ in range(random.randint(3, 6)):
                fabricante = random.choices(
                    list(FABRICANTES.keys()),
                    weights=[22, 16, 18, 16, 14, 8],
                    k=1
                )[0]

                perfil = FABRICANTES[fabricante]
                modelo = random.choice(perfil["modelos"])
                tipo = random.choice(perfil["tipos"])

                host_id = random.randint(2, 49)
                ip = f"{subred}.{host_id}"

                hostname = f"{tipo.upper().replace(' ', '-')}-{fabricante.upper()}-{edificio}-P{piso}-{indice:03d}"

                inventario.append({
                    "fabricante": fabricante,
                    "modelo": modelo,
                    "tipo_dispositivo": tipo,
                    "protocolo_telemetria": random.choice(perfil["protocolos"]),
                    "nivel_detalle": perfil["detalle_telemetria"],
                    "confiabilidad": perfil["confiabilidad"],
                    "edificio": edificio,
                    "piso": piso,
                    "hostname": hostname,
                    "ip_dispositivo": ip,
                    "mac": generar_mac(indice),
                })

                indice += 1

        # Hosts finales simulados: PCs, laptops, impresoras, cámaras
        for host_num in range(50, 90):
            piso = random.choice(info["pisos"])
            tipo_final = random.choice(["PC", "Laptop", "Impresora", "Cámara IP", "Smartphone"])
            ip = f"{subred}.{host_num}"

            inventario.append({
                "fabricante": "ClienteFinal",
                "modelo": tipo_final,
                "tipo_dispositivo": tipo_final,
                "protocolo_telemetria": "Derivado por flujo",
                "nivel_detalle": "derivado",
                "confiabilidad": 0.90,
                "edificio": edificio,
                "piso": piso,
                "hostname": f"{tipo_final.upper().replace(' ', '-')}-{edificio}-P{piso}-{host_num}",
                "ip_dispositivo": ip,
                "mac": generar_mac(indice),
            })

            indice += 1

    return inventario


# ==========================================================
# NORMALIZACIÓN / SIMULACIÓN DE TRÁFICO
# ==========================================================

def elegir_aplicacion():
    pesos = [app["peso"] for app in APLICACIONES]
    return random.choices(APLICACIONES, weights=pesos, k=1)[0]


def calcular_estado(dispositivo, bytes_generados, errores, perdida_pct):
    confiabilidad = dispositivo["confiabilidad"]

    # Probabilidad de falla más alta en equipos de menor confiabilidad.
    prob_falla = 1.0 - confiabilidad

    if random.random() < prob_falla * 0.08:
        return "CAIDO", "critica", "Dispositivo sin respuesta o caída simulada"

    if bytes_generados > 8_000_000 or perdida_pct > 8:
        return "SATURADO", "alta", "Saturación de enlace o pérdida elevada"

    if errores > 25 or perdida_pct > 3:
        return "DEGRADADO", "media", "Incremento de errores o pérdida moderada"

    return "UP", "normal", "Operación normal"


def generar_evento(inventario):
    dispositivo = random.choice(inventario)
    app = elegir_aplicacion()

    destino = random.choice(app["destinos"])
    paquetes = random.randint(10, 4000)

    # El tamaño cambia según aplicación.
    if app["nombre"] in ["Videoconferencia", "YouTube", "Descarga Masiva"]:
        bytes_generados = paquetes * random.randint(700, 1500)
    elif app["nombre"] in ["DNS"]:
        bytes_generados = paquetes * random.randint(60, 160)
    else:
        bytes_generados = paquetes * random.randint(200, 1000)

    # Simular que ciertos edificios/laboratorios tienen más carga.
    if dispositivo["edificio"] in ["B", "LAB"]:
        bytes_generados = int(bytes_generados * random.uniform(1.2, 2.5))

    # Simular que equipos SOHO o extensores tienen más pérdida/errores.
    fabricante = dispositivo["fabricante"]
    if fabricante in ["Steren", "TP-Link"]:
        perdida_pct = round(random.uniform(0, 8), 2)
        errores = random.randint(0, 45)
        latencia = round(random.uniform(10, 120), 2)
    elif fabricante in ["Ubiquiti", "Netgear"]:
        perdida_pct = round(random.uniform(0, 4), 2)
        errores = random.randint(0, 25)
        latencia = round(random.uniform(5, 80), 2)
    elif fabricante in ["Cisco", "Huawei"]:
        perdida_pct = round(random.uniform(0, 2), 2)
        errores = random.randint(0, 10)
        latencia = round(random.uniform(2, 40), 2)
    else:
        perdida_pct = round(random.uniform(0, 5), 2)
        errores = random.randint(0, 20)
        latencia = round(random.uniform(5, 90), 2)

    estado, severidad, descripcion = calcular_estado(
        dispositivo,
        bytes_generados,
        errores,
        perdida_pct
    )

    evento = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "fabricante": dispositivo["fabricante"],
        "modelo": dispositivo["modelo"],
        "tipo_dispositivo": dispositivo["tipo_dispositivo"],
        "protocolo_telemetria": dispositivo["protocolo_telemetria"],
        "nivel_detalle": dispositivo["nivel_detalle"],

        "edificio": dispositivo["edificio"],
        "piso": dispositivo["piso"],
        "hostname": dispositivo["hostname"],
        "ip_dispositivo": dispositivo["ip_dispositivo"],
        "mac": dispositivo["mac"],

        "ip_origen": dispositivo["ip_dispositivo"],
        "ip_destino": destino,
        "puerto_destino": app["puerto"],
        "protocolo": app["protocolo"],
        "aplicacion": app["nombre"],
        "criticidad": app["criticidad"],

        "bytes": bytes_generados,
        "paquetes": paquetes,
        "latencia_ms": latencia,
        "perdida_pct": perdida_pct,
        "errores": errores,

        "estado": estado,
        "severidad": severidad,
        "descripcion_evento": descripcion,
    }

    return evento


# ==========================================================
# EJECUCIÓN
# ==========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Simulador de red heterogénea para ClickHouse/Grafana"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=20,
        help="Cantidad de eventos por ciclo de inserción"
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=2.0,
        help="Segundos entre cada lote de eventos"
    )
    parser.add_argument(
        "--solo-crear-tabla",
        action="store_true",
        help="Solo crea la base y tabla en ClickHouse"
    )
    args = parser.parse_args()

    print("=== Simulador de Red Heterogénea - Prototipo de Telemetría ===")
    print(f"ClickHouse: http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
    print(f"Tabla destino: {DATABASE}.{TABLE}")

    print("[+] Creando/verificando base de datos y tabla...")
    crear_tabla()

    if args.solo_crear_tabla:
        print("[+] Tabla creada/verificada correctamente.")
        return

    inventario = generar_inventario()
    print(f"[+] Inventario simulado generado: {len(inventario)} dispositivos")
    print("[+] Iniciando generación de tráfico. Presiona Ctrl+C para detener.\n")

    total = 0

    try:
        while True:
            eventos = [generar_evento(inventario) for _ in range(args.batch)]
            insertar_eventos(eventos)
            total += len(eventos)

            muestra = eventos[0]
            print(
                f"[+] Insertados {len(eventos)} eventos | total={total} | "
                f"{muestra['edificio']} | {muestra['hostname']} | "
                f"{muestra['aplicacion']} | {muestra['bytes']} bytes | "
                f"{muestra['estado']}"
            )

            time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\n[+] Simulación detenida por el usuario.")
        print(f"[+] Total de eventos insertados: {total}")


if __name__ == "__main__":
    main()
