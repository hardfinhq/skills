# Items

An item is a product in the catalogue.

- A product sold or stocked by count with no serials, such as kits, cables or consumables, is a bulk item
- Creating a bulk item requires its unit of measure
- A serialized product is a device
- A bulk item's stock is never loaded as assets; Hardfin assets are serialized units
- `item get` and `item list` do not return a bulk item's unit of measure
