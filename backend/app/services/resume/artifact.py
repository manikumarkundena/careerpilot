from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from tempfile import NamedTemporaryFile


class PdfArtifactError(RuntimeError):
    """Raised when a PDF cannot be inspected for parser-visible text."""


@dataclass(slots=True, frozen=True)
class PdfArtifactReport:
    valid_pdf_signature: bool
    byte_size: int
    extractable_text: str
    missing_expected_text: tuple[str, ...]
    page_count: int | None = None

    @property
    def passed(self) -> bool:
        return (
            self.valid_pdf_signature
            and self.byte_size > 100
            and bool(self.extractable_text.strip())
            and not self.missing_expected_text
            and (self.page_count is None or self.page_count <= 1)
        )


def validate_pdf_artifact(
    pdf_bytes: bytes,
    expected_text: list[str],
    *,
    extractor: str = "pdftotext",
    inspector: str = "pdfinfo",
) -> PdfArtifactReport:
    """Validate PDF signature, page count, parser-visible text, and expected content."""
    if not pdf_bytes.startswith(b"%PDF-"):
        return PdfArtifactReport(False, len(pdf_bytes), "", tuple(expected_text))

    extractor_path = shutil.which(extractor)
    if extractor_path is None:
        raise PdfArtifactError(f"PDF text extractor not found: {extractor}")
    inspector_path = shutil.which(inspector)
    if inspector_path is None:
        raise PdfArtifactError(f"PDF page inspector not found: {inspector}")

    with NamedTemporaryFile(suffix=".pdf") as pdf_file:
        pdf_file.write(pdf_bytes)
        pdf_file.flush()
        try:
            extracted = subprocess.run(
                [extractor_path, "-layout", pdf_file.name, "-"],
                capture_output=True, text=True, timeout=15, check=False,
            )
            inspected = subprocess.run(
                [inspector_path, pdf_file.name],
                capture_output=True, text=True, timeout=15, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PdfArtifactError("PDF inspection timed out") from exc

    if extracted.returncode != 0:
        raise PdfArtifactError(f"PDF text extraction failed: {extracted.stderr[-1000:]}")
    if inspected.returncode != 0:
        raise PdfArtifactError(f"PDF page inspection failed: {inspected.stderr[-1000:]}")

    page_count = None
    for line in inspected.stdout.splitlines():
        if line.lower().startswith("pages:"):
            try:
                page_count = int(line.split(":", 1)[1].strip())
            except ValueError as exc:
                raise PdfArtifactError("PDF page inspector returned an invalid page count") from exc
            break
    if page_count is None or page_count < 1:
        raise PdfArtifactError("PDF page inspector did not return a valid page count")

    return build_pdf_artifact_report(
        pdf_bytes, extracted.stdout, expected_text, page_count=page_count,
    )


def build_pdf_artifact_report(
    pdf_bytes: bytes,
    extracted_text: str,
    expected_text: list[str],
    *,
    page_count: int | None = None,
) -> PdfArtifactReport:
    normalized = extracted_text.casefold()
    missing = tuple(
        value for value in expected_text if value.casefold() not in normalized
    )
    return PdfArtifactReport(
        valid_pdf_signature=pdf_bytes.startswith(b"%PDF-"),
        byte_size=len(pdf_bytes),
        extractable_text=extracted_text,
        missing_expected_text=missing,
        page_count=page_count,
    )
