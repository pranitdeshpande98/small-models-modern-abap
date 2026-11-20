import re

IMPLEMENTATION_PATTERN = re.compile(
    r"CLASS\s+\w+\s+IMPLEMENTATION.*?ENDCLASS\s*\.",
    flags=re.DOTALL | re.IGNORECASE,
)


def extract_implementation(generated_text):
    """Return 'CLASS ... IMPLEMENTATION. ... ENDCLASS.' from the model output, or None."""
    match = IMPLEMENTATION_PATTERN.search(generated_text)
    return match.group(0) if match else None


def build_full_class(definition, generated_text):
    """Join our known-good definition with the model's implementation.
    Returns None if the model never wrote an implementation."""
    implementation = extract_implementation(generated_text)
    if implementation is None:
        return None
    return definition.strip() + "\n\n" + implementation.strip() + "\n"