class SchoologyError(Exception):
    pass


class ConfigError(SchoologyError):
    pass


class FetchError(SchoologyError):
    pass


class ParseError(SchoologyError):
    pass
