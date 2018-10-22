class JsonSerializable(object):

    @staticmethod
    def __to_dict__(obj):

        if isinstance(obj, JsonSerializable):
            fields = [f for f in dir(obj) if not callable(f) and not f.startswith('__') and f.startswith('_')]
            return {
                key[1:]: JsonSerializable.__to_dict__(obj.__dict__[key]) for key in fields
            }
        elif type(obj) in [str, int, bool, dict, list]:
            return obj
        elif obj is None:
            return obj
        else:
            return str(obj)
