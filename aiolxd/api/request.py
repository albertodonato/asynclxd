"""Perform requests to the API."""


class ResponseError(Exception):
    """An API response error."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(
            'API request failed with {code}: {message}'.format(
                code=self.code, message=self.message))


async def request(session, method, path):
    """Perform an API request with the session."""
    headers = {'Content-Type': 'application/json'}
    response = await session.request(method, path, headers=headers)
    return _parse_response(await response.json())


def _parse_response(content):
    """Parse an API reposnse."""
    error_code = content.get('error_code')
    if error_code:
        raise ResponseError(error_code, content.get('error'))

    if content.get('type') == 'sync':
        return content.get('metadata')
