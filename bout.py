#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Bout (read bank-out) extracts transactions from pdf bank statements.

 _                                            _
(_)                                          (_)
(_) _  _  _       _  _  _     _         _  _ (_) _  _
(_)(_)(_)(_)_  _ (_)(_)(_) _ (_)       (_)(_)(_)(_)(_)
(_)        (_)(_)         (_)(_)       (_)   (_)
(_)        (_)(_)         (_)(_)       (_)   (_)     _
(_) _  _  _(_)(_) _  _  _ (_)(_)_  _  _(_)_  (_)_  _(_)
(_)(_)(_)(_)     (_)(_)(_)     (_)(_)(_) (_)   (_)(_)

"""
import io
import logging
import click
import csv
from collections import namedtuple
from datetime import datetime

logger = logging.getLogger("bout")

profiles = {}
Transaction = namedtuple("Transaction",
                         ["id", "date", "payee", "memo", "amount"])
InvalidTransaction = namedtuple("InvalidTransaction", [])


def get_icici_csv(data_row):
    """Convert a transaction row to tuple.

    Details of fields
        0: 'D',     # Transaction date
        2: 'M',     # Transaction details
        3: 'T',     # Deposit
        4: 'T-',    # Withdrawal
    """
    logger.debug("get_icicicsv: Data row = {}".format(data_row))
    columns = len(data_row)
    date = data_row[0].replace('-', '/')
    if _valid_date(date):
        amt = "-{}".format(data_row[4])
        if data_row[3] != 0.0:
            amt = data_row[3]
        return Transaction(id=0,
                           date=date,
                           payee="",      # Empty for ICICI bank account
                           memo=data_row[2],
                           amount=amt)
    return InvalidTransaction()


def get_icicicc_csv(data_row):
    """Convert a transaction row to tuple.

    Details of fields
        0: 'D',     # Transaction date
        2: 'M',     # Transaction details
        5: 'T',     # Amount
    """
    logger.debug("get_icicicsv: Data row = {}".format(data_row))
    date = data_row[0]
    columns = len(data_row)
    if _valid_date(date, date_format="%d/%m/%Y"):
        amt = "-{}".format(data_row[5])
        if data_row[6] == "CR":
            amt = data_row[5]
        return Transaction(id=0,
                           date=date,
                           payee="",      # Empty for ICICI bank account
                           memo=data_row[2],
                           amount=amt)
    return InvalidTransaction()


def qif_header():
    """Print qif header."""
    click.echo("!Account\nNMyAccount\nTMyBank\n^\n!Type:Bank")


def to_qif(transaction):
    """Transform a cleaned up row to qif format.

    Returns:
        string of a particular transaction in qif format

    See wikipedia for more details of QIF format.
    https://en.wikipedia.org/wiki/Quicken_Interchange_Format#Detail_items

    """
    logger.debug("to_qif: Input = {}".format(transaction))
    return "D{0}\nM{1}\nT{2}\n^\n\n"\
        .format(transaction.date, transaction.memo, transaction.amount)


def _valid_date(date_value, date_format="%d/%m/%Y"):
    """Validate a transaction date."""
    try:
        transaction_date = datetime.strptime(date_value, date_format)
        return transaction_date is not None
    except ValueError:
        return False


def _filter_csv_header(doc, header):
    head_skip = False
    mem = io.StringIO()
    with open(doc, encoding='utf-8', mode='r') as f:
        for line in f:
            if line.startswith(header):
                head_skip = True
                continue
            if head_skip and (not line or line.isspace()):
                break
            if head_skip and ',' in line:
                mem.write(line)
    mem.seek(0)
    return csv.reader(mem)


@click.command()
@click.argument("doc", type=click.Path(exists=True))
@click.option("--profile", prompt="Choose a profile", default="icici",
              show_default=True,
              type=click.Choice(["icici", "icicicc"]),
              help="Document type profile.")
@click.option("--debug", is_flag=True, show_default=True,
              help="Show diagnostic messages.")
def start(doc, profile, debug):
    """Bout (read bank-out) extracts transactions from csv bank statements."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.info("Verbose messages are enabled.")

    profiles.update({"icici": get_icici_csv,
                     "icicicc": get_icicicc_csv})

    rows = []
    if profile == "icici":
        header = "DATE,MODE,PARTICULARS,DEPOSITS,WITHDRAWALS,BALANCE"
        rows = _filter_csv_header(doc, header)
    elif profile == "icicicc":
        header = "Date,Sr.No.,Transaction Details,Reward Point Header,Intl.Amount,Amount(in Rs),BillingAmountSign"
        rows = _filter_csv_header(doc, header)

    # row -> clean_row
    # clean_row, profile -> transaction
    # transaction -> qif
    create_transaction = profiles[profile]
    print_header = False
    for r in rows:
        transaction = create_transaction(r)
        if type(transaction) is not InvalidTransaction:
            if not print_header:
                qif_header()
                print_header = True
            click.echo(to_qif(transaction))


if __name__ == '__main__':
    start()
