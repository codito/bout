#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO these tests need to be updated for csv parser.

"""Tests for bout."""
import logging
import pytest
from click.testing import CliRunner

import bout


@pytest.fixture
def row():
    """Build a row of pdf statement data parsed in stream mode."""
    return {"extraction_method": "stream", "top": 0.0, "left": 0.0,
            "width": 0.0, "height": 4.1, "data": []}


@pytest.fixture
def icici_data_row():
    """Build a cleaned up row of icici account data."""
    data = ["5", "08/07/2017", "10/07/2017", "-", "SomeDescription", "20000.0",
            "0.0", "27296.69"]
    r = row()
    r["data"].append([_get_cell(x) for x in data])
    return r


@pytest.fixture
def icicicc_data_row():
    """Build a cleaned up row of icici credit card transaction."""
    data = ["14/07/2017", "74143617199000258114409",
            "Some\rDescription", "414", "", "", "20,724.06"]
    r = row()
    r["extraction_method"] = "lattice"
    r["data"].append([_get_cell(x) for x in data])
    return r


def _get_cell(text):
    return {"top": 3.8, "left": 2.2, "width": 5.8, "height": 6.6, "text": text}


def test_clean_ignores_zero_row_data(row):
    r = bout.clean(row)

    assert len(r) == 0


def test_clean_ignores_zero_cell_data(row):
    cell = _get_cell("")
    cell["width"] = 0.0
    row["data"].append([cell, _get_cell("c2")])

    r = bout.clean(row)

    assert r == [["c2"]]


def test_clean_stream_not_merge_cell_data_empty_first_line(row):
    cell = _get_cell("")
    cell["width"] = 0.0
    row["data"].append([cell, _get_cell("c2")])
    row["data"].append([_get_cell("cc2"), _get_cell("c4")])

    r = bout.clean(row)

    assert r == [["cc2", "c2c4"]]


def test_clean_stream_merge_cell_data(row):
    # First line doesn't have empty text, c1 and c will be merged
    row["data"].append([_get_cell("c1"), _get_cell("c2")])
    row["data"].append([_get_cell("c"), _get_cell("c4")])

    r = bout.clean(row)

    assert r == [["c1c", "c2c4"]]


def test_clean_lattice_emits_multiple_lines(row):
    row["extraction_method"] = "lattice"
    row["data"].append([_get_cell("c1"), _get_cell("c2")])
    row["data"].append([_get_cell(""), _get_cell("c4")])

    r = bout.clean(row)

    assert r == [["c1", "c2"], ["", "c4"]]


def test_icici_transaction(mocker, icici_data_row):
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icici_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icici"])

    o = "D10/07/2017\nMSomeDescription\nT-20000.0\n^\n\n\n"
    assert result.exception is None
    assert result.exit_code == 0
    assert o in result.output


def test_icici_transaction_special_chars(mocker, icici_data_row):
    extra_row = {'top': 8.85, 'left': 5.01, 'width': 9.32, 'height': 6.63,
                 'text': '/2017/0'}
    icici_data_row["data"][0].insert(5, extra_row)
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icici_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icici"])

    o = "D10/07/2017\nMSomeDescription /2017/0\nT-20000.0\n^\n\n\n"
    assert result.exception is None
    assert result.exit_code == 0
    assert o in result.output


def test_icicicc_transaction_output_qif(mocker, icicicc_data_row):
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icicicc_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icicicc"])

    o = "D14/07/2017\nMSome\rDescription\nT-20,724.06\n^\n\n\n"
    assert result.exception is None
    assert result.exit_code == 0
    assert o in result.output


def test_icicicc_transaction_credit_output_qif(mocker, icicicc_data_row):
    icicicc_data_row["data"][0][6]["text"] = "20,724.06 CR"
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icicicc_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icicicc"])

    o = "D14/07/2017\nMSome\rDescription\nT20,724.06\n^\n\n\n"
    assert o in result.output


def test_icicicc_transaction_skips_extra_data(mocker, icicicc_data_row):
    icicicc_data_row["data"][0][0]["text"] = "invalid_date"
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icicicc_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icicicc"])

    assert result.exception is None
    assert result.exit_code == 0
    assert not result.output


def test_transaction_output_qif_header(mocker, icicicc_data_row):
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icicicc_data_row]

    result = runner.invoke(bout.start, [".", "--profile", "icicicc"])

    assert result.exception is None
    assert result.exit_code == 0
    assert "!Account\nNMyAccount\nTMyBank\n^\n!Type:Bank\n" in result.output


def test_option_debug_configures_logging(mocker, icici_data_row, caplog):
    runner = CliRunner()
    mocker.patch("tabula.read_pdf").return_value = [icici_data_row]

    result = runner.invoke(bout.start, [".", "--debug", "--profile", "icici"])

    debug = ("bout", logging.INFO, "Verbose messages are enabled.")
    assert result.exception is None
    assert result.exit_code is 0
    assert debug in caplog.record_tuples
