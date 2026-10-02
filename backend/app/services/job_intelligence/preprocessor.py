import re


def clean_job_description(text: str) -> str:
    """
    Clean and normalize raw job description text.

    The goal is to remove formatting noise while preserving
    meaningful job-description content.
    """
    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace non-breaking spaces and tabs.
    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")

    # Normalize repeated whitespace within lines.
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n[ ]*\n+", "\n\n", text)

    # Normalize common bullet characters.
    text = re.sub(r"[•●▪◦‣⁃]", "-", text)

    # Remove spaces around newlines.
    # Remove indentation at the beginning/end of each line
# without joining words across line boundaries.
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)

    # Final whitespace cleanup.
    return text.strip()
