import md5
import re
import logging
from datetime import datetime

from nudgebot.lib.actions import Approve, RequestChanges
from nudgebot.lib import FlowObject


logging.basicConfig()
logger = logging.getLogger('CasesLogger')
logger.setLevel(logging.INFO)


class Case(FlowObject):
    """A base class for a case"""
    def __init__(self, not_case=False):
        self.not_case = not_case

    def __repr__(self):
        return '<Case {}{} {}>'.format(
            ('not ' if self.not_case else ''), self.__class__.__name__,
            ' '.join(['{}={};'.format(key, val) for key, val in self._properties.items()])
        )

    def check_state(self):
        raise NotImplementedError()

    @property
    def state(self):
        logger.info('Evaluating state of case: {}'.format(self))
        state = self.check_state()
        if self.not_case:
            state = not state
        logger.info('Case state is {}'.format(state))
        return state

    def _md5(self, *args):
        strings = [str(arg) for arg in args]
        checksum = md5.new()
        checksum.update(str(self._pr_statistics.number()))
        checksum.update(self.__class__.__name__)
        checksum.update(str(self.not_case))
        for str_ in strings:
            checksum.update(str_)
        return checksum.hexdigest()


class PullRequestHasTitleTag(Case):

    def __init__(self, tag, *args, **kwargs):
        if isinstance(tag, (basestring, re._pattern_type)):
            tag = [tag]
        self.tag_options = tag
        super(PullRequestHasTitleTag, self).__init__(*args, **kwargs)

    def check_state(self):
        for tag in self.tag_options:
            for exists_tag in self._pr_statistics.title_tags():
                if (tag.match(exists_tag.name) if isinstance(tag, re._pattern_type)
                        else tag.lower() == exists_tag.name.lower()):
                        return True
        return False

    @property
    def hash(self):
        return self._md5(*[tag.pattern if isinstance(tag, re._pattern_type) else tag
                           for tag in self.tag_options])


class ReviewerWasSet(Case):

    def __init__(self, level=1, *args, **kwargs):
        self.level = level
        super(ReviewerWasSet, self).__init__(*args, **kwargs)

    def check_state(self):
        if self.level <= len(self._pr_statistics.reviewers()):
            for reviewer in self._pr_statistics.reviewers():
                if self.level == self._pr_statistics.repo().reviewers_pool.get_level(reviewer):
                    return True
        return False

    @property
    def hash(self):
        return self._md5(self.level)


class ReviewerRequestChanges(Case):

    def __init__(self, level=1, *args, **kwargs):
        self.level = level
        super(ReviewerRequestChanges, self).__init__(*args, **kwargs)

    def check_state(self):
        approvals = 0
        for reviewer, state in self._pr_statistics.review_states_by_user().items():
            if (reviewer in self._pr_statistics.repo().reviewers_pool.reviewers and
                    state == RequestChanges.STATE):
                approvals += 1
        return approvals == self.level

    @property
    def hash(self):
        return self._md5(self.level)


class ReviewerApproved(Case):

    def __init__(self, level=1, *args, **kwargs):
        self.level = level
        super(ReviewerApproved, self).__init__(*args, **kwargs)

    def check_state(self):
        approvals = 0
        for reviewer, state in self._pr_statistics.review_states_by_user().items():
            if (reviewer in self._pr_statistics.repo().reviewers_pool.reviewers and
                    state == Approve.STATE):
                approvals += 1
        return approvals == self.level

    @property
    def hash(self):
        return self._md5(self.level)


class InactivityForPeriod(Case):

    def __init__(self, days, hours, *args, **kwargs):
        self.days = days
        self.hours = hours
        super(InactivityForPeriod, self).__init__(*args, **kwargs)

    def check_state(self):
        timedelta = datetime.now() - self._pr_statistics.last_update()
        return timedelta.total_seconds() > (self.days * 86400 + self.hours * 3600)

    @property
    def hash(self):
        return self._md5(self._pr_statistics.last_update())


class WaitingForReviewCommentReaction(Case):

    def __init__(self, days, hours, *args, **kwargs):
        self.days = days
        self.hours = hours
        super(WaitingForReviewCommentReaction, self).__init__(*args, **kwargs)

    def check_state(self):
        for status in self._pr_statistics.review_comment_reaction_statuses():
            if status['age_seconds'] > (self.days * 86400 + self.hours * 3600):
                return True
        return False

    @property
    def hash(self):
        last_comments_hash = ''.join([
            status['last_comment'].user.login +
            status['last_comment'].created_at.strftime('%d-%m-%y-%H-%M-%S')
            for status in self._pr_statistics.review_comment_reaction_statuses()
        ])
        return self._md5(last_comments_hash, self.days, self.hours)


class DescriptionInclude(Case):

    def __init__(self, text, *args, **kwargs):
        self.text = text
        super(DescriptionInclude, self).__init__(*args, **kwargs)

    def check_state(self):
        if isinstance(self.text, re._pattern_type):
            return bool(self.text.search(self._pr_statistics.description()))
        return self.text in self._pr_statistics.description()

    @property
    def hash(self):
        return self._md5(
            getattr(self.text, 'pattern', self.text),
            self._pr_statistics.description()
        )


class CurrentRepoName(Case):

    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(CurrentRepoName, self).__init__(*args, **kwargs)

    def check_state(self):
        return self._pr_statistics.repo().name == self.name

    @property
    def hash(self):
        return self._md5(self.name)
