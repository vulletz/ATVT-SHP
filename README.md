# Prototipo de Observabilidad de Red Heterogénea - FCA UASLP

## Descripción

Este proyecto implementa un prototipo funcional de telemetría y visualización de tráfico de red para una infraestructura heterogénea basada en edificios, laboratorios, departamentos, access points y dispositivos simulados.

## Tecnologías utilizadas

- Docker
- ClickHouse
- Grafana
- VictoriaMetrics
- Telegraf
- Python

## Arquitectura

Simulador Python → ClickHouse → Grafana  
Telegraf → VictoriaMetrics → Grafana

## Componentes

- `simulador_red_heterogenea.py`: genera tráfico sintético normalizado.
- `docker-compose.yml`: levanta el stack de observabilidad.
- `dashboards/`: contiene el dashboard exportado de Grafana.

## Ejecución

```bash
sudo docker compose up -d
python3 simulador_red_heterogenea.py

## Acceso a Grafana

URL:

http://localhost:3000

## Alcance del prototipo

El sistema valida la ingesta, almacenamiento y visualización de eventos de red simulados. La instrumentación directa sobre equipos reales queda como trabajo futuro.
