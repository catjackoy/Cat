"""Conservative, dependency-free Lua text utilities.

These routines do not execute Lua and are not a substitute for a parser or a
specialized deobfuscator. Keep transformations conservative to avoid changing
program behavior.
"""
import re
from typing import Dict, List, Tuple


def analyze_lua(source: str) -> Dict[str, object]:
    checks = [
        (r"\bloadstring\s*\(", "Dynamic code loading: loadstring"),
        (r"\bload\s*\(", "Dynamic code loading: load"),
        (r"\bstring\.char\s*\(", "String construction via string.char"),
        (r"\bstring\.byte\s*\(", "Byte extraction via string.byte"),
        (r"\b(bit32|bit)\.(bxor|band|bor|lshift|rshift)\s*\(", "Bitwise operations"),
        (r"\b(getfenv|setfenv|_ENV)\b", "Environment manipulation"),
        (r"\bwhile\s+true\s+do\b", "Potential dispatcher/control-flow loop"),
        (r"\bpcall\s*\(", "Protected call usage"),
        (r"\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}", "Escaped byte sequences"),
        (r"\b(function|local)\s+[A-Za-z_][A-Za-z0-9_]*\s*=", "Named function/local assignments"),
        (r"\bdebug\.(getinfo|getupvalue|setupvalue)\b", "Debug library introspection"),
    ]
    indicators = [label for pattern, label in checks if re.search(pattern, source)]
    if len(source) > 50_000 and len(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source)) > 10_000:
        indicators.append("Large/high-token-count source; manual review may be difficult")
    return {
        "lines": source.count("\n") + (1 if source else 0),
        "characters": len(source),
        "indicators": indicators,
    }


def _decode_escape_match(match: re.Match) -> str:
    token = match.group(0)
    if token.startswith(r"\x") and len(token) == 4:
        try:
            value = int(token[2:], 16)
            return chr(value) if value >= 32 and value != 127 else token
        except ValueError:
            return token
    if len(token) > 1 and token[1:].isdigit():
        try:
            value = int(token[1:])
            return chr(value) if 32 <= value <= 126 else token
        except ValueError:
            return token
    simple = {r"\n": "\n", r"\r": "\r", r"\t": "\t", r"\\": "\\", r'\"': '"', r"\'": "'"}
    return simple.get(token, token)


def decode_strings(source: str) -> str:
    # Only transform escape sequences inside single/double quoted literals.
    # This deliberately avoids long-bracket strings and complex lexer cases.
    string_pattern = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
    escape_pattern = re.compile(r"\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}|\\[nrt\\\"']")
    def replace_string(match: re.Match) -> str:
        literal = match.group(0)
        quote = literal[0]
        body = literal[1:-1]
        decoded = escape_pattern.sub(_decode_escape_match, body)
        # Keep physical newlines escaped inside quoted literals.
        decoded = decoded.replace("\n", r"\n").replace("\r", r"\r")
        return quote + decoded + quote
    return string_pattern.sub(replace_string, source)


def beautify_lua(source: str) -> str:
    """A conservative whitespace pass; does not claim parser-level formatting."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in source.split("\n")]
    # Trim leading/trailing blank lines and collapse excessive blank runs.
    output: List[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 2:
                output.append("")
        else:
            blank_run = 0
            output.append(line)
    return "\n".join(output).strip() + "\n"


def deobfuscate_lua(source: str) -> Tuple[str, List[str]]:
    notes = [
        "Whitespace normalization applied.",
        "Common printable escape sequences decoded where unambiguous.",
        "No Lua code was executed.",
        "This starter does not yet invoke third-party engines such as Unprom, IronBrew2, XHider, or Luraph tools.",
    ]
    cleaned = beautify_lua(decode_strings(source))
    return cleaned, notes
