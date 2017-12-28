# Bout `1.0.0`
Parse bank statements (pdf) and export them to qif format.

[![Linux Build Status](https://img.shields.io/travis/codito/bout.svg)](https://travis-ci.org/codito/bout)
[![Windows Build status](https://img.shields.io/appveyor/ci/codito/bout.svg)](https://ci.appveyor.com/project/codito/bout)
[![codecov coverage](https://img.shields.io/codecov/c/github/codito/bout.svg)](http://codecov.io/github/codito/bout?branch=master)
[![PyPI](https://img.shields.io/pypi/v/bout.svg)](https://pypi.python.org/pypi/bout)

Supports *ICICI* bank and credit card statements out of box. Contributions are
most welcome for adding support for another bank. Create an
[issue](https://github.com/codito/bout/issues/new) to start.

# Installation

    pip install bout

# Usage

    $ # convert an ICICI statement to qif
    $ bout ~/Downloads/icici_statement.pdf --profile icici > /tmp/icici.qif
    $ cat /tmp/icici.qif
    !Account
    NMyAccount
    TMyBank
    ^
    !Type:Bank
    D01/07/2017
    MBIL/12419860068/VF M Jun 17/344548182
    T-354.56
    ^

    $ # convert a password protected ICICI Credit Card statement
    $ bout ~/Downloads/cc_jun.pdf --profile icicicc --password 21@3 > /tmp/icicicc.qif
    $ cat /tmp/icicicc.qif
    !Account
    NMyAccount
    TMyBank
    ^
    !Type:Bank
    D14/06/2017
    MAPOLLO HOSPITALS HYDERABAD IN
    T-60.00
    ^

    $ # print verbose messages to diagnose conversion
    $ bout ~/Downloads/cc_jun.pdf --debug --profile icicicc > /tmp/icicicc.qif

# Contribute
Please try `bout` and file any issues at github issues page. Your patches are
welcome!
