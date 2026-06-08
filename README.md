# Prototipo de Observabilidad de Red Heterogénea - FCA UASLP

## Implementación de una arquitectura de telemetría y visualización de tráfico basada en herramientas de código abierto

Este repositorio contiene el prototipo funcional desarrollado para la residencia profesional titulada:

> **Implementación de una Arquitectura de Telemetría y Visualización de Tráfico para Redes Heterogéneas basada en Estándares Abiertos**

El proyecto tiene como finalidad validar una arquitectura de observabilidad para una red institucional heterogénea mediante la simulación, normalización, almacenamiento y visualización de eventos de tráfico de red en tiempo real.

---

## 1. Descripción general

La Facultad de Contaduría y Administración de la UASLP cuenta con una infraestructura de red heterogénea, compuesta por equipos de distintas marcas, tecnologías y capacidades de monitoreo. Debido a esta diversidad, resulta necesario contar con una plataforma capaz de centralizar información proveniente de múltiples fuentes y presentarla de manera clara para la toma de decisiones operativas.

Este prototipo implementa un entorno de observabilidad compuesto por:

- **Grafana** para visualización de dashboards.
- **ClickHouse** para almacenamiento y análisis de eventos de tráfico.
- **VictoriaMetrics** para almacenamiento de métricas de series temporales.
- **Telegraf** para recolección de métricas del entorno.
- **Python** para generación de tráfico sintético y simulación de red heterogénea.
- **Docker Compose** para despliegue reproducible del entorno.

La solución permite representar tráfico por edificio, laboratorio, isla, salón, departamento, access point, hostname, IP, fabricante, aplicación y estado operativo.

---

## 2. Objetivo del prototipo

El objetivo de este prototipo es demostrar la viabilidad técnica de una arquitectura de telemetría y visualización de red capaz de:

1. Generar eventos de tráfico representativos de una red institucional.
2. Normalizar información proveniente de equipos heterogéneos.
3. Almacenar eventos de tráfico en una base de datos analítica.
4. Visualizar métricas, anomalías y comportamiento de red en tiempo real.
5. Facilitar la identificación de tráfico por edificio, área, equipo e IP.
6. Servir como base para una futura implementación sobre infraestructura real.

---

## 3. Alcance

Este proyecto corresponde a un **prototipo funcional** o **prueba de concepto**.

El entorno valida la arquitectura de observabilidad utilizando tráfico simulado, sin modificar equipos reales de producción ni intervenir directamente la red institucional.

### Incluye

- Despliegue de servicios mediante Docker Compose.
- Simulación de tráfico de red heterogéneo.
- Inserción de eventos normalizados en ClickHouse.
- Visualización en Grafana.
- Dashboard exportado en formato JSON.
- Segmentación lógica por edificios y áreas.
- Simulación de dispositivos cableados e inalámbricos.
- Simulación de estados operativos: `UP`, `DEGRADADO`, `SATURADO` y `CAIDO`.

### No incluye

- Configuración directa sobre switches o routers reales.
- Activación real de SNMPv3, NetFlow o IPFIX en equipos productivos.
- Descubrimiento automático real mediante LLDP/CDP.
- Monitoreo en producción de usuarios reales.
- Modificación física o lógica de la infraestructura institucional.

---
## 4. Arquitectura general

La arquitectura del prototipo se divide en dos rutas principales:

```text
Simulador Python
        ↓
ClickHouse
        ↓
Grafana
```

y:
```text
Telegraf
        ↓
VictoriaMetrics
        ↓
Grafana
```

#### Flujo principal de tráfico simulado
- El script simulador_red_heterogenea.py genera eventos de tráfico.
- Cada evento contiene información del edificio, área, equipo, IP, aplicación, bytes, paquetes, latencia, pérdida, errores y estado.
- Los datos son enviados mediante HTTP hacia ClickHouse.
- Grafana consulta ClickHouse y presenta la información en dashboards interactivos.
---
## 5. Tecnologías utilizadas

| Tecnología   |      Función dentro del prototipo |
|----------|:-------------|
| Docker |  Contenerización del entorno |
| Docker Compose |    Orquestación local de servicios   |
| Python 3 | Simulación de tráfico de red |
| ClickHouse | Base de datos analítica para eventos de tráfico |
| Grafana | Visualización de dashboards |
| VictoriaMetrics | Almacenamiento de métricas temporales |
| Telegraf | Recolección de métricas del sistema |
| GitHub | Control de versiones y respaldo del proyecto |

---

## 6. Estructura del repositorio
ATVT-SHP/  
├── docker-compose.yml  
├── telegraf.conf  
├── simulador_red_heterogenea.py  
├── dashboards/  
│   └── observabilidad_red_heterogenea_fca_uaslp.json  
├── docs/  
│   └── manuales y documentación futura  
└── README.md  

| Archivos principales   |      Archivo Descripción |
|----------|:-------------|
| docker-compose.yml |  Define los servicios de Grafana, ClickHouse, VictoriaMetrics y Telegraf |
| telegraf.conf |    Configuración de recolección y envío de métricas   |
| simulador_red_heterogenea.py | Script principal de simulación de tráfico |
| dashboards/observabilidad_red_heterogenea_fca_uaslp.json | Dashboard exportado de Grafana |
| README.md | Documentación general del proyecto |

---

## 7. Modelo de simulación

El simulador fue diseñado con base en la distribución física y lógica de la Facultad de Contaduría y Administración.

### Edificios simulados

El tráfico se divide en cuatro edificios principales:

- Edificio A
- Edificio B
- Edificio C
- Edificio D

Cada edificio contiene áreas, laboratorios, salones, departamentos y dispositivos asociados.

#### Inventario lógico dispositivo-switch

El prototipo incluye una tabla adicional llamada `telemetria.inventario_red`, la cual relaciona cada dispositivo simulado con el switch al que se encuentra conectado.

Esta tabla permite identificar:

- Hostname e IP del dispositivo.
- Edificio, piso y área.
- Switch asociado.
- IP del switch.
- Puerto lógico del switch.
- Tipo de conexión.
- VLAN o segmento lógico.
- SSID, cuando aplica.

Esto permite responder preguntas operativas como: “¿en qué switch se encuentra conectado este equipo?” o “¿qué dispositivos dependen de este switch?”.

---

## 8. Distribución lógica simulada
#### Edificio A
Incluye:
- Laboratorio A
- Salones A1 al A43
- Administración
- Departamento de Psicología
- Departamento de Equidad de Género
- Enfermería
- Cafetería
- Departamento de Ayuda Fiscal
- Módulo de Seguridad Universitaria
- Consejería y Sociedad
- Responsabilidad Social y Sustentabilidad
- Salas de titulación

#### Edificio B

Incluye:

- Salones multimedia SM1 al SM3
- Estancia de maestros con cubículos EM1 al EM47
- Sala interactiva SI1
- Laboratorio B
- Sala de consejo
- Departamento de titulación
- Dirección
- Servicios escolares
- Secretaría académica
- Secretaría general
- Procesamiento de datos
- Formación integral
- Ventanillas
- Aula magna

#### Edificio C

Incluye:

- Laboratorio C
- Salones C1 al C11
- Sala de simulación gerencial

#### Edificio D

Incluye:

- Salones D0 al D12
- Librería
- Servicio social
- Tesorería

---

## 9. Nomenclatura de equipos

El simulador utiliza una nomenclatura cercana a la empleada en los laboratorios y áreas internas.

#### Equipos de laboratorio

Formato:

> E<Edificio>-I<Isla>-<Número de equipo>

Ejemplo:

> EB-I1-01

Significa:

> Edificio B - Isla 1 - Equipo 01

#### Equipos de departamentos

Formato:

> E<Edificio>-<Siglas del área>-<Número de equipo>

Ejemplo:

> EA-A-01

Significa:

> Edificio A - Administración - Equipo 01

#### Salones

Ejemplo:

> EB-SM1-01

Significa:

> Edificio B - Salón Multimedia 1 - Equipo 01

#### Access Points

Ejemplos:

> EA-AP-CISCO-ALUMNOS-01  
EB-AP-CISCO-ACADEMICOS-02  
ED-AP-DEP-STEREN-01  
EXT-AP-CISCO-EXPLANADA-03  

---
## 10. Dispositivos simulados

El inventario generado por el script incluye:

- Computadoras de laboratorio
- Equipos de salones
- Equipos departamentales
- Impresoras
- Switches core
- Switches de acceso
- Access Points institucionales
- Access Points departamentales
- Access Points exteriores
- Dispositivos de distintas marcas

#### Fabricantes considerados
- Cisco
- Huawei
- Ubiquiti
- TP-Link
- Netgear
- Steren
- ClienteFinal

---
## 11. Access Points y redes inalámbricas

El simulador contempla redes inalámbricas institucionales y access points departamentales.

#### Access Points institucionales

Los access points institucionales se representan con el modelo:

> Cisco AIR-AP2802E-A-K9

Redes simuladas:

- UASLP-Alumnos
- UASLP-Academicos
- UASLP-Administrativos

También se simulan access points exteriores para cobertura de explanada.

#### Access Points departamentales

Además de la red universitaria, se simulan access points pequeños instalados en áreas departamentales, de marcas como:

- TP-Link
- Steren
- Netgear
- Ubiquiti
- Huawei

---

## 12. DNS institucionales simulados

El tráfico DNS generado por el simulador utiliza los siguientes servidores:
```text
10.128.131.10
148.224.251.130
148.224.17.25
148.224.17.26
```

Estos destinos permiten representar consultas DNS institucionales dentro del tráfico generado.

---
## 13. Comportamiento del tráfico

El simulador genera tráfico con características variables:

1. Mayor tráfico en laboratorios entre las 08:00 y las 15:00.
2. Mayor carga para redes inalámbricas de alumnos.
3. Mayor probabilidad de pérdida o errores en dispositivos SOHO.
4. Estados operativos variables
5. Tráfico hacia aplicaciones institucionales y externas.

#### Aplicaciones simuladas
1. Plataforma Educativa
2. Videoconferencia
3. YouTube
4. Correo Institucional
5. DNS
6. Actualizaciones
7. Redes Sociales
8. Descarga Masiva

---
## 14. Modelo de datos en ClickHouse

Los eventos se almacenan en la tabla:

telemetria.trafico_red

Cada registro representa un evento de tráfico con campos como:

|  Campo  |  Descripción  |
|---------|:----------|
|  timestamp  |  Fecha y hora del evento  |
|fabricante   |   Fabricante del dispositivo|
|modelo | Modelo del dispositivo|
|tipo_dispositivo    |    Tipo de equipo|
|protocolo_telemetria  |  Protocolo o fuente simulada|
|nivel_detalle |  Nivel de detalle de la telemetría|
|edificio   |     Edificio al que pertenece el equipo|
|piso  |  Piso asignado|
|area  |  Área, laboratorio, salón o departamento|
|codigo_area  |   Código corto del área|
|categoria_area|  Tipo de área|
|isla|    Isla de laboratorio, si aplica|
|ssid|    SSID, si aplica|
|segmento_red|    Tipo o segmento lógico de red|
|hostname|        Nombre del equipo|
|ip_dispositivo|  IP del equipo|
|mac|     Dirección MAC simulada|
|ip_origen|       IP origen del flujo|
|ip_destino|      IP destino del flujo|
|puerto_destino|  Puerto destino|
|protocolo|       Protocolo de transporte|
|aplicacion|      Aplicación asociada al tráfico|
|criticidad|      Criticidad de la aplicación|
|bytes|   Bytes transferidos|
|paquetes|        Paquetes transferidos|
|latencia_ms|     Latencia simulada|
|perdida_pct|     Porcentaje de pérdida simulado|
|errores| Errores simulados|
|estado|  Estado operativo|
|severidad|       Severidad del evento|
|descripcion_evento|      Descripción textual del evento|

---

## 15. Requisitos

Para ejecutar el prototipo se requiere:
```text
Sistema operativo Linux
Docker
Docker Compose
Python 3
Git
```

En el entorno de desarrollo se utilizó openSUSE Leap dentro de una máquina virtual.

---

## 16. Despliegue del entorno
### 16.1 Clonar el repositorio
```text
git clone https://github.com/vulletz/ATVT-SHP.git
cd ATVT-SHP
```

En caso de estar trabajando directamente en la VM donde ya existe el proyecto:

```text
cd ~
```

### 16.2 Levantar los contenedores
```text
sudo docker compose up -d
```

### 16.3 Verificar contenedores activos

```text
sudo docker ps
```

Deben aparecer servicios similares a:

```text
clickhouse_olap
grafana_dashboard
victoriametrics_tsdb
telegraf_colector
```
---
## 17. Ejecución del simulador

Para iniciar la generación de tráfico:

```text
python3 ~/simulador_red_heterogenea.py
```

El script mostrará eventos insertados en tiempo real:

```text
[+] Insertados 20 eventos | total=20 | B | EB-I2-16 | YouTube | 12722540 bytes | SATURADO
```

Para detenerlo:

```text
Ctrl + C
```

---

## 18. Verificación en ClickHouse

Ingresar al cliente de ClickHouse:

```text
sudo docker exec -it clickhouse_olap clickhouse-client \
  --user telegraf \
  --password admin123
```

Seleccionar la base:

```text
USE telemetria;
```

Contar eventos:

```text
SELECT count() FROM trafico_red;
```

Consultar tráfico por edificio:

```text
SELECT
    edificio,
    sum(bytes) AS trafico_total
FROM trafico_red
GROUP BY edificio
ORDER BY trafico_total DESC;
```

Consultar dispositivos detectados:

```text
SELECT
    edificio,
    area,
    hostname,
    ip_dispositivo,
    fabricante,
    tipo_dispositivo
FROM trafico_red
ORDER BY timestamp DESC
LIMIT 20;
```
---
## 19. Acceso a Grafana

Grafana queda disponible en:

> http://localhost:3000

En la máquina virtual puede accederse desde el navegador local usando el puerto 3000.

Credenciales:

```text
Usuario: admin
Contraseña: Overl00k?
```

---


## 20. Dashboard incluido

El repositorio incluye el dashboard exportado:

> dashboards/observabilidad_red_heterogenea_fca_uaslp.json

Este dashboard contiene paneles para:

```text
Disponibilidad general.
Total de eventos.
Eventos críticos.
Dispositivos únicos.
Tráfico total.
Tráfico por edificio.
Latencia promedio por edificio.
Últimas anomalías.
Eventos críticos.
Estado de dispositivos.
Tráfico por aplicación.
Fabricantes con más errores.
Pérdida promedio por fabricante.
Top IPs destino.
Mapa lógico por edificio.
Top máquinas con más tráfico.
```

---

## 21. Importar dashboard en Grafana

Para importar el dashboard:

1. Entrar a Grafana.
2. Ir a Dashboards.
3. Seleccionar New / Import.
4. Cargar el archivo:
5. dashboards/observabilidad_red_heterogenea_fca_uaslp.json
6. Seleccionar el datasource de ClickHouse.
7. Guardar el dashboard.

---

## 22. Consultas principales utilizadas
Tráfico por edificio

```text
SELECT
    toStartOfMinute(timestamp) AS time,
    edificio,
    sum(bytes) AS bytes
FROM telemetria.trafico_red
WHERE $__timeFilter(timestamp)
  AND edificio IN (${edificio:singlequote})
GROUP BY time, edificio
ORDER BY time;
```

Disponibilidad general
```text
SELECT
    round(
        countIf(estado_actual = 'UP') * 100.0 / count(),
        2
    ) AS disponibilidad
FROM
(
    SELECT
        hostname,
        argMax(estado, timestamp) AS estado_actual
    FROM telemetria.trafico_red
    WHERE $__timeFilter(timestamp)
    GROUP BY hostname
);
```

Top máquinas con más tráfico
```text
SELECT
    hostname,
    ip_dispositivo,
    edificio,
    fabricante,
    sum(bytes) AS trafico_total
FROM telemetria.trafico_red
WHERE $__timeFilter(timestamp)
GROUP BY hostname, ip_dispositivo, edificio, fabricante
ORDER BY trafico_total DESC
LIMIT 10;
```

Mapa lógico por edificio
```text
SELECT
    edificio,
    piso,
    hostname,
    ip_dispositivo,
    fabricante,
    tipo_dispositivo,
    estado,
    max(timestamp) AS ultima_lectura,
    sum(bytes) AS trafico_total,
    avg(latencia_ms) AS latencia_promedio,
    avg(perdida_pct) AS perdida_promedio
FROM telemetria.trafico_red
WHERE $__timeFilter(timestamp)
GROUP BY
    edificio,
    piso,
    hostname,
    ip_dispositivo,
    fabricante,
    tipo_dispositivo,
    estado
ORDER BY edificio, piso, trafico_total DESC;
```

---

## 23. Evidencias de funcionamiento

Durante las pruebas se validó que:

- Los contenedores del stack se ejecutan correctamente.
- El simulador genera inventario y eventos de tráfico.
- ClickHouse recibe e inserta los eventos.
- Grafana actualiza los paneles en tiempo real.
- El dashboard permite filtrar por edificio.
- Se visualizan anomalías, eventos críticos, tráfico por aplicación y dispositivos con mayor consumo.

#### Ejemplo de salida del simulador:

```text
[+] Inventario simulado generado: 431 dispositivos
[+] Insertados 20 eventos | total=20 | B | EB-I2-16 | YouTube | 12722540 bytes | SATURADO
[+] Insertados 20 eventos | total=40 | B | EB-AP-CISCO-ACADEMICOS-02 | Redes Sociales | 1321865 bytes | UP
```
---

## 24. Limitaciones del prototipo

Este prototipo no representa una implementación productiva completa. Sus principales limitaciones son:

- Los eventos son generados de forma sintética.
- No existe conexión directa con switches o routers reales.
- No se realiza descubrimiento automático real mediante LLDP/CDP.
- No se validan flujos reales NetFlow/IPFIX de equipos institucionales.
- Las direcciones IP, MAC y estados son simulados.
- Algunas segmentaciones inalámbricas son representaciones lógicas para fines de prueba.
---

## 25. Trabajo futuro

Como continuación natural del proyecto, se propone:

1. Integrar colectores reales SNMPv3.
2. Validar exportación NetFlow/IPFIX desde equipos compatibles.
3. Mapear la topología real mediante LLDP/CDP.
4. Asociar VLANs y segmentos reales de red.
5. Configurar alertas hacia correo o mensajería institucional.
6. Implementar control de usuarios y permisos en Grafana.
7. Generar una línea base real de tráfico.
8. Comparar tráfico simulado contra tráfico real capturado.
9. Desplegar la solución en un servidor institucional.
10. Documentar procedimientos de recuperación y mantenimiento.
---

## 26. Autor

#### Sebastian Heredia Pardo
##### Ingeniería en Telemática
### Universidad Politécnica de San Luis Potosí
#### Residencia profesional en la Facultad de Contaduría y Administración, UASLP
---

## 27. Responsable institucional

#### Ing. Jesús Eduardo Salinas Guel
##### Departamento de Innovación Educativa
### Facultad de Contaduría y Administración, UASLP

---

## 28. Estado actual

El proyecto se encuentra en estado de prototipo funcional, con generación de tráfico, almacenamiento en ClickHouse y visualización dinámica en Grafana.

```text
Estado: Funcional para demostración y validación del entorno
```
