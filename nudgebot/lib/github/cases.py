import md5
import re
from datetime import datetime

from nudgebot.lib.github.actions import Approve


class Case(object):

    def __init__(self, not_case=False):
        self._not_case = not_case

    def __repr__(self):
        return '<Case {}{}>'.format(('not ' if self._not_case else ''), self.name)

    @property
    def name(self):
        return self.__class__.__name__

    def define_stat_collection(self, stat_collection):
        self._stat_collection = stat_collection

    def check_state(self):
        raise NotImplementedError()

    @property
    def state(self):
        if self._not_case:
            return not self.check_state()
        return self.check_state()

    def _md5(self, *args):
        strings = [str(arg) for arg in args]
        checksum = md5.new()
        checksum.update(str(self._stat_collection.number))
        checksum.update(self.__class__.__name__)
        checksum.update(str(self._not_case))
        for str_ in strings:
            checksum.update(str_)
        return checksum.hexdigest()

    @property
    def hash(self):
        raise NotImplementedError()


class PullRequestHasTitleTag(Case):

    def __init__(self, tag, *args, **kwargs):
        if isinstance(tag, (basestring, re._pattern_type)):
            tag = [tag]
        self._tag_options = tag
        super(PullRequestHasTitleTag, self).__init__(*args, **kwargs)

    def check_state(self):
        for tag in self._tag_options:
            for exists_tag in self._stat_collection.title_tags:
                if (tag.match(exists_tag) if isinstance(tag, re._pattern_type)
                        else tag.lower() == exists_tag.name.lower()):
                        return True
        return False

    @property
    def hash(self):
        return self._md5(*[tag.pattern if isinstance(tag, re._pattern_type) else tag
                           for tag in self._tag_options])


class ReviewerWasSet(Case):

    def __init__(self, level=1, *args, **kwargs):
        self._level = level
        super(ReviewerWasSet, self).__init__(*args, **kwargs)

    def check_state(self):
        return self._level <= len(self._stat_collection.reviewers)

    @property
    def hash(self):
        return self._md5(self._level)


class ReviewerApproved(Case):

    def __init__(self, level=1, *args, **kwargs):
        self._level = level
        super(ReviewerApproved, self).__init__(*args, **kwargs)

    def check_state(self):
        approvals = 0
        for reviewer, state in self._stat_collection.review_states_by_user.items():
            if (reviewer in self._stat_collection.repo.reviewers_pool.reviewers and
                    state == Approve.STATE):
                approvals += 1
        return approvals == self._level

    @property
    def hash(self):
        return self._md5(self._level)


class InactivityForPeriod(Case):

    def __init__(self, days, hours, *args, **kwargs):
        self._days = days
        self._hours = hours
        super(InactivityForPeriod, self).__init__(*args, **kwargs)

    def check_state(self):
        timedelta = datetime.now() - self._stat_collection.last_update
        return timedelta.total_seconds() > (self._days * 86400 + self._hours * 3600)

    @property
    def hash(self):
        return self._md5(self._stat_collection.last_update, self.days, self.hours)


class WaitingForReviewCommentReaction(Case):

    def __init__(self, days, hours, *args, **kwargs):
        self._days = days
        self._hours = hours
        super(WaitingForReviewCommentReaction, self).__init__(*args, **kwargs)

    def check_state(self):
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


class DescriptionInclude(Case):

    def __init__(self, text, *args, **kwargs):
        self._text = text
        super(DescriptionInclude, self).__init__(*args, **kwargs)

    def check_state(self):
        if isinstance(self._text, re._pattern_type):
            return bool(self._text.search(self._stat_collection.description))
        return self._text in self._stat_collection.description

    @property
    def hash(self):
        return self._md5(
            getattr(self._text, 'pattern', self._text),
            self._stat_collection.description
        )
