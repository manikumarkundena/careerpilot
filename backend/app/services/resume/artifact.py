from __future__ import annotations

from dataclasses import dataclass


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
) -> PdfArtifactReport:
    """Validate basic parser-visible PDF properties.

    Full PDF parsing is intentionally delegated to a later dependency-backed
    implementation. This first gate verifies the artifact contract itself.
    """
    signature_ok = pdf_bytes.startswith(b"%PDF-")
    # pdftotext output is supplied by the caller in the current service
    # boundary; this keeps the core validator deterministic and dependency-free.
    extractable_text = ""
    missing = tuple(expected_text)

    return PdfArtifactReport(
        valid_pdf_signature=signature_ok,
        byte_size=len(pdf_bytes),
        extractable_text=extractable_text,
        missing_expected_text=missing,
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
