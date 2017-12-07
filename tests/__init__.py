from nudgebot.lib.github.users import ReviewerUser


REVIEWERS_LOGIN = [ReviewerUser('jaryn')]
GREAT_DESCRIPTIONS_TO_TEST = [
    """## Summary
Since we have many parameters per resource it's useless to pass default
parameters except name and namespace. Hence we have now 1 generic create function
at ContainersResourceBase which allows to create each resource easily with its required payload.
For each containers resource added 3 additional descriptors (see ContainersResourceBase docstring)
Example:
```python
>>> Project.create(provider, {"metadata": {"name": "foo"}})
>>> <Project name="foo">
```
(more examples in test/test_openshift.py)

**Additional changes in this PR:**
- Added more Create/Delete tests.
- fix ContainersResourceBase.\_\_eq\_\_ - failed in non-namespaced resources
- instead of override ContainersResourceBase.api we are now defining ContainersResourceBase.API

Test results:
- Unit (MOCKED=True):                                    47 passed in 26.44 seconds
- integration (MOCKED=False, real provider):  47 passed in 143.21 seconds
""",
    """API requests against rhv41 provider were resulting in empty results (`list_vm`)
    because of the filter kwarg setting.

At some point we'll need to migrate the entire module to
ovirt-engine-sdk-python 4.1.6+, but not yet.""",
    """The goal of this PR is to get rid of PowerShell and fully replace it with rest calls.
Stucture optimization and refactoring existing methods will be done in separate PRs.""",
    """- Added openshift tests (tests/test_openshift.py)
    - Option to run tests with both mock provider and real provider, default is mock.
- Fix image info parsing which was problematic in case we had more than one ':' in the image name.
  (happens when we have tag, in this case we have 2, one for the ID and one for the tag)"""
]
