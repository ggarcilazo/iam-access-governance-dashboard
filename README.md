# IAM Access Governance & Audit Dashboard

Sistema que simula un ciclo de **User Access Review** (revisión de accesos) tal como lo exigiría un auditor SOX, aplicado a identidades reales en la nube (AWS IAM), con detección automática de anomalías, almacenamiento relacional con SQL, y un flujo de certificación de accesos automatizado.

Proyecto construido como evidencia técnica práctica para roles de **Identity & Access Management (IAM)** y **Auditoría de Controles SOX**.

---

## 📌 Por qué existe este proyecto

Las empresas pagan herramientas costosas (SailPoint, Saviynt) para gobernar quién tiene acceso a qué, y para poder demostrarle a un auditor que ese acceso se revisa periódicamente. Este proyecto prototipa ese mismo ciclo — extracción de identidades, detección de riesgos, certificación de accesos — usando únicamente herramientas gratuitas o de nivel gratuito.

**Problema que resuelve:**
- ¿Quién tiene acceso a qué, y por qué?
- ¿Hay usuarios con privilegios excesivos que nadie ha revisado?
- ¿Hay violaciones de segregación de funciones (una persona que puede crear Y aprobar lo mismo)?
- ¿Cómo se documenta y aprueba/revoca ese acceso de forma trazable?

---

## 🏗️ Arquitectura

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   AWS IAM        │      │   Python/boto3    │      │   Azure SQL Database │
│  (usuarios,      │─────▶│   Extracción +    │─────▶│   (tablas relacio-   │
│   grupos,        │      │   Detección de    │      │    nales, JOINs,     │
│   políticas)      │      │   anomalías       │      │    snapshots)        │
└─────────────────┘      └──────────────────┘      └──────────┬──────────┘
                                                                 │
                          ┌──────────────────┐                  │
                          │  Google Sheets +  │◀─────────────────┘
                          │  Apps Script      │
                          │  (certificación   │
                          │   de accesos)     │
                          └──────────────────┘
```

**Flujo de datos:**
1. Un script en Python se conecta a AWS IAM (usuario de servicio de solo lectura) y extrae usuarios, grupos y políticas efectivas.
2. Un motor de reglas en Python evalúa esos datos contra 3 controles: privilegio excesivo, segregación de funciones (SoD), y cuentas huérfanas.
3. Los datos y hallazgos se cargan a una base relacional en Azure SQL, con tablas normalizadas y relaciones vía foreign keys.
4. Los hallazgos se llevan a una hoja de cálculo donde un "revisor" certifica cada uno (Aprobado/Revocado), quedando registrado quién y cuándo — vía Google Apps Script.

---

## 🧰 Stack técnico

| Componente | Herramienta | Costo |
|---|---|---|
| Identidad / origen de datos | AWS IAM (Free Tier) | Gratis |
| Extracción | Python 3 + `boto3` | Gratis |
| Base de datos | Azure SQL Database (free offer, General Purpose serverless) | Gratis |
| Detección de anomalías | Python (reglas basadas en RBAC y SoD) | Gratis |
| Certificación de accesos | Google Apps Script + Google Sheets | Gratis |
| Control de versiones | Git + GitHub | Gratis |

---

## 📁 Estructura del repositorio

```
iam-access-governance-dashboard/
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── rbac-matrix.md
│   └── sox-controls-mapping.md
├── extraction/
│   └── aws_iam/
│       ├── extract_users.py
│       └── snapshot_latest.json
├── database/
│   ├── schema.sql
│   └── load_snapshot.py
├── analysis/
│   ├── anomaly_detection.py
│   └── audit_report_latest.json
├── apps-script/
│   └── Code.gs
└── dashboard/
    └── looker-studio-link.md
```

---

## ✅ Qué demuestra este proyecto (mapeo a requisitos de vacantes)

**Para roles de IAM (AD / Entra ID / AWS):**
- Gestión práctica de usuarios, grupos y políticas en AWS IAM
- Aplicación real de RBAC: uso de grupos en vez de políticas directas a usuarios, principio de menor privilegio (`IAMReadOnlyAccess` para el usuario de servicio)
- Scripting en Python contra una API de identidad (boto3 / AWS SDK)
- Documentación de matriz de acceso

**Para roles de auditoría SOX:**
- SQL intermedio/avanzado: `JOIN`s de múltiples tablas, uso de `STRING_AGG`, CTEs para resolver problemas reales de fan-out en agregaciones
- Automatización con Google Apps Script (validación de datos, triggers `onEdit`, generación de reportes)
- Mapeo explícito de controles: segregación de funciones, revisión periódica de accesos, trazabilidad (quién aprobó, cuándo)
- Detección de hallazgos reproducible y basada en reglas, no manual

---

## ⚙️ Setup

### 1. Requisitos previos
- Cuenta de AWS con un usuario IAM de solo lectura (`IAMReadOnlyAccess`)
- Cuenta de Azure con una base SQL (puede ser el free offer)
- Python 3.10+
- Driver ODBC para SQL Server (17 o 18) instalado localmente

### 2. Clonar e instalar dependencias
```bash
git clone <tu-repo-url>
cd iam-access-governance-dashboard
pip install boto3 python-dotenv pyodbc
```

### 3. Variables de entorno
Copia `.env.example` a `.env` y completa con tus credenciales reales (este archivo **nunca** se sube al repo):
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

AZURE_SQL_SERVER=
AZURE_SQL_DATABASE=
AZURE_SQL_USER=
AZURE_SQL_PASSWORD=
```

### 4. Crear el esquema de base de datos
Ejecuta el contenido de `database/schema.sql` en el editor de consultas de Azure SQL (o vía cualquier cliente SQL).

### 5. Correr el pipeline completo
```bash
python extraction/aws_iam/extract_users.py   # extrae de AWS IAM
python analysis/anomaly_detection.py         # detecta hallazgos
python database/load_snapshot.py             # carga todo a Azure SQL
```

### 6. Configurar la hoja de certificación
1. Crea una Google Sheet con las columnas: `Usuario, Grupos, Politicas, Tipo_Hallazgo, Descripcion, Decision, Revisado_Por, Fecha_Revision`
2. Pega los hallazgos (query de ejemplo en `docs/sox-controls-mapping.md`)
3. Ve a **Extensiones → Apps Script**, pega el contenido de `apps-script/Code.gs`, guarda y autoriza los permisos
4. Usa el menú **"Auditoría IAM"** para generar el resumen de revisión

---

## 🔍 Ejemplo real de hallazgo detectado

```json
{
  "username": "rperez",
  "findings": [
    "SoD: pertenece a 'Approvers' Y 'Creators' simultáneamente",
    "Privilegio elevado: tiene 'PowerUserAccess'",
    "Privilegio elevado: tiene 'IAMFullAccess'"
  ]
}
```

Query SQL usado para consolidar esta evidencia (con CTEs para evitar fan-out en los JOINs):

```sql
WITH grupos AS (
    SELECT u.user_id, STRING_AGG(g.group_name, ', ') AS grupos
    FROM iam_users u
    JOIN user_groups ug ON u.user_id = ug.user_id
    JOIN iam_groups g ON ug.group_id = g.group_id
    GROUP BY u.user_id
),
politicas AS (
    SELECT u.user_id, STRING_AGG(p.policy_name, ', ') AS politicas
    FROM iam_users u
    JOIN user_effective_policies uep ON u.user_id = uep.user_id
    JOIN iam_policies p ON uep.policy_id = p.policy_id
    GROUP BY u.user_id
),
hallazgos AS (
    SELECT user_id, STRING_AGG(finding_type, ', ') AS hallazgos
    FROM audit_findings
    GROUP BY user_id
)
SELECT u.username, grupos.grupos, politicas.politicas, hallazgos.hallazgos
FROM iam_users u
LEFT JOIN grupos ON u.user_id = grupos.user_id
LEFT JOIN politicas ON u.user_id = politicas.user_id
LEFT JOIN hallazgos ON u.user_id = hallazgos.user_id
ORDER BY u.username;
```

> **Nota técnica:** la primera versión de este query intentó usar `STRING_AGG(DISTINCT ...)`, que no es válido en T-SQL. La solución fue descomponer la agregación en CTEs separados por relación antes de unirlos, evitando el fan-out desde el diseño del query en vez de parchearlo después.

---

## 🗺️ Roadmap / próximos pasos

- [ ] Incorporar Microsoft Entra ID como segunda fuente de identidad (además de AWS IAM)
- [ ] Automatizar la extracción periódica con n8n
- [ ] Dashboard en Looker Studio conectado a la Sheet de certificación (KPIs: % de revisión completada, hallazgos por tipo, usuarios de alto riesgo)

---

## 📄 Documentación adicional

- [`docs/rbac-matrix.md`](docs/rbac-matrix.md) — matriz de roles, grupos y políticas
- [`docs/sox-controls-mapping.md`](docs/sox-controls-mapping.md) — mapeo de cada control técnico a un requisito SOX

---

## Autor

Proyecto desarrollado como parte de un proceso de aplicación a posiciones de Identity & Access Management y Auditoría SOX.