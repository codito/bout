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
import logging
import click
import tabula
from datetime import datetime
from functools import reduce

logger = logging.getLogger("bout")


def _filter_zero_data(data):
    width = data.get("width", 0.0)
    inner_data = data.get("data", [])

    return None if width == 0.0 and len(inner_data) == 0 else data


def _filter_zero_text(data):
    width = data.get("width", 0.0)
    text = data.get("text", "")

    return None if width == 0.0 and text == "" else data


def _filter_transactions(clean_row, date_field):
    """Filter cleaned up rows to transactions."""
    # Apply mandatory field filters
    try:
        transaction_date = datetime.strptime(clean_row[date_field], "%d/%m/%Y")
        if transaction_date is not None:
            return clean_row
    except ValueError:
        return None


def _transform_credits_on_credit_card(key, text):
    if key == "T-" and text.endswith(" CR"):
        text = text.split(" ")[0]
        key = "T"
    return key, text


def clean(row, profile):
    """Filter cleans a row.

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
    clean_row = {}
    if _filter_zero_data(row) is None:
        # Malformed row, skip
        logger.debug("clean: Malformed row")
        return clean_row

    # Stream mode: handle multiple lines
    if profile == "icici":
        for line in row['data']:
            index = 0
            for cell in line:
                if _filter_zero_text(cell) is not None:
                    clean_row[index] = clean_row.get(index, '') + cell['text']
                index += 1
        logger.debug("clean: Output row = {}".format(clean_row))
        yield clean_row
    elif profile == "icicicc":
        # Lattice mode: multiple lines are already handled
        for line in row['data']:
            index = 0
            clean_row = {}
            for cell in line:
                clean_row[index] = cell['text']
                index += 1
            # if _filter_transactions(clean_row, 0) is not None:
                # logger.debug("clean: Output row = {}".format(clean_row))
                # yield clean_row
            yield clean_row


def to_qif(row, profile, transform):
    """Transform a cleaned up row to qif format.

    Returns:
        string of a particular transaction in qif format

    See wikipedia for more details of QIF format.
    https://en.wikipedia.org/wiki/Quicken_Interchange_Format#Detail_items

    """
    qif = ''
    if profile == 'icici':
        field_map = {
            2: 'D',     # Transaction date
            3: 'N',     # Cheque number
            4: 'M',     # Transaction details
            5: 'T-',    # Withdrawal
            6: 'T'      # Deposit
        }
    elif profile == 'icicicc':
        field_map = {
            0: 'D',     # Transaction date
            2: 'M',     # Transaction details
            6: 'T-',    # Withdrawal
        }

    qif = reduce(lambda x, k: x + "{0}{1}\n".format(k[0], k[1]),
                 (transform(v, row[k]) for k, v in field_map.items()),
                 "")
    qif += '^\n\n'
    return qif


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

    for row in df:
        for r in clean(row, profile):
            click.echo(to_qif(r, profile, _transform_credits_on_credit_card))


if __name__ == '__main__':
    start()
