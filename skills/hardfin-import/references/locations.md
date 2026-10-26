# Locations

Read `hardfin-cli`'s `references/locations.md` for the location data model.

- A name that is a part of a place, such as "Loading bay B", "Room 214" or a bin code like `R4-07-2`, is a zone under the site
  it belongs to, not a site of its own. Create the site first, then the zone. When the files do not say which site, ask
- Same-named sites under different customers, such as two customers that each have a "North Yard", are two locations.
  The customer column decides which an asset is at
- A site named the same as its customer is still one site under that customer
- Two sites at the same address in different files are still two records unless the user says otherwise; ask
- A PO box is not a physical site. An asset recorded at a PO box is a question: where is it really
- A location with only a city is loaded as given and listed in the plan
- An address field that holds something other than a street address, such as a map link, coordinates or a
  description of the land like `Plot behind the Brennick yard`, is a question. Ask for the street, naming the rows,
  rather than loading the text as the street or leaving the street blank
- A site name that ends with a place name after a dash or comma, such as `Quarry depot - Marlow Fields`, may carry
  its locality rather than be the site's own name. Ask whether the locality belongs in the name, naming the rows
- A street line can also hold the city, state or postal code that another column or file gives for the site, such as
  `Harlow 14 Mill Lane` beside a city of `Harlow`. The street line keeps only the street. Put the city and the rest in their own
  address fields, and say so in the plan
- When a tab per site holds the assets, the tab name is the site

Read the first location back and compare every address field; see `hardfin-cli`'s `references/locations.md`.
