"""SPF download automation per docs/source_of_truth/spf_dataset_construction.tex.

Implements: VariablePageURL, GetDownloadLinks, DownloadOneFile, DownloadByVariableNames.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Literal

OverwritePolicy = Literal["overwrite", "skip-if-exists"]
FileType = Literal[
    "dispersion",
    "median_level",
    "mean_level",
    "median_growth",
    "mean_growth",
    "individual",
    "documentation",
]

BASE_URL = "https://www.philadelphiafed.org/surveys-and-data/"

# Link text snippets and filename patterns for each file type (per SPF doc).
FILE_TYPE_PATTERNS = {
    "dispersion": (
        "Measures of Cross-Sectional Forecast Dispersion",
        re.compile(r"Dispersion_.*\.xlsx", re.I),
    ),
    "median_level": (
        "Median Responses",
        re.compile(r"Median_.*_Level\.xlsx", re.I),
    ),
    "mean_level": (
        "Mean Responses",
        re.compile(r"Mean_.*_Level\.xlsx", re.I),
    ),
    "median_growth": (
        "Annualized Percent Change of Median",
        re.compile(r"Median_.*_Growth\.xlsx", re.I),
    ),
    "mean_growth": (
        "Annualized Percent Change of Mean",
        re.compile(r"Mean_.*_Growth\.xlsx", re.I),
    ),
    "individual": (
        "Individual Responses",
        re.compile(r"Individual_.*\.xlsx", re.I),
    ),
    "documentation": (
        "Documentation",
        re.compile(r"spf-documentation\.pdf", re.I),
    ),
}


def variable_page_url(var: str) -> str:
    """Return the Philadelphia Fed data page URL for a variable.

    Per Algorithm VariablePageURL: path is lowercase; CPI uses cpi-spf.

    Args:
        var: Variable name as on Philadelphia Fed data-files index (e.g. NGDP, CPI10).

    Returns:
        Full URL for the variable's data page.
    """
    path = var.lower()
    if var.upper() == "CPI":
        path = "cpi-spf"
    return f"{BASE_URL}{path}"


def get_download_links(
    page_url: str,
    file_types: list[FileType],
) -> list[tuple[str, str]]:
    """Fetch variable page HTML and return (filename, download_url) for requested types.

    Per Algorithm GetDownloadLinks: fetch page, parse links, match to file_types,
    return list of (filename, download_url).

    Args:
        page_url: URL of the variable data page.
        file_types: Subset of dispersion, median_level, mean_level, median_growth,
            mean_growth, individual, and optionally documentation.

    Returns:
        List of (filename, download_url) for each matched link.
    """
    req = urllib.request.Request(page_url, headers={"User-Agent": "ME3AI-data-pipeline"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode(errors="replace")

    # Find all <a ... href="..."> links (href may appear after other attributes).
    href_re = re.compile(r'<a\s+[^>]*?href="([^"]+)"[^>]*>([^<]*)</a>', re.I | re.DOTALL)
    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    for href, link_text in href_re.findall(html):
        href = href.strip()
        link_text = re.sub(r"\s+", " ", link_text).strip()
        # Resolve relative URLs (Philadelphia Fed uses full URLs in href).
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.philadelphiafed.org" + href

        # Extract filename from URL (last path segment before query).
        path_part = href.split("?")[0]
        filename = path_part.rstrip("/").split("/")[-1]

        for ft in file_types:
            pattern_info = FILE_TYPE_PATTERNS.get(ft)
            if pattern_info is None:
                continue
            _label, pattern = pattern_info
            if pattern.search(filename):
                key = (filename, href)
                if key not in seen:
                    seen.add(key)
                    links.append((filename, href))
                break

    return links


def download_one_file(
    download_url: str,
    outpath: Path,
    overwrite: OverwritePolicy,
) -> Path | None:
    """Download one file from URL to outpath; respect overwrite policy.

    Per Algorithm DownloadOneFile: if skip-if-exists and file exists, return None;
    else download and return outpath.

    Args:
        download_url: Full URL of the file.
        outpath: Local path to write the file.
        overwrite: overwrite or skip-if-exists.

    Returns:
        outpath if file was written, None if skipped.
    """
    if overwrite == "skip-if-exists" and outpath.exists():
        return None
    outpath.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(download_url, headers={"User-Agent": "ME3AI-data-pipeline"})
    with urllib.request.urlopen(req) as resp:
        outpath.write_bytes(resp.read())
    return outpath


def download_by_variable_names(
    variable_names: list[str],
    file_types: list[FileType],
    out_dir: Path,
    overwrite: OverwritePolicy,
) -> list[Path]:
    """Download SPF workbooks for the given variables into out_dir.

    Per Algorithm DownloadByVariableNames: for each variable, get page URL,
    get download links for requested file_types, download each file; deduplicate
    so each path is returned once.

    Args:
        variable_names: List of variable names (e.g. CPI10, NGDP, RGDP).
        file_types: Which file types to download per variable.
        out_dir: Output directory (e.g. data-pipeline/input/).
        overwrite: overwrite or skip-if-exists.

    Returns:
        List of paths to written files in out_dir.
    """
    written: list[Path] = []
    seen: set[Path] = set()

    for var in variable_names:
        page_url = variable_page_url(var=var)
        links = get_download_links(page_url=page_url, file_types=file_types)
        for filename, url in links:
            outpath = out_dir / filename
            result = download_one_file(
                download_url=url,
                outpath=outpath,
                overwrite=overwrite,
            )
            if result is not None and result not in seen:
                seen.add(result)
                written.append(result)

    return written
