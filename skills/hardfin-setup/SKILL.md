---
name: hardfin-setup
description: Get a new company started in Hardfin - take its spreadsheets as they are and fill an empty organization until the assets dashboard shows its real equipment, customers and sites. Use when the user has just signed up, asks to get started, set Hardfin up, onboard, or move the company onto Hardfin. Works with the hardfin-import skill, which holds the import procedure and the quirks of the files.
---

# Set up Hardfin for a new company

The goal is a full assets dashboard in one sitting: every unit of the company's equipment in Hardfin, each with its
product, its location, its status and its cost, under the right customer, with as few questions as possible and not
one duplicate.

## 1. Check the organization is empty

Connect as step 1 of `hardfin-import` describes, and count items, customers, locations and assets. If any count is
above zero, tell the user what is already there and ask whether to add to it; the import then matches every row
against what exists.

## 2. Ask for the files once

Ask for everything in one message:

- The equipment list: serials, product or model, where each unit is, its status, when it was received, what it cost
- The product catalogue, if the company keeps one
- Customers and suppliers, and the sites of each, with addresses

Say that rough is fine: any spreadsheet, any column names, several tabs, as exported. Do not ask for anything to be
cleaned up first. When the files are already in the working folder, do not ask; use them.

## 3. Import everything

Follow `hardfin-import` from step 2 to step 6, for all four kinds: items, customers, locations and assets. Its plan
message is the one message of questions for the whole setup.

## 4. Offer the next step

When the counts check out, tell the user the assets dashboard now shows the company's equipment, then offer the next
record set in one line, such as "Projects are next: about 10 more minutes to get your contracts into Hardfin too. Go
ahead?"

Connecting a CRM or accounting system happens in the browser, not through this skill: send the user to the
Integrations page in the Hardfin web app. Never ask for a CRM or accounting password.
