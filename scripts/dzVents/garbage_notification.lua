-- GarbageCalendar Notification Script (dzVents)
--
-- Leest de eerste regel van het GarbageCalendar text-device en toont
-- "Vandaag <soort>" of "Morgen <soort>" in het meldingsdevice (NOTIFY_DEVICE_IDX).
--
-- Regels:
--   - "Morgen <soort>"  →  alleen zichtbaar vanaf 16:00 de dag vóór de ophaaldag.
--   - "Vandaag <soort>" →  zichtbaar van middernacht t/m 13:59 op de ophaaldag.
--   - In alle andere situaties wordt het device leeggemaakt.
--
-- Installatie:
--   1. Stel GARBAGE_DEVICE_IDX in op de idx van uw GarbageCalendar text-device.
--   2. Maak in Domoticz een Text-device aan met idx 2222 (of pas NOTIFY_DEVICE_IDX aan).
--   3. Kopieer dit bestand naar <domoticz>/scripts/dzVents/scripts/
--
-- Let op: het datumformaat van het GarbageCalendar-device moet 'wd dd mmm' zijn (de standaard).

local GARBAGE_DEVICE_IDX = 123   -- *** Pas aan naar de idx van uw GarbageCalendar device ***
local NOTIFY_DEVICE_IDX  = 2222

local DUTCH_MONTHS = {
    jan=1, feb=2, mrt=3, apr=4, mei=5, jun=6,
    jul=7, aug=8, sep=9, okt=10, nov=11, dec=12,
}

return {
    on = {
        devices = { GARBAGE_DEVICE_IDX },
        timer = {
            'at 00:01',  -- net na middernacht: zet "Vandaag" als ophaal vandaag is
            'at 14:00',  -- wis "Vandaag"-melding op de ophaaldag
            'at 16:00',  -- zet "Morgen"-melding als ophaal morgen is
        },
    },

    execute = function(domoticz, item)

        -- ── Haal het GarbageCalendar-device op ───────────────────────────────
        local garbageDevice = domoticz.devices(GARBAGE_DEVICE_IDX)
        if not garbageDevice then
            domoticz.log('GarbageCalendar notification: brondevice niet gevonden (idx=' ..
                GARBAGE_DEVICE_IDX .. ')', domoticz.LOG_ERROR)
            return
        end

        local sValue = garbageDevice.text or ''

        -- ── Extraheer de eerste regel ─────────────────────────────────────────
        -- De plugin schrijft regels gescheiden door '\n' (of '<br>' bij iconen).
        local firstLine = sValue:match('([^\n]+)') or ''

        -- Verwijder eventuele HTML-tags (bijv. <img ...> voor iconen)
        firstLine = firstLine:gsub('<[^>]+>', '')

        -- Trim witruimte
        firstLine = firstLine:match('^%s*(.-)%s*$')

        -- ── Parseer "wd DD mmm: SOORT"  bijv. "ma 12 apr: GFT" ───────────────
        local dateStr, gtype = firstLine:match('^(.-)%s*:%s*(.-)%s*$')
        if not dateStr or not gtype or gtype == '' then
            domoticz.devices(NOTIFY_DEVICE_IDX).updateText('')
            return
        end

        -- Datumgedeelte "wd DD mmm": weekdag-prefix + dag + maand
        local day, monthStr = dateStr:match('%a+%s+(%d+)%s+(%a+)')
        if not day or not monthStr then
            domoticz.devices(NOTIFY_DEVICE_IDX).updateText('')
            return
        end

        local month = DUTCH_MONTHS[monthStr:lower()]
        if not month then
            domoticz.devices(NOTIFY_DEVICE_IDX).updateText('')
            return
        end

        day = tonumber(day)

        -- ── Bereken epoch-tijden voor vandaag, morgen en de ophaaldag ─────────
        local nowT = os.date('*t')

        local function startOfDay(y, m, d)
            return os.time({ year=y, month=m, day=d, hour=0, min=0, sec=0 })
        end

        local todayEpoch    = startOfDay(nowT.year, nowT.month, nowT.day)
        local tomorrowEpoch = todayEpoch + 86400
        local pickupEpoch   = startOfDay(nowT.year, month, day)

        -- Schuif naar volgend jaar als de datum al gepasseerd is
        if pickupEpoch < todayEpoch then
            pickupEpoch = startOfDay(nowT.year + 1, month, day)
        end

        -- ── Bepaal het bericht op basis van tijd en ophaaldag ─────────────────
        local currentMinutes = nowT.hour * 60 + nowT.min
        local message = ''

        if pickupEpoch == todayEpoch then
            -- Ophaal vandaag: toon "Vandaag <soort>" tot 14:00
            if currentMinutes < 14 * 60 then
                message = 'Vandaag ' .. gtype
            end
        elseif pickupEpoch == tomorrowEpoch then
            -- Ophaal morgen: toon "Morgen <soort>" vanaf 16:00
            if currentMinutes >= 16 * 60 then
                message = 'Morgen ' .. gtype
            end
        end

        -- ── Werk het meldingsdevice bij (alleen bij wijziging) ────────────────
        local notifyDevice = domoticz.devices(NOTIFY_DEVICE_IDX)
        if notifyDevice.text ~= message then
            notifyDevice.updateText(message)
        end

    end,
}
