import random

import pytest

from nudgebot.lib.github.pull_request import (PullRequest, PullRequestTag, PRtag,
                                              PRstate)
from nudgebot.lib.github.users import BotUser


@pytest.fixture(scope='module')
def all_pull_requests():
    return PullRequest.get_all(state='open')


@pytest.fixture(scope='module')
def all_others_pull_requests(all_pull_requests):
    return [pr for pr in all_pull_requests if pr.owner.login != BotUser().login]


@pytest.fixture(scope='function')
def random_tags():
    return [
        PullRequestTag(random.choice([t for t in tag_type]))
        for tag_type in (PRtag, PRstate)
    ]
