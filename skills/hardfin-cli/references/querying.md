# Querying

A list is a page of records matching the search and filters.

A list answers `results` and `totalCount`, and holds at most 100 records a page.

A list leaves some records out unless you ask for them, and `totalCount` does not count
them:

| List                                          | Leaves out          | CLI | Connector params |
| --------------------------------------------- | ------------------- | --- | --- |
| `asset list`                                  | Scrapped assets     | `--scrapped all` | `scrapped: "all"` |
| `customer list`, `item list`, `location list` | Archived records    | `--archived all` | `archived: "all"` |
| `location list`                               | Transient locations | `--is-transient all` | `isTransient: "all"` |

An archived item's assets still appear in `asset list`. Summing `assetCount` over
`item list` misses them unless you pass `--archived all` to `item list`
(`archived: "all"` on `list_items` with the connector).

| List | Search: CLI / connector | Filters: CLI / connector |
| ---- | ----------------------- | ------------------------ |
| `asset list` / `list_assets` | `--search-query` / `searchQuery` | `--for-item` / `forItem`, `--for-customer` / `forCustomer`, `--at-site` / `atSite`, `--with-functional-statuses` / `withFunctionalStatuses`, `--scrapped` / `scrapped`, `--archived` / `archived` |
| `customer list` / `list_customers` | `--search` / `search` | `--is-customer` / `isCustomer`, `--is-supplier` / `isSupplier`, `--archived` / `archived` |
| `item list` / `list_items` | `--search` / `search` | `--type` / `type`, `--archived` / `archived` |
| `location list` / `list_locations` | `--search` / `search` | `--for-customer-ids` / `forCustomerIds`, `--for-organization` / `includeOrganization`, `--is-transient` / `isTransient`, `--archived` / `archived` |

With the connector, pass the filters as the list tool's arguments. `asset list` also takes
`--with-transit-statuses` (`withTransitStatuses`).

- A filter such as `--for-item` (`forItem`) takes the record's ID, not its key. Read the ID from a list or a get
- A search needs three characters or more
- An asset is large, about 6 kB. Ask for 20 at a time or fewer
- Stop at the last page, which is `totalCount` divided by `--limit` (`limit`), rounded up. A page past it fails with `bad_request`
- Page with `--page` / `page` and size pages with `--limit` / `limit`
- `hardfin <noun> list --help` lists every filter; with the connector, read the list tool's input schema

`location list` returns sites only. Zones come from `location zones list <siteKey>`,
without a parent field. With the connector, use `list_location_zones`,
with the site key as `locationKey`.

`--for-organization` (`includeOrganization`) on `location list` adds the organization's own sites to a
`--for-customer-ids` (`forCustomerIds`) filter. On its own, it lists only the organization's own sites.
