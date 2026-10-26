# Assets

An asset is one physical unit, identified by its serial, pointing at its item and its location.

- An asset requires a serial; the API refuses one without, whatever the help shows
- A serial is unique across the whole organization, not only within its item, whatever the help says
- Hardfin has no asset-tag, quantity, parent or net-book-value field on an asset
- A missing status defaults to functional
- An asset cannot be created scrapped: create it and then scrap it with its scrap date
- A scrapped asset reads back with status SCRAPPED
- Ownership is only for a sale
- A unit at a customer's site is still the organization's unless it was sold
- An asset's item cannot be changed after it is created
- Cost basis is the original cost, in its own currency
- Hardfin stores each asset's cost currency
- Inventory date is when the unit was received
- In-service date is when it went into use
