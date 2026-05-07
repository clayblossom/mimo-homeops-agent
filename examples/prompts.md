# Example Prompts

## Sleep Mode
```
Prepare my home for sleep mode, save energy, but keep the bedroom comfortable.
```
Expected: Turn off non-bedroom lights, AC to 25°C, purifier sleep, curtains close.

## Indonesian Commands
```
Matikan semua lampu kecuali ruang kerja.
```
Expected: All lights off except Study Room.

```
Kalau kamar panas dan ada orang, nyalakan AC 25°C eco dan purifier sleep mode.
```
Expected: Check sensors, activate AC and purifier in rooms with motion + high temp.

```
Hemat energi, matikan yang tidak perlu.
```
Expected: Turn off unused plugs, raise AC temps, eco modes.

## Status Queries
```
Apa status rumah sekarang?
```
Expected: Full home summary with active devices and sensor alerts.

```
Ada kebocoran atau masalah?
```
Expected: Check incident sensors, report any anomalies.

## Automation Building
```
Buat automation supaya kamar nyaman saat malam.
```
Expected: IF time > 22:00 AND bedroom_motion AND bedroom_temp > 27 THEN AC 25°C + purifier sleep.

## Energy Reports
```
Buat laporan energi hari ini.
```
Expected: Active devices, comfort score, waste alerts, savings summary.
