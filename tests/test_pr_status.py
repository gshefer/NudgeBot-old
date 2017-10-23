from githunt.utils.github.pull_request_status import PullRequestStatus


def test_pr_statuses():
    pr_statuses = PullRequestStatus.get_all()
    for prs in pr_statuses:
        print prs.json  # Calling for most of the functions
