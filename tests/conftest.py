import os
import sys
from unittest.mock import MagicMock, patch

# Mock AWS credentials before any imports to prevent credential errors during test collection
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test-access-key')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

# Mock SSM client globally for all tests
mock_ssm_client = MagicMock()
mock_ssm_client.get_parameter.return_value = None
mock_ssm_client.get_parameters.return_value = {}
mock_ssm_client.get_parameters_by_path.return_value = []

with patch('src.config.aws_ssm.SSMParameterStore') as mock_ssm_class:
    mock_ssm_class.return_value = mock_ssm_client
    sys.path.append(os.getcwd())