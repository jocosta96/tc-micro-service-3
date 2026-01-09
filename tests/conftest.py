import os
import sys
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

# Mock boto3.client to prevent real AWS calls during test collection
original_boto3_client = None

def mock_boto3_client(service_name, **kwargs):
    """Mock boto3.client to return a mock SSM client."""
    if service_name == 'ssm':
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': None}}
        mock_ssm.get_parameters.return_value = {'Parameters': []}
        mock_ssm.get_parameters_by_path.return_value = {'Parameters': []}
        return mock_ssm
    # For other services, try to use the original
    if original_boto3_client:
        return original_boto3_client(service_name, **kwargs)
    return MagicMock()

# Patch boto3.client before any src imports
import boto3
original_boto3_client = boto3.client
boto3.client = mock_boto3_client