"""
This module contains tests for the pr_reviewer module.
"""

import os
from unittest.mock import patch, MagicMock
import pytest

from src import pr_reviewer

ERROR_MESSAGE = 'An unexpected error occurred while processing the request. Please ' \
    'try again later.'


@patch('src.pr_reviewer.Github')
@patch('src.pr_reviewer.OpenAI')
def test_review_pull_request_no_files(mock_openai, mock_github):
    """
    Test the review_pull_request function when the PR has no files
    :param mock_openai:
    :param mock_github:
    :return:
    """
    # Set up mock objects
    mock_github.return_value.get_repo.return_value.get_pull.return_value.get_files.return_value = []
    mock_github.return_value.get_repo.return_value.get_pull.return_value.create_issue_comment.\
        return_value = None
    mock_openai.return_value.beta.threads.create_and_run.return_value.status = 'completed'
    mock_openai.return_value.beta.threads.messages.list.return_value.data = [MagicMock()]

    # Call the function with mock objects
    result = pr_reviewer.review_pull_request('repo_name', 1)

    # Assert that the function behaves as expected
    assert result is None


@patch('src.pr_reviewer.review_pull_request')
def test_lambda_handler_unauthorized_repo(mock_review_pull_request):
    """
    Test the lambda_handler function when the repo is unauthorized
    :param mock_review_pull_request:
    :return:
    """
    # Set up mock objects
    mock_review_pull_request.return_value.body = 'body'

    # Call the function with mock objects
    event = {
        "queryStringParameters": {
            "repo": "unauthorized_repo",
            "pr": "1"
        }
    }
    os.environ['AUTHORIZED_REPO'] = 'authorized_repo'
    result = pr_reviewer.lambda_handler(event, None)

    # Assert that the function behaves as expected
    assert result['statusCode'] == 403
    assert result['body'] == 'You are not unauthorized to use PR Reviewer on this repository !!!'


@pytest.mark.parametrize("error, expected_status_code, expected_body", [
    (KeyError('error'), 500, ERROR_MESSAGE),
    (SyntaxError('error'), 500, ERROR_MESSAGE),
    (ImportError('error'), 500, ERROR_MESSAGE)
])
@patch('src.pr_reviewer.review_pull_request')
def test_lambda_handler_error_occurred(mock_review_pull_request, error, expected_status_code,
                                       expected_body):
    """
    Test the lambda_handler function when an error occurred
    :param mock_review_pull_request:
    :return:
    """
    # Set up mock objects
    mock_review_pull_request.side_effect = error

    # Call the function with mock objects
    event = {
        "queryStringParameters": {
            "repo": "authorized_repo",
            "pr": "1"
        }
    }
    os.environ['AUTHORIZED_REPO'] = 'authorized_repo'
    result = pr_reviewer.lambda_handler(event, None)

    # Assert that the function behaves as expected
    assert result['statusCode'] == expected_status_code
    assert result['body'] == expected_body
