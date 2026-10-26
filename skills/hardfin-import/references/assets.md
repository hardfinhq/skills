# Assets

Read `hardfin-cli`'s `references/assets.md` for the asset data model.

## Serials

- A row whose serial is a placeholder, such as `TBD`, `N/A`, `?` or blank, is left out of the load and reported by
  file, tab and row
- A value in the serial column that is not one unit's serial is a question, naming its rows. Never load it as the
  serial. Three shapes give it away:
  - The same value on the rows of several units, which is a product code such as a GTIN
  - A run of small counters such as `1`, `2`, `3` that numbers the rows
  - A formula
- Serials of one product that all stop at the same length, such as every unit's serial at exactly ten characters
  while the product's labels run longer, can be cut by a legacy system's field width. Ask for the full serials,
  naming the rows, before loading any of them
- A MAC address in the serial column, such as `A4:5E:60:C2:19:8B`, can be a networked device's real serial. Load it as
  written
- The same serial on two rows is either one unit entered twice or a collision to ask about; see `identity.md`
- Read serials as stored and repair what Excel did, as `source-files.md` describes
- A full barcode string in the serial column, such as a GS1 string `(01)…(21)K7Q2210(17)…`, holds the serial after
  `(21)`; the product code and dates are not the serial
- The organization's own asset tags in the serial column, beside manufacturer serials in a tag column, are swapped:
  the manufacturer serial is the serial
- Asset tags, quantities, parents and net book values are reported, or kept in the description where they help, never
  forced into another field

## Status and lifecycle

- Map statuses as `values.md` describes; a blank or two-way status is a question, because Hardfin would default a
  missing status to functional
- A unit the files say is scrapped, retired or disposed of is created and then scrapped with its scrap date, as
  `hardfin-cli`'s `references/assets.md` describes. Without an exact date, ask for one
- A loaner or demo unit, a unit at a customer's site, or one with a customer named on its row, gets that location,
  never an owner, unless the files say it was sold

## Item, location and cost

- An asset's item cannot be changed after it is created, so check each row's item against the plan and the user's
  answers before its create
- Every asset's item must be in the items table and its location in the locations table; a missing one is added to
  that table and listed in the plan, never guessed from a similar name
- A location blank under a filled one in a grouped list is "same as above"; see `source-files.md`
- A foreign cost stays in its currency, never converted; see `hardfin-cli`'s `references/assets.md`

## Before the full load

Load one asset, read it back with `get` or `assetGetAsset` on the connector's `hardfin_read` with `params.assetKey`,
and compare every field sent, including cost, currency and dates, with what came back.
