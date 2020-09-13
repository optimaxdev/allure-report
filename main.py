import re
import sys
import os
import requests
import json
import base64

GITHUB_API_BASE_URL = 'https://api.github.com'


def escape(v: str) -> str:
    return repr(v)[1:-1]


def print_action_error(msg: str):
    sys.stdout.write(f'::error file={__name__}::{escape(msg)}\n')


def get_action_input(name):
    var = os.environ.get(f'INPUT_{name.upper()}', '')
    if var == '':
        print_action_error(f'Input required and not supplied: {name}')
        exit(1)
    return var


def report_files(results_directory):
    results_directory = os.path.dirname(
        os.path.realpath(__file__)) + results_directory
    files = os.listdir(results_directory)
    results = []
    for file in files:
        result = {}

        file_path = f'{results_directory}/{file}'

        if os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                    if content.strip():
                        b64_content = base64.b64encode(content)
                        result['file_name'] = file
                        result['content_base64'] = b64_content.decode('UTF-8')
                        results.append(result)
                    else:
                        print('Empty File skipped: ' + file_path)
            finally:
                f.close()
        else:
            print('Directory skipped: ' + file_path)
    request_body = {
        "results": results
    }
    json_request_body = json.dumps(request_body)
    print(f'Debugging empty reports:\n{files}')
    return json_request_body


def generate_report(allure_server, project_id, execution_name, execution_from, report_body):
    execution_type = 'github-actions'
    headers = {'Content-type': 'application/json'}

    print("Uploading test results")
    send_response = requests.post(
        f'{allure_server}/allure-docker-service/send-results?project_id={project_id}',
        headers=headers,
        data=report_body,
    )
    print(f'Response code: {send_response.status_code}')
    print(json.loads(send_response.content)['meta_data']['message'])

    print("Generating Allure report")
    generate_response = requests.get(
        f'{allure_server}/allure-docker-service/generate-report?project_id={project_id}&execution_name={execution_name}&execution_from={execution_from}&execution_type={execution_type}',
        headers=headers,
        data=report_body,
    )
    print(
        f'Debugging weird errors on generate step:\n{generate_response.content}')
    report_url = json.loads(generate_response.content)['data']['report_url']
    print(f'Response code: {generate_response.status_code}')
    return report_url


def clean_allure_results(allure_server, project_id):
    print('Purging result files')
    clean_response = requests.get(
        f'{allure_server}/allure-docker-service/clean-results?project_id={project_id}'
    )

    message = json.loads(clean_response.content)['meta_data']['message']
    print(message)
    return message


def find_allure_comments(token, repo, pr_number, regexp):
    headers = {'Authorization': f'token {token}'}

    response = requests.get(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/{pr_number}/comments',
        headers=headers,
    )
    print(f'Response code: {response.status_code}')
    comment_ids = [comment['id'] for comment in json.loads(
        response.content) if re.match(regexp, comment['body'])]
    return comment_ids


def post_allure_comment(token, repo, pr_number, body, comment_ids, report_url):
    headers = {'Authorization': f'token {token}'}
    data = {"body": f"{body}: {report_url}"}

    if len(comment_ids) == 0:
        print('Posting PR comment with Allure report link')
        response = requests.post(f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/{pr_number}/comments',
                                 headers=headers,
                                 data=json.dumps(data))
        print(f'Response code: {response.status_code}')

    elif len(comment_ids) == 1:
        print('Editing PR comment with latest Allure report link')
        response = requests.patch(f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/comments/{comment_ids[0]}',
                                  headers=headers,
                                  data=json.dumps(data))
        print(f'Response code: {response.status_code}')


def main():
    token = get_action_input('token')
    allure_server = get_action_input('allure_server')
    repo = os.environ['GITHUB_REPOSITORY']
    body = get_action_input('body')
    pr_number = get_action_input('pr_number')
    project_id = get_action_input('project_id')
    results_directory = get_action_input('results_directory')
    results_directory_full_path = f'github/workspace/{results_directory}'
    execution_name = f'PR-{pr_number}'
    execution_from = f'https://github.com/{repo}/pull/{pr_number}'

    report_body = report_files(results_directory_full_path)
    report_url = generate_report(
        allure_server, project_id, execution_name, execution_from, report_body)
    comment_ids = find_allure_comments(token, repo, pr_number, body)
    post_allure_comment(token, repo, pr_number, body, comment_ids, report_url)

    clean_allure_results(allure_server, project_id)


if __name__ == '__main__':
    main()

# TODO Function for extraction data from $GITHUB_EVENT_PATH json
# TODO Error handling in all functions
