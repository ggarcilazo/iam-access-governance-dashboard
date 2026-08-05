# Dashboard — Looker Studio

**Enlace público:** <[pega aquí el link que copiaste](https://datastudio.google.com/reporting/f6623f22-fc0c-430c-92af-de50602703e8)>

## KPIs incluidos
- % de revisión de accesos completada
- Distribución de hallazgos por tipo (SoD, privilegio excesivo, cuenta huérfana)
- Estado de decisiones (Pendiente / Aprobado / Revocado)
- Detalle de hallazgos con trazabilidad (revisor + fecha)

## Fuente de datos
Google Sheet `IAM-Access-Certification`, alimentada por el pipeline de extracción (AWS IAM + Entra ID) → detección de anomalías → certificación.