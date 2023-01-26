class Singleton(object):
    def __new__(cls):
        """ creates a singleton object, if it is not created,
        or else returns the previous singleton object"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance


class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if cls._inst is None:
            cls._inst = super(cls, cls).__new__(cls, *args, **kwargs)
            cls._inst.__init__(*args, **kwargs)
        return cls._inst

    def __init__(cls, name, bases, classdict):
        super(SingletonMeta, cls).__init__(name, bases, classdict)
        cls._inst = None

    def reset(cls, *args, **kwargs):
        del cls._inst
        cls._inst = None
        if args or kwargs:
            cls._inst = cls(*args, **kwargs)
        return cls._inst
