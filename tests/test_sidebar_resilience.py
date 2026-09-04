import pathlib

from utils import persistence


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_sidebar_uses_native_navigation_only():
    source = (ROOT / "utils" / "styles.py").read_text(encoding="utf-8")
    render_body = source.split("def render_sidebar_nav():", 1)[1].split(
        "def _get_active_theme", 1
    )[0]
    assert "st.page_link" not in render_body
    assert '[data-testid="stSidebarNav"] {{ display: none' not in source


def test_sidebar_does_not_override_streamlit_scroll_ownership():
    source = (ROOT / "utils" / "styles.py").read_text(encoding="utf-8")
    assert '[data-testid="stSidebarContent"] {{\n    overflow-y:' not in source
    assert '[data-testid="stSidebar"] > div {{\n    overflow:' not in source


def test_hosted_local_persistence_is_opt_in(monkeypatch):
    monkeypatch.delenv("DATAPRISM_LOCAL_PERSISTENCE", raising=False)
    assert persistence.is_local_persistence_enabled() is False


def test_corrupt_persisted_text_never_raises_decode_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DATAPRISM_LOCAL_PERSISTENCE", "1")
    monkeypatch.setattr(persistence, "SESSION_DIR", str(tmp_path))
    (tmp_path / "metadata.json").write_bytes(b"\x81\x8d\x90not-json")
    assert persistence.load_json("metadata") is None


def test_legacy_non_utf8_text_is_decoded(tmp_path, monkeypatch):
    monkeypatch.setenv("DATAPRISM_LOCAL_PERSISTENCE", "true")
    monkeypatch.setattr(persistence, "SESSION_DIR", str(tmp_path))
    (tmp_path / "doc_content.txt").write_bytes("caf\u00e9".encode("cp1252"))
    assert persistence.load_text("doc_content") == "caf\u00e9"


def test_data_cleaning_entry_script_is_ascii_safe():
    """Streamlit must be able to discover this page under any host locale."""
    raw = (ROOT / "pages" / "3_Data_Cleaning.py").read_bytes()
    raw.decode("ascii")


def test_data_cleaning_page_boots_without_exception():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "pages" / "3_Data_Cleaning.py"))
    app.run(timeout=15)
    assert not app.exception

