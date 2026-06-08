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
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

CLICKHOUSE_HOST = "127.0.0.1"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "telegraf"
CLICKHOUSE_PASSWORD = "admin123"

DATABASE = "telemetria"
TABLE = "trafico_red"
INVENTORY_TABLE = "inventario_red"

# ==========================================================
# MODELO DE RED
# ==========================================================

EDIFICIOS = {
    "A": {
        "subred": "192.168.10",
        "pisos": [1, 2, 3],
        "descripcion": "Edificio A - Laboratorios, aulas y departamentos administrativos",
    },
    "B": {
        "subred": "192.168.20",
        "pisos": [1, 2, 3],
        "descripcion": "Edificio B - Laboratorios, dirección, servicios escolares y áreas académicas",
    },
    "C": {
        "subred": "192.168.30",
        "pisos": [1, 2],
        "descripcion": "Edificio C - Laboratorio, aulas y simulación gerencial",
    },
    "D": {
        "subred": "192.168.40",
        "pisos": [1, 2],
        "descripcion": "Edificio D - Aulas y servicios administrativos",
    },
}

AREAS_FCA = {
    "A": [
        {"nombre": "Laboratorio A", "codigo": "LABA", "categoria": "Laboratorio", "tipo": "islas", "islas": {"I1": 30, "I2": 30, "I3": 20}},
        {"nombre": "Salón", "codigo": "AULA", "categoria": "Aula", "tipo": "salones", "prefijo": "A", "inicio": 1, "fin": 43, "equipos_por_salon": 1},
        {"nombre": "Administración", "codigo": "A", "categoria": "Departamento", "tipo": "departamento", "equipos": 3},
        {"nombre": "Departamento de Psicología", "codigo": "PSI", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
        {"nombre": "Departamento de Equidad de Género", "codigo": "EG", "categoria": "Departamento", "tipo": "departamento", "equipos": 1},
        {"nombre": "Enfermería", "codigo": "ENF", "categoria": "Servicio", "tipo": "departamento", "equipos": 1},
        {"nombre": "Cafetería", "codigo": "CAF", "categoria": "Servicio", "tipo": "departamento", "equipos": 2},
        {"nombre": "Departamento de Ayuda Fiscal", "codigo": "AF", "categoria": "Departamento", "tipo": "departamento", "equipos": 6},
        {"nombre": "Módulo Seguridad Universitaria", "codigo": "MSU", "categoria": "Seguridad", "tipo": "departamento", "equipos": 1},
        {"nombre": "Consejería y Sociedad", "codigo": "CS", "categoria": "Departamento", "tipo": "departamento", "equipos": 1},
        {"nombre": "Responsabilidad Social y Sustentabilidad", "codigo": "RSS", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
        {"nombre": "Salas de Titulación", "codigo": "ST", "categoria": "Sala", "tipo": "sin_equipos", "salas": 3},
    ],
    "B": [
        {"nombre": "Salón Multimedia", "codigo": "SM", "categoria": "Aula multimedia", "tipo": "salones", "prefijo": "SM", "inicio": 1, "fin": 3, "equipos_por_salon": 1},
        {"nombre": "Estancia de Maestros", "codigo": "EM", "categoria": "Cubículo", "tipo": "salones", "prefijo": "EM", "inicio": 1, "fin": 47, "equipos_por_salon": 1},
        {"nombre": "Sala Interactiva", "codigo": "SI", "categoria": "Sala", "tipo": "salones", "prefijo": "SI", "inicio": 1, "fin": 1, "equipos_por_salon": 1},
        {"nombre": "Laboratorio B", "codigo": "LABB", "categoria": "Laboratorio", "tipo": "islas", "islas": {"I1": 30, "I2": 30, "I3": 30}},
        {"nombre": "Sala de Consejo", "codigo": "SC", "categoria": "Sala", "tipo": "sin_equipos", "salas": 1},
        {"nombre": "Departamento de Titulación", "codigo": "TIT", "categoria": "Departamento", "tipo": "departamento", "equipos": 3},
        {"nombre": "Dirección", "codigo": "DIR", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
        {"nombre": "Servicios Escolares", "codigo": "SE", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
        {"nombre": "Secretaría Académica", "codigo": "SA", "categoria": "Departamento", "tipo": "departamento", "equipos": 3},
        {"nombre": "Secretaría General", "codigo": "SG", "categoria": "Departamento", "tipo": "departamento", "equipos": 5},
        {"nombre": "Procesamiento de Datos", "codigo": "PD", "categoria": "TI", "tipo": "departamento", "equipos": 2},
        {"nombre": "Formación Integral", "codigo": "FI", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
        {"nombre": "Ventanillas", "codigo": "VEN", "categoria": "Atención", "tipo": "departamento", "equipos": 4},
        {"nombre": "Aula Magna", "codigo": "AM", "categoria": "Auditorio", "tipo": "sin_equipos", "salas": 1},
    ],
    "C": [
        {"nombre": "Laboratorio C", "codigo": "LABC", "categoria": "Laboratorio", "tipo": "islas", "islas": {"I1": 30}},
        {"nombre": "Salón", "codigo": "AULA", "categoria": "Aula", "tipo": "salones", "prefijo": "C", "inicio": 1, "fin": 11, "equipos_por_salon": 1},
        {"nombre": "Sala de Simulación Gerencial", "codigo": "SSG", "categoria": "Sala especializada", "tipo": "departamento", "equipos": 6},
    ],
    "D": [
        {"nombre": "Salón", "codigo": "AULA", "categoria": "Aula", "tipo": "salones", "prefijo": "D", "inicio": 0, "fin": 12, "equipos_por_salon": 1},
        {"nombre": "Librería", "codigo": "LIB", "categoria": "Servicio", "tipo": "departamento", "equipos": 2},
        {"nombre": "Servicio Social", "codigo": "SS", "categoria": "Departamento", "tipo": "departamento", "equipos": 3},
        {"nombre": "Tesorería", "codigo": "TES", "categoria": "Departamento", "tipo": "departamento", "equipos": 2},
    ],
}

DNS_INSTITUCIONALES = [
    "10.128.131.10",
    "148.224.251.130",
    "148.224.17.25",
    "148.224.17.26",
]

SSIDS = [
    {
        "ssid": "UASLP-Alumnos",
        "categoria": "WiFi Alumnos",
        "cantidad_ap": 5,
        "peso_trafico": 1.8,
        "segmento": "WiFi-Alumnos",
    },
    {
        "ssid": "UASLP-Academicos",
        "categoria": "WiFi Académicos",
        "cantidad_ap": 5,
        "peso_trafico": 1.2,
        "segmento": "WiFi-Academicos",
    },
    {
        "ssid": "UASLP-Administrativos",
        "categoria": "WiFi Administrativos",
        "cantidad_ap": 5,
        "peso_trafico": 1.0,
        "segmento": "WiFi-Administrativos",
    },
]

AP_DEPARTAMENTALES = {
    "TP-Link": ["EAP225", "EAP245", "Archer C6", "TL-WA901N"],
    "Steren": ["COM-818", "COM-860", "Repetidor WiFi"],
    "Netgear": ["WAX214", "WAC104", "EX6120"],
    "Ubiquiti": ["UniFi AP AC Lite", "UniFi AP AC Pro"],
    "Huawei": ["AP2050DN", "AP4050DN"],
}

FABRICANTES = {
    "Cisco": {
        "modelos": ["Catalyst 2960", "Catalyst 3560", "ISR 4331", "AIR-AP2802E-A-K9"],
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
        "destinos": DNS_INSTITUCIONALES,
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
        area String,
        codigo_area String,
        categoria_area String,
        isla String,
        ssid String,
        segmento_red String,
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

def crear_tabla_inventario():
    query = f"""
    CREATE TABLE IF NOT EXISTS {DATABASE}.{INVENTORY_TABLE}
    (
        timestamp DateTime,
        hostname String,
        ip_dispositivo IPv4,
        mac String,
        edificio String,
        piso UInt8,
        area String,
        codigo_area String,
        categoria_area String,
        tipo_dispositivo String,
        fabricante String,
        modelo String,

        switch_hostname String,
        switch_ip IPv4,
        switch_fabricante String,
        switch_modelo String,
        puerto_switch String,

        tipo_conexion String,
        vlan String,
        ssid String,
        segmento_red String
    )
    ENGINE = ReplacingMergeTree(timestamp)
    ORDER BY (edificio, switch_hostname, puerto_switch, hostname)
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

def insertar_inventario(registros):
    if not registros:
        return

    query = f"INSERT INTO {DATABASE}.{INVENTORY_TABLE} FORMAT JSONEachRow"
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)

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
        print("\n[!] ClickHouse rechazó el INSERT del inventario")
        print(f"[!] Código HTTP: {e.code}")
        print("[!] Respuesta de ClickHouse:")
        print(e.read().decode("utf-8", errors="replace"))
        print("\n[!] Primer registro de inventario:")
        print(json.dumps(registros[0], indent=2, ensure_ascii=False))
        raise

# ==========================================================
# GENERACIÓN DE INVENTARIO
# ==========================================================

def generar_mac(indice):
    return f"02:00:00:{(indice // 65536) % 256:02x}:{(indice // 256) % 256:02x}:{indice % 256:02x}"


def generar_inventario():
    inventario = []
    indice = 1
    ip_usadas = set()

    def siguiente_ip(edificio, rango_inicio=2, rango_fin=254):
        subred = EDIFICIOS[edificio]["subred"]

        # Primero intenta respetar el rango sugerido.
        for host_id in range(rango_inicio, rango_fin + 1):
            ip = f"{subred}.{host_id}"
            if ip not in ip_usadas:
                ip_usadas.add(ip)
                return ip

        # Si el rango sugerido se llena, usa cualquier IP disponible del edificio.
        for host_id in range(2, 255):
            ip = f"{subred}.{host_id}"
            if ip not in ip_usadas:
                ip_usadas.add(ip)
                return ip

        raise RuntimeError(f"No quedan IPs disponibles para el edificio {edificio}")

    def agregar_dispositivo(
        edificio,
        piso,
        area,
        codigo_area,
        categoria_area,
        hostname,
        tipo_dispositivo="PC",
        fabricante="ClienteFinal",
        modelo="Equipo de cómputo",
        protocolo_telemetria="Derivado por flujo",
        nivel_detalle="derivado",
        confiabilidad=0.90,
        isla="N/A",
        ssid="N/A",
        segmento_red="Cableado institucional",
        rango_ip_inicio=50,
        rango_ip_fin=254,
    ):
        nonlocal indice

        ip = siguiente_ip(edificio, rango_ip_inicio, rango_ip_fin)

        inventario.append({
            "fabricante": fabricante,
            "modelo": modelo,
            "tipo_dispositivo": tipo_dispositivo,
            "protocolo_telemetria": protocolo_telemetria,
            "nivel_detalle": nivel_detalle,
            "confiabilidad": confiabilidad,

            "edificio": edificio,
            "piso": piso,
            "area": area,
            "codigo_area": codigo_area,
            "categoria_area": categoria_area,
            "isla": isla,
            "ssid": ssid,
            "segmento_red": segmento_red,

            "hostname": hostname,
            "ip_dispositivo": ip,
            "mac": generar_mac(indice),
        })

        indice += 1

    # 1. Equipos finales por edificio, área, salón, isla, etc.

    for edificio, areas in AREAS_FCA.items():
        pisos = EDIFICIOS[edificio]["pisos"]

        for area in areas:
            tipo = area["tipo"]

            if tipo == "sin_equipos":
                continue

            if tipo == "islas":
                piso = 1

                for isla, cantidad in area["islas"].items():
                    for equipo_num in range(1, cantidad + 1):
                        hostname = f"E{edificio}-{isla}-{equipo_num:02d}"

                        agregar_dispositivo(
                            edificio=edificio,
                            piso=piso,
                            area=area["nombre"],
                            codigo_area=area["codigo"],
                            categoria_area=area["categoria"],
                            hostname=hostname,
                            tipo_dispositivo="PC",
                            fabricante="ClienteFinal",
                            modelo="Equipo de laboratorio",
                            isla=isla,
                            rango_ip_inicio=50,
                            rango_ip_fin=180,
                        )

            elif tipo == "salones":
                for salon_num in range(area["inicio"], area["fin"] + 1):
                    piso = random.choice(pisos)
                    codigo_salon = f"{area['prefijo']}{salon_num}"

                    for equipo_num in range(1, area["equipos_por_salon"] + 1):
                        hostname = f"E{edificio}-{codigo_salon}-{equipo_num:02d}"

                        agregar_dispositivo(
                            edificio=edificio,
                            piso=piso,
                            area=f"{area['nombre']} {codigo_salon}",
                            codigo_area=codigo_salon,
                            categoria_area=area["categoria"],
                            hostname=hostname,
                            tipo_dispositivo="PC",
                            fabricante="ClienteFinal",
                            modelo="Equipo de aula",
                            isla="N/A",
                            rango_ip_inicio=50,
                            rango_ip_fin=220,
                        )

            elif tipo == "departamento":
                piso = random.choice(pisos)

                for equipo_num in range(1, area["equipos"] + 1):
                    hostname = f"E{edificio}-{area['codigo']}-{equipo_num:02d}"

                    tipo_dispositivo = random.choice(["PC", "Laptop", "Impresora"])

                    agregar_dispositivo(
                        edificio=edificio,
                        piso=piso,
                        area=area["nombre"],
                        codigo_area=area["codigo"],
                        categoria_area=area["categoria"],
                        hostname=hostname,
                        tipo_dispositivo=tipo_dispositivo,
                        fabricante="ClienteFinal",
                        modelo=tipo_dispositivo,
                        isla="N/A",
                        rango_ip_inicio=50,
                        rango_ip_fin=230,
                    )

    # 2. Infraestructura cableada por edificio

    for edificio in EDIFICIOS.keys():
        pisos = EDIFICIOS[edificio]["pisos"]

        for n in range(1, 3):
            fabricante = random.choice(["Cisco", "Huawei"])
            perfil = FABRICANTES[fabricante]
            modelo = random.choice(perfil["modelos"])

            agregar_dispositivo(
                edificio=edificio,
                piso=1,
                area="Infraestructura de red",
                codigo_area="CORE",
                categoria_area="Infraestructura",
                hostname=f"E{edificio}-CORE-{n:02d}",
                tipo_dispositivo="Switch Core",
                fabricante=fabricante,
                modelo=modelo,
                protocolo_telemetria=random.choice(perfil["protocolos"]),
                nivel_detalle=perfil["detalle_telemetria"],
                confiabilidad=perfil["confiabilidad"],
                isla="N/A",
                rango_ip_inicio=2,
                rango_ip_fin=20,
            )

        for piso in pisos:
            for n in range(1, 3):
                fabricante = random.choice(["Cisco", "Huawei", "Ubiquiti", "TP-Link", "Netgear"])
                perfil = FABRICANTES[fabricante]
                modelo = random.choice(perfil["modelos"])

                agregar_dispositivo(
                    edificio=edificio,
                    piso=piso,
                    area="Infraestructura de red",
                    codigo_area=f"SWP{piso}",
                    categoria_area="Infraestructura",
                    hostname=f"E{edificio}-SW-P{piso}-{n:02d}",
                    tipo_dispositivo="Switch Acceso",
                    fabricante=fabricante,
                    modelo=modelo,
                    protocolo_telemetria=random.choice(perfil["protocolos"]),
                    nivel_detalle=perfil["detalle_telemetria"],
                    confiabilidad=perfil["confiabilidad"],
                    isla="N/A",
                    rango_ip_inicio=21,
                    rango_ip_fin=49,
                )

    # 3. Access Points institucionales Cisco AIR-AP2802E-A-K9

    edificios_para_ap = ["A", "B", "C", "D"]

    for red in SSIDS:
        for ap_num in range(1, red["cantidad_ap"] + 1):
            edificio = edificios_para_ap[(ap_num - 1) % len(edificios_para_ap)]
            piso = random.choice(EDIFICIOS[edificio]["pisos"])

            agregar_dispositivo(
                edificio=edificio,
                piso=piso,
                area="Cobertura inalámbrica institucional",
                codigo_area="WIFI",
                categoria_area=red["categoria"],
                hostname=f"E{edificio}-AP-CISCO-{red['ssid'].replace('UASLP-', '').upper()}-{ap_num:02d}",
                tipo_dispositivo="Access Point",
                fabricante="Cisco",
                modelo="AIR-AP2802E-A-K9",
                protocolo_telemetria="SNMPv3",
                nivel_detalle="alto",
                confiabilidad=0.97,
                isla="N/A",
                ssid=red["ssid"],
                segmento_red=red["segmento"],
                rango_ip_inicio=181,
                rango_ip_fin=210,
            )

    # 4. Access Points departamentales / SOHO. Mínimo 3 por edificio

    for edificio in EDIFICIOS.keys():
        for ap_local in range(1, 4):
            piso = random.choice(EDIFICIOS[edificio]["pisos"])

            fabricante = random.choice(list(AP_DEPARTAMENTALES.keys()))
            modelo = random.choice(AP_DEPARTAMENTALES[fabricante])
            perfil = FABRICANTES.get(fabricante, FABRICANTES["TP-Link"])

            agregar_dispositivo(
                edificio=edificio,
                piso=piso,
                area="AP departamental",
                codigo_area="APDEP",
                categoria_area="WiFi Departamental",
                hostname=f"E{edificio}-AP-DEP-{fabricante.upper()}-{ap_local:02d}",
                tipo_dispositivo="Access Point SOHO",
                fabricante=fabricante,
                modelo=modelo,
                protocolo_telemetria=random.choice(perfil["protocolos"]),
                nivel_detalle=perfil["detalle_telemetria"],
                confiabilidad=max(0.75, perfil["confiabilidad"] - 0.03),
                isla="N/A",
                ssid=f"Depto-{edificio}-{ap_local}",
                segmento_red="WiFi departamental local",
                rango_ip_inicio=211,
                rango_ip_fin=230,
            )

    # 5. Access Points exteriores para explanada

    for ap_ext in range(1, 4):
        edificio = random.choice(["A", "B", "C", "D"])
        red = random.choice(SSIDS)

        agregar_dispositivo(
            edificio=edificio,
            piso=1,
            area="Explanada",
            codigo_area="EXT",
            categoria_area="WiFi Exterior",
            hostname=f"EXT-AP-CISCO-EXPLANADA-{ap_ext:02d}",
            tipo_dispositivo="Access Point Exterior",
            fabricante="Cisco",
            modelo="AIR-AP2802E-A-K9",
            protocolo_telemetria="SNMPv3",
            nivel_detalle="alto",
            confiabilidad=0.96,
            isla="N/A",
            ssid=red["ssid"],
            segmento_red=red["segmento"],
            rango_ip_inicio=231,
            rango_ip_fin=240,
        )

    return inventario

def generar_topologia_switches(inventario):
    """
    Genera una tabla lógica de conexión entre dispositivos finales/APs
    y switches de acceso/core.

    No representa descubrimiento real LLDP/CDP, sino una simulación de
    topología lógica para validar visualización e inventario.
    """

    timestamp_actual = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    switches_por_edificio = {}
    cores_por_edificio = {}

    for dispositivo in inventario:
        edificio = dispositivo["edificio"]

        if dispositivo["tipo_dispositivo"] == "Switch Acceso":
            switches_por_edificio.setdefault(edificio, []).append(dispositivo)

        if dispositivo["tipo_dispositivo"] == "Switch Core":
            cores_por_edificio.setdefault(edificio, []).append(dispositivo)

    registros = []
    contador_puertos = {}

    def siguiente_puerto(switch_hostname):
        contador_puertos.setdefault(switch_hostname, 0)
        contador_puertos[switch_hostname] += 1
        return f"Gi1/0/{contador_puertos[switch_hostname]}"

    for dispositivo in inventario:
        tipo = dispositivo["tipo_dispositivo"]
        edificio = dispositivo["edificio"]

        # Los switches core no se conectan a sí mismos en esta tabla.
        if tipo == "Switch Core":
            continue

        # Los switches de acceso cuelgan del core.
        if tipo == "Switch Acceso":
            candidatos = cores_por_edificio.get(edificio, [])
            tipo_conexion = "Uplink"
            vlan = "Troncal"
        # Los AP institucionales/exteriores suelen ir a switch de acceso o core.
        elif tipo in ["Access Point", "Access Point Exterior", "Access Point SOHO"]:
            candidatos = switches_por_edificio.get(edificio, []) or cores_por_edificio.get(edificio, [])
            tipo_conexion = "Inalámbrico"
            vlan = dispositivo.get("segmento_red", "WiFi")
        # Equipos finales cableados van a switches de acceso.
        else:
            candidatos = switches_por_edificio.get(edificio, []) or cores_por_edificio.get(edificio, [])
            tipo_conexion = "Cableado"
            vlan = "LAN-Cableada"

        if not candidatos:
            # Fallback por si un edificio queda sin switches por algún bug.
            continue

        # Preferir switches del mismo piso si existen.
        mismos_piso = [
            sw for sw in candidatos
            if sw.get("piso") == dispositivo.get("piso")
        ]

        if mismos_piso:
            switch = random.choice(mismos_piso)
        else:
            switch = random.choice(candidatos)

        puerto = siguiente_puerto(switch["hostname"])

        registros.append({
            "timestamp": timestamp_actual,
            "hostname": dispositivo["hostname"],
            "ip_dispositivo": dispositivo["ip_dispositivo"],
            "mac": dispositivo["mac"],
            "edificio": dispositivo["edificio"],
            "piso": dispositivo["piso"],
            "area": dispositivo["area"],
            "codigo_area": dispositivo["codigo_area"],
            "categoria_area": dispositivo["categoria_area"],
            "tipo_dispositivo": dispositivo["tipo_dispositivo"],
            "fabricante": dispositivo["fabricante"],
            "modelo": dispositivo["modelo"],

            "switch_hostname": switch["hostname"],
            "switch_ip": switch["ip_dispositivo"],
            "switch_fabricante": switch["fabricante"],
            "switch_modelo": switch["modelo"],
            "puerto_switch": puerto,

            "tipo_conexion": tipo_conexion,
            "vlan": vlan,
            "ssid": dispositivo.get("ssid", "N/A"),
            "segmento_red": dispositivo.get("segmento_red", "Cableado institucional"),
        })

    return registros

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

    
    # Simular mayor tráfico en laboratorios entre 08:00 y 15:00.
    hora_actual = datetime.now(ZoneInfo("America/Mexico_City")).hour

    if dispositivo["categoria_area"] == "Laboratorio":
        if 8 <= hora_actual <= 15:
            bytes_generados = int(bytes_generados * random.uniform(2.0, 4.5))
        else:
            bytes_generados = int(bytes_generados * random.uniform(0.8, 1.5))

    # El Edificio B suele concentrar más tráfico por Laboratorio B y áreas administrativas.
    if dispositivo["edificio"] == "B":
        bytes_generados = int(bytes_generados * random.uniform(1.1, 1.8))

    # La red de alumnos suele generar mayor consumo inalámbrico.
    if dispositivo["ssid"] == "UASLP-Alumnos":
        bytes_generados = int(bytes_generados * random.uniform(1.5, 2.8))

    # Simular que equipos SOHO o extensores tienen más pérdida/errores.
    fabricante = dispositivo["fabricante"]
    if dispositivo["tipo_dispositivo"] in ["Access Point SOHO", "Extensor WiFi"] or fabricante in ["Steren", "TP-Link"]:
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
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),        

        "fabricante": dispositivo["fabricante"],
        "modelo": dispositivo["modelo"],
        "tipo_dispositivo": dispositivo["tipo_dispositivo"],
        "protocolo_telemetria": dispositivo["protocolo_telemetria"],
        "nivel_detalle": dispositivo["nivel_detalle"],

        "edificio": dispositivo["edificio"],
        "piso": dispositivo["piso"],
        "area": dispositivo["area"],
        "codigo_area": dispositivo["codigo_area"],
        "categoria_area": dispositivo["categoria_area"],
        "isla": dispositivo["isla"],
        "ssid": dispositivo["ssid"],
        "segmento_red": dispositivo["segmento_red"],

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

    print("[+] Creando/verificando bases de datos y tablas...")
    crear_tabla()
    crear_tabla_inventario()

    if args.solo_crear_tabla:
        print("[+] Tabla creada/verificada correctamente.")
        return

    inventario = generar_inventario()
    print(f"[+] Inventario simulado generado: {len(inventario)} dispositivos")

    topologia = generar_topologia_switches(inventario)
    insertar_inventario(topologia)
    print(f"[+] Topología lógica generada: {len(topologia)} enlaces dispositivo-switch")

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
