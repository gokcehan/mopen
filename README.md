# Mopen

`mopen` is a file opener using mimetypes and mailcap.
It is a simple command line interface to combine [mimetypes](https://docs.python.org/3/library/mimetypes.html) and [mailcap](https://docs.python.org/3/library/mailcap.html) modules in Python standard library.
First module is used to find the MIME type of a file from its extension, and the second module executes the mailcap command of the MIME type.
An action can be provided to execute the corresponding command in the mailcap entry.
Compressed files are first decompressed to a temporary file using [gzip](https://docs.python.org/3/library/gzip.html), [bz2](https://docs.python.org/3/library/bz2.html), and [lzma](https://docs.python.org/3/library/lzma.html) modules in Python standard library.

## Features

The following features of the mailcap standard are supported in [mailcap](https://docs.python.org/3/library/mailcap.html) module.

- Actions (i.e. `view`, `compose`, `composetyped`, `edit`, and `print`) (any arbitrary action is also possible)
- Test fields (i.e. `test`) (automatically tested)
- File name substitution (i.e. `%s`)
- Type name substitution (i.e. `%t`)
- Parameter substitution (i.e. `%{foo}`)

## Non-Features

The following features of the mailcap standard are not implemented in [mailcap](https://docs.python.org/3/library/mailcap.html) module.

- Flags (i.e. `needsterminal` and `copiousoutput`) are ignored
- Fields (i.e. `description`, `textualnewlines`, `x11-bitmap`, and `nametemplate`) are ignored
- Substitutions for multipart files (i.e. `%F` and `%n`) are ignored

## Installation

You can install `mopen` as a python package using `pip`:

    pip install mopen

Or you can download it from github and put it somewhere in `$PATH`:

    curl https://raw.githubusercontent.com/gokcehan/mopen/master/mopen/mopen.py -o mopen
    chmod +x mopen
    mkdir -p ~/.local/bin
    mv mopen ~/.local/bin

You may create aliases in your shell for quick actions:

    alias medit='mopen -a edit'
    alias mprint='mopen -a print'

Wrapper shell files can be used if aliases are not available (e.g. non-interactive environments).
You may create such files somewhere in `$PATH` as follows:

    mkdir -p ~/.local/bin
    cat << 'EOF' > ~/.local/bin/medit
    #!/bin/sh
    mopen -a edit "$@"
    EOF
    chmod +x ~/.local/bin/medit
    cat << 'EOF' > ~/.local/bin/mprint
    #!/bin/sh
    mopen -a print "$@"
    EOF
    chmod +x ~/.local/bin/mprint

## Usage

Most systems already come bundled with configuration files for MIME types and Mailcap in standard locations.

The following entry shows standard file extensions for `text/plain` MIME type:

    $ grep 'text/plain' /etc/mime.types
    text/plain              txt asc text pm el c h cc hh cxx hxx f90 conf log

You can configure a mailcap command for `text/plain` MIME type with an entry:

    $ cat ~/.mailcap
    text/plain; less %s

You can now use `mopen` as follows:

    $ mopen file.txt
    # executes: less file.txt

You can also use environmental variables in your mailcap commands:

    $ cat ~/.mailcap
    text/plain; $PAGER %s
    $ echo $PAGER
    less
    $ mopen file.txt
    # executes: less file.txt

In fact, you can use any shell syntax in your mailcap commands:

    $ cat ~/.mailcap
    text/plain; [ $(wc -l < %s) -le 10 ] && cat %s || less %s
    $ mopen file.txt
    # executes: [ $(wc -l < dummy.txt) -le 10 ] && cat dummy.txt || less dummy.txt

Mailcap allows different actions to be provided in mailcap entries.
First command in the entry corresponds to the default `view` action.
You can run different actions as follows:

    $ cat ~/.mailcap
    text/plain; less %s; edit=vim %s
    $ mopen -a edit file.txt
    # executes: vim file.txt

Mailcap specification defines `view`, `compose`, `composetyped`, `edit`, and `print` actions, though you can pass any arbitrary action to `mopen` as long as it is defined in the mailcap entry.
An additional `test` action can be provided to test whether an entry should be available or not.
For example, you can check if a display is available before running an image viewer:

    $ grep 'image/png' /etc/mime.types
    image/png					png
    $ cat ~/.mailcap
    image/*; foo %s; test=[ -n "$DISPLAY" ]
    $ mopen file.png
    # views the image with foo if a display is available
    
You can also use this to test whether a program is available to provide fallbacks:

    $ cat ~/.mailcap
    image/*; foo %s; test=[ -x "$(command -v foo)" ]
    image/*; bar %s; test=[ -x "$(command -v bar)" ]
    $ mopen file.png
    # prefers foo over bar when available

Standard IO is connected to the command so you can use `mopen` in pipes.
For example, most programs read from stdin when no argument is given.
If you don't give a filename to `mopen` it expands `%s` in the mailcap command to nothing.
For this use, you need to be explicit about the type since there is no file extension to guess the MIME type from:

    $ cat ~/.mailcap
    text/plain; less %s
    $ seq 10 | mopen -t text
    # opens less with numbers up to 10

Some programs instead use a convention to read from stdin when `-` is given as an argument.
You can similarly give `-` as the filename if you are explicit about the type:

    $ cat ~/.mailcap
    text/plain; vim %s
    $ seq 10 | mopen -t text -
    # opens vim with numbers up to 10

# MIME info

Most systems come bundled with a database of MIME types for standard registered file extensions.
Unfortunately, standard extensions can be insufficient in many cases.
For example a filename with `.py` extension is not known as a Python file.
It is possible to register this extension as a text file by adding it to a configuration file for MIME types:

    $ cat /usr/local/etc/mime.types
    text/plain  py

You can also register it as a different extension type so that you are able to differentiate it from plain text files:

    $ cat /usr/local/etc/mime.types
    text/x-python  py

It can be tedious to manually compose such a database yourself.
Luckily `shared-mime-info` is likely installed in your system and has MIME type information for many common types.
Since this database uses globs to match filenames, you need to convert globs to extensions to be able to use it.
You can use a command similar to the following to achieve that:

**Note:** Make sure `/usr/share/mime/globs` exists and `/usr/local/etc/mime.types` is empty.

    cat /usr/share/mime/globs |         # read type-glob pairs
    sed '/^#/d' |                       # remove comment lines
    sed 's/*\.//' |                     # convert simple globs to extensions
    sed '/[[*]/d' |                     # remove entries still containing globs
    awk -F: '{ e[$1]=e[$1]" "$2 } END { for (t in e) { printf "%-80s%s\n", t, e[t] } } ' |  # group extensions by type
    sort |                              # sort by type
    sudo tee /usr/local/etc/mime.types  # write type-extension pairs

Note that this conversion does not work for all types since globs are more expressive than file extensions, though it works for the vast majority of types.

# Troubleshoot

Run `mopen` with verbose flag:

    mopen -v file.txt

Show mailcap files and entries:

    python -m mailcap

Guess MIME type and encoding of a file from its extension:

    python -m mimetypes -l file.txt

Guess extension of a MIME type:

    python -m mimetypes -l -e text/plain

Show MIME type files:

    python -c 'import pprint; import mimetypes; pprint.pprint(mimetypes.knownfiles)'

Show mapping of extensions to MIME types:

    python -c 'import pprint; import mimetypes; pprint.pprint(mimetypes.types_map)'

Show mapping of extensions to non-standard but common MIME types:

    python -c 'import pprint; import mimetypes; pprint.pprint(mimetypes.common_types)'

Show mapping of extensions to encodings:

    python -c 'import pprint; import mimetypes; pprint.pprint(mimetypes.encodings_map)'

Show mapping of extensions combining MIME type and encoding to separate extensions:

    python -c 'import pprint; import mimetypes; pprint.pprint(mimetypes.suffix_map)'

## Standards

- [Mailcap](https://tools.ietf.org/html/rfc1524.html)
- [MIME Types](https://www.iana.org/assignments/media-types/media-types.xhtml)
- [MIME Apps](https://specifications.freedesktop.org/mime-apps-spec/mime-apps-spec-latest.html)
- [MIME Info](https://specifications.freedesktop.org/shared-mime-info-spec/shared-mime-info-spec-latest.html)
