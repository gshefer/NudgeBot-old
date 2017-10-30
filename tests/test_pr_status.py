from nudgebot.utils.github.pull_request import PullRequest


def test_pr_statuses():
    pr_statuses = PullRequest.get_all()
    for prs in pr_statuses:
        print prs.json  # Calling for most of the functions
