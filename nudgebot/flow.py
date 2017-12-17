import re

from config import config
from nudgebot.lib.github.cases import (PullRequestHasTitleTag, DescriptionInclude,
                                       ReviewerWasSet, InactivityForPeriod,
                                       ReviewerApproved, WaitingForReviewCommentReaction,
                                       CurrentRepoName)
from nudgebot.lib.github.actions import (PullRequestTitleTagSet, RUN_TYPES,
                                         CreateIssueComment, AddReviewerFromPool,
                                         ReportForInactivity, AskForReviewCommentReactions)

PRstates = ['WIP', 'BLOCKED', 'WIPTEST', 'RFR']

FLOW = {
    CurrentRepoName(config().config.github.repos[0].repo): {
        DescriptionInclude(re.compile('.'), not_case=True): CreateIssueComment(
            'Please add some description to the pull request.'),
        PullRequestHasTitleTag(PRstates, not_case=True):
            [
                PullRequestTitleTagSet('WIP', run_type=RUN_TYPES.ALWAYS),
                CreateIssueComment('Please add a state to the PR title - setting state as [WIP].',
                                   run_type=RUN_TYPES.ALWAYS)
            ],
        PullRequestHasTitleTag('RFR'): {
            ReviewerWasSet(level=1, not_case=True): AddReviewerFromPool(1),
            ReviewerApproved(level=1): {
                ReviewerWasSet(level=2, not_case=True): AddReviewerFromPool(2),
                PullRequestHasTitleTag(re.compile('\d+LP'), not_case=True): PullRequestTitleTagSet('1LP')
            },
            InactivityForPeriod(3, 0): ReportForInactivity(),
            InactivityForPeriod(7, 0): ReportForInactivity(),
            WaitingForReviewCommentReaction(2, 0): AskForReviewCommentReactions(2, 0)
        }
    }
}
