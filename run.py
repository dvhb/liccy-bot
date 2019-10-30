from licenses import app
from licenses.main.core import LicensesThreading
from licenses.report.confluence import ConfluenceReportThreading

import argparse

parser = argparse.ArgumentParser(prog='Licenses Verification')
parser.add_argument('--with-licenses-collector', dest='with_licenses_collector', action='store_true')
parser.add_argument('--with-confluence-report', dest='with_confluence_report', action='store_true')
args = parser.parse_args()

if __name__ == '__main__':
    if args.with_licenses_collector:
        LicensesThreading(24 * 3600)
    if args.with_confluence_report:
        ConfluenceReportThreading(24 * 3600)
    app.run(use_reloader=False, host='0.0.0.0')
