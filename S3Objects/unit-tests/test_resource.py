import base64
import importlib

import pytest

from botocore.stub import Stubber

# 'lambda' is a python keyword
resource = importlib.import_module('lambda.resource')


mock_send_event = {
        'ResourceProperties': {
            'Target': {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
            }
        },
        'StackId': 'test-stack',
        'RequestId': 'test-request',
        'LogicalResourceId': 'test-resource',
        'ResponseURL': 'http://example.com',
    }


def test_send(mocker):
    status = 'test'
    reason = 'test'

    mocker.patch('lambda.resource.build_opener', autospec=True)
    resource.sendResponse(mock_send_event, None, status, reason)
    # assert no exception is raised


mock_empty_event = {
        'ResourceProperties': {},
        'RequestType': '',
    }


mock_unexpected_event = {
        'ResourceProperties': {
            'Target': {},
            'Body': '',
        },
        'RequestType': 'test-unexpected',
    }


mock_delete_event = {
        'ResourceProperties': {
            'Target': {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
            },
            'Source': '',
        },
        'RequestType': 'Delete',
    }


mock_body_event = {
        'ResourceProperties': {
            'Target': {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
            },
            'Body': 'test-body',
        },
        'RequestType': 'Create',
    }


mock_base64_event = {
        'ResourceProperties': {
            'Target': {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
            },
            'Base64Body': 'dGVzdC1ib2R5',  # 'test-body'
        },
        'RequestType': 'Create',
    }


mock_source_event = {
        'ResourceProperties': {
            'Target': {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
                'ACL': 'test-acl',
            },
            'Source': 'test-source',
        },
        'RequestType': 'Create',
    }


@pytest.mark.parametrize(
    "mock_event,s3_action,result,message",
    [
        (mock_empty_event, None, 'FAILED', 'Missing required parameters'),
        (mock_unexpected_event, None, 'FAILED', 'Unexpected: test-unexpected'),
        (mock_delete_event, 'delete_object', 'SUCCESS', 'Deleted'),
        (mock_body_event, 'put_object', 'SUCCESS', 'Created'),
        (mock_base64_event, 'put_object', 'SUCCESS', 'Created'),
        (mock_source_event, 'copy_object', 'SUCCESS', 'Created'),
    ]
)
def test_handler(mocker, mock_event, s3_action, result, message):
    mock_send = mocker.patch('lambda.resource.sendResponse')

    with Stubber(resource.s3_client) as stub:
        if s3_action:
            stub.add_response(s3_action, {})

        resource.handler(mock_event, {})
        stub.assert_no_pending_responses()

    mock_send.assert_called_with(mock_event, {}, result, message)
