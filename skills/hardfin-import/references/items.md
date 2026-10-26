# Items

Load items first. Read `hardfin-cli`'s `references/items.md` for the item data model.

- The company's product list, when there is one, is the master: one item per row, under its name and code as written
- A model or item column whose value reads as a body type or a category rather than a product, such as
  `CAGED TIPPER T/L` beside a type column saying the same, is a question. Ask for the product's real name before
  creating the item, since an item cannot be changed on an asset later
- A product name that ends in an ellipsis or stops partway through a word, such as `Ostrand flow meter with remote
  sen…`, was cut by an export. Ask for the full name, naming the rows, before creating the item
- Two product rows with the same description but different names or codes, such as `Tessly gauge` and
  `Tessly gauge B` both described as `Digital gauge, 4 inch`, may be one product entered twice. Ask whether they are
  one item and which name and code Hardfin uses, naming both rows
- A product row that names two codes, such as a manufacturer part number in the SKU column and the company's own stock
  code in its description, is a question. Ask which one Hardfin uses as the SKU
- A product an asset uses that is missing from the product list is an item to create. List it in the plan with the
  rows that use it, and ask for any field the files do not hold, such as its code or type. Never invent a code
- A product the list holds that no asset uses, such as a service or an accessory, is still an item: load it unless
  the user says otherwise. A row that reads as an invoice adjustment rather than a product, such as freight, a
  discount, a surcharge or rounding, is a question: ask whether the organization bills it through Hardfin, naming
  the rows
- Name variants on asset rows map to the product list's name; see `identity.md`
- A product name that carries a customer, site or configuration, such as a model followed by "(Acme build)" or
  "for Harbor Works", may be one customer's setup of a base product rather than a product of its own. Ask whether the
  qualifier belongs in the item name, proposing the base name, and name the rows that use it
- A product code that Excel turned into a date, or that lost leading zeros, is restored or asked about as
  `source-files.md` describes
- An item's type follows what it is, not only what the list calls it. When the list's type and the rows disagree,
  propose the type the rows support and say why; see `hardfin-cli`'s `references/items.md`
- Check a bulk item's unit of measure with the create's answer, not a read back;
  see `hardfin-cli`'s `references/items.md`
- Check `hardfin item create --help`, or describe `itemCreateItem` on `hardfin_create` with the connector, for the type
  values and required fields before building the table
