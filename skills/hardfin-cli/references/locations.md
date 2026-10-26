# Locations

A location is where assets are.

- Hardfin has two types: a SITE, a physical place with an address, and a ZONE, a part of a
  site, such as a dock, a room or a bin
- A zone needs its parent site
- A site with a customer belongs to that customer
- A site with no customer is one of the organization's own places, such as its warehouse or depot
- The organization's own warehouse, stockroom or depot, where unassigned stock waits, is a site marked as inventory
- The address fields are named by the API, such as `addressLine1`
- A command refuses a field it does not take with `invalid_input`, which names the field and the ones taken there

See `references/querying.md` for listing sites and zones.
Read the first record back and compare every field sent.
