from licenses import app
from licenses.main.core import LicensesThreading

import argparse

parser = argparse.ArgumentParser(prog='Licenses Verification')
parser.add_argument('--with-licenses-collector', dest='with_licenses_collector', action='store_true')
args = parser.parse_args()

if __name__ == '__main__':
    if args.with_licenses_collector:
        LicensesThreading(24 * 3600)
    app.run(debug=True)
