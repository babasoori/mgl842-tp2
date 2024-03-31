import os
from github import Github
from openai import OpenAI
import time
import logging

logger = logging.getLogger()
logger.setLevel("INFO")


def review_pull_request(repo_name, pr_number):
    """
    Review a GitHub Pull Request using OpenAI and post the feedback as a comment
    :param repo_name:
    :param pr_number:
    :return:
    """
    # Extract the secrets

    print(f"Reviewing PR {pr_number} in repo {repo_name}")

    my_github_token = os.getenv('MY_GITHUB_TOKEN')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    assistant_id = os.getenv('ASSISTANT_ID')
    # Initialize OpenAI and GitHub clients
    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai_api_key,
    )
    github = Github(my_github_token)
    # Fetch the pull request
    repo = github.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)

    # Extract PR details
    pr_files = pull_request.get_files()

    logging.info({"PR Files": pr_files})

    # Concatenate file changes to send to OpenAI
    changes = ""
    for file in pr_files:  # Limit to first 3 files to stay within token limits
        changes += f"File: {file.filename}\n+++ {file.patch}\n\n"

    # Construct the prompt for OpenAI
    prompt = (
        f"Review the following GitHub Pull Request changes:\n"
        f"{changes}\n"
        f"Provide a brief description of the changes, make suggestions for improvement of the code and provide code"
        f"snippet with your suggestions and for refactoring the code for the pull request. Always add a code snippet "
        f"with a suggestion and one for refactoring. This will give the developer new ideas to improve their code\n "
        f"Your feedback will be posted as a comment for the PR. Also when you add a suggestion add a corresponding "
        f"code snippet to explain the improvement. Also give the HOW TO DO the changes or improvement you suggest\n"
        f"This will provide the developer with useful insights for improving the code and making the pull request "
        f"better\n. "
        f"The suggestion and especially the code snippets are for giving tangible and actionable feedback. \n"
        f"Thanks for you help.")

    run = client.beta.threads.create_and_run(
        assistant_id=assistant_id,
        thread={
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)  # Wait for 1 second
        run = client.beta.threads.runs.retrieve(
            thread_id=run.thread_id,
            run_id=run.id
        )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=run.thread_id
        )
        logging.info({"Messages": messages})
    else:
        logging.info({"Run Status": run.status})

    # # Extract and post the OpenAI response as a PR comment
    logging.info({"OpenAI Response": messages.data[0].content[0].text.value})
    return pull_request.create_issue_comment(messages.data[0].content[0].text.value)


def lambda_handler(event, context):
    """
    Lambda handler for the PR Reviewer API
    :param event:
    :param context:
    :return:
    """
    logging.info({"event": event, "context": context})

    logging.info({"queryStringParameters": event.get("queryStringParameters")})

    body = ("Hello. The OpenAI PR Reviewer API is still constructions. Check back in a few days. "
            "Thanks for your patience!")

    query_string_parameters = event.get("queryStringParameters", {})
    if query_string_parameters:
        repo = query_string_parameters.get("repo")
        if repo == os.getenv('AUTHORIZED_REPO'):
            comment = review_pull_request(repo, int(event["queryStringParameters"]["pr"]))
            body = comment.body
        else:
            body = "Unauthorized repository"

    res = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "*/*"
        },
        "body": body
    }

    logging.info({"response": res})

    return res

