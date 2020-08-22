#!/usr/bin/env python
#
# mopen.py
#
# https://github.com/gokcehan/mopen
#
# File opener using mimetypes and mailcap
#

from __future__ import print_function

import argparse
import mailcap
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description='File opener using mimetypes and mailcap',
        epilog='Mailcap specification can be found at https://tools.ietf.org/html/rfc1524.html')

    parser.add_argument(
        'file',
        nargs='*',
        help=(
            "file path to be opened"
            " (This is first used to guess type when it is not provided."
            " This is then passed to the mailcap command to expand '%%s'."
            " If no file is given, an empty value is passed to the mailcap command."
            " An arbitrary value can also be used if type is provided."
            " For example, value '-' can be used,"
            " which is a common convention to read from stdin by many programs."
            " Commands are executed one by one when multiple files are given.)"))

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="show more information")

    parser.add_argument(
        '-a',
        '--action',
        default='view',
        help=(
            "specify mailcap action to execute"
            " (By default 'view' command is executed,"
            " which is the default non-optional field in mailcap entries."
            " Arbitrary non-standard actions can also be used."
            " Standard input/output/error are connected to the command.)"))

    parser.add_argument(
        '-t',
        '--type',
        help=(
            "specify MIME type"
            " (MIME type is guessed from the file extension by default."
            " MIME type is often specified as a 'type/subtype' pair."
            " It can also be specified as 'type/*' to match all subtypes."
            " A shorthand 'type' can be used for this case.)"))

    parser.add_argument(
        '-e',
        '--encoding',
        help=(
            "specify encoding along with type if the file is compressed"
            " (Encoding is guessed from the file extension by default."
            " Compressed files are first decompressed to a temporary file"
            " and the path of this temporary file is passed to the mailcap command"
            " as the file path to expand '%%s'."
            " Supported encodings are 'gzip', 'bzip2', and 'xz'.)"))

    parser.add_argument(
        '-p',
        '--parameter',
        default=[],
        action='append',
        help=(
            "pass a parameter to the mailcap command"
            " (Parameter is given as a 'name=value' pair"
            " where '%%{name}' is expanded to 'value' in the mailcap command."
            " This option can be given multiple times to pass multiple parameters"
            " each with a single 'name=value' pair.)"))

    args = parser.parse_args()

    if not args.type and args.encoding:
        parser.error('encoding can only be used with type option')

    for arg in args.parameter:
        if '=' not in arg:
            parser.error("expected 'name=value' pair as parameter")

    return args


def decode(fname, enc):
    import tempfile
    tmp = tempfile.NamedTemporaryFile()

    if enc == 'gzip':
        import gzip as mod
    elif enc == 'bzip2':
        import bz2 as mod
    elif enc == 'xz':
        import lzma as mod
    else:
        return None

    with mod.open(fname, 'rb') as f:
        tmp.write(f.read())
        tmp.flush()

    return tmp


def quote(fname):
    if fname == '':
        return ''
    return "'" + fname.replace("'", "'\"'\"'") + "'"


def run():
    args = parse_args()

    caps = mailcap.getcaps()

    if len(args.file) == 0:
        args.file.append('')

    err = False
    for fname in args.file:
        if args.verbose:
            print('file:', fname)

        typ = args.type
        enc = args.encoding

        if not typ:
            import mimetypes
            typ, enc = mimetypes.guess_type(fname, strict=False)

        if not typ:
            print('error: no MIME type found:', fname, file=sys.stderr)
            err = True
            continue

        if args.verbose:
            print('type:', typ)
            print('encoding:', enc)

        if enc:
            tmp = decode(fname, enc)
            if not tmp:
                print('error: encoding not supported:', enc, file=sys.stderr)
                err = True
                continue
            fname = tmp.name

        cmd, ent = mailcap.findmatch(
            caps,
            typ,
            key=args.action,
            filename=quote(fname),
            plist=args.parameter)

        if args.verbose:
            print('command:', cmd)

        if args.verbose:
            print('entry:', ent)

        if not cmd:
            print('error: no', args.action, 'command found:', fname, file=sys.stderr)
            err = True
            continue

        ret = subprocess.call(cmd, shell=True, stdin=sys.stdin)

        if ret != 0:
            print('error: command returned non-zero exit code:', ret, file=sys.stderr)
            err = True
            continue

    if err:
        sys.exit(1)


if __name__ == '__main__':
    run()
