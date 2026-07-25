from src.ui.markdown import normalize_math_delimiters


def test_normalizes_display_and_inline_latex_for_streamlit():
    source = r"Before \(\lambda_1\), then \[\frac{7}{8.5} \approx 0.8235\]"

    rendered = normalize_math_delimiters(source)

    assert r"$\lambda_1$" in rendered
    assert r"$$\frac{7}{8.5} \approx 0.8235$$" in rendered


def test_does_not_rewrite_latex_delimiters_in_fenced_code():
    source = "Example:\n```latex\n\\[x + y\\]\n```"

    assert normalize_math_delimiters(source) == source
