"""Tests for utils/data_loader.py's read_csv_robust / load_file_flexible.

Run with:  pytest tests/test_data_loader.py -v
"""
import io

from utils.data_loader import read_csv_robust


class FakeUploadedFile:
    """Minimal stand-in for streamlit's UploadedFile (BytesIO-like)."""

    def __init__(self, data: bytes, name: str = "test.csv"):
        self._buf = io.BytesIO(data)
        self.name = name

    def seek(self, pos):
        self._buf.seek(pos)

    def read(self):
        return self._buf.read()


class TestReadCsvRobust:
    def test_plain_utf8(self):
        raw = "name,amount\nAda,100\nGrace,200\n".encode("utf-8")
        df, err = read_csv_robust(FakeUploadedFile(raw))
        assert err is None
        assert list(df.columns) == ["name", "amount"]
        assert len(df) == 2

    def test_utf8_bom(self):
        raw = "name,amount\nAda,100\n".encode("utf-8-sig")
        df, err = read_csv_robust(FakeUploadedFile(raw))
        assert err is None
        assert "name" in df.columns  # BOM must not leak into the first column name

    def test_windows_1252_with_accents_and_currency(self):
        """The exact real-world case that broke plain pd.read_csv: an Excel
        'CSV' export in Windows-1252 containing accented names and £/€ signs."""
        text = "name,amount,note\nJos\xe9,100,Caf\xe9 \xa3 receipt\n"
        raw = text.encode("cp1252")
        df, err = read_csv_robust(FakeUploadedFile(raw))
        assert err is None
        assert df.loc[0, "name"] == "José"
        assert "Café" in df.loc[0, "note"]

    def test_latin1_fallback(self):
        raw = "city,pop\nS\xe3o Paulo,12000000\n".encode("latin-1")
        df, err = read_csv_robust(FakeUploadedFile(raw))
        assert err is None
        assert len(df) == 1

    def test_tsv_separator(self):
        raw = "a\tb\n1\t2\n".encode("utf-8")
        df, err = read_csv_robust(FakeUploadedFile(raw), sep="\t")
        assert err is None
        assert list(df.columns) == ["a", "b"]

    def test_empty_file_returns_error(self):
        df, err = read_csv_robust(FakeUploadedFile(b""))
        assert df is None
        assert "empty" in err.lower()

    def test_oversized_file_returns_friendly_error(self):
        # Fabricate a "file" just over the limit without allocating that much
        # real memory in the test: patch the module constant down instead.
        import utils.data_loader as dl
        original_limit = dl.MAX_UPLOAD_MB
        try:
            dl.MAX_UPLOAD_MB = 0  # anything > 0 bytes now "exceeds" the limit
            raw = b"a,b\n1,2\n"
            df, err = dl.read_csv_robust(FakeUploadedFile(raw))
            assert df is None
            assert "MB" in err
        finally:
            dl.MAX_UPLOAD_MB = original_limit

    def test_corrupt_csv_gives_parse_error_not_crash(self):
        # Unbalanced quotes -> pandas C parser error, should be caught and
        # returned as an error message rather than raising.
        raw = 'a,b\n"unterminated quote,1\n'.encode("utf-8")
        df, err = read_csv_robust(FakeUploadedFile(raw))
        # Either it parses leniently or returns a clear error - either way,
        # it must not raise an unhandled exception (the test itself is the
        # assertion: reaching this line means no exception propagated).
        assert df is not None or err is not None
