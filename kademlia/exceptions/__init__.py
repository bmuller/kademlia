class InvalidJsonException(Exception):

    def __init__(self, message):
        MESSAGE_PATTERN = 'Can not parse json : %s'

        super(Exception, self).__init__(MESSAGE_PATTERN.format(message))


class UnauthorizedOperationException(BaseException):

    def __init__(self):
        MESSAGE_PATTERN = 'You are not authorized to perform operation'

        BaseException.__init__(self, MESSAGE_PATTERN)


class InvalidSignException(BaseException):

    def __init__(self, message):
        MESSAGE_PATTERN = 'Signature is not valid: %s'

        BaseException.__init__(self, MESSAGE_PATTERN.format(str(message)))
