# Source files: what the cells do not say

Company files are exports, hand-kept workbooks and copies of copies. Read them as the company meant them, not as a
program displays them.

## Files and tabs

- Read every file and every tab before planning. One tab often holds two kinds of record, such as customers with the
  sites of each, and one kind is often split across tabs, such as one tab per site
- Without a spreadsheet library, use the inspector's `--values <folder>` to write every worksheet's cell values as CSV
- When each tab holds one site's units and no column names the site, the tab name is the site for every row on it
- Skip tabs that are notes, instructions, archives or old versions, such as a tab named "Archive" or "Last year", and
  say which were skipped and why. A note on a skipped tab can still answer a question about a live one: read it
- A hidden sheet, row or column is still data the company kept. Read it; never treat hidden as deleted. Say in the
  plan what was hidden and what you did with it
- A workbook defined name that covers some rows of a tab, such as `ActiveFleet` over rows 2 to 40 of a longer list,
  may mark the rows the company works from. The inspector lists each defined name and its range. Ask whether the
  rows outside it are loaded, naming them
- When two files hold the same records, such as "Copy of" an export beside the export, ask which is current
- Two exports of the same register from different dates are versions. A unit in the older one that the newer one
  lacks may have been sold, scrapped or filtered out. Ask what happened to it, naming the units, and never load it as
  active without an answer

## Headers and rows

- The header row is often below a title, a date or a blank row. Find it per tab
- Skip rows that are not records: totals, subtotals, counts, section labels such as `--- ROBOTS ---`, repeated
  header rows, and blank rows. A totals row is a check: compare it with your own sum and report a difference
- Blank columns and columns with no header are not data, though a few cells in them may hold stray spaces
- Column names say little; values say more. Map a column by what it holds, and treat a column with a misleading name,
  such as "Worth" holding a depreciated amount, as described in `values.md`

## What Excel and earlier systems did to values

- Read every cell as stored, not as displayed. A display format can hide digits, and a stored number can be a mangled
  text value
- An identifier column of text values holding a few bare numbers that are shorter than the rest lost its leading
  zeros: pad them to the width of the others
- A long identifier shown as `7.21E+11` is stored in full: use the stored digits. Text that only looks like scientific
  notation, such as `6E2207` in a text cell, is an identifier, not a number
- A number of 16 or more digits ending in 0 was rounded by Excel to 15 significant digits. The real digits are gone:
  ask for them, never load the rounded value
- A code that became a date, such as a product code shown as `4-Jun` with a date number underneath, lost its text: ask
  for the original code
- A leading apostrophe that forced text, as in `'04417`, is not part of the value
- A workbook saved in the 1904 date system stores every date 1,462 days earlier: the inspector reports it. Convert
  with that system, or every date lands four years early
- A formula's cached value is what the company saw. An error value such as `#REF!` is a question, and so is a formula
  in an identifier column, such as a serial or a SKU: an identifier is typed, not computed, so the cached result may
  not be the label

## Formatting carries meaning

- A fill colour, font colour or strikethrough on a row or cell often carries a status, such as red for broken. Use the
  workbook's legend when it has one; when it does not, ask what the formatting means, naming the colour and the rows.
  Never ignore a fill the inspector reports
- Strikethrough on a whole row or cell has no fixed meaning: it can mark a unit retired, sold or scrapped, or a row
  entered by mistake. Never drop a struck-through row or load it as if unmarked without asking what it means
- Struck-through words inside a cell beside words that are not struck are deleted text, such as an old name struck out
  before its replacement. The value is the words not struck. The inspector lists each such cell
- A merged cell spanning rows applies to each row under it

## Comments on cells

- A cell comment or note that gives a different value for its cell, such as a label serial behind a ticket number in
  the serial column, is a question: quote both values and propose the one the comment supports
- In a list grouped by site or customer, a blank cell under a filled one usually means "same as above": fill it down
  and say so in the plan. When the layout does not make that clear, ask, proposing the value above

## CSV files

- A quoted field may hold the delimiter, as in `"Bracket, wall"`; parse with a CSV reader, never by splitting on
  commas, and never repair a row whose field count looks off without checking the quoting
- Files not in UTF-8 garble accents; decode with the encoding the inspector reports
- Values with leading or trailing spaces are the same values trimmed
- Invisible formatting characters, such as right-to-left and left-to-right marks (U+200F, U+200E), zero-width spaces
  and a stray byte-order mark, are not part of a value. Strip them from names and identifiers, and keep the visible
  text exactly. The inspector lists each cell that holds one, for workbooks and CSV files alike
- A `.zip` input holds files to read like any other. Skip operating-system entries such as `__MACOSX/` and
  `.DS_Store`, which hold no records. The inspector reads the archive's files in place
