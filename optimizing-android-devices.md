---
name: optimizing-android-devices
description: Use when diagnosing sluggishness, stutter, high memory pressure, thermal throttling, battery drain, bloatware, or privacy vulnerabilities on an Android mobile device connected via ADB.
---

# Optimizing Android Devices (Diagnostics, Performance, Debloating & Privacy)

## Overview

A complete operational playbook for an AI agent to diagnose, tune, debloat, and secure any Android mobile device connected over ADB. It addresses real hardware bottlenecks: swapping virtual RAM to flash storage, thermal downclocking, background profile leaks, uncompiled JIT bytecode, telemetry daemons, and unencrypted radio/DNS vectors.

**Primary Principle:** Evidence before modification. Always audit baseline metrics (RAM, CPU frequency, active profiles, thermal throttle state) before applying changes, and verify measurable impact after each phase.

**Fallback Rule:** If any command, setting key, or package name fails or differs across Android versions (Android 11–16) or OEM skins (Samsung One UI, Google Pixel, Xiaomi HyperOS, OnePlus OxygenOS, Motorola, etc.), **do not guess**. You MUST search the web (`search_web`) for device-specific documentation, XDA Developers forum threads, Reddit r/Android / r/GalaxyS / r/GooglePixel, or GitHub repositories for verified keys.

---

## Quick Reference: Core Commands

| Category | Operation | Command |
| :--- | :--- | :--- |
| **Auth** | Check connection & device | `adb devices -l` |
| **Diagnostics** | Memory & Swap / zRAM | `adb shell dumpsys meminfo` |
| **Diagnostics** | CPU frequency limits | `adb shell cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq` |
| **Diagnostics** | Battery, temp & health | `adb shell dumpsys battery` |
| **Diagnostics** | Active Android users/profiles | `adb shell pm list users` |
| **Diagnostics** | Display refresh mode | `adb shell settings get system peak_refresh_rate` |
| **Diagnostics** | Frame rendering jank | `adb shell dumpsys gfxinfo <package_name>` |
| **Performance** | Disable Virtual RAM / Swap | `adb shell settings put global ram_expand_size 0` *(Reboot required)* |
| **Performance** | Set 0.5x animation scales | `adb shell "settings put global window_animation_scale 0.5 && settings put global transition_animation_scale 0.5 && settings put global animator_duration_scale 0.5"` |
| **Performance** | Dev Options off (Bypass bans) | `adb shell settings put global development_settings_enabled 0` |
| **Performance** | AOT native compile app | `adb shell cmd package compile -m speed-profile <package_name>` |
| **Performance** | Kernel Cached Apps Freezer | `adb shell settings put global cached_apps_freezer enabled` |
| **Debloat** | Safe user uninstall | `adb shell pm uninstall -k --user 0 <package_name>` |
| **Debloat** | Reinstall debloated app | `adb shell cmd package install-existing <package_name>` |
| **Privacy** | Encrypted Private DNS (AdGuard) | `adb shell "settings put global private_dns_mode hostname && settings put global private_dns_specifier dns.adguard.com"` |
| **Privacy** | Encrypted Private DNS (Cloudflare)| `adb shell "settings put global private_dns_mode hostname && settings put global private_dns_specifier one.one.one.one"` |
| **Privacy** | Alert on clipboard read | `adb shell settings put secure clipboard_show_access_notifications 1` |
| **Privacy** | Hide sensitive lockscreen OTPs | `adb shell settings put secure lock_screen_allow_private_notifications 0` |
| **Security** | Disable 2G radio downgrade | `adb shell settings put global allow_2g 0` |
| **Security** | Enable Lockdown in power menu | `adb shell settings put secure lockdown_in_power_menu 1` |

---

## Phase 1: Device Connection & Environment Setup

### 1.1 Verify USB Debugging & Device State
```bash
adb devices -l
```
* If device is `unauthorized`: Instruct the user to check their phone screen and tap **"Always allow from this computer"**.
* If device is `offline`: Run `adb kill-server && adb start-server`.
* **Sandbox Constraint:** ADB communicates over loopback `tcp:5037`. In agent environments with network sandboxing, ADB commands require bypassing isolation (`BypassSandbox: true`).

### 1.2 Inspect Hardware & System Profiles
```bash
adb shell "
echo '=== DEVICE IDENTITY ==='
getprop ro.product.model
getprop ro.product.brand
getprop ro.board.platform
getprop ro.build.version.release
getprop ro.build.version.security_patch

echo '=== ACTIVE USER PROFILES ==='
pm list users
"
```
> [!IMPORTANT]
> **Check for Multi-Profile Memory Leaks:** If `pm list users` shows secondary profiles (e.g. `User 95` for Dual Messenger / Parallel Apps, or `User 150` for Secure Folder / Work Profile), each profile runs duplicate background instances of Google Play Services, Accounts, and Media Providers, often consuming **1.5 GB+ of physical RAM**.

---

## Phase 2: Comprehensive Diagnostics Protocol

Run an end-to-end diagnostic pass before proposing or applying fixes:

```bash
adb shell "
echo '=== 1. MEMORY & VIRTUAL SWAP ==='
dumpsys meminfo | head -n 25

echo '=== 2. BATTERY & THERMALS ==='
dumpsys battery | grep -E 'level|temperature|status|health'

echo '=== 3. CPU THROTTLING & POWER SAVER ==='
settings get global low_power
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null || echo 'CPU freq restricted'

echo '=== 4. REFRESH RATE & DISPLAY ==='
settings get system min_refresh_rate 2>/dev/null
settings get system peak_refresh_rate 2>/dev/null

echo '=== 5. STORAGE & CACHE ==='
df -h /data
"
```

### Diagnosing Root Causes from Telemetry:
1. **High Swap Usage (>2.5 GB swap with active zRAM compression):**
   * *Root Cause:* "RAM Plus" / "Dynamic RAM" / "Virtual Memory Extension" is enabled.
   * *Impact:* Physical RAM is wasted on zRAM compression tables, forcing the CPU into constant memory compression/decompression cycles and massive page faults in `systemui`.
2. **CPU Clock Capped at ~70% & Display Locked at 60 Hz:**
   * *Root Cause:* Android Power Saving mode is active (`low_power=1`).
3. **High Janky Frames (>15% in launcher):**
   * Check frame stats: `adb shell dumpsys gfxinfo <launcher_package>`. If median frame time > 16.6ms (60Hz) or > 8.3ms (120Hz), the system is dropping frames due to memory thrashing or CPU downclocking.

---

## Phase 3: Root-Cause Performance Fixes

### 3.1 Disable Virtual RAM (RAM Plus / Memory Extension)
Virtual RAM uses slow internal UFS flash storage as secondary swap. On modern Android devices with 6 GB–12 GB of physical RAM, it degrades performance.

1. **Check current size:**
   ```bash
   adb shell settings get global ram_expand_size
   ```
2. **Disable it (Set to 0):**
   ```bash
   adb shell settings put global ram_expand_size 0
   ```
3. **Reboot the device:** Instruct the user to reboot the phone for the kernel swap allocation table to be completely dismantled.
4. **Post-Reboot Verification:** Confirm available physical RAM increases by 1.0 GB–1.5 GB and zRAM overhead decreases.

### 3.2 Animation Scaling with Corporate/Banking Compliance
Slow animations make responsive hardware feel sluggish.

1. **Set animation scales to 0.5x:**
   ```bash
   adb shell "settings put global window_animation_scale 0.5 && settings put global transition_animation_scale 0.5 && settings put global animator_duration_scale 0.5"
   ```
2. **Turn Developer Options OFF to prevent banking/MDM app detection:**
   ```bash
   adb shell settings put global development_settings_enabled 0
   ```
   *The 0.5x values remain active in the global settings table even when Developer Options is turned off.*

### 3.3 Batch AOT Native App Compilation (`dexopt`)
Android compiles apps using a hybrid JIT (Just-In-Time) and cloud-profile model. Over time or after OS updates, apps drop back to interpreted code, causing stutter on launch and scrolling.

Run an automated AOT pass to compile third-party apps into native machine code:

```python
import subprocess

# Get 3rd party packages
res = subprocess.check_output(["adb", "shell", "pm", "list", "packages", "-3", "--user", "0"]).decode()
packages = [line.replace("package:", "").strip() for line in res.splitlines() if line.strip()]

print(f"Compiling {len(packages)} packages to speed-profile native machine code...")
for idx, pkg in enumerate(packages, 1):
    cmd = ["adb", "shell", f"cmd package compile -m speed-profile {pkg}"]
    out = subprocess.check_output(cmd).decode().strip()
    print(f"[{idx}/{len(packages)}] {pkg} -> {out}")
```
*For high-priority frequently used apps (e.g. Chrome, WhatsApp, Instagram), you can use `-m speed` for full ahead-of-time compilation.*

### 3.4 Enable Kernel "Cached Apps Freezer"
Freezes the CPU execution of minimized/cached apps in RAM using cgroup v2, eliminating rogue background battery drain without terminating apps:
```bash
adb shell settings put global cached_apps_freezer enabled
```

### 3.5 Reclaiming Multi-Profile Memory (Secure Folder / Work Profile)
If secondary profiles (`User 150` / `User 95`) are running in the background:
* Instruct the user to open Secure Folder → Tap **3 dots** → Tap **"Lock and exit"**.
* This terminates the duplicate user sandbox and unmounts the encrypted volume, immediately freeing **~1.5 GB of RAM**.

---

## Phase 4: Non-Root System Debloating

### 4.1 Safe Debloat Pattern
Never delete system APKs directly. Use user-profile uninstallation:
```bash
adb shell pm uninstall -k --user 0 <package_name>
```
* **Why it's safe:** The package is uninstalled for the primary user (frees RAM, stops background services, removes icon), but the original APK remains on the read-only system partition.
* **Instant Restoration:**
  ```bash
  adb shell cmd package install-existing <package_name>
  ```

### 4.2 Universal Bloatware Catalog

#### Meta / Facebook Telemetry & Silent Updaters
*Even with these removed, Instagram and WhatsApp function 100% normally.*
* `com.facebook.services` (Background analytics and tracking)
* `com.facebook.appmanager` (Silent app update daemon)
* `com.facebook.system` (System installer bridge)

#### OEM Tracking, Beacons & Shopping Ads
* `com.samsung.android.ipsgeofence` (Samsung Visit In - scans retail beacons for mall ads)
* `com.samsung.android.rubin.app` (Samsung Customization Service - tracks habits for ads, ~90MB RAM)
* `com.samsung.android.kidsinstaller` (Samsung Kids mode container)

#### Duplicate Voice Assistants & Unused Engines
* `com.samsung.android.bixby.wakeup` (Always-listening voice trigger)
* `com.samsung.android.bixby.agent` (Bixby Voice main)
* `com.samsung.android.bixby.ondevice.enus` (Offline voice model, ~335MB storage)
* `com.samsung.android.bixbyvision.framework` (Camera object recognition)
*(Keep `com.samsung.android.app.routines` safe for Modes & Routines!)*

#### Redundant Stock Apps
* `com.google.android.youtube` (Remove if user has YouTube ReVanced installed)
* `com.android.chrome` & `com.sec.android.app.chromecustomizations` (Safe to remove if user uses Firefox/Brave; in-app browsing continues working via Android System WebView)
* `com.samsung.android.aremoji` & `aremojieditor` (3D avatar stickers)

---

## Phase 5: Privacy & Network Security Hardening

### 5.1 Encrypted Private DNS Configuration
Enables DNS-over-TLS (DoT) system-wide, blocking ISP tracking and in-app banner ads:

* **For Ad Blocking + Encryption (AdGuard):**
  ```bash
  adb shell "settings put global private_dns_mode hostname && settings put global private_dns_specifier dns.adguard.com"
  ```
* **For Maximum Raw Speed + Encryption (Cloudflare 1.1.1.1):**
  ```bash
  adb shell "settings put global private_dns_mode hostname && settings put global private_dns_specifier one.one.one.one"
  ```
* **Verification Test:**
  ```bash
  # Test ad sinkhole (should resolve to 127.0.0.1 or 0.0.0.0)
  adb shell ping -c 1 pagead2.googlesyndication.com
  # Test TLS Port 853 connection
  adb shell "netstat -tupn 2>/dev/null | grep ':853'"
  ```

### 5.2 Cellular & Telemetry Hardening
1. **Disable 2G Radio Downgrade:**
   * Prevents fake cell towers (IMSI-catchers) from forcing phones onto unencrypted 2G to intercept SMS OTPs:
     ```bash
     adb shell settings put global allow_2g 0
     ```
2. **Clipboard Access Alerts:**
   * Alerts whenever any background or foreground app reads copied passwords or bank details:
     ```bash
     adb shell settings put secure clipboard_show_access_notifications 1
     ```
3. **Lockscreen Sensitive Content Masking:**
   * Masks incoming WhatsApp and SMS OTP message text on the locked display:
     ```bash
     adb shell settings put secure lock_screen_allow_private_notifications 0
     ```
4. **Emergency Lockdown Mode:**
   * Adds instant biometric-kill switch to the power menu:
     ```bash
     adb shell settings put secure lockdown_in_power_menu 1
     ```

---

## Phase 6: Sideloading & Cryptographic Verification Protocol

When official stores region-lock legitimate system tools (e.g. Samsung Thermal Guardian or Good Guardians on Indian/regional CSCs), follow this verification protocol before installing:

### 6.1 Download Strategy
Due to Cloudflare Turnstile anti-bot checks blocking terminal scraping on APKMirror/Uptodown:
* Push the direct download page to the phone's browser via ADB:
  ```bash
  adb shell am start -a android.intent.action.VIEW -d "<apkmirror_download_url>"
  ```
* Once downloaded, pull the APK from `/sdcard/Download/` to the local terminal:
  ```bash
  adb pull "/sdcard/Download/<apk_file>.apk" ./scratch/target.apk
  ```

### 6.2 Cryptographic Signature & Certificate Verification
Extract the APK's X.509 certificate and verify its SHA-256 fingerprint against an authentic OEM package already installed on the phone:

```bash
# 1. Extract and inspect certificate using OpenSSL
python3 -c "
import zipfile
with zipfile.ZipFile('./scratch/target.apk') as z:
    with open('./scratch/CERT.RSA', 'wb') as f:
        f.write(z.read('META-INF/CERT.RSA'))
"
openssl pkcs7 -inform DER -in ./scratch/CERT.RSA -print_certs | openssl x509 -fingerprint -sha256 -noout

# 2. Compare against installed OEM app signature on device
adb shell dumpsys package <known_oem_package> | grep -A 2 -i "signatures"
```
* **Pass Condition:** The SHA-256 fingerprint of the downloaded APK matches the device's installed OEM signature bit-for-bit (e.g. Samsung's master key `34:DF:0E:7A:...`).
* **Install only after verification passes:**
  ```bash
  adb install -r ./scratch/target.apk
  ```

---

## Phase 7: Hardware Testing & Secret Maintenance Dialers

Samsung and other OEMs maintain hardware diagnostics and crash-dump purgers in engineering dialer codes:

| Dialer Code | Name | Function |
| :--- | :--- | :--- |
| `*#9900#` | **SysDump** | Tap **"Delete dumpstate/logcat"** to flush old crash dumps and ANR logs from `/data/log/`. |
| `*#0*#` | **Hardware Test** | Tests OLED subpixels (Red/Green/Blue), digitizer touch matrix, stereo speakers, and sensor calibration. |
| `*#0011#` | **ServiceMode** | Displays active 5G NR and LTE carrier aggregation bands, bandwidth, and RSRP/SINR radio quality. |
| `*#0228#` | **Battery Status** | ADC voltage readout, fuel gauge calibration, and real-time battery resistance telemetry. |

---

## Phase 8: Autonomous Web Research & Fallback Protocol

> [!CAUTION]
> **MANDATORY FALLBACK RULE:** Android versions, vendor kernel trees, and OEM skins differ significantly.
> * If a setting command returns `Error` or `null`
> * If a package name is not found on the device
> * If a feature behaves unexpectedly after toggling

**YOU MUST NOT GUESS.** Take the following actions immediately:
1. **Extract Device Codenames & Platform:**
   ```bash
   adb shell "getprop ro.product.name; getprop ro.board.platform; getprop ro.build.version.release"
   ```
2. **Search Public Technical Forums:**
   Use the `search_web` tool with targeted queries:
   * `"site:xda-developers.com [Device Model] debloat list [Android Version]"`
   * `"site:reddit.com/r/Android [Package Name] safe to remove"`
   * `"site:github.com [Feature Name] adb settings put"`
3. **Verify OEM Specific Equivalents:**
   * **Samsung One UI:** Uses `sec_`, `rampart_`, `sem_` prefixes for proprietary settings.
   * **Xiaomi HyperOS / MIUI:** Requires "Disable MIUI optimization" or `setprop persist.sys.miui_optimization 0` for certain package operations.
   * **OnePlus / ColorOS:** Uses `oppo_` or `oplus_` custom settings tables.
   * **Google Pixel:** Pure AOSP keys under `global` and `secure`.

---

## Common Rationalizations & Red Flags

| Rationalization | Reality | Correct Action |
| :--- | :--- | :--- |
| *"RAM Plus gives more memory, so it must make multitasking better."* | Flash storage is 100x slower than LPDDR5 RAM; swap causes major page faults and launcher stutter. | Always check `dumpsys meminfo` swap allocation and disable it. |
| *"Developer Options must stay enabled for 0.5x animations."* | Banking, enterprise MDM, and DRM apps block devices with Developer Options enabled. | Set animation scales in `global` table, then toggle `development_settings_enabled 0`. |
| *"I can just guess the debloat package name."* | Uninstalling core telecom, IMS, or Knox security packages can trigger bootloops. | Query `pm list packages` first; research unknown packages on XDA/web before removing. |
| *"Cloudflare 1.1.1.1 will block all mobile ads."* | Standard Cloudflare only provides DNS resolution; it does not filter ads. | Use `dns.adguard.com` for ad blocking, or `one.one.one.one` for raw unblocked speed. |
