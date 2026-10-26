# Customers

Load customers before locations. Read `hardfin-cli`'s `references/customers.md` for the customer data model.

- The company's own customer or account list is the master: one customer per row
- Load suppliers and vendors when the files list them, unless the user says otherwise. Each is a customer record
  marked as a supplier, as `hardfin-cli`'s `references/customers.md` describes
- A company that appears both as a customer and as a supplier is one record with both booleans set, never two
- A company named on a site or asset row but missing from the master list is a customer to create; list it in the
  plan
- Names that differ only by a country or region, such as `Halvard Pumps (UK)` and `Halvard Pumps (DE)`, may be one
  company with sites in several countries or separate companies. So may a master list name and the same name with a
  country added. Ask which, naming the rows, before creating a customer for either
- Take a name exactly as the master list writes it, legal suffix and all, even when another file shortens it. Shorten
  it only when the user says so. A comma, semicolon or dash left dangling at the end of the cell, as in
  `Harrow Valves,`, is not part of the name: drop it and say so in the plan
- A company cell that carries two names is one company under two names. The shapes include an old and a new name,
  such as `Corvel Metals (now Ardent Alloys)`, `formerly …` or `acquired by …`, and a legal and a trading name, such as
  `Brask Holdings DBA Brask Field Services`, `d/b/a …`, `t/a …` or `trading as …`. Ask which name Hardfin uses, and
  load one customer under it, never the cell as written
- Merge name variants and keep look-alikes apart as `identity.md` describes. Companies that share a domain, or a parent
  and its subsidiary, are separate customers
- A billing address, payment terms or a contact on the row belong to the customer only where Hardfin has a field for
  them. Something with no field is reported, not stuffed into another field; see `hardfin-cli`'s
  `references/customers.md`
- A PO box is a billing address, never a site
- Check `hardfin customer create --help` for the supplier and customer flags and the address fields before building
  the table
