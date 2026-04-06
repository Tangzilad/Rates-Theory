import importlib
import sys
import types


def _streamlit_stub_module() -> types.ModuleType:
    module = types.ModuleType("streamlit")

    class _DummyCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _DummySidebar:
        def selectbox(self, _label, options, index=0):
            return options[index]

    def _noop(*_args, **_kwargs):
        return None

    module.set_page_config = _noop
    module.title = _noop
    module.warning = _noop
    module.header = _noop
    module.write = _noop
    module.markdown = _noop
    module.subheader = _noop
    module.json = _noop
    module.error = _noop
    module.caption = _noop
    module.metric = _noop
    module.pyplot = _noop
    module.stop = _noop
    module.divider = _noop
    module.number_input = lambda *_a, **_k: 0.0
    module.slider = lambda *_a, **_k: 1.0
    module.columns = lambda n: [module for _ in range(n)]
    module.expander = lambda *_a, **_k: _DummyCtx()
    module.tabs = lambda labels: [_DummyCtx() for _ in labels]
    module.sidebar = _DummySidebar()
    return module


def test_streamlit_app_module_import_bootstraps_registry(monkeypatch):
    monkeypatch.setenv("RATES_THEORY_DISABLE_UI_BOOTSTRAP", "1")
    monkeypatch.setitem(sys.modules, "streamlit", _streamlit_stub_module())
    module = importlib.import_module("streamlit_app.app")

    registry = module.build_chapter_registry()
    assert "1" in registry and "18" in registry
