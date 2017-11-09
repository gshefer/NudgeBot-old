import random

import pytest

from nudgebot.lib.github.pull_request import (PullRequest, PullRequestTag, PRtag,
                                              PRstate)
from nudgebot.lib.github.actions import (PullRequestTagSet, PullRequestTagRemove,
                                         AddReviewers, RemoveReviewers, CreateIssueComment,
                                         BotUser)
from nudgebot.lib.github.users import ReviewerUser
from config import config


REVIEWERS_LOGIN = [ReviewerUser('jaryn')]


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


@pytest.mark.parametrize('execution_number', range(5))
def test_pull_request_title_tags(all_pull_requests, random_tags, execution_number):
    """Testing the functionality of setting/removing tags in pull request titles"""
    rand_pr = random.choice(all_pull_requests)
    action = PullRequestTagSet(rand_pr, BotUser(), *random_tags)
    action.run()
    found_tags = rand_pr.tags
    assert found_tags == random_tags
    action = PullRequestTagRemove(rand_pr, BotUser(), *rand_pr.tags)
    action.run()
    found_tags = rand_pr.tags
    assert not found_tags


@pytest.mark.parametrize('execution_number', range(3))
def test_request_reviewer(all_pull_requests, execution_number):
    rand_pr = random.choice(all_pull_requests)
    action = AddReviewers(rand_pr, BotUser(), *REVIEWERS_LOGIN)
    action.run()
    assert REVIEWERS_LOGIN[-1] in rand_pr.reviewers
    action = RemoveReviewers(rand_pr, BotUser(), *REVIEWERS_LOGIN)
    action.run()
    assert REVIEWERS_LOGIN[-1] not in rand_pr.reviewers


@pytest.mark.parametrize('execution_number', range(3))
def test_create_issue_comment(all_pull_requests, execution_number):
    rand_pr = random.choice(all_pull_requests)
    body = 'This is comment number {}!'.format(execution_number)
    action = CreateIssueComment(rand_pr, BotUser(), body)
    action.run()
    assert action.is_done()
    [
        comment for comment in rand_pr.get_issue_comments()
        if comment.body == body and comment.user.login == config().credentials.github.username
    ].pop().delete()
    assert not action.is_done()
