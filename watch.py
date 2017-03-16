from pathlib import Path
import os
import logging
import xmlrpc.client
import base64
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Aria2RPCClient():
    def __init__(
            self,
            endpoint='http://localhost:6800',
            secret=None,
            username=None,
            password=None
            ):
        if not endpoint.endswith('/rpc'):
            endpoint = os.path.join(endpoint, '/rpc')

        self.client = xmlrpc.client.ServerProxy('http://localhost:6800/rpc')
        self.token = None
        if secret is not None:
            self.token = "token:" + secret
        elif username is not None and password is not None:
            self.token = ":".join([username, password])

    def pack(self, *args):
        if self.token is None:
            return args
        else:
            return [self.token, *args]

    def add_urls(self, *urls):
        return self.client.aria2.addUri(*self.pack(urls))

    def add_torrent(self, torrent_file):
        torrent = base64.b64encode(torrent_file.read_bytes()).decode()
        return self.client.aria2.addTorrent(*self.pack(torrent))


class Aria2RPCEventHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        if src.suffixes[-2:] == ['.urls', '.txt']:
            self.download_urls(src)
        if src.suffix == '.torrent':
            self.add_torrent(src)

    def download_urls(self, src):
        try:
            urls = src.read_text().splitlines()
        except Exception as e:
            logging.error("%s parse url: %s", src, e)
            return

        for url in urls:
            try:
                guid = self.client.add_urls(url)
                logging.info("Add job %s: %s", guid, url)
            except Exception as e:
                logging.error("%s parse url: %s", src, e)

    def add_torrent(self, src):
        try:
            guid = self.client.add_torrent(src)
            logging.info("Add torrent %s: %s", guid, src)
        except Exception as e:
            logging.error("%s add torrent: %s", src, e)


logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )

dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
dir_path.joinpath('aria2.session').touch(644)

token = None
token_file = dir_path / '.token'
if token_file.exists():
    token = token_file.read_text().strip()


downloads_dir = str(dir_path / 'downloads')
event_handler = Aria2RPCEventHandler(Aria2RPCClient(secret=token))
observer = Observer()
observer.schedule(event_handler, str(downloads_dir))
logging.info("Observe %s", downloads_dir)
observer.start()

try:
    observer.join()
except KeyboardInterrupt:
    observer.stop()
    observer.join()

