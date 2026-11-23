"""Local HTTP regression for exact range reads and fail-closed response handling."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import unittest

from ct_planes import plan_ranges, read_range

OBJECT = bytes(range(24))
ETAG = '"test-revision"'


class RangeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('If-Match') != ETAG or self.headers.get('Range') != 'bytes=6-11':
            self.send_error(400)
            return
        body = OBJECT if self.path == '/ignore-range' else OBJECT[6:12]
        self.send_response(200 if self.path == '/ignore-range' else 206)
        self.send_header('Content-Range', 'bytes 6-11/25' if self.path == '/wrong-range' else 'bytes 6-11/24')
        self.send_header('ETag', '"changed"' if self.path == '/changed' else ETAG)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class NativePlaneRangeTest(unittest.TestCase):
    def test_disjoint_planes_and_duplicate_requests(self):
        key = (0, 0, 0)
        self.assertEqual(plan_ranges([(key, z) for z in (0, 1, 1, 3)], (4, 2, 3)),
                         [(key, 0, 11), (key, 18, 23)])
        with self.assertRaises(ValueError):
            plan_ranges([(key, 4)], (4, 2, 3))

    def test_http_response_validation(self):
        with HTTPServer(('127.0.0.1', 0), RangeHandler) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                self.assertEqual(read_range(base+'/good', 6, 11, object_bytes=24, etag=ETAG), OBJECT[6:12])
                for case in ('ignore-range', 'wrong-range', 'changed'):
                    with self.subTest(case=case), self.assertRaises(ValueError):
                        read_range(base+'/'+case, 6, 11, object_bytes=24, etag=ETAG)
            finally:
                server.shutdown()
                thread.join()


if __name__ == '__main__':
    unittest.main()
