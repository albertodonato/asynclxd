from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest

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


@pytest.fixture
def session():
    yield FakeSession()


@pytest.fixture
def upload_file(tmpdir):
    upload_file = Path(tmpdir / "upload")
    upload_file.write_text("data")
    yield upload_file


@pytest.mark.asyncio
class TestRequest:
    async def test_request(self, session):
        """The request call makes an HTTP request and returns a response."""
        session.responses.append(["/1.0"])
        resp = await request(session, "GET", "/")
        assert resp.status == 200
        assert await resp.json() == ["/1.0"]
        assert session.calls == [("GET", "/", None, {}, None)]

    async def test_request_with_content(self, session):
        """The request call can include content in the request."""
        session.responses.append("response data")
        content = {"some": "content"}
        await request(session, "POST", "/", content=content)
        assert session.calls == [
            ("POST", "/", None, {"Content-Type": "application/json"}, content)
        ]

    async def test_request_with_upload_path(self, session, upload_file):
        """The request call can include content from a file."""
        session.responses.append("response data")
        await request(session, "POST", "/", upload=upload_file)
        assert session.calls == [
            ("POST", "/", None, {"Content-Type": "application/octet-stream"}, "data")
        ]

    async def test_request_with_upload_file_descriptor(self, session, upload_file):
        """The request call can include content from a file descriptor."""
        session.responses.append("response data")
        upload = upload_file.open()
        await request(session, "POST", "/", upload=upload)
        assert session.calls == [
            ("POST", "/", None, {"Content-Type": "application/octet-stream"}, "data")
        ]
        # the passed file descriptor is closed
        assert upload.closed

    async def test_request_with_params(self, session):
        """The request call can include params in the request."""
        session.responses.append("response data")
        params = {"a": "param"}
        await request(session, "POST", "/", params=params)
        assert session.calls == [("POST", "/", params, {}, None)]

    async def test_request_with_headers(self, session):
        """The request call can include extra headers in the request."""
        session.responses.append("response data")
        headers = {"X-Sample": "value"}
        await request(session, "POST", "/", headers=headers)
        assert session.calls == [("POST", "/", None, {"X-Sample": "value"}, None)]

    async def test_request_error(self, session):
        """The request call raises an error on failed requests."""
        session.responses.append(make_http_response(status=404, reason="Not found"))
        with pytest.raises(ResponseError) as error:
            await request(session, "GET", "/"),
        exception = error.value
        assert exception.code == 404
        assert exception.message == "Not found"
        assert str(exception) == "API request failed with 404: Not found"

    async def test_request_error_from_payload(self, session):
        """Error details can be obtained from the response payload."""
        session.responses.append(make_error_response("Cancelled", code=401))
        with pytest.raises(ResponseError) as error:
            await request(session, "GET", "/"),
        exception = error.value
        assert exception.code == 401
        assert exception.message == "Cancelled"
        assert str(exception) == "API request failed with 401: Cancelled"

    async def test_request_error_paylod_code_overrides_http(self, session):
        """The error code from the payload takes precedence on the HTTP one."""
        session.responses.append(
            make_error_response("Cancelled", code=401, http_status=400)
        )
        with pytest.raises(ResponseError) as error:
            await request(session, "GET", "/"),
        assert error.value.code == 401


class TestResponse:
    def test_instantiate(self):
        """A Response can be instantiated."""
        headers = {"ETag": "abcde"}
        content = {"type": "sync", "metadata": {"some": "content"}}
        response = Response(FakeRemote(), 200, headers, content)
        assert response.http_code == 200
        assert response.etag == "abcde"
        assert response.type == "sync"
        assert response.metadata == {"some": "content"}

    def test_instantiate_with_binary_content(self):
        """A Response can be instantiated with binary content."""
        content = StringIO("some content")
        response = Response(FakeRemote(), 200, {}, content)
        assert response.type == "raw"
        assert response.metadata is None
        assert response._content is content

    def test_operation_not_async(self):
        """If the response is sync, the operation is None."""
        content = {"type": "sync", "metadata": {"some": "content"}}
        response = Response(FakeRemote(), 200, {}, content)
        assert response.operation is None

    def test_operation_async(self):
        """If the response is async, the operation is defined."""
        metadata = {"some": "content"}
        response = Response(
            FakeRemote(),
            202,
            {"Location": "/operations/op"},
            {"type": "async", "metadata": metadata},
        )
        assert isinstance(response.operation, Operation)
        assert response.operation.uri == "/operations/op"
        assert response.operation.details() == metadata

    @pytest.mark.asyncio
    async def test_write_content(self):
        """Response binary content can be written to file."""
        content = FakeStreamReader(StringIO("some content"))
        response = Response(FakeRemote(), 200, {}, content)
        out_stream = StringIO()
        await response.write_content(out_stream)
        assert out_stream.getvalue() == "some content"

    @pytest.mark.asyncio
    async def test_write_content_not_binary(self):
        """If there's no binary payload, trying to write raises an error."""
        response = Response(FakeRemote(), 200, {}, {"some": "content"})
        with pytest.raises(ValueError) as error:
            await response.write_content(StringIO())
        assert str(error.value) == "No binary payload"

    def test_pprint(self):
        """The pprint method pretty-prints the response."""
        headers = {"ETag": "abcde", "Location": "/some/url"}
        content = {"type": "sync", "metadata": {"some": "content"}}
        response = Response(FakeRemote(), 200, headers, content)
        assert response.pprint() == dedent(
            """\
            {'etag': 'abcde',
             'http-code': 200,
             'location': '/some/url',
             'metadata': {'some': 'content'},
             'type': 'sync'}"""
        )
