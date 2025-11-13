import re

def remove_code_safe(text: str) -> str:
    """
    Elimina blocs i fragments inline de codi C++ del text
    i els substitueix per '[CODI NO DISPONIBLE]'.
    No repeteix el marcador si apareix diverses vegades seguides.
    """

    cpp_indicators = [
        r"^\s*#\s*include\s*<[^>]+>",
        r"^\s*(using\s+namespace\s+std\s*;)",
        r"^\s*(int|void|float|double|char)\s+main\s*\(",
        r"^\s*(class|struct|template)\b",
        r"std::\w+",
        r"\b(?:cout|cin|cerr|clog|endl)\b",
        r"^\s*for\s*\(.*;.*;.*\)",
        r"^\s*while\s*\(.*\)",
        r"^\s*\{|\}\s*$",
        r"\breturn\b",
    ]
    cpp_line_pattern = re.compile("|".join(cpp_indicators))

    text = re.sub(r"```(?:\s*(?:cpp|c\+\+|c)\b)[\s\S]*?```",#r"```(?:cpp|c\+\+)?\s*[\s\S]*?```",
                  "\n[CODI NO DISPONIBLE]\n",
                  text,
                  flags=re.IGNORECASE)

    def replace_if_cpp_block(match):
        block = match.group(0)
        # Si el contingut del bloc coincideix amb algun indicador C++
        if cpp_line_pattern.search(block):
            return "\n[CODI NO DISPONIBLE]\n"
        return block  # sense canvis

    text = re.sub(r"```[\s\S]*?```", replace_if_cpp_block, text)

    lines = text.splitlines()
    clean_lines = []
    code_buffer = []

    def flush_code_buffer():
        # Si hi ha un bloc amb 2 o més línies de codi, el substituïm
        if len(code_buffer) >= 2:
            return ["[CODI NO DISPONIBLE]"]
        else:
            return code_buffer

    for line in lines:
        stripped = line.strip()
        if cpp_line_pattern.search(stripped):
            code_buffer.append(line)
        elif code_buffer:
            clean_lines.extend(flush_code_buffer())
            code_buffer.clear()
            clean_lines.append(line)
        else:
            clean_lines.append(line)

    if code_buffer:
        clean_lines.extend(flush_code_buffer())

    text = "\n".join(clean_lines)

    inline_patterns = [
        r"`[^`]*?;[^`]*?`",
        r"std::\w+(?:\s*<[^>]+>)?(?:\s*<<\s*[^;]+)+;",
        r"(?:std::)?(?:cout|cin|cerr|clog|endl)\b[^;]*;",
        r"std::\w+(?:\s*<[^>]+>)?(?:\s+\w+)?(?:\s*=\s*[^;]+)?;",
        r"\b(int|float|double|char|bool|string)\s+\w+\s*=\s*[^;]+;",
        r"\bfor\s*\([^)]*\)",
        r"\bwhile\s*\([^)]*\)",
        r"\bif\s*\([^)]*\)",
        r"new\s+\w+\s*\([^)]*\)",
        r"delete\s+\w+\s*;",
        r"\breturn\s+[^;]+;",
    ]

    for pat in inline_patterns:
        text = re.sub(pat, "[CODI NO DISPONIBLE]", text)

    # Neteja
    text = re.sub(r"(\[CODI NO DISPONIBLE\]\s*){2,}", "[CODI NO DISPONIBLE]\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text
