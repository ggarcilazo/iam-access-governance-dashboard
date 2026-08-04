import json

SOD_CONFLICTING_GROUPS = [
    ("Approvers", "Creators"),
]
PRIVILEGED_POLICIES = ["AdministratorAccess", "IAMFullAccess", "PowerUserAccess"]
INACTIVITY_THRESHOLD_DAYS = 90

def load_snapshot(path='extraction/aws_iam/snapshot_latest.json'):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_sod_violations(user):
    findings = []
    user_groups = set(user['groups'])
    for group_a, group_b in SOD_CONFLICTING_GROUPS:
        if group_a in user_groups and group_b in user_groups:
            findings.append(f"⚠️  SoD: pertenece a '{group_a}' Y '{group_b}' simultáneamente")
    return findings

def check_excessive_privilege(user):
    findings = []
    for policy in user.get('effective_policies', []):
        if policy in PRIVILEGED_POLICIES:
            findings.append(f"🔴 Privilegio elevado: tiene '{policy}'")
    return findings

def check_orphaned_account(user):
    findings = []
    if user['days_inactive'] is None and user['days_since_created'] > INACTIVITY_THRESHOLD_DAYS:
        findings.append(f"👻 Cuenta huérfana: sin actividad de password, creada hace {user['days_since_created']} días")
    elif user['days_inactive'] and user['days_inactive'] > INACTIVITY_THRESHOLD_DAYS:
        findings.append(f"👻 Sin uso hace {user['days_inactive']} días")
    return findings

def run_audit():
    users = load_snapshot()
    report = []

    for user in users:
        findings = (
            check_sod_violations(user)
            + check_excessive_privilege(user)
            + check_orphaned_account(user)
        )
        if findings:
            report.append({'username': user['username'], 'findings': findings})

    return report

if __name__ == '__main__':
    results = run_audit()
    if not results:
        print("✅ Sin hallazgos.")
    for r in results:
        print(f"\n👤 {r['username']}")
        for f in r['findings']:
            print(f"   {f}")

    with open('analysis/audit_report_latest.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)