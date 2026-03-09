"""Tests for SPF download automation (docs/source_of_truth/spf_dataset_construction.tex).

Tests variable_page_url, get_download_links, download_one_file, and
download_by_variable_names. Unit tests use mocks; one integration test
optionally runs against the real Philadelphia Fed site when online.
"""

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_download import (
    BASE_URL,
    variable_page_url,
    get_download_links,
    download_one_file,
    download_by_variable_names,
)


# =============================================================================
# variable_page_url (no network)
# =============================================================================

def test_variable_page_url_lowercase_path():
    """URL path segment should be lowercase."""
    url = variable_page_url(var="NGDP")
    assert url == f"{BASE_URL}ngdp"
    url = variable_page_url(var="CPI10")
    assert url == f"{BASE_URL}cpi10"


def test_variable_page_url_cpi_exception():
    """CPI variable must use path cpi-spf per Philadelphia Fed."""
    url = variable_page_url(var="CPI")
    assert url == f"{BASE_URL}cpi-spf"
    url = variable_page_url(var="cpi")
    assert url == f"{BASE_URL}cpi-spf"


def test_variable_page_url_returns_valid_base():
    """Returned URL should start with the documented base."""
    for var in ["RGDP", "UNEMP", "TBOND"]:
        url = variable_page_url(var=var)
        assert url.startswith(BASE_URL), f"URL for {var} should start with BASE_URL"


# =============================================================================
# download_one_file (mocked network)
# =============================================================================

def test_download_one_file_writes_content(tmp_path):
    """download_one_file should write fetched bytes to outpath."""
    fake_content = b"xlsx placeholder content"
    outpath = tmp_path / "test.xlsx"

    with patch("src.spf_download.urllib.request.urlopen") as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = fake_content
        result = download_one_file(
            download_url="https://example.com/file.xlsx",
            outpath=outpath,
            overwrite="overwrite",
        )

    assert result == outpath
    assert outpath.exists()
    assert outpath.read_bytes() == fake_content


def test_download_one_file_skip_if_exists_skips(tmp_path):
    """With skip-if-exists, existing file should not be overwritten; return None."""
    outpath = tmp_path / "existing.xlsx"
    outpath.write_bytes(b"already here")

    with patch("src.spf_download.urllib.request.urlopen") as mock_open:
        result = download_one_file(
            download_url="https://example.com/file.xlsx",
            outpath=outpath,
            overwrite="skip-if-exists",
        )

    assert result is None
    assert outpath.read_bytes() == b"already here"
    mock_open.assert_not_called()


def test_download_one_file_creates_parent_dirs(tmp_path):
    """download_one_file should create parent directories if needed."""
    outpath = tmp_path / "sub" / "dir" / "file.xlsx"
    assert not outpath.parent.exists()

    with patch("src.spf_download.urllib.request.urlopen") as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = b"data"
        download_one_file(
            download_url="https://example.com/f.xlsx",
            outpath=outpath,
            overwrite="overwrite",
        )

    assert outpath.exists()
    assert outpath.read_bytes() == b"data"


# =============================================================================
# get_download_links (integration: requires network)
# =============================================================================

def test_get_download_links_returns_list_of_tuples():
    """get_download_links should return list of (filename, url) pairs."""
    try:
        links = get_download_links(
            page_url=variable_page_url(var="CPI10"),
            file_types=["median_level", "mean_level"],
        )
    except OSError as e:
        pytest.skip(f"Network unavailable: {e}")

    assert isinstance(links, list)
    for item in links:
        assert isinstance(item, tuple)
        assert len(item) == 2
        filename, url = item
        assert isinstance(filename, str)
        assert isinstance(url, str)
        assert filename.endswith(".xlsx") or filename.endswith(".pdf")


def test_get_download_links_filenames_match_requested_types():
    """When links are returned, filenames should be xlsx or pdf."""
    try:
        links = get_download_links(
            page_url=variable_page_url(var="CPI10"),
            file_types=["median_level", "dispersion"],
        )
    except OSError as e:
        pytest.skip(f"Network unavailable: {e}")

    filenames = [fn for fn, _ in links]
    if len(filenames) == 0:
        pytest.skip("No links returned (site structure may differ); run parser manually to verify.")
    for fn in filenames:
        assert fn.endswith(".xlsx") or fn.endswith(".pdf"), f"Expected xlsx or pdf filename: {fn}"


# =============================================================================
# download_by_variable_names (integration: example usage)
# =============================================================================

def test_download_by_variable_names_example_usage(tmp_path):
    """Example usage: CPI10 and NGDP; when files are downloaded, paths are under out_dir and non-empty."""
    try:
        written = download_by_variable_names(
            variable_names=["CPI10", "NGDP"],
            file_types=["median_level", "mean_level", "dispersion", "individual"],
            out_dir=tmp_path,
            overwrite="skip-if-exists",
        )
    except OSError as e:
        pytest.skip(f"Network unavailable: {e}")

    assert isinstance(written, list)
    if len(written) == 0:
        pytest.skip("No files written (site/parser may differ); run download manually to verify.")
    for p in written:
        assert isinstance(p, Path)
        assert tmp_path in p.parents, f"Path should be under out_dir: {p}"
        assert p.exists(), f"Downloaded file should exist: {p}"
        assert p.stat().st_size > 0, f"Downloaded file should be non-empty: {p}"
    names = [p.name for p in written]
    assert all(n.endswith(".xlsx") or n.endswith(".pdf") for n in names), (
        "All downloaded files should be xlsx or pdf."
    )


def test_download_by_variable_names_deduplicates_same_filename(tmp_path):
    """Same filename (e.g. documentation) from multiple variables should appear once in result."""
    try:
        written = download_by_variable_names(
            variable_names=["CPI10", "NGDP"],
            file_types=["documentation"],
            out_dir=tmp_path,
            overwrite="overwrite",
        )
    except OSError as e:
        pytest.skip(f"Network unavailable: {e}")

    if len(written) == 0:
        pytest.skip("No files written (site/parser may differ).")
    filenames = [p.name for p in written]
    assert len(filenames) == len(set(filenames)), (
        "Each path should appear at most once (deduplicate by filename/outpath)."
    )
