import boto3
from dotenv import load_dotenv
import os

load_dotenv()

iam = boto3.client(
    'iam',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

response = iam.list_users()
for user in response['Users']:
    print(f"Usuario: {user['UserName']} | Creado: {user['CreateDate']}")