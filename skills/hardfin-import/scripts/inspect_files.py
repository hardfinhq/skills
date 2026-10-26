# Copyright (c) 2026. Hardfin, Inc. All rights reserved.
"""Inspect spreadsheet metadata using only the Python standard library.

Usage: python3 inspect_files.py [--json] [--values <folder>] <file or folder> [...]
Folders are inspected without recursion; findings are printed to stdout.
"""

import argparse
import csv
import io
import json
import posixpath
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree as ET


MAX_ENTRIES = 20
MAX_VALUE_LENGTH = 80
# A column with more quoted delimiters than this, such as addresses, is summarized rather than listed.
QUOTED_LIST_LIMIT = 3
FORMULA_EXAMPLES = 5
LONG_NUMBER_DIGITS = 15
BOTTOM_ROWS = 10
SNIFFER_SAMPLE_LENGTH = 65536
MAX_NAME_DEPTH = 10
HEADER_TEXT_FRACTION = 0.5
SEP_DIRECTIVE = re.compile(r"sep=([^\r\n])(?:\r\n|\r|\n)", re.I)
CUSTOM_FORMAT_START = 164
DATE_SYSTEM_OFFSET = 1462
SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60
EXCEL_LEAP_DAY = 60
UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".csv", ".tsv", ".txt"}
UNSUPPORTED_REASONS = {
    ".xls": "Legacy binary Excel format",
    ".numbers": "Apple Numbers format",
    ".ods": "OpenDocument spreadsheet format",
    ".pdf": "PDF document format",
}
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CELL_REFERENCE = re.compile(r"^([A-Z]+)([0-9]+)$")
NUMBER_TEXT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
LEADING_ZERO = re.compile(r"^[+-]?0\d+(?:\.\d*)?$")
IDENTIFIER_HEADER = re.compile(r"sku|serial|identifier|\bid\b|code|tag|postal|zip", re.I)
TOTAL_TEXT = re.compile(r"^(?:grand\s+total|sub\s*total|total|sum|count)\b", re.I)
BUILTIN_FORMATS = {
    0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00",
    9: "0%", 10: "0.00%", 11: "0.00E+00", 12: "# ?/?", 13: "# ??/??",
    14: "mm-dd-yy", 15: "d-mmm-yy", 16: "d-mmm", 17: "mmm-yy",
    18: "h:mm AM/PM", 19: "h:mm:ss AM/PM", 20: "h:mm", 21: "h:mm:ss",
    22: "m/d/yy h:mm", 37: "#,##0 ;(#,##0)", 38: "#,##0 ;[Red](#,##0)",
    39: "#,##0.00;(#,##0.00)", 40: "#,##0.00;[Red](#,##0.00)",
    45: "mm:ss", 46: "[h]:mm:ss", 47: "mmss.0", 48: "##0.0E+0", 49: "@",
}
BUILTIN_DATE_IDS = set(range(14, 23)) | set(range(27, 37)) | set(range(45, 48)) | set(range(50, 59))
INDEXED_COLORS = (
    "000000", "FFFFFF", "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF", "00FFFF",
    "000000", "FFFFFF", "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF", "00FFFF",
    "800000", "008000", "000080", "808000", "800080", "008080", "C0C0C0", "808080",
    "9999FF", "993366", "FFFFCC", "CCFFFF", "660066", "FF8080", "0066CC", "CCCCFF",
    "000080", "FF00FF", "FFFF00", "00FFFF", "800080", "800000", "008080", "0000FF",
    "00CCFF", "CCFFFF", "CCFFCC", "FFFF99", "99CCFF", "FF99CC", "CC99FF", "FFCC99",
    "3366FF", "33CCCC", "99CC00", "FFCC00", "FF9900", "FF6600", "666699", "969696",
    "003366", "339966", "003300", "333300", "993300", "993366", "333399", "333333",
)


def tag(name):
    """Return a spreadsheet XML name."""
    return "{%s}%s" % (MAIN_NS, name)


def quoted(value):
    """Quote a bounded value as inert report data."""
    value = str(value)
    if len(value) > MAX_VALUE_LENGTH:
        value = value[:MAX_VALUE_LENGTH - 1] + "…"

    return json.dumps(value, ensure_ascii=False)


def truth(value):
    """Read an XML boolean."""
    return value in ("1", "true", "on")


def column_number(letters):
    """Convert a column label to its one-based number."""
    result = 0
    for letter in letters:
        result = result * 26 + ord(letter) - ord("A") + 1

    return result


def column_letter(number):
    """Convert a one-based column number to its label."""
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(ord("A") + remainder) + result

    return result


def finding(findings, kind, location, detail, entries=None):
    """Append a finding with a bounded list of examples."""
    item = {"kind": kind, "location": location, "detail": detail}
    if entries is not None:
        item.update(entries=entries[:MAX_ENTRIES], count=len(entries),
                    omitted=max(0, len(entries) - MAX_ENTRIES))

    findings.append(item)


def relationships(archive, part):
    """Resolve relationship targets relative to their owning part."""
    directory, filename = posixpath.split(part)
    path = posixpath.join(directory, "_rels", filename + ".rels")
    if path not in archive.namelist():
        return {}

    result = {}
    for relation in ET.fromstring(archive.read(path)):
        if relation.get("TargetMode") == "External":
            continue

        target = relation.attrib["Target"]
        resolved = target.lstrip("/") if target.startswith("/") else posixpath.join(directory, target)
        result[relation.attrib["Id"]] = (posixpath.normpath(resolved), relation.attrib["Type"])

    return result


def rich_text(element):
    """Read text runs without phonetic annotations."""
    return "".join(node.text or "" for node in element.iter(tag("t"))
                   if node not in element.findall(".//" + tag("rPh") + "/" + tag("t")))


def partial_strikethrough(element):
    """Read struck and unstruck text from a mixed rich string."""
    struck, unstruck = [], []
    # Only strings with both struck and unstruck text need a partial-strikethrough finding.
    for node in element:
        if node.tag == tag("r"):
            text = rich_text(node)
            strike = node.find(tag("rPr") + "/" + tag("strike"))
            target = struck if strike is not None and truth(strike.get("val", "1")) else unstruck
        elif node.tag == tag("t"):
            text = node.text or ""
            target = unstruck
        else:
            continue

        if text:
            target.append(text)

    return (struck, unstruck) if struck and unstruck else None


def color_name(element, theme, indexed):
    """Describe an Excel color and any tint."""
    if element is None:
        return None

    # A color can be stored directly or refer to a workbook palette.
    if "rgb" in element.attrib:
        name = element.attrib["rgb"][-6:]
    elif "theme" in element.attrib:
        index = int(element.attrib["theme"])
        name = theme[index] if index < len(theme) else "Theme %d" % index
    elif "indexed" in element.attrib:
        index = int(element.attrib["indexed"])
        name = indexed[index] if index < len(indexed) else "Indexed %d" % index
    else:
        name = "Automatic"

    tint = element.get("tint")
    if tint and float(tint):
        name += " (tint %s)" % tint

    return name


def read_styles(archive, parts):
    """Read cell appearance and number formats."""
    theme = []
    theme_path = next((path for path, kind in parts.values() if kind.endswith("/theme")), None)
    if theme_path:
        root = ET.fromstring(archive.read(theme_path))
        scheme = root.find(".//{%s}clrScheme" % DRAWING_NS)
        if scheme is not None:
            for color in scheme:
                child = next(iter(color), None)
                theme.append(child.get("lastClr", child.get("val", "Unknown")) if child is not None else "Unknown")

            # The scheme lists dark before light, but a cell's theme index counts light first, as lt1, dk1, lt2, dk2.
            theme[0:4] = [theme[i] for i in (1, 0, 3, 2) if i < len(theme)]

    path = next((path for path, kind in parts.values() if kind.endswith("/styles")), None)
    root = ET.fromstring(archive.read(path)) if path else ET.Element(tag("styleSheet"))
    indexed_nodes = root.findall(tag("colors") + "/" + tag("indexedColors") + "/" + tag("rgbColor"))
    indexed = [node.get("rgb", "")[-6:] for node in indexed_nodes] or INDEXED_COLORS
    fills = []
    # Pattern and gradient fills both carry colors that a value-only read omits.
    for fill in root.findall(tag("fills") + "/" + tag("fill")):
        pattern = fill.find(tag("patternFill"))
        if pattern is not None and pattern.get("patternType", "none") not in ("none", "gray125"):
            colors = [color_name(pattern.find(tag(name)), theme, indexed) for name in ("fgColor", "bgColor")]
            fills.append(pattern.get("patternType", "pattern") + " fill " + "/".join(color for color in colors if color))
        elif fill.find(tag("gradientFill")) is not None:
            colors = [color_name(node, theme, indexed) for node in fill.findall(".//" + tag("color"))]
            fills.append("Gradient fill " + "/".join(colors))
        else:
            fills.append(None)

    fonts = []
    for font in root.findall(tag("fonts") + "/" + tag("font")):
        strike = font.find(tag("strike"))
        fonts.append((color_name(font.find(tag("color")), theme, indexed),
                      strike is not None and truth(strike.get("val", "1"))))

    formats = dict(BUILTIN_FORMATS)
    formats.update({int(node.attrib["numFmtId"]): node.attrib["formatCode"]
                    for node in root.findall(tag("numFmts") + "/" + tag("numFmt"))})
    styles = []
    bases = root.findall(tag("cellStyleXfs") + "/" + tag("xf"))
    # Missing cell attributes inherit the corresponding named style attributes.
    for node in root.findall(tag("cellXfs") + "/" + tag("xf")):
        base_id = int(node.get("xfId", "0"))
        attributes = dict(bases[base_id].attrib) if base_id < len(bases) else {}
        attributes.update(node.attrib)
        fill_id = int(attributes.get("fillId", "0"))
        font_id = int(attributes.get("fontId", "0"))
        format_id = int(attributes.get("numFmtId", "0"))
        font_color, strike = fonts[font_id] if font_id < len(fonts) else (None, False)
        styles.append({"fill": fills[fill_id] if fill_id < len(fills) else None,
                       "font": font_color, "strike": strike, "format_id": format_id,
                       "format": formats.get(format_id, "Builtin format %d" % format_id),
                       "quote_prefix": truth(attributes.get("quotePrefix"))})

    return styles or [{"fill": None, "font": None, "strike": False, "format_id": 0,
                      "format": "General", "quote_prefix": False}]


def read_cells(root, shared, styles):
    """Read stored cells and their effective row or column styles."""
    cells = []
    columns = root.findall(tag("cols") + "/" + tag("col"))
    # A cell's explicit style takes precedence over row and column defaults.
    for row in root.findall(tag("sheetData") + "/" + tag("row")):
        for node in row.findall(tag("c")):
            reference = node.attrib["r"]
            match = CELL_REFERENCE.fullmatch(reference)
            if match is None:
                raise ValueError("Invalid cell reference: " + quoted(reference))

            col = column_number(match.group(1))
            column_style = next((item.get("style", "0") for item in columns
                                 if int(item.attrib["min"]) <= col <= int(item.attrib["max"])), "0")
            style_id = int(node.get("s", row.get("s", column_style)))
            kind = node.get("t", "n")
            value = node.findtext(tag("v"), "")
            text_node = None
            if kind == "s":
                text_node = shared[int(value)] if value else None
            elif kind == "inlineStr":
                text_node = node.find(tag("is"))

            if kind in ("s", "inlineStr"):
                value = rich_text(text_node) if text_node is not None else ""

            formula = node.find(tag("f"))
            cells.append({"ref": reference, "row": int(match.group(2)), "col": col,
                          "value": value, "text": kind in ("s", "inlineStr", "str"),
                          "numeric": kind == "n" and value != "", "error": kind == "e",
                          "boolean": kind == "b",
                          "formula": formula is not None,
                          "style": styles[style_id],
                          "partial_strike": partial_strikethrough(text_node) if text_node is not None else None})

    return cells


def header_guess(cells):
    """Find the first row whose populated width is at least half text."""
    populated = [cell for cell in cells if cell["value"] != ""]
    if not populated:
        return None, {}

    width = max(cell["col"] for cell in populated) - min(cell["col"] for cell in populated) + 1
    rows = defaultdict(list)
    for cell in populated:
        rows[cell["row"]].append(cell)

    # A header labels the rows below it, so the last populated row is data even when it is mostly text.
    for row, members in sorted(rows.items())[:-1]:
        texts = [cell for cell in members if cell["text"] and cell["value"].strip()]
        if len(texts) >= width * HEADER_TEXT_FRACTION:
            return row, {cell["col"]: cell["value"] for cell in texts}

    return None, {}


def column_label(col, headers):
    """Label a column with its number and available header."""
    header = " (%s)" % quoted(headers[col]) if col in headers else ""
    return "Column %s [%d]%s" % (column_letter(col), col, header)


def cell_label(cell, headers):
    """Label a cell with its available header."""
    header = " (%s)" % quoted(headers[cell["col"]]) if cell["col"] in headers else ""
    return cell["ref"] + header


def cell_entry(cell, headers):
    """Describe a cell's stored value."""
    value = "value " + quoted(cell["value"]) if cell["value"] else "value empty"
    return cell_label(cell, headers) + ": " + value


def invisible_entry(cell, headers):
    """Describe invisible characters in a cell's text."""
    value = cell["value"]
    first = len(value) - len(value.lstrip("\r\n"))
    last = len(value.rstrip("\r\n"))
    # Line breaks within multiline values are records' content, while edge controls need attention.
    codes = sorted({ord(char) for index, char in enumerate(value)
                    if unicodedata.category(char) in ("Cf", "Cc")
                    and not (char in "\r\n" and first <= index < last)})
    if codes:
        return cell_label(cell, headers) + ": " + ", ".join("U+%04X" % code for code in codes)

    return None


def inspect_invisible(cells, headers, findings):
    """Report cells containing invisible or control characters."""
    entries = [entry for cell in cells if (entry := invisible_entry(cell, headers))]
    if entries:
        finding(findings, "invisible_characters", "Cells", "Values with invisible or control characters", entries)


def number_format_kinds(style):
    """Classify number formats without literal or escaped text."""
    known_code = not style["format"].startswith("Builtin format ")
    code = re.sub(r'"[^"]*"|\\.|_.|\*.', "", style["format"]) if known_code else ""
    unbracketed = re.sub(r"\[[^\]]*\]", "", code)
    kinds = []
    if re.search(r"[eE][+-]0", unbracketed):
        kinds.append("Scientific number format")

    if "%" in unbracketed:
        kinds.append("Percentage number format")

    if (style["format_id"] in BUILTIN_DATE_IDS or re.search(r"[ymdhs]", unbracketed, re.I)
            or re.search(r"\[[hms]+\]", code, re.I)):
        kinds.append("Date/time number format")

    if style["format_id"] >= CUSTOM_FORMAT_START:
        kinds.append("Custom number format")

    return kinds


def inspect_cell_values(cells, header_row, headers, findings):
    """Report numeric precision, mixed identifiers, and number formats."""
    columns = defaultdict(list)
    for cell in cells:
        if cell["row"] > (header_row or 0) and cell["value"] != "":
            columns[cell["col"]].append(cell)

    text_columns = set()
    # Mixed columns are identified from body values rather than their header alone.
    for col, members in columns.items():
        texts = [cell for cell in members if cell["text"]]
        numbers = [cell for cell in members if cell["numeric"]]
        # An identifier column is text-like by its header even when Excel turned every value in it into a number.
        if (texts and len(texts) >= len(numbers)) or IDENTIFIER_HEADER.search(headers.get(col, "")):
            text_columns.add(col)
            if texts and numbers:
                widths = sorted(set(len(cell["value"]) for cell in texts))
                finding(findings, "mixed_numeric_text", column_label(col, headers),
                        "Numeric cells beside text cells; text widths " + ", ".join(map(str, widths[:MAX_ENTRIES]))
                        + ("; %d more widths" % (len(widths) - MAX_ENTRIES) if len(widths) > MAX_ENTRIES else ""),
                        [cell_entry(cell, headers) for cell in numbers])

    groups = defaultdict(list)
    # Stored decimal digits and the final integer digit expose long numeric values.
    for cell in cells:
        style = cell["style"]
        for kind in number_format_kinds(style):
            if kind == "Date/time number format" and cell["col"] not in text_columns:
                continue

            detail = kind + " " + quoted(style["format"])
            if kind == "Date/time number format":
                detail += " in a text-like column"

            groups[("number_format", cell["col"], detail)].append(cell_entry(cell, headers))

        if style["quote_prefix"] and cell["text"] and NUMBER_TEXT.fullmatch(cell["value"]):
            groups[("quote_prefix", cell["col"], "Numeric-looking text with quotePrefix")].append(cell_entry(cell, headers))

        if cell["numeric"]:
            number = Decimal(cell["value"])
            if not number.is_finite():
                continue

            digits = len(number.as_tuple().digits) + max(0, number.as_tuple().exponent)
            if digits >= LONG_NUMBER_DIGITS:
                parts = number.as_tuple()
                integer_digits = len(parts.digits) + parts.exponent
                ends_zero = parts.exponent > 0 or (parts.exponent <= 0 and integer_digits > 0
                            and not any(parts.digits[integer_digits - 1:]))
                ending = "; ends in 0" if ends_zero else ""
                detail = "Numeric value with at least %d significant digits%s" % (LONG_NUMBER_DIGITS, ending)
                groups[("long_number", cell["col"], detail)].append(cell_entry(cell, headers))

    for (kind, col, detail), entries in groups.items():
        finding(findings, kind, column_label(col, headers), detail, entries)


def inspect_appearance(root, cells, styles, headers, findings):
    """Group visible cell formatting by appearance and column."""
    populated = [cell for cell in cells if cell["value"] != ""]
    width = max((cell["col"] for cell in populated), default=0)
    body_rows = {cell["row"] for cell in populated}
    groups = defaultdict(list)
    default = styles[0]
    for cell in cells:
        style = cell["style"]
        if style["fill"] and style["fill"] != default["fill"]:
            groups[("fill", style["fill"], cell["col"])].append(cell)

        if style["font"] and style["font"] != default["font"]:
            groups[("font_color", "Font color " + style["font"], cell["col"])].append(cell)

        if style["strike"]:
            groups[("strikethrough", "Strikethrough", cell["col"])].append(cell)

    consumed = set()
    row_groups = defaultdict(list)
    for (kind, appearance, col), members in groups.items():
        if kind == "fill":
            for cell in members:
                row_groups[(appearance, cell["row"])].append(cell)

    # A uniformly filled used row is emitted once instead of once per column.
    for (appearance, row), members in row_groups.items():
        if width > 1 and {cell["col"] for cell in members} >= set(range(1, width + 1)):
            finding(findings, "row_fill", "Row %d" % row, appearance,
                    [cell_entry(cell, headers) for cell in members])
            consumed.update(cell["ref"] for cell in members)

    # Column default fills cover even unstored cells and are reported without expansion.
    for column in root.findall(tag("cols") + "/" + tag("col")):
        style = styles[int(column.get("style", "0"))]
        if style["fill"] and style["fill"] != default["fill"]:
            first, last = int(column.attrib["min"]), int(column.attrib["max"])
            members = [cell for cell in cells if first <= cell["col"] <= last
                       and cell["style"]["fill"] == style["fill"]]
            label = column_label(first, headers) if first == last else "Columns %s:%s [%d:%d]" % (
                column_letter(first), column_letter(last), first, last)
            finding(findings, "column_fill", label, style["fill"],
                    [cell_entry(cell, headers) for cell in members])
            consumed.update(cell["ref"] for cell in members)

    for (kind, appearance, col), members in groups.items():
        if kind == "fill":
            members = [cell for cell in members if cell["ref"] not in consumed]

        if not members:
            continue

        whole_column = kind == "fill" and len(body_rows) > 1 and {cell["row"] for cell in members} >= body_rows
        finding(findings, "column_fill" if whole_column else kind, column_label(col, headers),
                appearance + (" across the used column" if whole_column else ""),
                [cell_entry(cell, headers) for cell in members])


def validation_values(formula, sheet_name, context, depth=0):
    """Read literal or referenced validation choices without evaluating formulas."""
    formula = formula.lstrip("=")
    if formula.startswith('"') and formula.endswith('"'):
        return formula[1:-1].replace('""', '"').split(",")

    # Named validation lists can refer to other names or a fixed worksheet range.
    definitions, sheets = context
    definition = definitions.get((sheet_name, formula), definitions.get((None, formula)))
    if definition is not None and depth < MAX_NAME_DEPTH:
        return validation_values(definition, sheet_name, context, depth + 1)

    if "!" in formula:
        sheet_name, formula = formula.rsplit("!", 1)
        sheet_name = sheet_name.strip("'").replace("''", "'")

    bounds = formula.replace("$", "").split(":")
    matches = [CELL_REFERENCE.fullmatch(bound) for bound in bounds]
    if len(matches) not in (1, 2) or not all(matches) or sheet_name not in sheets:
        return None

    first, last = matches[0], matches[-1]
    first_col, last_col = column_number(first.group(1)), column_number(last.group(1))
    first_row, last_row = int(first.group(2)), int(last.group(2))
    cells = sheets[sheet_name]()
    return [cell["value"] for cell in cells if first_col <= cell["col"] <= last_col
            and first_row <= cell["row"] <= last_row and cell["value"] != ""]


def inspect_sheet(archive, path, shared, styles, name, order, state, validation_context):
    """Inspect one worksheet's cells and structural metadata."""
    root = ET.fromstring(archive.read(path))
    cells = read_cells(root, shared, styles)
    header_row, headers = header_guess(cells)
    findings = []
    populated = [cell for cell in cells if cell["value"] != ""]
    dimension = root.find(tag("dimension"))
    used_range = dimension.get("ref") if dimension is not None else None
    if not used_range and cells:
        used_range = "%s%d:%s%d" % (column_letter(min(cell["col"] for cell in cells)),
                                     min(cell["row"] for cell in cells),
                                     column_letter(max(cell["col"] for cell in cells)),
                                     max(cell["row"] for cell in cells))

    sheet = {"name": name, "order": order, "state": state, "used_range": used_range,
             "header_row": header_row, "findings": findings}
    rows = Counter(cell["row"] for cell in populated)
    columns = Counter(cell["col"] for cell in populated)
    hidden_rows = ["Row %s: %d non-empty cells" % (row.attrib["r"], rows[int(row.attrib["r"])])
                   for row in root.findall(tag("sheetData") + "/" + tag("row")) if truth(row.get("hidden"))]
    if hidden_rows:
        finding(findings, "hidden_rows", "Rows", "Hidden rows", hidden_rows)

    # Hidden column spans remain compact even when they extend to Excel's last column.
    hidden_columns = []
    for column in root.findall(tag("cols") + "/" + tag("col")):
        if truth(column.get("hidden")):
            first, last = int(column.attrib["min"]), int(column.attrib["max"])
            for col in range(first, last + 1):
                hidden_columns.append("%s: %d non-empty cells" % (column_label(col, headers), columns[col]))

    if hidden_columns:
        finding(findings, "hidden_columns", "Columns", "Hidden columns", hidden_columns)

    merges = [node.attrib["ref"] for node in root.findall(tag("mergeCells") + "/" + tag("mergeCell"))]
    if merges:
        finding(findings, "merged_ranges", "Ranges", "Merged ranges", merges)

    # Declared or styled columns beyond the final populated column are still part of the file.
    if populated:
        final_value_col = max(cell["col"] for cell in populated)
        final_stored_col = max((cell["col"] for cell in cells), default=final_value_col)
        if used_range:
            match = CELL_REFERENCE.fullmatch(used_range.split(":")[-1])
            if match:
                final_stored_col = max(final_stored_col, column_number(match.group(1)))

        if final_stored_col > final_value_col:
            finding(findings, "trailing_blank_columns", "Columns %s:%s [%d:%d]" % (
                column_letter(final_value_col + 1), column_letter(final_stored_col), final_value_col + 1, final_stored_col),
                "%d trailing blank columns in the used range" % (final_stored_col - final_value_col))

    inspect_appearance(root, cells, styles, headers, findings)
    inspect_cell_values(cells, header_row, headers, findings)
    inspect_invisible(cells, headers, findings)
    partial = [cell_label(cell, headers) + ": struck " + ", ".join(map(quoted, cell["partial_strike"][0]))
               + "; not struck " + ", ".join(map(quoted, cell["partial_strike"][1]))
               for cell in cells if cell["partial_strike"] and not cell["style"]["strike"]]
    if partial:
        finding(findings, "partial_strikethrough", "Cells", "Rich text with struck and unstruck runs", partial)

    formulas = [cell for cell in cells if cell["formula"]]
    if formulas:
        finding(findings, "formulas", "Cells", "%d formulas; first %d cells" % (
            len(formulas), min(FORMULA_EXAMPLES, len(formulas))),
            [cell_entry(cell, headers) for cell in formulas[:FORMULA_EXAMPLES]])

    errors = [cell_entry(cell, headers) for cell in cells if cell["error"]]
    if errors:
        finding(findings, "cached_errors", "Cells", "Error values (cached for formula cells)", errors)

    # Notes are separate XML parts linked from the owning worksheet.
    for comment_path, kind in relationships(archive, path).values():
        if kind.endswith("/comments") or kind.endswith("/threadedComment"):
            comments = ET.fromstring(archive.read(comment_path))
            entries = []
            for node in comments.iter():
                if node.tag.rsplit("}", 1)[-1] in ("comment", "threadedComment"):
                    texts = [child.text or "" for child in node.iter()
                             if child.tag.rsplit("}", 1)[-1] in ("t", "text") and child.text]
                    ref = node.get("ref", "Unknown cell")
                    match = CELL_REFERENCE.fullmatch(ref)
                    label = cell_label({"ref": ref, "col": column_number(match.group(1))}, headers) if match else ref
                    entries.append(label + ": " + quoted("".join(texts)))

            if entries:
                finding(findings, "comments", "Cells", "Comments and notes", entries)

    for node in root.findall(".//" + tag("dataValidation")):
        if node.get("type") == "list":
            formula = node.findtext(tag("formula1"), "")
            values = validation_values(formula, name, validation_context)
            reference = node.get("sqref", "Unknown range")
            first_cell = CELL_REFERENCE.fullmatch(reference.split(":")[0].split(" ")[0])
            label = reference
            if first_cell and column_number(first_cell.group(1)) in headers:
                label += " (%s)" % quoted(headers[column_number(first_cell.group(1))])

            finding(findings, "validation_list", label, "Allowed values source " + quoted(formula),
                    [quoted(value) for value in values] if values is not None else None)

    # Only the first text cell of a row near the populated bottom can label a totals row.
    bottom = max(rows, default=0)
    totals = []
    for row in sorted(rows):
        texts = sorted((cell for cell in populated if cell["row"] == row and cell["text"]), key=lambda cell: cell["col"])
        if row >= bottom - BOTTOM_ROWS + 1 and texts and TOTAL_TEXT.match(texts[0]["value"].strip()):
            totals.append("Row %d: %s" % (row, cell_entry(texts[0], headers)))

    if totals:
        finding(findings, "totals_rows", "Rows", "Totals-like rows near the bottom", totals)

    return sheet


def date_value(value, date1904):
    """Convert an Excel date serial to ISO text."""
    seconds = int((Decimal(value) * SECONDS_PER_DAY).to_integral_value(rounding=ROUND_HALF_UP))
    days, seconds = divmod(seconds, SECONDS_PER_DAY)
    # Excel's 1900 calendar includes a fictitious leap day that ISO date objects cannot represent.
    if not date1904 and days == EXCEL_LEAP_DAY:
        result = "1900-02-29"
    else:
        epoch = date(1904, 1, 1) if date1904 else date(1899, 12, 31)
        offset = days if date1904 or days < EXCEL_LEAP_DAY else days - 1
        result = (epoch + timedelta(days=offset)).isoformat()

    if seconds:
        hours, remainder = divmod(seconds, SECONDS_PER_HOUR)
        minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)
        result += "T%02d:%02d:%02d" % (hours, minutes, seconds)

    return result


def write_values(path, sheet, cells, folder, date1904):
    """Write stored worksheet values to a UTF-8 CSV."""
    stem = path.stem
    # Archive members keep the archive name and member directories in their export filenames.
    for parent in path.parents:
        if parent.suffix.lower() == ".zip":
            stem = str(path.relative_to(parent.parent).with_suffix(""))
            break

    filename = UNSAFE_FILENAME.sub("_", stem + " - " + sheet["name"]).rstrip(" .") + ".csv"
    target = folder / filename
    width = max((cell["col"] for cell in cells), default=0)
    # The worksheet's declared range can include trailing used columns without values.
    if cells and sheet["used_range"]:
        match = CELL_REFERENCE.fullmatch(sheet["used_range"].split(":")[-1])
        if match:
            width = max(width, column_number(match.group(1)))

    rows = defaultdict(dict)
    # Only populated rows are exported, including hidden rows and cached formula results.
    for cell in cells:
        value = cell["value"]
        if value == "":
            continue

        if cell["boolean"]:
            value = "TRUE" if truth(value) else "FALSE"
        elif cell["numeric"] and "Date/time number format" in number_format_kinds(cell["style"]):
            # A number too large for a date, such as an identifier given a date format, keeps its stored digits.
            try:
                value = date_value(value, date1904)
            except OverflowError:
                pass

        rows[cell["row"]][cell["col"]] = value

    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["row"] + [column_letter(col) for col in range(1, width + 1)])
        for row, values in sorted(rows.items()):
            writer.writerow([row] + [values.get(col, "") for col in range(1, width + 1)])

    sheet["csv_path"] = str(target)


def inspect_workbook(path, values_folder=None, raw=None):
    """Inspect a zipped Excel workbook without importing dependencies."""
    result = {"path": str(path), "status": "inspected", "findings": [], "sheets": []}
    with zipfile.ZipFile(path if raw is None else io.BytesIO(raw)) as archive:
        workbook_path = "xl/workbook.xml"
        root = ET.fromstring(archive.read(workbook_path))
        parts = relationships(archive, workbook_path)
        properties = root.find(tag("workbookPr"))
        date1904 = properties is not None and truth(properties.get("date1904"))
        result["date_system"] = "1904" if date1904 else "1900"
        if date1904:
            finding(result["findings"], "date1904", "Workbook", "1904 DATE SYSTEM: date serials offset by %s days from the 1900 system" % format(DATE_SYSTEM_OFFSET, ","))

        shared_path = next((part for part, kind in parts.values() if kind.endswith("/sharedStrings")), None)
        shared = list(ET.fromstring(archive.read(shared_path))) if shared_path else []
        styles = read_styles(archive, parts)
        nodes = root.findall(tag("sheets") + "/" + tag("sheet"))
        definitions = {}
        for node in root.findall(tag("definedNames") + "/" + tag("definedName")):
            scope = int(node.attrib["localSheetId"]) if "localSheetId" in node.attrib else None
            scope_name = nodes[scope].attrib["name"] if scope is not None else None
            definitions[(scope_name, node.attrib["name"])] = node.text or ""

        # Excel's own names, such as print areas and filter ranges, say nothing about which rows matter.
        named = ["%s: %s" % (quoted(name), text) for (_, name), text in definitions.items()
                 if not name.startswith("_xl")]
        if named:
            finding(result["findings"], "defined_names", "Workbook", "Defined names and the ranges they cover", named)

        sheet_cells = {}
        cell_cache = {}

        def cached_cells(sheet_path):
            """Read validation source cells once per worksheet."""
            if sheet_path not in cell_cache:
                cell_cache[sheet_path] = read_cells(ET.fromstring(archive.read(sheet_path)), shared, styles)

            return cell_cache[sheet_path]

        for node in nodes:
            relation = parts.get(node.get("{%s}id" % REL_NS))
            if relation and relation[1].endswith("/worksheet"):
                sheet_cells[node.attrib["name"]] = lambda sheet_path=relation[0]: cached_cells(sheet_path)

        # A malformed worksheet is isolated so the remaining sheets still have reports.
        for order, node in enumerate(nodes, 1):
            name, state = node.attrib["name"], node.get("state", "visible")
            try:
                sheet_path, kind = parts[node.attrib["{%s}id" % REL_NS]]
                if not kind.endswith("/worksheet"):
                    result["sheets"].append({"name": name, "order": order, "state": state,
                                             "status": "not inspected", "reason": "Non-worksheet sheet type", "findings": []})
                    continue

                sheet = inspect_sheet(archive, sheet_path, shared, styles, name, order, state,
                                      (definitions, sheet_cells))
                if values_folder is not None:
                    write_values(path, sheet, cached_cells(sheet_path), values_folder, date1904)

                result["sheets"].append(sheet)
            except (KeyError, ValueError, ET.ParseError, IndexError, InvalidOperation, OSError) as error:
                result["sheets"].append({"name": name, "order": order, "state": state,
                                         "status": "error", "reason": str(error), "findings": []})

        if result["sheets"] and not any("status" not in sheet for sheet in result["sheets"]):
            result["status"] = "error"
            result["reason"] = "No worksheet could be inspected"

    return result


def inspect_delimited(path, values_folder=None, raw=None):
    """Inspect delimited text records and their lexical values."""
    archived = raw is not None
    raw = path.read_bytes() if raw is None else raw
    if not raw:
        raise ValueError("Empty delimited file")

    encoding = "UTF-8 with BOM" if raw.startswith(b"\xef\xbb\xbf") else "UTF-8 without BOM"
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
        encoding = "UTF-16LE with BOM" if raw.startswith(b"\xff\xfe") else "UTF-16BE with BOM"
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
            encoding = "Not UTF-8; decoded cp1252"

    # Excel writes a first line such as "sep=;" to name the delimiter; it is not a record, so the header is line 2.
    directive = SEP_DIRECTIVE.match(text)
    body = text[directive.end():] if directive else text
    first = 2 if directive else 1
    try:
        if directive:
            delimiter = directive[1]
            reader = csv.reader(io.StringIO(body, newline=""), delimiter=delimiter, strict=True)
            delimiter_method = "sep= directive on line 1"
        else:
            dialect = csv.Sniffer().sniff(body[:SNIFFER_SAMPLE_LENGTH], delimiters=",\t;|")
            delimiter = dialect.delimiter
            reader = csv.reader(io.StringIO(body, newline=""), dialect, strict=True)
            delimiter_method = "csv.Sniffer"
    except csv.Error:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        reader = csv.reader(io.StringIO(body, newline=""), delimiter=delimiter, strict=True)
        delimiter_method = "Extension fallback; csv.Sniffer could not decide"

    records = []
    stopped = None
    # A file cut off inside a quoted field still has its earlier records, so they are kept and the cut is reported.
    try:
        for fields in reader:
            records.append(fields)
    except csv.Error as error:
        stopped = "Reading stopped at line %d: %s. Rows after the last complete one are not reported" % (
            reader.line_num + first - 1, error)

    if not records or not any(records):
        raise ValueError("Empty delimited file")

    header = records[0]
    headers = {col: value for col, value in enumerate(header, 1) if value}
    findings = []
    line_endings = Counter(re.findall(r"\r\n|\r|\n", text))
    endings = ", ".join("%s=%d" % (quoted(ending), count) for ending, count in line_endings.items()) or "None"
    finding(findings, "encoding", "File", encoding)
    finding(findings, "delimiter", "File", "Delimiter %s (%s)" % (quoted(delimiter), delimiter_method))
    finding(findings, "line_endings", "File", "Line endings: " + endings)
    if stopped:
        finding(findings, "truncated", "File", stopped)

    if directive:
        finding(findings, "sep_directive", "File",
                "Line 1 is an Excel sep= directive naming %s; it is not a record" % quoted(delimiter))

    cells = []
    mismatches = []
    embedded = defaultdict(list)
    spaces = []
    zeros = defaultdict(list)
    columns = defaultdict(list)
    # CSV row numbers count logical records, including quoted multiline fields as one row.
    for row, fields in enumerate(records, first):
        if len(fields) != len(header):
            mismatches.append("Row %d: %d fields; header has %d" % (row, len(fields), len(header)))

        for col, value in enumerate(fields, 1):
            cell = {"ref": "%s%d" % (column_letter(col), row), "row": row, "col": col,
                    "value": value, "boolean": False, "numeric": False}
            cells.append(cell)
            label = cell_label(cell, headers)
            entry = label + ": value " + quoted(value)
            if delimiter in value:
                embedded[col].append(entry)

            if value != value.strip():
                spaces.append(entry)

            if row > first and value:
                columns[col].append((value, entry))
                if LEADING_ZERO.fullmatch(value):
                    zeros[col].append(entry)

    for kind, detail, entries in (("field_counts", "Field counts differ from the header", mismatches),
                                  ("whitespace", "Values with leading or trailing spaces", spaces)):
        if entries:
            finding(findings, kind, "Cells" if kind != "field_counts" else "Rows", detail, entries)

    # Quoted delimiters are normal in some columns, such as addresses, so a column full of them is one line.
    for col, entries in embedded.items():
        if len(entries) > QUOTED_LIST_LIMIT:
            detail = "%d of %d values contain the delimiter inside quotes" % (len(entries), len(records) - 1)
            finding(findings, "quoted_delimiters", column_label(col, headers), detail, entries[:1])
        else:
            finding(findings, "quoted_delimiters", column_label(col, headers),
                    "Values containing the delimiter inside quotes", entries)

    for col, members in columns.items():
        numbers = [entry for value, entry in members if NUMBER_TEXT.fullmatch(value.strip())]
        texts = [entry for value, entry in members if not NUMBER_TEXT.fullmatch(value.strip())]
        if numbers and texts:
            finding(findings, "mixed_numeric_text", column_label(col, headers), "Values mix numbers and text",
                    [entry for value, entry in members])

        if zeros[col]:
            finding(findings, "leading_zeros", column_label(col, headers), "Numbers with leading zeros", zeros[col])

    inspect_invisible(cells, headers, findings)
    sheet = {"name": path.name, "order": 1, "state": "visible", "used_range": "A1:%s%d" % (
        column_letter(max(map(len, records))), len(records) + first - 1), "header_row": first, "findings": findings}
    if values_folder is not None and (archived or encoding.startswith("UTF-16")):
        write_values(path, sheet, cells, values_folder, False)

    return {"path": str(path), "status": "inspected", "findings": [], "sheets": [sheet]}


def inspect_archive(path, values_folder):
    """Inspect supported archive members without extracting them."""
    result = {"path": str(path), "status": "inspected", "findings": [], "members": []}
    metadata = []
    with zipfile.ZipFile(path) as archive:
        # Operating-system metadata holds no records even when its name has a supported extension.
        for member in archive.infolist():
            parts = member.filename.split("/")
            if "__MACOSX" in parts or any(part.startswith("._") or part == ".DS_Store" for part in parts):
                metadata.append(quoted(member.filename))
            elif not member.is_dir() and Path(member.filename).suffix.lower() in SUPPORTED_EXTENSIONS:
                member_path = Path(str(path) + "/" + member.filename)
                # A member that cannot be read, such as an encrypted or corrupt one, is reported alone.
                try:
                    raw = archive.read(member)
                except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as error:
                    result["members"].append({"path": str(member_path), "status": "error", "reason": str(error)})
                    continue

                result["members"].append(inspect_path(member_path, values_folder, raw))

    if metadata:
        finding(result["findings"], "metadata", "Archive", "Operating-system metadata holds no records", metadata)

    return result


def inspect_path(path, values_folder=None, raw=None):
    """Report a supported file or its inspection failure."""
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS | {".zip"}:
        return {"path": str(path), "status": "not inspected", "reason": UNSUPPORTED_REASONS.get(extension, "Unsupported file type")}

    try:
        if extension == ".zip":
            return inspect_archive(path, values_folder)

        return (inspect_workbook(path, values_folder, raw) if extension in (".xlsx", ".xlsm")
                else inspect_delimited(path, values_folder, raw))
    except (OSError, ValueError, KeyError, IndexError, ET.ParseError, zipfile.BadZipFile,
            RuntimeError, NotImplementedError, csv.Error, UnicodeError, InvalidOperation) as error:
        return {"path": str(path), "status": "error", "reason": str(error)}


def render_findings(findings, prefix="  "):
    """Render findings using the same bounded data as JSON."""
    for item in findings:
        print(prefix + item["location"] + ": " + item["detail"])
        for entry in item.get("entries", []):
            print(prefix + "  " + entry)

        if item.get("omitted"):
            print(prefix + "  … %d more (%d total)" % (item["omitted"], item["count"]))


def render_text(results, archive=None):
    """Print one report section per file and subsection per sheet."""
    for result in results:
        name = (Path(archive).name + "/" + str(Path(result["path"]).relative_to(archive))
                if archive is not None else Path(result["path"]).name)
        print("File " + quoted(name))
        if result["status"] != "inspected":
            print("  %s: %s" % (result["status"].capitalize(), quoted(result.get("reason", ""))))

        render_findings(result.get("findings", []))
        csv_paths = [sheet["csv_path"] for sheet in result.get("sheets", []) if "csv_path" in sheet]
        if csv_paths:
            print("  CSV files written: " + ", ".join(json.dumps(path, ensure_ascii=False) for path in csv_paths))

        for sheet in result.get("sheets", []):
            print("  Sheet %d %s: state %s, used range %s, header row guess %s" % (
                sheet["order"], quoted(sheet["name"]), sheet["state"], sheet.get("used_range") or "Empty",
                sheet.get("header_row") or "None"))
            if sheet.get("status"):
                print("    %s: %s" % (sheet["status"].capitalize(), quoted(sheet["reason"])))
            elif not sheet["findings"]:
                print("    Nothing notable")

            render_findings(sheet["findings"], "    ")

        print()
        render_text(result.get("members", []), result["path"])


def main():
    """Inspect command-line inputs and return the requested exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print findings as JSON")
    parser.add_argument("--values", type=Path, metavar="folder", help="Write worksheet values as UTF-8 CSV files")
    parser.add_argument("paths", nargs="+", help="Files or folders to inspect without recursion")
    args = parser.parse_args()
    if args.values is not None:
        args.values.mkdir(parents=True, exist_ok=True)

    results = []
    seen = set()
    # Folder expansion is shallow, deterministic, and deduplicated across input arguments.
    for argument in args.paths:
        path = Path(argument)
        try:
            files = sorted((child for child in path.iterdir() if child.is_file()), key=lambda child: child.name.casefold()) if path.is_dir() else [path]
            if not files:
                results.append({"path": str(path), "status": "not inspected", "reason": "Folder contains no files"})

            for file in files:
                resolved = file.resolve()
                if resolved in seen:
                    continue

                seen.add(resolved)
                results.append(inspect_path(file, args.values))

        except OSError as error:
            results.append({"path": str(path), "status": "error", "reason": str(error)})

    if args.json:
        print(json.dumps({"files": results}, indent=2, ensure_ascii=False))
    else:
        render_text(results)

    return 0 if any(result["status"] == "inspected" for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
