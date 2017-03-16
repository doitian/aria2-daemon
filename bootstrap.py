#!/usr/bin/env python

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import binascii
import os

dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
dir_path.joinpath('aria2.session').touch(644)

token_file = dir_path / '.token'
if token_file.exists():
    token = token_file.read_text().strip()
else:
    token = binascii.hexlify(os.urandom(8)).decode('utf-8')
    token_file.write_text(token)

env = Environment(loader=FileSystemLoader(str(dir_path)))
template = env.get_template("aria2.conf.jinja2")

dir_path.joinpath('aria2.conf').write_text(
        template.render(pwd=dir_path, token=token)
)
