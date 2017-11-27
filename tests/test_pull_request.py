import random

import pytest

from nudgebot.lib.github.pull_request import (PullRequest, PullRequestTag, PRtag,
                                              PRstate)
from nudgebot.lib.github.actions import (PullRequestTagSet, PullRequestTagRemove,
                                         AddReviewers, RemoveReviewers, CreateIssueComment,
                                         BotUser, CreateReviewComment, RequestChanges,
                                         Approve)
from nudgebot.lib.github.users import ReviewerUser


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


def get_random_pull_request(pull_requests, exclude_self=False):
    if exclude_self:
        pull_requests = [pr for pr in pull_requests if pr.owner.login != BotUser().login]
    return random.choice(pull_requests)


def test_pull_requests(all_pull_requests):
    for pr in all_pull_requests:
        print pr.json  # Calling for most of the functions


@pytest.mark.parametrize('execution_number', range(5))
def test_pull_request_title_tags(all_pull_requests, random_tags, execution_number):
    """Testing the functionality of setting/removing tags in pull request titles"""
    rand_pr = get_random_pull_request(all_pull_requests)
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
    rand_pr = get_random_pull_request(all_pull_requests)
    action = AddReviewers(rand_pr, BotUser(), *REVIEWERS_LOGIN)
    action.run()
    assert REVIEWERS_LOGIN[-1] in rand_pr.reviewers
    action = RemoveReviewers(rand_pr, BotUser(), *REVIEWERS_LOGIN)
    action.run()
    assert REVIEWERS_LOGIN[-1] not in rand_pr.reviewers


@pytest.mark.parametrize('execution_number', range(3))
def test_create_issue_comment(all_pull_requests, execution_number):
    rand_pr = get_random_pull_request(all_pull_requests)
    body = 'This is comment number {}!'.format(execution_number)
    action = CreateIssueComment(rand_pr, BotUser(), body)
    comment = action.run()
    assert action.is_done()
    comment.delete()
    assert not action.is_done()


def test_request_changes(all_pull_requests):
    rand_pr = get_random_pull_request(all_pull_requests, exclude_self=True)
    action = RequestChanges(rand_pr, BotUser(),
                            body='Please address all comments and fix accordingly')
    action.run()
    assert action.is_done()


def test_approve(all_pull_requests):
    rand_pr = get_random_pull_request(all_pull_requests, exclude_self=True)
    action = Approve(rand_pr, BotUser(), body='Excellent work!')
    action.run()
    assert action.is_done()


@pytest.mark.parametrize('execution_number', range(3))
def test_create_review_comment(all_pull_requests, execution_number):
    rand_pr = get_random_pull_request(all_pull_requests, exclude_self=True)
    body = 'This is comment number {}!'.format(execution_number)
    path = random.choice(list(rand_pr.get_commits())[-1].files).filename
    action = CreateReviewComment(rand_pr, BotUser(), body, path, 1)
    comment = action.run()
    assert action.is_done()
    comment.delete()
    assert not action.is_done()
