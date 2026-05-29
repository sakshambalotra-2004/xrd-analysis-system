"""
tests/test_csv_reader.py
========================
Unit tests for services/csv_reader.py — CSV Reader Module.
"""

import io
import pytest
import pandas as pd

from services.csv_reader import CSVReader, CSVReadError


@pytest.fixture
def reader():
    return CSVReader()


# ---------------------------------------------------------------------------
# Valid CSV inputs
# ---------------------------------------------------------------------------

def _make_bytes(content: str) -> bytes:
    return content.encode("utf-8")


VALID_CSV = """\
2theta (°),Intensity
20.543,40
26.347,100
35.922,10
39.081,6
41.200,55
"""

VALID_CSV_ALT_HEADERS = """\
angle,counts
20.5,40
26.3,100
35.9,10
39.1,6
41.2,55
"""

VALID_CSV_SEMICOLON = """\
2theta;intensity
20.5;40
26.3;100
35.9;10
39.1;6
41.2;55
"""


class TestLoadBytes:
    def test_standard_headers(self, reader):
        df = reader.load_bytes(_make_bytes(VALID_CSV))
        assert list(df.columns) == ["two_theta", "intensity"]
        assert len(df) == 5

    def test_alternative_headers(self, reader):
        df = reader.load_bytes(_make_bytes(VALID_CSV_ALT_HEADERS))
        assert "two_theta" in df.columns
        assert "intensity" in df.columns

    def test_semicolon_delimiter(self, reader):
        df = reader.load_bytes(_make_bytes(VALID_CSV_SEMICOLON))
        assert len(df) == 5

    def test_sorted_by_two_theta(self, reader):
        shuffled = "2theta (°),Intensity\n35.9,10\n20.5,40\n26.3,100\n39.1,6\n41.2,55\n"
        df = reader.load_bytes(_make_bytes(shuffled))
        assert df["two_theta"].is_monotonic_increasing

    def test_float64_dtypes(self, reader):
        df = reader.load_bytes(_make_bytes(VALID_CSV))
        assert df["two_theta"].dtype == "float64"
        assert df["intensity"].dtype == "float64"

    def test_two_theta_range(self, reader):
        df = reader.load_bytes(_make_bytes(VALID_CSV))
        assert df["two_theta"].between(0, 180).all()


# ---------------------------------------------------------------------------
# Invalid / edge-case CSV inputs
# ---------------------------------------------------------------------------

class TestCSVReadErrors:
    def test_missing_two_theta_column(self, reader):
        bad = "angle_x,intensity\n20.5,40\n26.3,100\n35.9,10\n39.1,6\n41.2,55\n"
        with pytest.raises(CSVReadError, match="No 2θ column"):
            reader.load_bytes(_make_bytes(bad))

    def test_missing_intensity_column(self, reader):
        bad = "2theta (°),counts_x\n20.5,40\n26.3,100\n35.9,10\n39.1,6\n41.2,55\n"
        with pytest.raises(CSVReadError, match="No intensity column"):
            reader.load_bytes(_make_bytes(bad))

    def test_too_few_rows(self, reader):
        tiny = "2theta (°),Intensity\n20.5,40\n26.3,100\n"
        with pytest.raises(CSVReadError, match="Too few"):
            reader.load_bytes(_make_bytes(tiny))

    def test_all_nan_intensity(self, reader):
        bad = "2theta (°),Intensity\n20.5,abc\n26.3,def\n35.9,ghi\n39.1,jkl\n41.2,mno\n"
        with pytest.raises(CSVReadError):
            reader.load_bytes(_make_bytes(bad))

    def test_negative_intensity_rows_removed(self, reader):
        csv = "2theta,intensity\n20.5,40\n26.3,-5\n35.9,10\n39.1,6\n41.2,55\n50.0,20\n"
        df = reader.load_bytes(_make_bytes(csv))
        assert (df["intensity"] >= 0).all()

    def test_empty_bytes(self, reader):
        with pytest.raises(CSVReadError):
            reader.load_bytes(b"")