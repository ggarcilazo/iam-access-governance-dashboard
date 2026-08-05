# Mapeo de controles SOX — IAM Access Governance & Audit Dashboard

Este documento conecta cada objetivo de control interno (tipo SOX) con su implementación técnica concreta en el proyecto, y la evidencia que lo respalda.

| Control (objetivo SOX) | Implementación técnica | Evidencia |
|---|---|---|
| **Menor privilegio** — el acceso debe limitarse a lo estrictamente necesario para la función | Cuenta de servicio `iam-audit-readonly` con política `IAMReadOnlyAccess`, sin acceso de consola. Acceso asignado por grupo, no individual. | `docs/rbac-matrix.md`, captura de IAM → Users → Security credentials |
| **Segregación de funciones (SoD)** — una misma persona no debe poder crear y aprobar el mismo tipo de cambio | `check_sod_violations()` en `analysis/anomaly_detection.py` — compara membresías de grupo del usuario contra una lista de combinaciones conflictivas (`Approvers` + `Creators`) | Hallazgo `SOD_VIOLATION` sobre `rperez` en `audit_report_latest.json` y en la hoja de certificación |
| **Detección de privilegio excesivo** | `check_excessive_privilege()` — marca cualquier política efectiva del usuario (directa o heredada de grupo) que esté en una lista de políticas de alto riesgo (`AdministratorAccess`, `IAMFullAccess`, `PowerUserAccess`) | Hallazgo `EXCESSIVE_PRIVILEGE` sobre `mlopez-admin-orphan` y `rperez` |
| **Detección de cuentas huérfanas / inactivas** | `check_orphaned_account()` — calcula días desde creación y desde último uso de password; umbral configurado en 90 días | Lógica en `analysis/anomaly_detection.py` (`INACTIVITY_THRESHOLD_DAYS`) — no se disparó en los datos de prueba por ser usuarios recién creados, ver nota de limitación abajo |
| **Revisión periódica de accesos (User Access Review)** | Flujo de certificación en Google Sheets: cada hallazgo requiere una decisión explícita (`Pendiente / Aprobado / Revocado`), controlada por validación de datos | Google Sheet `IAM-Access-Certification`, columna `Decision` |
| **Trazabilidad de la revisión** | Trigger `onEdit()` en Apps Script — al cambiar la decisión, se registra automáticamente quién revisó (`Session.getActiveUser().getEmail()`) y cuándo | Columnas `Revisado_Por` y `Fecha_Revision` auto-llenadas |
| **Reporte de cumplimiento / KPI de revisión** | Función `resumenRevision()` — calcula % de hallazgos ya certificados (aprobados + revocados sobre el total) | Popup de resumen en Sheets; base para el dashboard de Looker Studio |
| **Snapshot histórico / auditoría temporal** | Tabla `snapshots` en Azure SQL — cada corrida de extracción queda registrada con timestamp, permitiendo comparar el estado de accesos entre fechas | `database/schema.sql`, tabla `snapshots` |

## Limitación conocida

El check de "cuenta huérfana" (inactividad > 90 días) no se disparó en los datos de prueba porque todos los usuarios se crearon el mismo día que se corrió el análisis (`days_since_created: 0`). La lógica está implementada y calibrada a un umbral estándar de industria (90 días); simplemente no hay antigüedad suficiente en los datos de prueba para activarla. Esto se documenta de forma transparente en vez de forzar un resultado falso.

## Por qué SQL con JOINs es parte de la evidencia de control

Los controles de SoD y privilegio excesivo dependen de relacionar correctamente usuario → grupo → política. Un error en el diseño de esas relaciones (como el fan-out documentado en el README, causado por `STRING_AGG(DISTINCT ...)` no soportado en T-SQL) puede producir falsos positivos o hallazgos duplicados — por eso el diseño del query, no solo el resultado, es parte del control.
