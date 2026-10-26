# Customers

A customer record is a company the organization works with. The record is named `customer` in the CLI and the API,
but that name does not mean the company buys from the organization. A company the organization only buys from is a
customer record too.

Two booleans on the record say what the company is to the organization:

| Field        | Flag            | `true` means                                    |
| ------------ | --------------- | ----------------------------------------------- |
| `isCustomer` | `--is-customer` | The organization sells or leases to the company |
| `isSupplier` | `--is-supplier` | The organization buys from the company          |

- The two booleans are independent. A company the organization both sells to and buys from is one record with both
  `true`, never two records
- A supplier or vendor is a customer record with `isSupplier` true, and with `isCustomer` false unless the
  organization also sells to it. On `customer create` and `customer update`, `--no-is-customer` and
  `--no-is-supplier` set a boolean false
- `customer list --is-supplier` lists only suppliers, and `customer list --is-customer` lists only customers. Without
  either flag the list holds every company
- Locations point at customer records
- Hardfin has no payment terms field on a customer
