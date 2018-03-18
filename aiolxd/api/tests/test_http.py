from io import StringIO
from pathlib import Path
from textwrap import dedent

from asynctest import TestCase
from fixtures import TestWithFixtures
from toolrack.testing import TempDirFixture

from ..http import (
    request,
    Response,
    ResponseError,
)
from ..resources.operations import Operation
from ..testing import (
    FakeRemote,
    FakeSession,
    FakeStreamReader,
    make_error_response,
    make_http_response,
)


class RequestTests(TestCase, TestWithFixtures):

    def setUp(self):
        super().setUp()
        self.tempdir = self.useFixture(TempDirFixture())
        self.session = FakeSession()

    async def test_request(self):
        """The request call makes an HTTP request and returns a response."""
        self.session.responses.append(['/1.0'])
        resp = await request(self.session, 'GET', '/')
        self.assertEqual(resp.status, 200)
        self.assertEqual(await resp.json(), ['/1.0'])
        self.assertEqual(self.session.calls, [('GET', '/', None, {}, None)])

    async def test_request_with_content(self):
        """The request call can include content in the request."""
        self.session.responses.append('response data')
        content = {'some': 'content'}
        await request(self.session, 'POST', '/', content=content)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None, {'Content-Type': 'application/json'},
              content)])

    async def test_request_with_upload_path(self):
        """The request call can include content from a file."""
        upload_file = Path(self.tempdir.mkfile(content='data'))
        self.session.responses.append('response data')
        await request(self.session, 'POST', '/', upload=upload_file)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None,
              {'Content-Type': 'application/octet-stream'}, 'data')])

    async def test_request_with_upload_file_descriptor(self):
        """The request call can include content from a file descriptor."""
        upload_file = Path(self.tempdir.mkfile(content='data'))
        self.session.responses.append('response data')
        upload = upload_file.open()
        await request(self.session, 'POST', '/', upload=upload)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None,
              {'Content-Type': 'application/octet-stream'}, 'data')])
        # the passed file descriptor is closed
        self.assertTrue(upload.closed)

    async def test_request_with_params(self):
        """The request call can include params in the request."""
        self.session.responses.append('response data')
        params = {'a': 'param'}
        await request(self.session, 'POST', '/', params=params)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', params, {}, None)])

    async def test_request_with_headers(self):
        """The request call can include extra headers in the request."""
        self.session.responses.append('response data')
        headers = {'X-Sample': 'value'}
        await request(self.session, 'POST', '/', headers=headers)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None, {'X-Sample': 'value'}, None)])

    async def test_request_error(self):
        """The request call raises an error on failed requests."""
        self.session.responses.append(
            make_http_response(status=404, reason='Not found'))
        with self.assertRaises(ResponseError) as cm:
            await request(self.session, 'GET', '/'),
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.message, 'Not found')
        self.assertEqual(
            str(cm.exception), 'API request failed with 404: Not found')

    async def test_request_error_from_payload(self):
        """Error details can be obtained from the response payload."""
        self.session.responses.append(
            make_error_response('Cancelled', code=401))
        with self.assertRaises(ResponseError) as cm:
            await request(self.session, 'GET', '/'),
        self.assertEqual(cm.exception.code, 401)
        self.assertEqual(cm.exception.message, 'Cancelled')
        self.assertEqual(
            str(cm.exception), 'API request failed with 401: Cancelled')

    async def test_request_error_paylod_code_overrides_http(self):
        """The error code from the payload takes precedence on the HTTP one."""
        self.session.responses.append(
            make_error_response('Cancelled', code=401, http_status=400))
        with self.assertRaises(ResponseError) as cm:
            await request(self.session, 'GET', '/'),
        self.assertEqual(cm.exception.code, 401)


class ResponseTests(TestCase):

    def test_instantiate(self):
        """A Response can be instantiated."""
        headers = {'ETag': 'abcde'}
        content = {'type': 'sync', 'metadata': {'some': 'content'}}
        response = Response(FakeRemote(), 200, headers, content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.etag, 'abcde')
        self.assertEqual(response.type, 'sync')
        self.assertEqual(response.metadata, {'some': 'content'})

    def test_instantiate_with_binary_content(self):
        """A Response can be instantiated with binary content."""
        content = StringIO('some content')
        response = Response(FakeRemote(), 200, {}, content)
        self.assertEqual(response.type, 'raw')
        self.assertIsNone(response.metadata)
        self.assertIs(response._content, content)

    def test_operation_not_async(self):
        """If the response is sync, the operation is None."""
        content = {'type': 'sync', 'metadata': {'some': 'content'}}
        response = Response(FakeRemote(), 200, {}, content)
        self.assertIsNone(response.operation)

    def test_operation_async(self):
        """If the response is async, the operation is defined."""
        metadata = {'some': 'content'}
        response = Response(
            FakeRemote(), 202, {'Location': '/operations/op'},
            {'type': 'async', 'metadata': metadata})
        self.assertIsInstance(response.operation, Operation)
        self.assertEqual(response.operation.uri, '/operations/op')
        self.assertEqual(response.operation.details(), metadata)

    async def test_write_content(self):
        """Response binary content can be written to file."""
        content = FakeStreamReader(StringIO('some content'))
        response = Response(FakeRemote(), 200, {}, content)
        out_stream = StringIO()
        await response.write_content(out_stream)
        self.assertEqual(out_stream.getvalue(), 'some content')

    async def test_write_content_not_binary(self):
        """If there's no binary payload, trying to write raises an error."""
        response = Response(FakeRemote(), 200, {}, {'some': 'content'})
        with self.assertRaises(ValueError) as cm:
            await response.write_content(StringIO())
        self.assertEqual(str(cm.exception), 'No binary payload')

    def test_pprint(self):
        """The pprint method pretty-prints the response."""
        headers = {'ETag': 'abcde', 'Location': '/some/url'}
        content = {'type': 'sync', 'metadata': {'some': 'content'}}
        response = Response(FakeRemote(), 200, headers, content)
        self.assertEqual(
            dedent("""\
            {'etag': 'abcde',
             'http-code': 200,
             'location': '/some/url',
             'metadata': {'some': 'content'},
             'type': 'sync'}"""),
            response.pprint())
