"""Serve the published app on loopback, with cacheable framework files."""
from argparse import ArgumentParser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class DemoHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.startswith("/_framework/"):
            self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Path to published wwwroot")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    handler = partial(DemoHandler, directory=args.directory)
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()
