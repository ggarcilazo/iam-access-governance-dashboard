import pyodbc
import json
from dotenv import load_dotenv
import os

load_dotenv()

conn_str = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server=tcp:{os.getenv('AZURE_SQL_SERVER')},1433;"
    f"Database={os.getenv('AZURE_SQL_DATABASE')};"
    f"Uid={os.getenv('AZURE_SQL_USER')};"
    f"Pwd={os.getenv('AZURE_SQL_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

PRIVILEGED_POLICIES = ["AdministratorAccess", "IAMFullAccess", "PowerUserAccess"]

def get_or_create_group(cursor, group_name):
    cursor.execute("SELECT group_id FROM iam_groups WHERE group_name = ?", group_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO iam_groups (group_name) OUTPUT INSERTED.group_id VALUES (?)",
        group_name
    )
    return cursor.fetchone()[0]

def get_or_create_policy(cursor, policy_name):
    cursor.execute("SELECT policy_id FROM iam_policies WHERE policy_name = ?", policy_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    is_privileged = 1 if policy_name in PRIVILEGED_POLICIES else 0
    cursor.execute(
        "INSERT INTO iam_policies (policy_name, is_privileged) OUTPUT INSERTED.policy_id VALUES (?, ?)",
        policy_name, is_privileged
    )
    return cursor.fetchone()[0]

def load_data():
    with open('extraction/aws_iam/snapshot_latest.json', 'r', encoding='utf-8') as f:
        users_snapshot = json.load(f)
    with open('analysis/audit_report_latest.json', 'r', encoding='utf-8') as f:
        audit_report = json.load(f)

    findings_by_user = {r['username']: r['findings'] for r in audit_report}

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # 1. Nuevo snapshot
    cursor.execute(
        "INSERT INTO snapshots (source) OUTPUT INSERTED.snapshot_id VALUES ('aws_iam')"
    )
    snapshot_id = cursor.fetchone()[0]

    for user in users_snapshot:
        # 2. Usuario
        cursor.execute(
            """INSERT INTO iam_users
               (snapshot_id, aws_user_id, username, created_date, days_since_created, password_last_used, days_inactive)
               OUTPUT INSERTED.user_id
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            snapshot_id, user['user_id'], user['username'], user['created'],
            user['days_since_created'], user['password_last_used'], user['days_inactive']
        )
        user_id = cursor.fetchone()[0]

        # 3. Grupos
        for group_name in user['groups']:
            group_id = get_or_create_group(cursor, group_name)
            cursor.execute(
                "INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)",
                user_id, group_id
            )

        # 4. Políticas efectivas
        for policy_name in user['effective_policies']:
            policy_id = get_or_create_policy(cursor, policy_name)
            cursor.execute(
                "INSERT INTO user_effective_policies (user_id, policy_id) VALUES (?, ?)",
                user_id, policy_id
            )

        # 5. Hallazgos de auditoría
        for finding_text in findings_by_user.get(user['username'], []):
            finding_type = (
                'SOD_VIOLATION' if 'SoD' in finding_text else
                'EXCESSIVE_PRIVILEGE' if 'Privilegio' in finding_text else
                'ORPHANED_ACCOUNT'
            )
            cursor.execute(
                "INSERT INTO audit_findings (user_id, finding_type, description) VALUES (?, ?, ?)",
                user_id, finding_type, finding_text
            )

    conn.commit()
    print(f"✅ Snapshot {snapshot_id} cargado: {len(users_snapshot)} usuario(s), {sum(len(f) for f in findings_by_user.values())} hallazgo(s)")
    cursor.close()
    conn.close()

if __name__ == '__main__':
    load_data()