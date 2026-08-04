import boto3
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone

load_dotenv()

iam = boto3.client(
    'iam',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

def get_group_policies(group_name):
    policies = iam.list_attached_group_policies(GroupName=group_name)
    return [p['PolicyName'] for p in policies['AttachedPolicies']]

def get_users_with_details():
    users_data = []
    response = iam.list_users()

    for user in response['Users']:
        username = user['UserName']

        attached = iam.list_attached_user_policies(UserName=username)
        direct_policies = [p['PolicyName'] for p in attached['AttachedPolicies']]

        groups = iam.list_groups_for_user(UserName=username)
        group_names = [g['GroupName'] for g in groups['Groups']]

        # Políticas heredadas de cada grupo (esto es lo que faltaba)
        group_policies = []
        for gname in group_names:
            group_policies.extend(get_group_policies(gname))

        password_last_used = user.get('PasswordLastUsed')
        days_inactive = (datetime.now(timezone.utc) - password_last_used).days if password_last_used else None
        days_since_created = (datetime.now(timezone.utc) - user['CreateDate']).days

        users_data.append({
            'username': username,
            'user_id': user['UserId'],
            'created': user['CreateDate'].isoformat(),
            'days_since_created': days_since_created,
            'groups': group_names,
            'direct_policies': direct_policies,
            'effective_policies': list(set(direct_policies + group_policies)),
            'password_last_used': password_last_used.isoformat() if password_last_used else None,
            'days_inactive': days_inactive
        })

    return users_data

if __name__ == '__main__':
    data = get_users_with_details()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    with open('extraction/aws_iam/snapshot_latest.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Snapshot guardado con {len(data)} usuario(s)")