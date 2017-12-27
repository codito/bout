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
import itertools
import logging
import click
import tabula
from collections import namedtuple
from datetime import datetime
from functools import reduce

logger = logging.getLogger("bout")

profiles = {}
Transaction = namedtuple("Transaction",
                         ["date", "payee", "memo", "amount"])
InvalidTransaction = namedtuple("InvalidTransaction", [])


def get_icici(data_row):
    """Convert a transaction row to a transaction tuple.

    Details of fields
        2: 'D',     # Transaction date
        3: 'N',     # Cheque number
        4: 'M',     # Transaction details
        x: x,       # Extra columns (occasional)
        5: 'T-',    # Withdrawal
        6: 'T'      # Deposit
    """
    logger.debug("get_icici: Data row = {}".format(data_row))
    columns = len(data_row)
    if _valid_date(data_row[2]):
        amt = "-{}".format(data_row[-3])
        if data_row[-2] != "0.0":
            amt = data_row[-2]
        return Transaction(date=data_row[2],
                           payee="",      # Empty for ICICI bank account
                           memo=" ".join(data_row[4:columns-3]),
                           amount=amt)
    return InvalidTransaction()


def get_icicicc(data_row):
    """Convert a transaction row to a transaction tuple.

    Details of fields
        0: 'D',     # Transaction date
        2: 'M',     # Transaction details
        6: 'T-',    # Withdrawal
    """
    logger.debug("get_icicicc: Data row = {}".format(data_row))
    if _valid_date(data_row[0]):
        amt = "-{}".format(data_row[6])
        if amt.endswith(" CR"):
            amt = data_row[6].split(" ")[0]
        return Transaction(date=data_row[0],
                           payee="",      # Empty for ICICI bank account
                           memo=data_row[2],
                           amount=amt)
    return InvalidTransaction()


def clean(row):
    """Clean a parsed data row.

    Multiple lines in a row are merged together.
    Column values which have no text and zero width are ignored.

    A row has the following json specification:
        "extraction_method": "stream",
        "top": 0.0,
        "left": 0.0,
        "width": 939.0,
        "height": 441.1400146484375,
        "data": [
            [
                {
                    "top": 428.54,
                    "left": 182.22,
                    "width": 6.9449920654296875,
                    "height": 6.639999866485596,
                    "text": "1"
                },
                ... more columns
            ],
            ... more lines
        ]
    """
    logger.debug("clean: Input row = {}".format(row))
    if _filter_zero_data(row) is None:
        # Malformed row, skip
        logger.debug("clean: Malformed row")
        return []

    lines = [[d['text'] for d in l] for l in row['data']]
    mode = row["extraction_method"]

    # Lattice mode: multiple lines are already handled
    if mode == "lattice":
        return lines

    # Stream mode: merge multiple lines together
    if mode == "stream":
        def merge_dict(d1, d2):
            return ["{}{}".format(d1[i], d2[i]) for i in range(len(d1))]
        merged_line = reduce(merge_dict, lines)

        # remove entries which have empty data!
        return [[v for v in merged_line if v]]


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


def _filter_zero_data(data):
    width = data.get("width", 0.0)
    inner_data = data.get("data", [])

    return None if width == 0.0 and len(inner_data) == 0 else data


def _filter_zero_text(data):
    width = data.get("width", 0.0)
    text = data.get("text", "")

    return None if width == 0.0 and text == "" else data


def _valid_date(date_value):
    """Validate a transaction date."""
    try:
        transaction_date = datetime.strptime(date_value, "%d/%m/%Y")
        return transaction_date is not None
    except ValueError:
        return False


@click.command()
@click.argument("doc", type=click.Path(exists=True))
@click.option("--password", is_flag=True,
              help="Ask for a password to open the document.")
@click.option("--profile", prompt="Choose a profile", default="icici",
              show_default=True,
              type=click.Choice(["icici", "icicicc"]),
              help="Document type profile.")
@click.option("--debug", is_flag=True, show_default=True,
              help="Show diagnostic messages.")
def start(doc, password, profile, debug):
    """Bout (read bank-out) extracts transactions from pdf bank statements."""
    passval = click.prompt("Password", hide_input=True) if password else None

    lattice = True if profile == 'icicicc' else False
    df = tabula.read_pdf(doc, output_format='json', pages='all',
                         password=passval, lattice=lattice)
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.info("Verbose messages are enabled.")

    profiles.update({"icici": get_icici, "icicicc": get_icicicc})

    # row -> clean_row
    # clean_row, profile -> transaction
    # transaction -> qif
    create_transaction = profiles[profile]
    print_header = False
    for r in itertools.chain.from_iterable(map(clean, df)):
        transaction = create_transaction(r)
        if type(transaction) is not InvalidTransaction:
            if not print_header:
                qif_header()
                print_header = True
            click.echo(to_qif(transaction))


if __name__ == '__main__':
    start()
