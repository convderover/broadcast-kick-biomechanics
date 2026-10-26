"""Local document builds must preserve the exact published PDFs."""
import hashlib
import pytest

# Authoring dependencies are optional for the numerical test suite.
pytest.importorskip("typst")
pytest.importorskip("pypandoc")
import generar_documentos as documents


def test_build_preprint_preserves_published_copies(monkeypatch):
    copies = list((documents.DOCS / "preprint").glob("*.pdf"))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copies}

    def forbidden_build(*args, **kwargs):
        pytest.fail("Published preprint must not be rebuilt from local reading sources")

    monkeypatch.setattr(documents, "build", forbidden_build)
    documents.build_preprint()
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copies}
