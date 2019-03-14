class HTTPError(Exception):
    def __init__(self, url, status, reason):
        self.url = url
        self.status = status
        self.reason = reason

        super().__init__(f"{url} responded with {status} {reason}.")
