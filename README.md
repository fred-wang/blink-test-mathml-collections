# MathML testing

To download collections of MathML documents, run:

    ./configure
    make

The `check_collection.py` script allows to test a collection of MathML documents
and collect any errors. Read the help using

    python3 check_collection.py -h

The `download_mediawiki.sh` script allows to download a specific MediaWiki page
in the mediawiki/ subdirectory.

## Examples

    python3 check_collection.py \
      --abort-on-fatal \
      --abort-on-legacy-math \
      /path/to/chromium/out/Release/content_shell igalia

will run the collection in the igalia/ folder with the specified content_shell
and output corresponding *stderr.txt and *stdout.txt files. It will stop if
a FATAL error occurs or if legacy layout is performed for a <math> tag.

    ./download_mediawiki.sh https://en.wikipedia.org Fourier_transform

will download the https://en.wikipedia.org/wiki/Fourier_transform page. You can
then test that file e.g.

    python3 check_collection.py \
      /path/to/chromium/out/Release/content_shell \
      mediawiki/Fourier_transform.html
