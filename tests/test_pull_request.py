import random

import pytest

from nudgebot.lib.github.pull_request import PullRequest, PullRequestTag, PRtag,\
    PRstate


@pytest.fixture(scope='module')
def all_pull_requests():
    return PullRequest.get_all(state='open')


@pytest.fixture(scope='function')
def random_tags():
    return [
        PullRequestTag(random.choice([t for t in tag_type]))
        for tag_type in (PRtag, PRstate)
    ]


def test_pull_requests(all_pull_requests):
    for pr in all_pull_requests:
        print pr.json  # Calling for most of the functions


@pytest.mark.parametrize('execution_number', range(7))
def test_pull_request_title_tags(all_pull_requests, random_tags, execution_number):
    """Testing the functionality of setting/removing tags in pull request titles"""
    rand_pr = random.choice(all_pull_requests)
    rand_pr.tags = random_tags
    found_tags = rand_pr.tags
    assert found_tags == random_tags
    del rand_pr.tags
    found_tags = rand_pr.tags
    assert not found_tags
