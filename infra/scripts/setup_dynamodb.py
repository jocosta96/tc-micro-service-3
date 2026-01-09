#!/usr/bin/env python3
"""
Script para criar/verificar tabela e índices do Payment Service no DynamoDB.
Rodar antes de subir o serviço pela primeira vez.

Uso:
    # DynamoDB Local:
    export PAYMENT_DYNAMO_ENDPOINT=http://localhost:8000
    python infra/scripts/setup_dynamodb.py
    
    # AWS Real:
    python infra/scripts/setup_dynamodb.py
"""
import boto3
import os
import sys
from pathlib import Path
from botocore.exceptions import ClientError

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.payment_config import payment_config


def setup_payment_table():
    """Cria tabela payment-transactions com índices necessários"""
    
    table_name = os.getenv("PAYMENT_TABLE_NAME", "payment-transactions")
    region = os.getenv("PAYMENT_AWS_REGION", "us-east-1")
    endpoint = os.getenv("PAYMENT_DYNAMO_ENDPOINT", None)  # Para DynamoDB local
    
    print(f"🔧 Configurando DynamoDB Payment Service...")
    print(f"   Table: {table_name}")
    print(f"   Region: {region}")
    print(f"   Endpoint: {endpoint or 'AWS default'}")
    
    dynamodb = boto3.client(
        "dynamodb",
        endpoint_url=payment_config.endpoint_url or None,
        region_name=payment_config.region_name,
        aws_access_key_id=payment_config.dynamo_access_key_id or None,
        aws_secret_access_key=payment_config.dynamo_secret_access_key or None,
        aws_session_token=payment_config.dynamo_session_token or None,
    )
    
    try:
        # Verificar se tabela já existe
        response = dynamodb.describe_table(TableName=table_name)
        print(f"✅ Tabela '{table_name}' já existe")
        
        # Listar GSIs
        gsis = response['Table'].get('GlobalSecondaryIndexes', [])
        print(f"📋 Índices existentes:")
        for gsi in gsis:
            print(f"   - {gsi['IndexName']}")
        
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"❌ Erro ao verificar tabela: {e}")
            return False
        print(f"📦 Tabela '{table_name}' não existe. Criando...")
    
    # Criar tabela com índices
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"}  # Partition key
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "order_id", "AttributeType": "N"},
                {"AttributeName": "provider_tx_id", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "order_id-index",
                    "KeySchema": [
                        {"AttributeName": "order_id", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                },
                {
                    "IndexName": "provider_tx_id-index",
                    "KeySchema": [
                        {"AttributeName": "provider_tx_id", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        
        print(f"✅ Tabela '{table_name}' criada com sucesso!")
        print("📋 Índices criados:")
        print("   - id (PK) - buscar por transaction_id")
        print("   - order_id-index (GSI) - buscar por order_id")
        print("   - provider_tx_id-index (GSI) - buscar por provider_tx_id")
        print("\n⏳ Aguardando tabela ficar ACTIVE...")
        
        # Aguardar tabela ficar ativa
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print("✅ Tabela ativa e pronta para uso!")
        return True
    
    except ClientError as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False


if __name__ == "__main__":
    success = setup_payment_table()
    sys.exit(0 if success else 1)
