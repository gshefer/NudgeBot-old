class FlowObject(object):
    """A base class for Flow object"""

    def __setattr__(self, name, value):
        if not hasattr(self, '_properties'):
            super(FlowObject, self).__setattr__('_properties', {})
        if not name.startswith('_'):
            self._properties[name] = str(value)
        return super(FlowObject, self).__setattr__(name, value)

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def properties(self):
        return {name: getattr(self, name) for name in self._properties}

    def load_pr_statistics(self, pr_statistics):
        self._pr_statistics = pr_statistics

    @property
    def hash(self):
        raise NotImplementedError()
