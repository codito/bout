#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for bout."""
import pytest
from sure import expect

import bout


@pytest.fixture
def row():
    """Build a row of pdf statement data parsed in stream mode."""
    return {"extraction_method": "stream", "top": 0.0, "left": 0.0,
            "width": 0.0, "height": 4.1, "data": []}


@pytest.fixture
def icici_data():
    """Build a cleaned up row of icici account data."""
    return {0: "5", 1: "08/07/2017", 2: "10/07/2017", 3: "-", 4:
            "SomeDescription", 5: "20000.0", 6:
            "0.0", 7: "27296.69"}


@pytest.fixture
def icicicc_data():
    """Build a cleaned up row of icici credit card transaction."""
    return {0: "14/07/2017", 1: "74143617199000258114409", 2:
            "Some\rDescription", 3: "414", 4: "", 5: "", 6: "20,724.06"}


def _get_cell(text):
    return {"top": 3.8, "left": 2.2, "width": 5.8,
            "height": 6.6, "text": text}


def test_clean_ignores_zero_row_data(row):
    r = list(bout.clean(row, "icici"))

    expect(r).to.have.length_of(0)


def test_clean_ignores_zero_cell_data(row):
    cell = _get_cell("")
    cell["width"] = 0.0
    row["data"].append([cell, _get_cell("c2")])

    r = list(bout.clean(row, "icici"))

    expect(r).to.have.length_of(1)
    expect(r).to.eql([{1: "c2"}])


def test_clean_stream_merge_cell_data_zero_cell(row):
    cell = _get_cell("")
    cell["width"] = 0.0
    row["data"].append([cell, _get_cell("c2")])
    row["data"].append([_get_cell("cc2"), _get_cell("c4")])

    r = list(bout.clean(row, "icici"))

    expect(r).to.have.length_of(1)
    expect(r).to.eql([{0: "cc2", 1: "c2c4"}])


def test_clean_stream_merge_cell_data(row):
    row["data"].append([_get_cell("c1"), _get_cell("c2")])
    row["data"].append([_get_cell(""), _get_cell("c4")])

    r = list(bout.clean(row, "icici"))

    expect(r).to.eql([{0: "c1", 1: "c2c4"}])


def test_clean_lattice_emits_multiple_lines(row):
    row["extraction_method"] = "lattice"
    row["data"].append([_get_cell("c1"), _get_cell("c2")])
    row["data"].append([_get_cell(""), _get_cell("c4")])

    r = list(bout.clean(row, "icicicc"))

    expect(r).to.eql([{0: "c1", 1: "c2"}, {0: "", 1: "c4"}])


def test_qif_for_icici(icici_data):
    q = bout.to_qif(icici_data, "icici",
                    bout._transform_credits_on_credit_card)

    expect(q).to.eql("D10/07/2017\nN-\nMSomeDescription\nT-20000.0\nT0.0"
                     "\n^\n\n")


def test_qif_for_icicicc(icicicc_data):
    q = bout.to_qif(icicicc_data, "icicicc",
                    bout._transform_credits_on_credit_card)

    expect(q).to.eql("D14/07/2017\nMSome\rDescription\nT-20,724.06"
                     "\n^\n\n")


def test_qif_for_icicicc_credit_transaction(icicicc_data):
    icicicc_data[6] = "20,724.06 CR"

    q = bout.to_qif(icicicc_data, "icicicc",
                    bout._transform_credits_on_credit_card)

    expect(q).to.eql("D14/07/2017\nMSome\rDescription\nT20,724.06"
                     "\n^\n\n")
