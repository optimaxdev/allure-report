> GIthub action to generate allure report and post comment with report link on PR

## Inputs
- `token`: Github token
- `allure_server`: Allure server URL
- `body`: Comment body
- `pr_number`: Number of PR to comment
- `project_id`: Allure-server project id to associate report with (e.g. gusa-desktop-integrations)
- `results_directory`: Directory with allure-results xml files (e.g. __specs__/allure-results)
  