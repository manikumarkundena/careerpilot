from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


class ResumePdfError(RuntimeError):
    """Raised when resume LaTeX cannot be compiled into a valid PDF."""


def compile_latex_to_pdf(
    latex_source: str,
    *,
    output_name: str = "resume.pdf",
    compiler: str = "pdflatex",
) -> bytes:
    """Compile trusted renderer output into a PDF.

    The compiler is invoked without a shell. The temporary build directory
    prevents auxiliary LaTeX files from entering the application workspace.
    """
    if not latex_source.strip():
        raise ResumePdfError("LaTeX source is empty")
    if Path(output_name).name != output_name:
        raise ResumePdfError("output_name must be a filename")

    executable = shutil.which(compiler)
    if executable is None:
        raise ResumePdfError(f"LaTeX compiler not found: {compiler}")

    with TemporaryDirectory(prefix="careerpilot-resume-") as temp_dir:
        workdir = Path(temp_dir)
        tex_path = workdir / "resume.tex"
        pdf_path = workdir / output_name
        tex_path.write_text(latex_source, encoding="utf-8")

        try:
            completed = subprocess.run(
                [
                    executable,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(workdir),
                    str(tex_path),
                ],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ResumePdfError("LaTeX compilation timed out") from exc

        if completed.returncode != 0 or not pdf_path.is_file():
            detail = (completed.stdout + "\n" + completed.stderr).strip()
            raise ResumePdfError(
                f"LaTeX compilation failed: {detail[-2000:]}"
            )

        data = pdf_path.read_bytes()
        if not data.startswith(b"%PDF-") or len(data) < 100:
            raise ResumePdfError("Compiler produced an invalid PDF artifact")

        return data
