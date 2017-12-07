import random

import pytest

from nudgebot.lib.github.users import BotUser
from nudgebot.lib.github.actions import (PullRequestTagSet, PullRequestTagRemove,
                                         AddReviewers, RemoveReviewers,
                                         CreateIssueComment, CreateReviewComment,
                                         RequestChanges, Approve, EditDescription)
from . import REVIEWERS_LOGIN, GREAT_DESCRIPTIONS_TO_TEST


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
    comment = action.run()
    assert action.is_done()
    comment.delete()
    assert not action.is_done()


def test_request_changes(all_others_pull_requests):
    rand_pr = random.choice(all_others_pull_requests)
    action = RequestChanges(rand_pr, BotUser(),
                            body='Please address all comments and fix accordingly')
    action.run()
    assert action.is_done()


def test_approve(all_others_pull_requests):
    rand_pr = random.choice(all_others_pull_requests)
    action = Approve(rand_pr, BotUser(), body='Excellent work!')
    action.run()
    assert action.is_done()


@pytest.mark.parametrize('execution_number', range(3))
def test_create_review_comment(all_others_pull_requests, execution_number):
    rand_pr = random.choice(all_others_pull_requests)
    body = 'This is comment number {}!'.format(execution_number)
    path = random.choice(list(rand_pr.get_commits())[-1].files).filename
    action = CreateReviewComment(rand_pr, BotUser(), body, path, 1)
    comment = action.run()
    assert action.is_done()
    comment.delete()
    assert not action.is_done()


@pytest.mark.parametrize('execution_number', range(2))
def test_edit_description(all_pull_requests, execution_number):
    rand_pr = random.choice(all_pull_requests)
    action = EditDescription(rand_pr, BotUser(),
                             description=random.choice(GREAT_DESCRIPTIONS_TO_TEST))
    action.run()
    assert action.is_done()
    EditDescription(rand_pr, BotUser(),
                    description='').run()
    assert not action.is_done()
