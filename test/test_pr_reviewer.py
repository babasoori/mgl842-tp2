import os
import pytest
from unittest.mock import patch, MagicMock
from src import pr_reviewer

@patch('src.pr_reviewer.Github')
@patch('src.pr_reviewer.OpenAI')
def test_review_pull_request(mock_openai, mock_github):
    # Set up mock objects
    mock_github.return_value.get_repo.return_value.get_pull.return_value.get_files.return_value = []
    mock_openai.return_value.beta.threads.create_and_run.return_value.status = 'completed'
    mock_openai.return_value.beta.threads.messages.list.return_value.data = [MagicMock()]

    # Call the function with mock objects
    result = pr_reviewer.review_pull_request('repo_name', 1)

    # Assert that the function behaves as expected
    assert result is not None

@patch('src.pr_reviewer.review_pull_request')
def test_lambda_handler(mock_review_pull_request):
    # Set up mock objects
    mock_review_pull_request.return_value.body = 'body'

    # Call the function with mock objects
    event = {
        "queryStringParameters": {
            "repo": "repo",
            "pr": "1"
        }
    }
    os.environ['AUTHORIZED_REPO'] = 'repo'
    result = pr_reviewer.lambda_handler(event, None)

    # Assert that the function behaves as expected
    assert result['statusCode'] == 200
    assert result['body'] == 'body'