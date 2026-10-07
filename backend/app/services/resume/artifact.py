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

    @property
    def passed(self) -> bool:
        return (
            self.valid_pdf_signature
            and self.byte_size > 100
            and bool(self.extractable_text.strip())
            and not self.missing_expected_text
        )


def validate_pdf_artifact(
    pdf_bytes: bytes,
    expected_text: list[str],
    *,
    extractor: str = "pdftotext",
) -> PdfArtifactReport:
    """Validate PDF signature, parser-visible text, and expected content."""
    if not pdf_bytes.startswith(b"%PDF-"):
        return PdfArtifactReport(False, len(pdf_bytes), "", tuple(expected_text))

    executable = shutil.which(extractor)
    if executable is None:
        raise PdfArtifactError(f"PDF text extractor not found: {extractor}")

    with NamedTemporaryFile(suffix=".pdf") as pdf_file:
        pdf_file.write(pdf_bytes)
        pdf_file.flush()
        try:
            completed = subprocess.run(
                [executable, "-layout", pdf_file.name, "-"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PdfArtifactError("PDF text extraction timed out") from exc

    if completed.returncode != 0:
        raise PdfArtifactError(
            f"PDF text extraction failed: {completed.stderr[-1000:]}"
        )

    return build_pdf_artifact_report(
        pdf_bytes,
        completed.stdout,
        expected_text,
    )


def build_pdf_artifact_report(
    pdf_bytes: bytes,
    extracted_text: str,
    expected_text: list[str],
) -> PdfArtifactReport:
    normalized = extracted_text.casefold()
    missing = tuple(
        value for value in expected_text
        if value.casefold() not in normalized
    )
    return PdfArtifactReport(
        valid_pdf_signature=pdf_bytes.startswith(b"%PDF-"),
        byte_size=len(pdf_bytes),
        extractable_text=extracted_text,
        missing_expected_text=missing,
    )
