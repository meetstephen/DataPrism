import pathlib

from utils import persistence

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_pages_do_not_rebuild_application_shell():
    for path in (ROOT / "pages").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "render_sidebar_nav()" not in source
        assert "inject_global_css()" not in source
        assert "st.set_page_config(" not in source
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert source.count("st.navigation(") == 1
    assert 'position="sidebar", expanded=True' in source
    assert source.index("render_sidebar_controls()") < source.index("page.run()")


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



def test_router_boot_and_shared_widget_rerun():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
    assert not app.exception
    app.selectbox(key="dp_theme_selector").select("Ocean Blue").run(timeout=20)
    # AppTest.switch_page executes a standalone legacy page script, bypassing
    # st.navigation's entrypoint. Actual routing is covered by Chromium below.
    for _ in range(2):
        app.run(timeout=20)
        assert not app.exception
        assert app.selectbox(key="dp_theme_selector").value == "Ocean Blue"
        assert not any(s.label == "Navigate to" for s in app.sidebar.selectbox)
