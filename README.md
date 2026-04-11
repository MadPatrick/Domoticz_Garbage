# Domoticz Garbage Calendar Plugin

A Domoticz Python plugin that retrieves your garbage/waste collection schedule and displays upcoming pickup dates in a Domoticz Text device.  
Supports 17 different waste-collection data sources used in the Netherlands and Belgium.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Plugin parameters](#plugin-parameters)
  - [config.txt settings](#configtxt-settings)
  - [Module-specific notes](#module-specific-notes)
- [Supported modules](#supported-modules)
- [Waste types](#waste-types)
- [Notification device](#notification-device)
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
2. Copy `plugin.py` (and optionally `config.txt`) into that directory:
   ```bash
   cp plugin.py config.txt <domoticz>/plugins/GarbageCalendar/
   ```
3. Restart Domoticz:
   ```bash
   sudo systemctl restart domoticz
   ```
4. In the Domoticz web interface go to **Setup → Hardware**, click **Add**, and choose **GarbageCalendar** from the type list.
5. Fill in the parameters (see [Configuration](#configuration)) and click **Add**.

Domoticz will create two **Text** devices:

| Device name | Description |
|---|---|
| **Garbage Calendar** | Shows the next upcoming pickup dates |
| **Garbage Container** | Shows a "Vandaag / Morgen" reminder (see [Notification device](#notification-device)) |

---

## Configuration

### Plugin parameters

These parameters are set in the Domoticz hardware setup UI:

| Label | Description | Default |
|---|---|---|
| **Module** | Data source / waste provider (see [Supported modules](#supported-modules)) | `2` |
| **Postcode** | Your postal code (e.g. `1234AB`) | *(empty)* |
| **Huisnummer** | House number | *(empty)* |
| **Huisnummer suffix** | House number addition (e.g. `A`, `bis`) | *(empty)* |
| **Extra** | Module-specific extra value (see [Module-specific notes](#module-specific-notes)) | *(empty)* |

### config.txt settings

Advanced settings are configured by editing `config.txt` in the plugin directory.  
The plugin re-reads this file on every restart (no Domoticz restart required — just restart the plugin via **Setup → Hardware**).

| Key | Description | Default |
|---|---|---|
| `UpdateTime` | Time of day to refresh the schedule (HH:MM) | `02:30` |
| `ShowEvents` | Number of upcoming pickups to display | `3` |
| `VandaagTot` | Until what time the "Vandaag" notification is shown (HH:MM) | `16:00` |
| `MorgenVanaf` | From what time the "Morgen" notification is shown (HH:MM) | `16:00` |

Pickup dates are always displayed in the format **`wd dd mmm`** (e.g. `ma 07 apr`).

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

## Notification device

The plugin automatically creates a second Text device called **"Garbage Container"** that shows a short reminder:

| Situation | Text shown |
|---|---|
| Collection day, before `VandaagTot` | `Vandaag <soort>` |
| Day before collection, from `MorgenVanaf` | `Morgen <soort>` |
| Outside these windows | *(empty)* |

The reminder times can be adjusted in `config.txt` (see [config.txt settings](#configtxt-settings)).  
No additional scripts or dzVents rules are needed — the plugin updates both devices automatically.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Device shows nothing | Check the Domoticz log (**Setup → Log**) for `[GC/...]` error messages. |
| Wrong data / empty response | Verify that your postcode and house number are correct for the selected module. |
| Module 9 (omrin) fails to import | Install the `cryptography` package: `pip install cryptography`. |
| ximmio returns no data | Find the correct `companyCode` for your municipality (see [Module-specific notes](#module-specific-notes)). |
| "Garbage Container" device not updating | Check `VandaagTot` and `MorgenVanaf` in `config.txt`; restart the plugin after saving. |
