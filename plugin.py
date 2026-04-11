#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GarbageCalendar - Domoticz Python Plugin
# Retrieves garbage pickup schedules and updates a Domoticz Text device.
#
# Supported modules:
#   1  - mijnafvalwijzer       (HTML scraping, NL)
#   2  - mijnafvalwijzer_api   (JSON API, NL)
#   3  - ximmio                (Ximmio waste API, NL)
#   4  - rova_api              (Rova waste API, NL)
#   5  - rd4_api               (RD4 waste API, NL)
#   6  - opzet                 (Opzet iCal, NL - requires Hostname)
#   7  - opzet_api             (Opzet REST API, NL - requires Hostname)
#   8  - recycleapp-be         (RecycleApp Belgium - requires Street)
#   9  - omrin                 (Omrin NL - requires 'cryptography' package)
#   10 - burgerportaal         (Firebase-based, NL - requires BPName: assen/bar/rmn)
#   11 - rmn                   (RMN via burgerportaal, NL)
#   12 - deafvalapp            (De Afval App, NL)
#   13 - zuidlimburg           (ZuidLimburg HTML scraping, NL)
#   14 - montferland           (Montferland REST, NL)
#   15 - csv_file              (Local CSV file - requires file path in Extra field)
#   16 - afvalinfo             (afvalinfo.nl via trashapi, NL - requires Hostname = gemeente/city)
#   17 - reinis                (reinis.nl REST API, NL)
#
# Installation:
#   Copy this file to: <domoticz>/plugins/GarbageCalendar/plugin.py
#   Restart Domoticz, then add the plugin via Setup > Hardware.

"""
<plugin key="GarbageCalendar" name="GarbageCalendar" author="MadPatrick/jvanderzande" version="1.0.0"
    wikilink="https://github.com/MadPatrick/Domoticz_Garbage/wiki"
    externallink="https://github.com/MadPatrick/Domoticz_Garbage">
    <description>
        <h2>Garbage Calendar</h2><br/>
        Haalt uw afvalkalender op en toont de komende ophaaldata in een Domoticz tekst-device.<br/><br/>
        <b>Module keuze (Mode1):</b> kies de module die past bij uw gemeente.<br/>
        <b>Extra veld (Mode5)</b> is module-afhankelijk:<br/>
        - opzet / opzet_api: hostname (bijv. inzamelkalender.hvcgroep.nl)<br/>
        - ximmio: Companycode (open uw gemeente-website, druk F12, zoek in controller.js naar companyCode)<br/>
        - recycleapp-be: straatnaam<br/>
        - burgerportaal: BPName (assen / bar / rmn)<br/>
        - csv_file: volledig pad naar het CSV-bestand<br/>
        - afvalinfo: gemeentenaam (bijv. sliedrecht, papendrecht)<br/>
        - mijnafvalwijzer / mijnafvalwijzer_api: optionele hostname override<br/>
        - overige modules: leeg laten<br/>
    </description>
    <params>
        <param field="Mode1" label="Module" width="280px" required="true" default="2">
            <options>
                <option label="1 - mijnafvalwijzer (HTML)" value="1" />
                <option label="2 - mijnafvalwijzer_api" value="2" default="true" />
                <option label="3 - ximmio" value="3" />
                <option label="4 - rova_api" value="4" />
                <option label="5 - rd4_api" value="5" />
                <option label="6 - opzet (iCal)" value="6" />
                <option label="7 - opzet_api" value="7" />
                <option label="8 - recycleapp-be (BE)" value="8" />
                <option label="9 - omrin *" value="9" />
                <option label="10 - burgerportaal" value="10" />
                <option label="11 - rmn" value="11" />
                <option label="12 - deafvalapp" value="12" />
                <option label="13 - zuidlimburg" value="13" />
                <option label="14 - montferland" value="14" />
                <option label="15 - csv_file" value="15" />
                <option label="16 - afvalinfo (NL)" value="16" />
                <option label="17 - reinis (NL)" value="17" />
            </options>
        </param>
        <param field="Mode2" label="Postcode" width="100px" required="false" default="" />
        <param field="Mode3" label="Huisnummer" width="75px" required="false" default="" />
        <param field="Mode4" label="Huisnummer suffix" width="75px" required="false" default="" />
        <param field="Mode5" label="Extra: Hostname / Straat / BPName / Companycode / CSV-pad / Gemeente(afvalinfo)" width="300px" required="false" default="" />
        <param field="Mode6" label="Datumformaat (wd/wdd/dd/mm/mmm/mmmm/yyyy)" width="150px" required="false" default="wd dd mmm" />
        <param field="Address" label="Domoticz adres" width="150px" required="true" default="127.0.0.1" />
        <param field="Port" label="Domoticz poort" width="75px" required="true" default="8080" />
        <param field="Username" label="Dagelijkse verversingstijd (HH:MM)" width="100px" required="false" default="02:30" />
        <param field="Password" label="Aantal te tonen events" width="75px" required="false" default="3" />
    </params>
</plugin>
"""

import Domoticz
import json
import re
import os
import html as _html
import datetime
import urllib.request
import urllib.parse
import urllib.error
import threading
from typing import List, Dict, Optional

# --------------------------------------------------------------------------------------------
# Dutch date/time helpers
# --------------------------------------------------------------------------------------------

DUTCH_WEEKDAYS_SHORT = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']
DUTCH_WEEKDAYS_LONG = ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag']
DUTCH_MONTHS_SHORT = ['', 'jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
DUTCH_MONTHS_LONG = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
                     'juli', 'augustus', 'september', 'oktober', 'november', 'december']

# --------------------------------------------------------------------------------------------
# Waste type aliases
# --------------------------------------------------------------------------------------------

TYPE_ALIASES = [
    ('groente',    'GFT'),
    ('gft',        'GFT'),
    ('oud papier', 'Papier'),
    ('papier',     'Papier'),
    ('karton',     'Papier'),
    ('restafval',  'Restafval'),
    ('pmd',        'PMD'),
    ('plastic',    'PMD'),
    ('glas',       'Glas'),
    ('textiel',    'Textiel'),
    ('kerstbomen', 'Kerstbomen'),
]

# Maps canonical display names to HTML entity icon + coloured label.
# Uses HTML entities + inline style so Domoticz Text devices render them correctly,
# just like other Domoticz plugins that use styled HTML in sValue.
WASTE_ICONS: Dict[str, str] = {
    'GFT':        "<span style='color:#4caf50;'>GFT</span>",
    'Papier':     "<span style='color:#2196f3;'>Papier</span>",
    'Restafval':  "<span style='color:#607d8b;'>Restafval</span>",
    'PMD':        "<span style='color:#ff9800;'>PMD</span>",
    'Glas':       "<span style='color:#00bcd4;'>Glas</span>",
    'Textiel':    "<span style='color:#9c27b0;'>Textiel</span>",
    'Kerstbomen': "<span style='color:#388e3c;'>Kerst</span>",
}


def apply_type_alias(gtype: str) -> str:
    lower = gtype.lower()
    for key, alias in TYPE_ALIASES:
        if key in lower:
            return alias
    return gtype


INPUT_MONTHS: Dict[str, int] = {
    'jan': 1, 'feb': 2, 'mrt': 3, 'maa': 3, 'mar': 3,
    'apr': 4, 'mei': 5, 'may': 5, 'jun': 6, 'jul': 7,
    'aug': 8, 'sep': 9, 'okt': 10, 'oct': 10, 'nov': 11, 'dec': 12,
}


def format_date(d: datetime.date, fmt: str) -> str:
    result = fmt
    result = result.replace('wdd', DUTCH_WEEKDAYS_LONG[d.weekday()])
    result = result.replace('wd', DUTCH_WEEKDAYS_SHORT[d.weekday()])
    result = result.replace('mmmm', DUTCH_MONTHS_LONG[d.month])
    result = result.replace('mmm', DUTCH_MONTHS_SHORT[d.month])
    result = result.replace('mm', f'{d.month:02d}')
    result = result.replace('dd', f'{d.day:02d}')
    result = result.replace('yyyy', str(d.year))
    result = result.replace('yy', str(d.year)[-2:])
    return result


def parse_iso_date(s: str) -> Optional[datetime.date]:
    if not s:
        return None
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def parse_compact_date(s: str) -> Optional[datetime.date]:
    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def parse_dutch_date(s: str) -> Optional[datetime.date]:
    parts = s.strip().split()
    today = datetime.date.today()
    try:
        if len(parts) == 3:
            if parts[2].isdigit() and len(parts[2]) == 4:
                dd, mm_str, yyyy = int(parts[0]), parts[1].lower(), int(parts[2])
            else:
                dd, mm_str, yyyy = int(parts[1]), parts[2].lower(), today.year
            mm = INPUT_MONTHS.get(mm_str)
            if mm:
                d = datetime.date(yyyy, mm, dd)
                if d < today and len(parts[2]) != 4:
                    d = datetime.date(yyyy + 1, mm, dd)
                return d
        elif len(parts) == 2:
            dd, mm_str = int(parts[0]), parts[1].lower()
            mm = INPUT_MONTHS.get(mm_str)
            if mm:
                d = datetime.date(today.year, mm, dd)
                if d < today:
                    d = datetime.date(today.year + 1, mm, dd)
                return d
    except (ValueError, TypeError):
        pass
    return None


# --------------------------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------------------------

DEFAULT_HEADERS = {'User-Agent': 'GarbageCalendar-DomoticzPlugin/1.0'}


def http_get(url: str, headers: Optional[Dict] = None, timeout: int = 30) -> str:
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    req = urllib.request.Request(url, headers=merged)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        try:
            Domoticz.Error(f'HTTP {e.code} for {url}: {e.reason}')
        except Exception:
            pass
        return ''
    except Exception as e:
        try:
            Domoticz.Error(f'Request failed for {url}: {e}')
        except Exception:
            pass
        return ''


def http_post(url: str, data: bytes, headers: Optional[Dict] = None, timeout: int = 30) -> str:
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=merged, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        try:
            Domoticz.Error(f'HTTP {e.code} for {url}: {e.reason}')
        except Exception:
            pass
        return ''
    except Exception as e:
        try:
            Domoticz.Error(f'Request failed for {url}: {e}')
        except Exception:
            pass
        return ''


# --------------------------------------------------------------------------------------------
# Base module class
# --------------------------------------------------------------------------------------------

class GarbageModule:
    name = 'base'

    def fetch(self, zipcode: str, housenr: str, housenrsuf: str, extra: str) -> List[Dict]:
        raise NotImplementedError

    def _log(self, msg: str) -> None:
        try:
            Domoticz.Log(f'[GC/{self.name}] {msg}')
        except Exception:
            pass

    def _debug(self, msg: str) -> None:
        try:
            Domoticz.Debug(f'[GC/{self.name}] {msg}')
        except Exception:
            pass

    def _error(self, msg: str) -> None:
        try:
            Domoticz.Error(f'[GC/{self.name}] {msg}')
        except Exception:
            pass

    @staticmethod
    def _make_entry(gtype: str, d: datetime.date, wdesc: str = '', icon_url: str = '') -> Dict:
        return {'type': gtype, 'date': d, 'wdesc': wdesc, 'icon_url': icon_url}


# --------------------------------------------------------------------------------------------
# Module 1: m_mijnafvalwijzer  (HTML scraping)
# --------------------------------------------------------------------------------------------

class MijnAfvalwijzerModule(GarbageModule):
    name = 'm_mijnafvalwijzer'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        host = extra.strip() if extra.strip() else 'www.mijnafvalwijzer.nl'
        url = f'https://{host}/nl/{zipcode}/{housenr}{housenrsuf}'
        self._log(f'GET {url}')
        html = http_get(url)
        if not html:
            self._error('Empty response')
            return []

        html = re.sub(r'<img\s+src="data:image[^"]*">', '', html)

        start = html.find('href="#waste')
        if start == -1:
            start = html.find('ITEMS layout -->')
        if start == -1:
            self._error('Calendar section not found in HTML')
            return []

        end = html.find('<!-- DESKTOP/TABLET VIEW:', start)
        if end == -1:
            end = start + 120000
        section = html[start:min(end, len(html))]

        today = datetime.date.today()
        results = []
        for block in re.finditer(r'<a\s[^>]*href="#waste-.*?</a>', section, re.DOTALL):
            txt = block.group(0)
            m_type = re.search(r'href="#waste-([^"]+)"', txt)
            m_date = re.search(r'class="span-line-break">(.*?)</span>', txt, re.DOTALL)
            m_desc = re.search(r'afvaldescr[^>]*>(.*?)</span>', txt, re.DOTALL)
            if not m_type or not m_date:
                continue
            gtype = m_type.group(1).strip()
            dstr = re.sub(r'\s+', ' ', m_date.group(1)).strip()
            wdesc = m_desc.group(1).strip() if m_desc else ''
            d = parse_dutch_date(dstr)
            if d and d >= today:
                results.append(self._make_entry(gtype, d, wdesc))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 2: m_mijnafvalwijzer_api  (JSON API)
# --------------------------------------------------------------------------------------------

class MijnAfvalwijzerApiModule(GarbageModule):
    name = 'm_mijnafvalwijzer_api'
    _API_KEY = '5ef443e778f41c4f75c69459eea6e6ae0c2d92de729aa0fc61653815fbd6a8ca'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        host = extra.strip() if extra.strip() else 'api.mijnafvalwijzer.nl'
        today = datetime.date.today()
        year = today.year
        url = (
            f'https://{host}/webservices/appsinput/'
            f'?apikey={self._API_KEY}&method=postcodecheck'
            f'&postcode={zipcode}&street=&huisnummer={housenr}'
            f'&toevoeging={housenrsuf or ""}'
            f'&app_name=afvalwijzer&platform=phone&mobiletype=android'
            f'&afvaldata={year}-01-01&version=58&langs=nl'
        )
        self._log(f'GET {url}')
        raw = http_get(url)
        if not raw:
            self._error('Empty response')
            return []
        try:
            jdata = json.loads(raw)
        except json.JSONDecodeError as e:
            self._error(f'JSON error: {e}')
            return []

        results = []
        for key in ['ophaaldagen', 'ophaaldagenNext']:
            section = jdata.get(key, {})
            if not isinstance(section, dict):
                continue
            for record in section.get('data', []):
                if not isinstance(record, dict):
                    continue
                gtype = record.get('type', '')
                d = parse_iso_date(record.get('date', ''))
                if d and d >= today:
                    results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 3: m_ximmio
# --------------------------------------------------------------------------------------------

class XimmioModule(GarbageModule):
    name = 'm_ximmio'
    _HOSTS = ['https://wasteprod2api.ximmio.com', 'https://wasteapi.2go-mobile.com']

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        companycode = extra.strip()
        if not companycode:
            self._error('Companycode is required (use the Extra field)')
            return []

        today = datetime.date.today()
        webhost = None
        unique_id = ''

        for host in self._HOSTS:
            post_data = urllib.parse.urlencode({
                'companyCode': companycode,
                'postCode': zipcode,
                'houseNumber': housenr,
                'houseNumberAddition': housenrsuf or '',
            }).encode()
            raw = http_post(f'{host}/api/FetchAdress', post_data,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
            if not raw or raw.strip().startswith('[]'):
                continue
            try:
                adata = json.loads(raw)
            except json.JSONDecodeError:
                continue
            datalist = adata.get('dataList', [])
            if datalist and isinstance(datalist, list):
                unique_id = datalist[0].get('UniqueId', '')
                if unique_id:
                    webhost = host
                    break

        if not unique_id or not webhost:
            self._error('Could not retrieve UniqueId - check Zipcode, Housenr and Companycode')
            return []

        self._log(f'UniqueId: {unique_id}')
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        post_data = urllib.parse.urlencode({
            'companyCode': companycode,
            'uniqueAddressID': unique_id,
            'startDate': start_date,
            'endDate': end_date,
        }).encode()
        raw = http_post(f'{webhost}/api/GetCalendar', post_data,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if not raw or raw.strip().startswith('[]'):
            self._error('Could not retrieve calendar')
            return []
        try:
            cdata = json.loads(raw)
        except json.JSONDecodeError:
            self._error('Calendar JSON parse error')
            return []

        results = []
        for record in cdata.get('dataList', []):
            gtype = record.get('_pickupTypeText', '')
            wdesc = record.get('description', '') or ''
            if wdesc == 'Null':
                wdesc = ''
            for dstr in record.get('pickupDates', []):
                d = parse_iso_date(dstr)
                if d and d >= today:
                    results.append(self._make_entry(gtype, d, wdesc))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 4: m_rova_api
# --------------------------------------------------------------------------------------------

class RovaApiModule(GarbageModule):
    name = 'm_rova_api'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        today = datetime.date.today()
        results = []
        for year in [today.year, today.year + 1]:
            url = (
                f'https://www.rova.nl/api/waste-calendar/year'
                f'?postalcode={zipcode}&houseNumber={housenr}'
                f'&addition={housenrsuf or ""}&year={year}'
            )
            self._log(f'GET {url}')
            raw = http_get(url)
            if not raw:
                continue
            try:
                items = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(items, list):
                continue
            for record in items:
                waste_type = record.get('wasteType', {}) or {}
                gtype = waste_type.get('code', '') if isinstance(waste_type, dict) else ''
                wdesc = waste_type.get('title', '') if isinstance(waste_type, dict) else ''
                d = parse_iso_date(record.get('date', ''))
                if d and d >= today:
                    results.append(self._make_entry(gtype, d, wdesc))
            if len(results) >= 10:
                break

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 5: m_rd4_api
# --------------------------------------------------------------------------------------------

class Rd4ApiModule(GarbageModule):
    name = 'm_rd4_api'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        today = datetime.date.today()
        results = []
        for year in [today.year, today.year + 1]:
            url = (
                f'https://data.rd4.nl/api/v1/waste-calendar'
                f'?postal_code={zipcode}&house_number={housenr}'
                f'&house_number_extension={housenrsuf or ""}&year={year}'
            )
            self._log(f'GET {url}')
            raw = http_get(url)
            if not raw:
                continue
            try:
                jdata = json.loads(raw)
            except json.JSONDecodeError:
                continue
            outer = jdata.get('data', {}).get('items', [[]])
            items = outer[0] if outer and isinstance(outer, list) else []
            if not isinstance(items, list):
                continue
            for record in items:
                gtype = record.get('type', '')
                d = parse_iso_date(record.get('date', ''))
                if d and d >= today:
                    results.append(self._make_entry(gtype, d, gtype))
            if len(results) >= 10:
                break

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 6: m_opzet  (iCal)
# --------------------------------------------------------------------------------------------

class OpzetModule(GarbageModule):
    name = 'm_opzet'

    def _get_bag_id(self, hostname: str, zipcode: str, housenr: str, housenrsuf: str) -> str:
        url = f'https://{hostname}/rest/adressen/{zipcode}-{housenr}'
        self._log(f'GET {url}')
        raw = http_get(url)
        if not raw or raw.strip().startswith('[]'):
            self._error('Empty or [] address response')
            return ''
        try:
            adata = json.loads(raw)
        except json.JSONDecodeError:
            self._error('Address JSON parse error')
            return ''
        bag_id = ''
        for record in adata:
            if not isinstance(record, dict):
                continue
            bag_id = record.get('bagId', '')
            if record.get('huisletter', '') == housenrsuf:
                break
        return bag_id

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        hostname = extra.strip()
        if not hostname:
            self._error('Hostname required (use the Extra field)')
            return []

        today = datetime.date.today()
        bag_id = self._get_bag_id(hostname, zipcode, housenr, housenrsuf)
        if not bag_id:
            self._error('No bagId found - check Zipcode, Housenr and Hostname')
            return []
        self._log(f'bagId: {bag_id}')

        url = f'https://{hostname}/ical/{bag_id}'
        self._log(f'GET {url}')
        ical = http_get(url)
        if not ical:
            self._error('Empty iCal response')
            return []

        results = []
        for m in re.finditer(
            r'DTSTART;VALUE=DATE:(\d{8})\r?\n.*?SUMMARY:(.*?)\r?\n',
            ical, re.DOTALL
        ):
            d = parse_compact_date(m.group(1))
            gtype = re.sub(r'[\r\n\\]', '', m.group(2)).strip()
            if d and d >= today:
                results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 7: m_opzet_api  (REST API)
# --------------------------------------------------------------------------------------------

class OpzetApiModule(OpzetModule):
    name = 'm_opzet_api'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        hostname = extra.strip()
        if not hostname:
            self._error('Hostname required (use the Extra field)')
            return []

        today = datetime.date.today()
        bag_id = self._get_bag_id(hostname, zipcode, housenr, housenrsuf)
        if not bag_id:
            self._error('No bagId found - check Zipcode, Housenr and Hostname')
            return []
        self._debug(f'bagId: {bag_id}')

        raw_types = http_get(f'https://{hostname}/rest/adressen/{bag_id}/afvalstromen')
        type_map: Dict[int, str] = {}
        icon_map: Dict[int, str] = {}
        if raw_types:
            try:
                for item in json.loads(raw_types):
                    if isinstance(item, dict):
                        tid = item.get('id')
                        type_map[tid] = item.get('title', '')
                        icon_val = item.get('icon', '') or ''
                        if icon_val:
                            if icon_val.startswith('http'):
                                icon_map[tid] = icon_val
                            elif icon_val.startswith('/'):
                                icon_map[tid] = f'https://{hostname}{icon_val}'
            except json.JSONDecodeError:
                pass

        results = []
        for year in [today.year, today.year + 1]:
            url = f'https://{hostname}/rest/adressen/{bag_id}/kalender/{year}'
            self._debug(f'GET {url}')
            raw = http_get(url)
            if not raw or raw.strip().startswith('[]'):
                continue
            try:
                cal_data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for record in cal_data:
                if not isinstance(record, dict):
                    continue
                type_id = record.get('afvalstroom_id')
                dstr = record.get('ophaaldatum')
                if not dstr:
                    continue
                gtype = type_map.get(type_id, str(type_id) if type_id is not None else '')
                icon_url = icon_map.get(type_id, '')
                d = parse_iso_date(dstr)
                if d and d >= today:
                    results.append(self._make_entry(gtype, d, icon_url=icon_url))
            if len(results) >= 10:
                break

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 8: m_recycleapp-be
# --------------------------------------------------------------------------------------------

class RecycleAppBeModule(GarbageModule):
    name = 'm_recycleapp-be'
    _BASE_URL = 'https://api.fostplus.be/recycle-public/app/v1'
    _SECRET = (
        'Op2tDi2pBmh1wzeC5TaN2U3knZan7ATcfOQgxh4vqC0mDKmnPP2qzoQusmInpglfIkxx8SZrasBqi5zgMSvy'
        'HggK9j6xCQNQ8xwPFY2o03GCcQfcXVOyKsvGWLze7iwcfcgk2Ujpl0dmrt3hSJMCDqzAlvTrsvAEiaSzC9hK'
        'RwhijQAFHuFIhJssnHtDSB76vnFQeTCCvwVB27DjSVpDmq8fWQKEmjEncdLqIsRnfxLcOjGIVwX5V0LBntVbe'
        'iBvcjyKF2nQ08rIxqHHGXNJ6SbnAmTgsPTg7k6Ejqa7dVfTmGtEPdftezDbuEc8DdK66KDecqnxwOOPSJIN0z'
        'aJ6k2Ye2tgMSxxf16gxAmaOUqHS0i7dtG5PgPSINti3qlDdw6DTKEPni7X0rxM'
    )

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        street = extra.strip()
        if not street:
            self._error('Street name required (use the Extra field)')
            return []

        today = datetime.date.today()
        base_headers = {'x-secret': self._SECRET, 'x-consumer': 'recycleapp.be'}

        raw = http_get(f'{self._BASE_URL}/access-token', headers=base_headers)
        if not raw:
            self._error('Could not get access token')
            return []
        try:
            access_token = json.loads(raw).get('accessToken', '')
        except json.JSONDecodeError:
            return []
        if not access_token:
            self._error('Empty access token')
            return []

        auth_headers = {**base_headers, 'Authorization': access_token}

        raw = http_get(f'{self._BASE_URL}/zipcodes?q={urllib.parse.quote(zipcode)}',
                       headers=auth_headers)
        try:
            postcode_id = json.loads(raw).get('items', [{}])[0].get('id', '')
        except (json.JSONDecodeError, IndexError):
            self._error('Could not get postcode_id')
            return []

        raw = http_get(
            f'{self._BASE_URL}/streets?q={urllib.parse.quote(street)}&zipcodes={postcode_id}',
            headers=auth_headers,
        )
        try:
            street_id = json.loads(raw).get('items', [{}])[0].get('id', '')
        except (json.JSONDecodeError, IndexError):
            self._error('Could not get street_id')
            return []

        start = today.strftime('%Y-%m-%d')
        end = (today + datetime.timedelta(days=180)).strftime('%Y-%m-%d')
        url = (
            f'{self._BASE_URL}/collections'
            f'?zipcodeId={postcode_id}&streetId={street_id}'
            f'&houseNumber={housenr}&fromDate={start}&untilDate={end}&size=100'
        )
        self._log(f'GET {url}')
        raw = http_get(url, headers=auth_headers)
        try:
            cdata = json.loads(raw)
        except json.JSONDecodeError:
            self._error('Calendar JSON parse error')
            return []

        results = []
        for item in cdata.get('items', []):
            fraction = item.get('fraction', {}) or {}
            gtype = fraction.get('name', {}).get('nl', '') if isinstance(fraction, dict) else ''
            d = parse_iso_date(item.get('timestamp', ''))
            if d and d >= today:
                results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 9: m_omrin
# --------------------------------------------------------------------------------------------

class OmrinModule(GarbageModule):
    name = 'm_omrin'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        try:
            import uuid
            import base64
            from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            self._error(
                "The 'cryptography' package is required for the omrin module. "
                "Install with: pip3 install cryptography"
            )
            return []

        today = datetime.date.today()
        app_id = str(uuid.uuid4())
        thnr = housenr + (housenrsuf or '')

        token_body = json.dumps({
            'AppId': app_id, 'AppVersion': '', 'OsVersion': '', 'Platform': 'HomeAssistant',
        })
        raw = http_post(
            'https://api-omrin.freed.nl/Account/GetToken/',
            token_body.encode(),
            headers={'Content-Type': 'application/json'},
        )
        if not raw:
            self._error('Could not get token')
            return []
        try:
            jtoken = json.loads(raw)
        except json.JSONDecodeError:
            self._error('Token JSON parse error')
            return []

        public_key_b64 = jtoken.get('PublicKey', '')
        if not public_key_b64:
            self._error('No PublicKey in token response')
            return []

        pem_key = f'-----BEGIN PUBLIC KEY-----\n{public_key_b64}\n-----END PUBLIC KEY-----\n'
        try:
            pub_key = serialization.load_pem_public_key(pem_key.encode(), backend=default_backend())
        except Exception as e:
            self._error(f'Failed to load public key: {e}')
            return []

        request_body = json.dumps({
            'a': False, 'Email': None, 'Password': None,
            'PostalCode': zipcode, 'HouseNumber': thnr,
        })
        try:
            encrypted = pub_key.encrypt(request_body.encode(), asym_padding.PKCS1v15())
        except Exception as e:
            self._error(f'Encryption failed: {e}')
            return []

        encrypted_b64 = base64.b64encode(encrypted).decode()
        raw = http_post(
            f'https://api-omrin.freed.nl/Account/FetchAccount/{app_id}',
            f'"{encrypted_b64}"'.encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        if not raw:
            self._error('Empty FetchAccount response')
            return []
        try:
            jdata = json.loads(raw)
        except json.JSONDecodeError:
            self._error('FetchAccount JSON parse error')
            return []

        results = []
        for key in ['CalendarV2', 'CalendarHomeV2']:
            for record in jdata.get(key, []):
                if not isinstance(record, dict):
                    continue
                gtype = record.get('Omschrijving', '')
                d = parse_iso_date(record.get('Datum', ''))
                if d and d >= today:
                    results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 10: m_burgerportaal
# --------------------------------------------------------------------------------------------

class BurgerportaalModule(GarbageModule):
    name = 'm_burgerportaal'
    _FIREBASE_KEY = 'AIzaSyA6NkRqJypTfP-cjWzrZNFJzPUbBaGjOdk'
    _BP_CODES: Dict[str, str] = {
        'assen': '138204213565303512',
        'bar':   '138204213564933497',
        'rmn':   '138204213564933597',
    }
    _GCF_BASE = 'https://europe-west3-burgerportaal-production.cloudfunctions.net/exposed'

    def __init__(self, token_file: Optional[str] = None):
        _plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self._token_file = token_file or os.path.join(_plugin_dir, 'gc_burgerportaal_token.txt')

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        bp_name = extra.strip().lower()
        if bp_name not in self._BP_CODES:
            self._error(f'BPName "{bp_name}" not supported. Use: assen / bar / rmn')
            return []
        org_id = self._BP_CODES[bp_name]
        return self._fetch_for_org(zipcode, housenr, housenrsuf, org_id)

    def _fetch_for_org(self, zipcode, housenr, housenrsuf, org_id):
        today = datetime.date.today()
        thnr = housenr + (housenrsuf or '')
        id_token = self._get_id_token()
        if not id_token:
            return []

        url = f'{self._GCF_BASE}/organisations/{org_id}/address?zipcode={zipcode.upper()}&housenumber={thnr}'
        self._log(f'GET {url}')
        raw = http_get(url, headers={'authorization': id_token})
        try:
            adata = json.loads(raw)
            address_id = adata[0].get('addressId', '') if adata else ''
        except (json.JSONDecodeError, IndexError, KeyError):
            self._error('Could not get addressId')
            return []

        if not address_id:
            self._error('Empty addressId')
            return []

        url2 = f'{self._GCF_BASE}/organisations/{org_id}/address/{address_id}/calendar'
        self._log(f'GET {url2}')
        raw2 = http_get(url2, headers={'authorization': id_token})
        try:
            cal = json.loads(raw2)
        except json.JSONDecodeError:
            self._error('Calendar JSON parse error')
            return []

        results = []
        for record in cal:
            if not isinstance(record, dict):
                continue
            gtype = record.get('fraction', '')
            d = parse_iso_date(record.get('collectionDate', ''))
            if d and d >= today:
                results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results

    def _get_id_token(self):
        refresh_token = self._load_refresh_token()
        if len(refresh_token) >= 200:
            return self._refresh_id_token(refresh_token)
        return self._signup_and_get_token()

    def _load_refresh_token(self):
        try:
            with open(self._token_file, 'r') as f:
                return f.read().strip()
        except Exception:
            return ''

    def _save_refresh_token(self, token):
        try:
            with open(self._token_file, 'w') as f:
                f.write(token)
        except Exception:
            pass

    def _signup_and_get_token(self):
        url = (f'https://www.googleapis.com/identitytoolkit/v3/relyingparty/'
               f'signupNewUser?key={self._FIREBASE_KEY}')
        raw = http_post(url, b'', headers={'Content-Length': '0'})
        try:
            data = json.loads(raw)
            id_token = data.get('idToken', '')
            refresh_token = data.get('refreshToken', '')
            if refresh_token:
                self._save_refresh_token(refresh_token)
            return id_token
        except json.JSONDecodeError:
            self._error('Could not get Firebase signup token')
            return ''

    def _refresh_id_token(self, refresh_token):
        url = f'https://securetoken.googleapis.com/v1/token?key={self._FIREBASE_KEY}'
        post_data = f'grant_type=refresh_token&refresh_token={urllib.parse.quote(refresh_token)}'.encode()
        raw = http_post(url, post_data,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            data = json.loads(raw)
            id_token = data.get('id_token', '')
            new_refresh = data.get('refresh_token', '')
            if new_refresh:
                self._save_refresh_token(new_refresh)
            return id_token if id_token else self._signup_and_get_token()
        except json.JSONDecodeError:
            return self._signup_and_get_token()


# --------------------------------------------------------------------------------------------
# Module 11: m_rmn
# --------------------------------------------------------------------------------------------

class RmnModule(BurgerportaalModule):
    name = 'm_rmn'
    _RMN_ORG_ID = '138204213564933597'

    def __init__(self, token_file: Optional[str] = None):
        _plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self._token_file = token_file or os.path.join(_plugin_dir, 'gc_rmn_token.txt')

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        return self._fetch_for_org(zipcode, housenr, housenrsuf, self._RMN_ORG_ID)


# --------------------------------------------------------------------------------------------
# Module 12: m_deafvalapp
# --------------------------------------------------------------------------------------------

class DeAfvalAppModule(GarbageModule):
    name = 'm_deafvalapp'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        today = datetime.date.today()
        url = (
            f'https://dataservice.deafvalapp.nl/dataservice/DataServiceServlet'
            f'?service=OPHAALSCHEMA&land=NL&postcode={zipcode}'
            f'&straatId=0&huisnr={housenr}{housenrsuf or ""}'
        )
        self._log(f'GET {url}')
        raw = http_get(url)
        if not raw:
            self._error('Empty response')
            return []

        results = []
        for line in raw.splitlines():
            parts = line.strip().split(';')
            if len(parts) < 2:
                continue
            gtype = parts[0].strip()
            if not gtype or gtype.lower() == 'garbagedate':
                continue
            for dstr in parts[1:]:
                dstr = dstr.strip()
                if not dstr:
                    continue
                m = re.match(r'(\d+)-(\d+)-(\d{4})', dstr)
                if m:
                    try:
                        d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                        if d >= today:
                            results.append(self._make_entry(gtype, d))
                    except ValueError:
                        pass

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 13: m_zuidlimburg
# --------------------------------------------------------------------------------------------

class ZuidLimburgModule(GarbageModule):
    name = 'm_zuidlimburg'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        today = datetime.date.today()
        url = (
            f'https://www.rd4info.nl/NSI/Burger/Aspx/afvalkalender_public_text.aspx'
            f'?pc={zipcode}&nr={housenr}{housenrsuf or ""}&t'
        )
        self._log(f'GET {url}')
        html = http_get(url)
        if not html:
            self._error('Empty response')
            return []

        m = re.search(r'<div id="Afvalkalender1_pnlAfvalKalender">(.*?)</div>', html, re.DOTALL)
        if not m:
            self._error('Could not find calendar section in HTML')
            return []
        section = m.group(1)

        results = []
        for row in re.finditer(r'<td>.*?\s+(.*?)</td><td>(.*?)</td>', section, re.DOTALL):
            dstr = re.sub(r'\s+', ' ', row.group(1)).strip()
            gtype = row.group(2).strip()
            d = self._parse_date(dstr, today)
            if d and d >= today:
                results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results

    @staticmethod
    def _parse_date(s, today):
        parts = s.strip().split()
        try:
            if len(parts) >= 2:
                dd = int(parts[0])
                mm = INPUT_MONTHS.get(parts[1].lower())
                yyyy = int(parts[-1]) if (len(parts) > 2 and parts[-1].isdigit() and len(parts[-1]) == 4) else today.year
                if mm:
                    return datetime.date(yyyy, mm, dd)
        except (ValueError, TypeError):
            pass
        return None


# --------------------------------------------------------------------------------------------
# Module 14: m_montferland
# --------------------------------------------------------------------------------------------

class MontferlandModule(GarbageModule):
    name = 'm_montferland'
    _BASE = 'http://afvalwijzer.afvaloverzicht.nl'
    _PWD = urllib.parse.quote('gsd$2014')

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        today = datetime.date.today()

        url = (
            f'{self._BASE}/Login.ashx?Username=GSD&Password={self._PWD}'
            f'&Postcode={zipcode}&Huisnummer={housenr}&Toevoeging={housenrsuf or ""}'
        )
        self._log(f'GET {url}')
        raw = http_get(url)
        if not raw or raw.strip().startswith('[]'):
            self._error('Could not get address info - check Zipcode/Housenr')
            return []
        try:
            adata = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not adata:
            return []
        adres_id = adata[0].get('AdresID', '')
        admin_id = adata[0].get('AdministratieID', '')
        if not adres_id or not admin_id:
            self._error('No AdresID or AdministratieID in response')
            return []

        results = []
        for year in [today.year, today.year + 1]:
            date_str = urllib.parse.quote(today.strftime('%d/%m/%Y 01:00:00 AM'))
            url2 = (
                f'{self._BASE}/OphaalDatums.ashx?ADM_ID={admin_id}'
                f'&Username=GSD&Password={self._PWD}'
                f'&ADR_ID={adres_id}&Jaar={year}&Date={date_str}'
            )
            self._log(f'GET {url2}')
            raw2 = http_get(url2)
            if not raw2 or raw2.strip().startswith('[]'):
                continue
            try:
                items = json.loads(raw2)
            except json.JSONDecodeError:
                continue
            for record in items:
                if not isinstance(record, dict):
                    continue
                gtype = record.get('Soort', '')
                d = parse_iso_date(record.get('Datum', ''))
                if d and d >= today:
                    results.append(self._make_entry(gtype, d))
            if len(results) >= 10:
                break

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 15: m_csv_file
# --------------------------------------------------------------------------------------------

class CsvFileModule(GarbageModule):
    name = 'm_csv_file'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        csv_path = extra.strip()
        if not csv_path:
            self._error('CSV file path required (use the Extra field)')
            return []
        if not os.path.isfile(csv_path):
            self._error(f'CSV file not found: {csv_path}')
            return []

        today = datetime.date.today()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except OSError as e:
            self._error(f'Could not read CSV file: {e}')
            return []

        results = []
        for line in content.splitlines():
            parts = line.strip().split(';')
            if len(parts) < 2:
                continue
            dstr = parts[0].strip()
            gtype = parts[1].strip()
            if not gtype or dstr.lower() == 'garbagedate':
                continue
            m = re.match(r'(\d+)-(\d+)-(\d{4})', dstr)
            if m:
                try:
                    d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                    if d >= today:
                        results.append(self._make_entry(gtype, d))
                except ValueError:
                    pass

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 16: m_afvalinfo
# --------------------------------------------------------------------------------------------

class AfvalInfoModule(GarbageModule):
    name = 'm_afvalinfo'
    _BASE = 'https://trashapi.azurewebsites.net/trash'

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        gemeente = extra.strip()
        if not gemeente:
            self._error('Municipality name required (use the Extra field, e.g. "sliedrecht")')
            return []

        today = datetime.date.today()
        params = urllib.parse.urlencode({
            'Location': gemeente,
            'ZipCode': zipcode,
            'HouseNumber': housenr,
            'HouseNumberSuffix': housenrsuf or '',
        })
        url = f'{self._BASE}?{params}'
        self._log(f'GET {url}')
        raw = http_get(url)
        if not raw:
            self._error('Empty response')
            return []
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            self._error(f'JSON error: {e}')
            return []

        if not isinstance(items, list):
            self._error('Unexpected response format (expected a JSON array)')
            return []

        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            gtype = item.get('nameType', '')
            if not gtype:
                continue
            for dstr in item.get('pickupDates', []):
                d = parse_iso_date(dstr)
                if d and d >= today:
                    results.append(self._make_entry(gtype, d))

        results.sort(key=lambda x: x['date'])
        return results


# --------------------------------------------------------------------------------------------
# Module 17: m_reinis
# --------------------------------------------------------------------------------------------

class ReinisModule(OpzetApiModule):
    name = 'm_reinis'
    _HOSTNAME = 'reinis.nl'

    def _get_bag_id(self, hostname, zipcode, housenr, housenrsuf):
        url = f'https://{hostname}/adressen/{zipcode}:{housenr}'
        self._debug(f'GET {url}')
        raw = http_get(url)
        if not raw or raw.strip().startswith('[]'):
            self._error('Empty or [] address response')
            return ''
        try:
            adata = json.loads(raw)
        except json.JSONDecodeError:
            self._error('Address JSON parse error')
            return ''
        bag_id = ''
        for record in adata:
            if not isinstance(record, dict):
                continue
            bag_id = record.get('bagid', '')
            if record.get('huisletter', '') == housenrsuf:
                break
        return bag_id

    def fetch(self, zipcode, housenr, housenrsuf, extra):
        return super().fetch(zipcode, housenr, housenrsuf, self._HOSTNAME)


# --------------------------------------------------------------------------------------------
# Module registry
# --------------------------------------------------------------------------------------------

MODULES: Dict[str, GarbageModule] = {
    '1':  MijnAfvalwijzerModule(),
    '2':  MijnAfvalwijzerApiModule(),
    '3':  XimmioModule(),
    '4':  RovaApiModule(),
    '5':  Rd4ApiModule(),
    '6':  OpzetModule(),
    '7':  OpzetApiModule(),
    '8':  RecycleAppBeModule(),
    '9':  OmrinModule(),
    '10': BurgerportaalModule(),
    '11': RmnModule(),
    '12': DeAfvalAppModule(),
    '13': ZuidLimburgModule(),
    '14': MontferlandModule(),
    '15': CsvFileModule(),
    '16': AfvalInfoModule(),
    '17': ReinisModule(),
}

# --------------------------------------------------------------------------------------------
# Domoticz Plugin class
# --------------------------------------------------------------------------------------------

class BasePlugin:
    UNIT_TEXT   = 1
    UNIT_SWITCH = 2
    HEARTBEAT_SECS = 30

    def __init__(self):
        self._module: Optional[GarbageModule] = None
        self._zipcode = ''
        self._housenr = ''
        self._housenrsuf = ''
        self._extra = ''
        self._date_fmt = 'wd dd mmm'
        self._show_events = 3
        self._update_hour = 2
        self._update_min = 30
        self._last_fetch_date: Optional[datetime.date] = None
        self._cached_results: List[Dict] = []
        self._fetching = False
        self._lock = threading.Lock()
        self.imageID = -1

    def onStart(self):
        Domoticz.Heartbeat(self.HEARTBEAT_SECS)

        module_key = Parameters.get('Mode1', '2').strip()
        self._zipcode = Parameters.get('Mode2', '').strip()
        self._housenr = Parameters.get('Mode3', '').strip()
        self._housenrsuf = Parameters.get('Mode4', '').strip()
        self._extra = Parameters.get('Mode5', '').strip()
        self._date_fmt = Parameters.get('Mode6', 'wd dd mmm').strip() or 'wd dd mmm'

        try:
            self._show_events = max(1, int(Parameters.get('Password', '3') or '3'))
        except ValueError:
            self._show_events = 3

        update_time = Parameters.get('Username', '02:30').strip()
        try:
            h, m = update_time.split(':')
            self._update_hour = int(h)
            self._update_min = int(m)
        except (ValueError, AttributeError):
            self._update_hour = 2
            self._update_min = 30

        try:
            if "Garbage" not in Images:
                Domoticz.Image("Garbage.zip").Create()
            if "Garbage" in Images:
                self.imageID = Images["Garbage"].ID
            else:
                Domoticz.Error("Unable to load icon pack 'Garbage.zip'")
        except Exception as e:
            Domoticz.Error(f"Error loading icon pack 'Garbage': {e}")

        self._module = MODULES.get(module_key)
        if not self._module:
            Domoticz.Error(f'Unknown module key: "{module_key}". Check Mode1 parameter.')
            return

        Domoticz.Log(
            f'GarbageCalendar started | module: {self._module.name} | '
            f'postcode: {self._zipcode} | huisnr: {self._housenr}{self._housenrsuf} | '
            f'refresh at: {self._update_hour:02d}:{self._update_min:02d} | '
            f'events: {self._show_events}'
        )

        if self.UNIT_TEXT not in Devices:
            self._create_text_device()
            Domoticz.Log('Text device "GarbageCalendar" created')

        if self.UNIT_SWITCH not in Devices:
            self._create_switch_device()
            Domoticz.Log('Switch device "GarbageCalendar Today" created')

        self._trigger_fetch()

    def onStop(self):
        Domoticz.Log('GarbageCalendar stopped')

    def onHeartbeat(self):
        if not self._module:
            return

        now = datetime.datetime.now()
        today = now.date()

        with self._lock:
            already_fetched_today = (self._last_fetch_date == today)

        if not already_fetched_today:
            past_update_time = (
                now.hour > self._update_hour or
                (now.hour == self._update_hour and now.minute >= self._update_min)
            )
            if past_update_time:
                self._trigger_fetch()
        else:
            self._update_device()

    def _create_text_device(self):
        image_kwarg = {'Image': self.imageID} if self.imageID >= 0 else {}
        Domoticz.Device(Name='GarbageCalendar', Unit=self.UNIT_TEXT,
                        TypeName='Text', Used=1, **image_kwarg).Create()

    def _create_switch_device(self):
        image_kwarg = {'Image': self.imageID} if self.imageID >= 0 else {}
        Domoticz.Device(Name='GarbageCalendar Today', Unit=self.UNIT_SWITCH,
                        TypeName='Switch', Used=1, **image_kwarg).Create()

    def _trigger_fetch(self):
        with self._lock:
            if self._fetching:
                return
            self._fetching = True
        t = threading.Thread(target=self._do_fetch, daemon=True)
        t.start()

    def _do_fetch(self):
        try:
            Domoticz.Log(f'Fetching calendar data from {self._module.name}...')
            results = self._module.fetch(
                self._zipcode,
                self._housenr,
                self._housenrsuf,
                self._extra,
            )
            with self._lock:
                self._cached_results = results
                self._last_fetch_date = datetime.date.today()
            Domoticz.Log(f'Fetch complete: {len(results)} upcoming event(s) found')
            self._update_device()
        except Exception as e:
            Domoticz.Error(f'Fetch error: {e}')
        finally:
            with self._lock:
                self._fetching = False

    def _update_device(self):
        """Update the Domoticz text device with the next N upcoming events.

        Layout per regel:
            📅  <datum vaste breedte>    <icon> <gekleurde naam>

        De datum-kolom krijgt een vaste breedte via display:inline-block zodat
        de icon+naam op elke regel op dezelfde horizontale positie begint.
        Regels worden gescheiden door <br> — betrouwbaarder in Domoticz dan <table>.
        """
        today = datetime.date.today()

        with self._lock:
            future = [r for r in self._cached_results if r['date'] >= today]

        future = future[:self._show_events]

        if not future:
            text = 'Geen ophaaldata beschikbaar'
        else:
            lines = []
            for r in future:
                date_str = format_date(r['date'], self._date_fmt)
                display_type = apply_type_alias(r['type'])
                icon_url = r.get('icon_url', '')

                # Datum in vaste breedte zodat de tweede kolom uitlijnt op elke regel
                date_cell = (
                    "&#128197;&nbsp;"
                    "<span style='display:inline-block;min-width:95px;"
                    "color:#969696;font-weight:bold;'>"
                    f"{date_str}"
                    "</span>"
                )

                if icon_url:
                    safe_url = _html.escape(icon_url, quote=True)
                    icon_cell = (
                        f'<img src="{safe_url}" '
                        f'style="height:12px;vertical-align:middle;margin-right:4px;">'
                        f"{display_type}"
                    )
                else:
                    icon_cell = WASTE_ICONS.get(
                        display_type,
                        f"<span style='color:#999;'>{display_type}</span>"
                    )

                lines.append(f"{date_cell}{icon_cell}")

            text = '<br>'.join(lines)

        if self.UNIT_TEXT not in Devices:
            self._create_text_device()

        if self.UNIT_SWITCH not in Devices:
            self._create_switch_device()

        if Devices[self.UNIT_TEXT].sValue != text:
            Devices[self.UNIT_TEXT].Update(nValue=0, sValue=text)

        today_pickup = bool(future and future[0]['date'] == today)
        n_value = 1 if today_pickup else 0
        sv_value = 'On' if today_pickup else 'Off'
        if Devices[self.UNIT_SWITCH].nValue != n_value:
            Devices[self.UNIT_SWITCH].Update(nValue=n_value, sValue=sv_value)


# --------------------------------------------------------------------------------------------------------------------------------------------------------
# Domoticz module-level callbacks
# --------------------------------------------------------------------------------------------------------------------------------------------------------

_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
