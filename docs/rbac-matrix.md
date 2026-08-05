# Matriz RBAC — IAM Access Governance & Audit Dashboard

Esta matriz documenta el diseño de control de acceso basado en roles (RBAC) implementado en AWS IAM para este proyecto. Refleja el principio de **menor privilegio**: los permisos se asignan a grupos por función laboral, nunca directamente a usuarios individuales.

## Grupos y políticas

| Grupo | Política adjunta | Nivel de privilegio | Propósito |
|---|---|---|---|
| `IAM-Auditors-ReadOnly` | `IAMReadOnlyAccess` | Bajo | Cuenta de servicio para scripts de auditoría (solo lectura, no puede modificar nada) |
| `Finance-Team` | `ReadOnlyAccess` | Bajo | Simula un equipo de negocio con acceso de consulta estándar |
| `Legacy-Admins` | `AdministratorAccess` | 🔴 Crítico | Simula una cuenta administrativa heredada, sin uso — caso de prueba de "cuenta huérfana con privilegio excesivo" |
| `Approvers` | `IAMFullAccess` | 🔴 Alto | Simula función de aprobación de cambios de acceso |
| `Creators` | `PowerUserAccess` | 🔴 Alto | Simula función de creación de recursos/cambios |

## Usuarios y su acceso efectivo

| Usuario | Grupo(s) | Política(s) efectiva(s) | Hallazgo | Estado de revisión |
|---|---|---|---|---|
| `iam-audit-readonly` | IAM-Auditors-ReadOnly | IAMReadOnlyAccess | Ninguno | N/A (cuenta de servicio, no requiere certificación) |
| `jgarcia-finance` | Finance-Team | ReadOnlyAccess | Ninguno | N/A |
| `mlopez-admin-orphan` | Legacy-Admins | AdministratorAccess | Privilegio elevado sin actividad reciente | Aprobado (ver `audit_findings`) |
| `rperez` | Approvers, Creators | IAMFullAccess, PowerUserAccess | Segregación de funciones violada + privilegio elevado (x2) | Revocado (SoD) / Pendiente (privilegios) |

## Regla de segregación de funciones (SoD) definida

```
Approvers ∩ Creators = conflicto
```

Un usuario no debería pertenecer simultáneamente a un grupo con capacidad de **crear** un cambio y a un grupo con capacidad de **aprobar** ese mismo tipo de cambio, ya que rompe el control de "cuatro ojos" (four-eyes principle) estándar en auditoría interna.

## Cómo se generó esta matriz

Extraída automáticamente vía `extraction/aws_iam/extract_users.py`, que consulta la API de IAM (`list_users`, `list_groups_for_user`, `list_attached_group_policies`) y resuelve las políticas efectivas de cada usuario (directas + heredadas de grupo).
