# Domoticz Garbage Calendar Plugin

A Domoticz Python plugin that retrieves your garbage/waste collection schedule and displays upcoming pickup dates in a Domoticz Text device.  
Supports 17 different waste-collection data sources used in the Netherlands and Belgium.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Parameters](#parameters)
  - [Date format tokens](#date-format-tokens)
  - [Module-specific notes](#module-specific-notes)
- [Supported modules](#supported-modules)
- [Waste types](#waste-types)
- [dzVents notification script](#dzvents-notification-script)
- [Troubleshooting](#troubleshooting)

---

## Requirements

- [Domoticz](https://www.domoticz.com/) with Python plugin support enabled  
- Python 3.6 or higher  
- Module **9 (omrin)** additionally requires the `cryptography` Python package:
  ```
  pip install cryptography
  ```

---

## Installation

1. Create the plugin directory inside your Domoticz installation:
   ```bash
   mkdir -p <domoticz>/plugins/GarbageCalendar
   ```
2. Copy `plugin.py` into that directory:
   ```bash
   cp plugin.py <domoticz>/plugins/GarbageCalendar/
   ```
3. Restart Domoticz:
   ```bash
   sudo systemctl restart domoticz
   ```
4. In the Domoticz web interface go to **Setup → Hardware**, click **Add**, and choose **GarbageCalendar** from the type list.
5. Fill in the parameters (see [Configuration](#configuration)) and click **Add**.

Domoticz will create a single **Text** device that shows the next upcoming pickup dates.

---

## Configuration

### Parameters

| Label | Description | Default |
|---|---|---|
| **Module** | Data source / waste provider (see [Supported modules](#supported-modules)) | `2` |
| **Postcode** | Your postal code (e.g. `1234AB`) | *(empty)* |
| **Huisnummer** | House number | *(empty)* |
| **Huisnummer suffix** | House number addition (e.g. `A`, `bis`) | *(empty)* |
| **Extra** | Module-specific extra value (see [Module-specific notes](#module-specific-notes)) | *(empty)* |
| **Datumformaat** | Date format string for displayed dates (see [Date format tokens](#date-format-tokens)) | `wd dd mmm` |
| **Domoticz adres** | IP address of your Domoticz instance | `127.0.0.1` |
| **Domoticz poort** | Port of your Domoticz instance | `8080` |
| **Dagelijkse verversingstijd** | Time of day to refresh the schedule (HH:MM) | `02:30` |
| **Aantal te tonen events** | Number of upcoming pickups to display | `3` |

### Date format tokens

Use these tokens in the **Datumformaat** field to compose your preferred date string:

| Token | Output example | Description |
|---|---|---|
| `wd` | `ma` | Dutch weekday abbreviation (2 letters) |
| `wdd` | `maandag` | Dutch weekday full name |
| `dd` | `07` | Day number, zero-padded |
| `mm` | `04` | Month number, zero-padded |
| `mmm` | `apr` | Dutch month abbreviation |
| `mmmm` | `april` | Dutch month full name |
| `yyyy` | `2025` | Four-digit year |
| `yy` | `25` | Two-digit year |

**Examples:**

| Format string | Result |
|---|---|
| `wd dd mmm` | `ma 07 apr` |
| `wdd dd mmmm yyyy` | `maandag 07 april 2025` |
| `dd-mm-yyyy` | `07-04-2025` |

### Module-specific notes

| Module | Extra field value |
|---|---|
| `1` – mijnafvalwijzer (HTML) | *(optional)* Custom hostname (default: `www.mijnafvalwijzer.nl`) |
| `2` – mijnafvalwijzer_api | *(optional)* Custom API hostname (default: `api.mijnafvalwijzer.nl`) |
| `3` – ximmio | **Required.** Company code. Open your municipality's website, press F12, search `controller.js` for `companyCode`. |
| `6` – opzet (iCal) | **Required.** Hostname (e.g. `inzamelkalender.hvcgroep.nl`) |
| `7` – opzet_api | **Required.** Hostname |
| `8` – recycleapp-be | **Required.** Street name |
| `10` – burgerportaal | **Required.** BPName: `assen`, `bar`, or `rmn` |
| `15` – csv_file | **Required.** Full path to the local CSV file |
| `16` – afvalinfo | **Required.** Municipality name (e.g. `sliedrecht`, `papendrecht`) |
| All others | Leave **Extra** empty |

---

## Supported modules

| # | Name | Method | Country |
|---|---|---|---|
| 1 | mijnafvalwijzer | HTML scraping | 🇳🇱 NL |
| 2 | mijnafvalwijzer_api | JSON API | 🇳🇱 NL |
| 3 | ximmio | Ximmio waste API | 🇳🇱 NL |
| 4 | rova_api | Rova waste API | 🇳🇱 NL |
| 5 | rd4_api | RD4 waste API | 🇳🇱 NL |
| 6 | opzet | Opzet iCal | 🇳🇱 NL |
| 7 | opzet_api | Opzet REST API | 🇳🇱 NL |
| 8 | recycleapp-be | RecycleApp REST API | 🇧🇪 BE |
| 9 | omrin | Omrin API (requires `cryptography`) | 🇳🇱 NL |
| 10 | burgerportaal | Firebase-based portal | 🇳🇱 NL |
| 11 | rmn | RMN via burgerportaal | 🇳🇱 NL |
| 12 | deafvalapp | De Afval App | 🇳🇱 NL |
| 13 | zuidlimburg | ZuidLimburg HTML scraping | 🇳🇱 NL |
| 14 | montferland | Montferland REST API | 🇳🇱 NL |
| 15 | csv_file | Local CSV file | Any |
| 16 | afvalinfo | afvalinfo.nl via trashapi | 🇳🇱 NL |
| 17 | reinis | reinis.nl REST API | 🇳🇱 NL |

---

## Waste types

The plugin normalises raw waste type names from the provider into standard display names and renders them with a colour-coded HTML label in the Domoticz Text device:

| Display name | Colour | Includes |
|---|---|---|
| **GFT** | 🟢 Green | groente, gft |
| **Papier** | 🔵 Blue | papier, oud papier, karton |
| **Restafval** | ⚫ Grey | restafval |
| **PMD** | 🟠 Orange | pmd, plastic |
| **Glas** | 🔵 Cyan | glas |
| **Textiel** | 🟣 Purple | textiel |
| **Kerstbomen** | 🟢 Dark green | kerstbomen |

Unknown waste types are displayed as-is.

---

## dzVents notification script

The repository includes an optional **dzVents** script (`scripts/dzVents/garbage_notification.lua`) that reads the GarbageCalendar Text device and shows a short notification in a second Text device.

### What it does

- **"Vandaag \<type\>"** – shown from midnight until 14:00 on the collection day.  
- **"Morgen \<type\>"** – shown from 16:00 the day before collection.  
- Outside these windows the notification device is cleared automatically.

### Setup

1. Open `garbage_notification.lua` and set the two constants at the top:
   ```lua
   local GARBAGE_DEVICE_IDX = 123   -- idx of your GarbageCalendar Text device
   local NOTIFY_DEVICE_IDX  = 2222  -- idx of the notification Text device
   ```
2. In Domoticz, create a new **Text** device and note its `idx` — use that for `NOTIFY_DEVICE_IDX`.
3. Copy the script to your Domoticz scripts folder:
   ```bash
   cp scripts/dzVents/garbage_notification.lua <domoticz>/scripts/dzVents/scripts/
   ```
4. Domoticz will pick up the script automatically (no restart needed).

> **Note:** The GarbageCalendar device date format must use the default `wd dd mmm` format for the script to parse dates correctly.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Device shows nothing | Check the Domoticz log (**Setup → Log**) for `[GC/...]` error messages. |
| Wrong data / empty response | Verify that your postcode and house number are correct for the selected module. |
| Module 9 (omrin) fails to import | Install the `cryptography` package: `pip install cryptography`. |
| ximmio returns no data | Find the correct `companyCode` for your municipality (see [Module-specific notes](#module-specific-notes)). |
| Date format looks wrong | Adjust the **Datumformaat** parameter using the tokens in [Date format tokens](#date-format-tokens). |
| Script does not trigger | Ensure `GARBAGE_DEVICE_IDX` matches the actual `idx` shown in Domoticz for the GarbageCalendar device. |
