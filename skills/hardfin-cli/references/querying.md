# Querying

A list is a page of records matching the search and filters.

A list answers `results` and `totalCount`, and holds at most 100 records a page.

A list leaves some records out unless you ask for them, and `totalCount` does not count
them:

| List                                          | Leaves out          | To include them      |
| --------------------------------------------- | ------------------- | -------------------- |
| `asset list`                                  | Scrapped assets     | `--scrapped all`     |
| `customer list`, `item list`, `location list` | Archived records    | `--archived all`     |
| `location list`                               | Transient locations | `--is-transient all` |

An archived item's assets still appear in `asset list`. Summing `assetCount` over
`item list` misses them unless you pass `--archived all` to `item list`.

| List            | Search with      | Filters worth knowing                                                                                              |
| --------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------ |
| `asset list`    | `--search-query` | `--for-item`, `--for-customer`, `--at-site`, `--with-functional-statuses`, `--with-transit-statuses`, `--scrapped` |
| `customer list` | `--search`       | `--is-customer`, `--is-supplier`, `--archived`                                                                     |
| `item list`     | `--search`       | `--type`, `--archived`                                                                                             |
| `location list` | `--search`       | `--for-customer-ids`, `--is-transient`, `--archived`                                                               |

- A filter such as `--for-item` takes the record's ID, not its key. Read the ID from a list or a get
- A search needs three characters or more
- An asset is large, about 6 kB. Ask for 20 at a time or fewer
- Stop at the last page, which is `totalCount` divided by `--limit`, rounded up. A page past it fails with `bad_request`
- `hardfin <noun> list --help` lists every filter

`location list` returns sites only. Zones come from `location zones list <siteKey>`,
without a parent field.

`--for-organization` on `location list` adds the organization's own sites to a
`--for-customer-ids` filter. On its own, it lists only the organization's own sites.
