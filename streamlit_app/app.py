"""Streamlit entrypoint for Rates-Theory."""

from src import pdf_parser
from src.models import mean_reversion, mvou, options, pca_module, swap_spreads, yield_curve


def main() -> None:
    """Minimal app bootstrap."""
    print("Rates-Theory app scaffold ready.")
    _ = (
        pdf_parser,
        mean_reversion,
        mvou,
        options,
        pca_module,
        swap_spreads,
        yield_curve,
    )


if __name__ == "__main__":
    main()
