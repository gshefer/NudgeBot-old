import random

from nudgebot.lib.github.pull_request import PullRequestTag, PRstate
from nudgebot.lib.github.cases import NoPullRequestStateSet


def test_no_pr_status_set(all_pull_requests):
    rand_pr = random.choice(all_pull_requests)
    original_tags = rand_pr.tags
    case = NoPullRequestStateSet(rand_pr)
    rand_pr.tags = [PullRequestTag(PRstate.WIP)]
    assert not case.state
    rand_pr.tags = []
    assert case.state
    rand_pr.tags = original_tags
