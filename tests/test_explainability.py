from core.injection_scanner import InjectionScanner


def test_scan_includes_explainability_field():
    scanner = InjectionScanner()
    # use_llm=False to avoid external calls; explainability should be a dict (possibly empty)
    res = scanner.scan("This is a clean document.", use_llm=False)
    assert hasattr(res, "explainability")
    assert isinstance(res.explainability, dict)
