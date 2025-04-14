class DummyHttpRequest:
    def __init__(self, method, url, body=None, params=None, route_params=None):
        self.method = method
        self.url = url
        self._body = body or b""
        self.params = params or {}
        self.route_params = route_params or {}

    def get_body(self):
        return self._body