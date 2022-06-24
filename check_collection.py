# Copyright (c) 2019-2022 Igalia S.L.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import fnmatch
import glob
import know_failures
import os
import re
import subprocess
import sys

def is_know_failure(error_type, error_message):
    for regexp in know_failures.KNOWN_FAILURES_REGEXP[error_type]:
        if re.search(regexp, error_message):
            return True
    return False

def check_file(args, path):
    directory, name = os.path.split(path)
    stdout_path = os.path.join(directory, "%s.stdout.txt" % name)
    if (args.SKIP_FILE_WITH_STDOUT and os.path.isfile(stdout_path)):
        print("Skipping %s" % path)
        return

    print("Testing %s" % path)
    result = subprocess.run([args.CONTENT_SHELL,
                             "--run-web-tests",
                             "--enable-blink-features=MathMLCore",
                             path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True)
    stdout = open(stdout_path, "w")
    stdout.write(result.stdout)
    stdout.close()
    stderr = open(os.path.join(directory, "%s.stderr.txt" % name), "w")
    stderr.write(result.stderr)
    stderr.close()

    if args.ABORT_ON_LEGACY_MATH:
        for line in result.stdout.splitlines():
            if "LayoutBlockFlow {math}" in line:
                sys.stderr.write(result.stdout)
                print("\n Found legacy <math> layout!")
                sys.exit(1)
        
    new_failures = {}
    for line in result.stderr.splitlines():
        # Check FATAL and ERROR messages.
        groups = re.search(r"^\[[\d:/.]+:(FATAL|ERROR):[^\]]+\] (.+)$", line)
        if not groups:
            continue
        error_type = groups[1]
        error_message = groups[2]
        if is_know_failure(error_type, error_message):
            continue
        if error_type not in new_failures:
            new_failures[error_type] = []
        new_failures[error_type].append(error_message)

    if new_failures:
        sys.stderr.write(result.stderr)
        print("%s contains new failures:" % path)
        for error_type in new_failures:
            for error_message in new_failures[error_type]:
                sys.stderr.write("%s: %s" % (error_type, error_message))

    if "FATAL" in new_failures and args.ABORT_ON_FATAL:
        sys.exit(1)
        
def check_directory(args, path):
    for walk in os.walk(path):
        for page in fnmatch.filter(walk[2], '*.html'):
            check_file(args, os.path.join(walk[0], page))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Run Chromium's content_shell on a collection of "
                     "documents. Known failures are written in "
                     "know_failures.py")
    )
    parser.add_argument("CONTENT_SHELL", help=(
        "Executable to use e.g. chromium or content_shell.")
    )
    parser.add_argument('COLLECTION',
                        help="Path to a directory containing the collection.")

    parser.add_argument('--abort-on-fatal', dest='ABORT_ON_FATAL',
                        action='store_true',
                        help="Abort execution when a new FATAL error is found.")

    parser.add_argument('--abort-on-legacy-math', dest='ABORT_ON_LEGACY_MATH',
                        action='store_true',
                        help=("Abort execution when a <math> tag is laid out "
                              "with legacy layout instead of LayoutNG"))
    
    parser.add_argument('--skip-file-with-stdout', dest='SKIP_FILE_WITH_STDOUT',
                        action='store_true',
                        help=("Do not run test again for files with a "
                              "corresponding stdout.txt output."))

    command_args = parser.parse_args()

    if not os.path.isfile(command_args.CONTENT_SHELL):
        sys.stderr.write("%s does not exist.\n" % command_args.CONTENT_SHELL)
        sys.exit(1)

    if (not os.path.isfile(command_args.COLLECTION) and
        not os.path.isdir(command_args.COLLECTION)):
        sys.stderr.write("%s does not exist.\n" % command_args.COLLECTION)
        sys.exit(1)

    # TODO(fwang): Support archive and URL for big collections.
    if os.path.isdir(command_args.COLLECTION):
        check_directory(command_args, command_args.COLLECTION)
    else:
        check_file(command_args, command_args.COLLECTION)
