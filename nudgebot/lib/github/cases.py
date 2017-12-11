import md5
from datetime import datetime

from nudgebot.lib.github.pull_request import PRstate
from nudgebot.lib.github.actions import Approve


class Case(object):

    def define_stat_collection(self, stat_collection):
        self._stat_collection = stat_collection

    @property
    def state(self):
        raise NotImplementedError()

    def _md5(self, *args):
        strings = [str(arg) for arg in args]
        checksum = md5.new()
        checksum.update(str(self._stat_collection.number))
        checksum.update(self.__class__.__name__)
        for str_ in strings:
            checksum.update(str_)
        return checksum.hexdigest()

    @property
    def hash(self):
        raise NotImplementedError()


class NoPullRequestStateSet(Case):

    @property
    def state(self):
        return not [tag for tag in self._stat_collection.tags
                    if tag.type == PRstate]

    @property
    def hash(self):
        return self._md5('NoPrState')


class PullRequestHasTag(Case):

    def __init__(self, tag):
        self._tag = tag

    @property
    def state(self):
        return self._tag in self._stat_collection.tags

    @property
    def hash(self):
        return self._md5(self._tag)


class ReviewerNotSet(Case):

    def __init__(self, level=1):
        self._level = level

    @property
    def state(self):
        return self._level > len(self._stat_collection.reviewers)

    @property
    def hash(self):
        return self._md5(self._level)


class ReviewerApproved(Case):

    def __init__(self, level=1):
        self._level = level

    @property
    def state(self):
        approvals = 0
        for state in self._stat_collection.review_states_by_user.values():
            if state == Approve.STATE:
                approvals += 1
        return approvals == self._level

    @property
    def hash(self):
        return self._md5(self._level)


class InactivityForPeriod(Case):

    def __init__(self, days, hours):
        self._days = days
        self._hours = hours

    @property
    def state(self):
        timedelta = datetime.now() - self._stat_collection.last_update
        return timedelta.total_seconds() > (self._days * 86400 + self._hours * 3600)

    @property
    def hash(self):
        return self._md5(self._stat_collection.last_update, self.days, self.hours)


class WaitingForReviewCommentReaction(Case):

    def __init__(self, days, hours):
        self._days = days
        self._hours = hours

    @property
    def state(self):
        for status in self._stat_collection.review_comment_reaction_statuses:
            if status['age_seconds'] > (self._days * 86400 + self._hours * 3600):
                return True
        return False

    @property
    def hash(self):
        last_comments_hash = ''.join([
            status['last_comment'].user.login +
            status['last_comment'].created_at.strftime('%d-%m-%y-%H-%M-%S')
            for status in self._stat_collection.review_comment_reaction_statuses
        ])
        return self._md5(last_comments_hash, self.days, self.hours)
