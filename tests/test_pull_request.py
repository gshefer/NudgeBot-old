from nudgebot.utils.github.pull_request import PullRequest


def test_pull_requests():
    pr_statuses = PullRequest.get_all(state='open', logins=['gshefer'])
    for prs in pr_statuses:
        print prs.json  # Calling for most of the functions
