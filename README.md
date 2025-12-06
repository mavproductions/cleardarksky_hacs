# ClearDarkSky Forecast for Home Assistant 🌌

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/mavproductions/cleardarksky_hacs.svg)](https://github.com/mavproductions/cleardarksky_hacs/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This custom component integrates astronomy forecast data from [ClearDarkSky.com](https://www.cleardarksky.com/) into Home Assistant, providing specialized sensors essential for hobby astronomers, stargazers, and anyone interested in optimal viewing conditions.

## What's New in v1.3.2

### New Feature
- **Day Moon Visible Sensor**: Binary sensor showing when the moon is visible during daylight hours
  - Combines moon position, illumination, and cloud cover data for accurate visibility prediction
  - Perfect for daytime moon photography planning or avoiding moon glare

### From v1.3.1
- **Fixed "Clear Hours Tonight"**: Was incorrectly showing 22+ hours - now properly counts only hours within tonight's darkness period

### From v1.3.0
- **Discrete Color Matching**: Completely rewritten chart parsing using exact ClearDarkSky color codes with Euclidean distance algorithm
- **New Sensor**: "Current Observing Quality" - Real-time quality based on current cloud cover, transparency, and seeing
- **Renamed Sensor**: "Observing Quality" → "Tonight's Observing Forecast" for clarity

## Features ✨

- **Seeing & Transparency**: Tracks atmospheric seeing (star twinkling/steadiness) and sky transparency (clarity)
- **Cloud Cover**: Provides hourly forecast for cloud coverage with percentage-based ratings
- **Darkness Calculations**: Automatic astronomical twilight and darkness hours tracking
- **Quality Ratings**: Dual quality sensors for current conditions and tonight's forecast
- **Binary Sensors**: Quick "is tonight good for observing?" sensors for automation
- **Visual Chart Display**: Camera entity showing the full ClearDarkSky forecast chart
- **48-Hour Forecast**: Hourly predictions for planning your observing sessions
- **Aurora Viewing Support**: Perfect companion to the [Aurora Integration](https://www.home-assistant.io/integrations/aurora/) for comprehensive aurora visibility forecasting

## Perfect for Aurora Chasers! 🌌✨

This integration pairs **perfectly** with Home Assistant's official [**Aurora Integration**](https://www.home-assistant.io/integrations/aurora/) which uses NOAA Space Weather data to forecast aurora activity.

**Why use both together?**
- **Aurora Integration** → Tells you **IF** aurora will be visible (geomagnetic activity/Kp index)
- **Clear Dark Sky** → Tells you **CAN YOU SEE IT** (cloud cover, transparency, darkness)

### The Perfect Aurora Alert Setup

Combine both integrations for intelligent aurora alerts that only notify when:
1. ✅ Aurora activity is high (NOAA forecast)
2. ✅ Skies are clear (ClearDarkSky)
3. ✅ It's dark enough (astronomical darkness)

See the automation example below!

## Installation ⬇️

### Method 1: HACS (Recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed and set up in your Home Assistant instance
2. In the Home Assistant UI, navigate to **HACS → Integrations**
3. Click the **⋮** menu (three dots) in the top right and select **Custom repositories**
4. Add this repository:
   - **URL**: `https://github.com/mavproductions/cleardarksky_hacs`
   - **Category**: `Integration`
5. Click **Add**, then search for "**Clear Dark Sky**" in HACS
6. Click **Download** and restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from the [releases page](https://github.com/mavproductions/cleardarksky_hacs/releases)
2. Extract the `cleardarksky` folder to your `custom_components` directory
3. Restart Home Assistant


## Configuration ⚙️

The integration is configured entirely via the Home Assistant UI:

1. Go to **Settings → Devices & Services → Integrations**
2. Click the **+ Add Integration** button
3. Search for "**Clear Dark Sky**"
4. Enter your **chart key** from ClearDarkSky.com
   - Visit [ClearDarkSky.com](https://www.cleardarksky.com/)
   - Find your location and note the chart key (e.g., `Torontokey` from `https://www.cleardarksky.com/c/Torontokey.html`)
5. Optionally configure latitude/longitude (defaults to Home Assistant location)

## Available Sensors 🔭

### Numeric Sensors (14 total)

| Sensor | Description | Unit | Example Rating |
|--------|-------------|------|----------------|
| **Clear Hours Tonight** | Number of clear hours during darkness period | hours | - |
| **Darkness Hours** | Total hours of astronomical darkness | hours | - |
| **Astronomical Dusk** | Time when astronomical twilight ends | timestamp | - |
| **Astronomical Dawn** | Time when astronomical twilight begins | timestamp | - |
| **Current Observing Quality** | Real-time quality based on current conditions | - | Excellent / Good / Fair / Poor |
| **Tonight's Observing Forecast** | Forecast quality for tonight's darkness hours | - | Excellent / Good / Fair / Poor |
| **Cloud Cover (Current)** | Current cloud coverage percentage | % | Clear / Mostly Clear / Partly Cloudy / Mostly Cloudy / Overcast |
| **Cloud Cover (Average)** | Average cloud coverage over 48h forecast | % | (same ratings) |
| **Transparency (Current)** | Current atmospheric transparency | % | Excellent / Good / Fair / Poor / Very Poor |
| **Transparency (Average)** | Average transparency over 48h forecast | % | (same ratings) |
| **Seeing (Current)** | Current atmospheric steadiness | % | Excellent / Good / Fair / Poor / Very Poor |
| **Seeing (Average)** | Average seeing over 48h forecast | % | (same ratings) |
| **Darkness (Current)** | Current darkness level | % | Dark / Twilight / Dusk-Dawn / Daylight |

### Binary Sensors (4 total)

| Sensor | Description | On When |
|--------|-------------|---------|
| **Day Moon Visible** | Is the moon visible during daylight? | Daytime + moon above horizon + bright enough + far from sun + clear skies |
| **Clear Sky Tonight** | Is tonight mostly clear? | Clear hours ≥ 50% of darkness hours |
| **Good Observing Conditions** | Are conditions good for observing? | Clear hours ≥ 70% of darkness hours |
| **Astronomical Darkness** | Is it currently astronomically dark? | Current time between dusk and dawn |

### Camera Entity

| Entity | Description | Update Interval |
|--------|-------------|-----------------|
| **Clear Dark Sky Chart** | Displays the full ClearDarkSky forecast chart image | 60 minutes |

## Automation Examples

### 🌌 Aurora Alert (Combines Aurora + ClearDarkSky Integrations)

**The ultimate aurora notification** - only alerts when aurora is active AND you can actually see it!

```yaml
automation:
  - alias: "Aurora Alert: Perfect Viewing Conditions"
    description: "Notify when aurora is visible AND skies are clear"
    trigger:
      # Trigger when aurora visibility turns on
      - platform: state
        entity_id: binary_sensor.aurora_visibility
        to: "on"
    condition:
      # Only notify if ALL conditions are met
      - condition: state
        entity_id: binary_sensor.cleardarksky_astronomical_darkness
        state: "on"
      - condition: numeric_state
        entity_id: sensor.cleardarksky_cloud_cover_current
        below: 30  # Less than 30% clouds
      - condition: numeric_state
        entity_id: sensor.cleardarksky_transparency_current
        above: 60  # Good transparency
    action:
      - service: notify.mobile_app
        data:
          title: "🌌 AURORA ALERT!"
          message: >
            Aurora visible with PERFECT viewing conditions!

            🌠 Aurora Intensity: {{ states('sensor.aurora_intensity') }}
            ☁️ Cloud Cover: {{ states('sensor.cleardarksky_cloud_cover_current') }}%
            👁️ Transparency: {{ state_attr('sensor.cleardarksky_transparency_current', 'rating') }}
            🌑 Clear Hours: {{ states('sensor.cleardarksky_clear_hours_tonight') }}

            Get outside NOW! 📸
          data:
            priority: high
            notification_icon: mdi:weather-night
```

### Notify When Good Observing Conditions

```yaml
automation:
  - alias: "Notify: Good Astronomy Conditions Tonight"
    trigger:
      - platform: state
        entity_id: binary_sensor.cleardarksky_good_observing
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Clear Skies Tonight!"
          message: >
            Great conditions for stargazing!
            Cloud Cover: {{ states('sensor.cleardarksky_cloud_cover_current') }}%
            Transparency: {{ state_attr('sensor.cleardarksky_transparency_current', 'rating') }}
            Clear Hours: {{ states('sensor.cleardarksky_clear_hours_tonight') }}
```

### Turn on Observatory Lights at Astronomical Dusk

```yaml
automation:
  - alias: "Observatory: Dusk Lighting"
    trigger:
      - platform: time
        at: sensor.cleardarksky_astronomical_dusk
    action:
      - service: light.turn_on
        target:
          entity_id: light.observatory_red_lights
```

## Troubleshooting

### Conditions Don't Match Reality

If sensors show poor/cloudy when skies are actually clear:

1. Enable debug logging in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.cleardarksky: debug
   ```

2. Restart Home Assistant and check **Settings → System → Logs**

3. Look for RGB values being sampled from the chart - these should show:
   - **Clear sky**: Dark blue like RGB(10, 30, 150)
   - **Cloudy**: Light/white like RGB(200, 210, 220)

4. If values look wrong, the chart format may have changed - please [open an issue](https://github.com/mavproductions/cleardarksky_hacs/issues)

### Chart Key Not Found

- Verify your chart key is correct by visiting `https://www.cleardarksky.com/c/YOURKEYcsk.gif`
- Chart key should be the part before `csk.gif` or after `/c/` in the URL

### Sensors Not Updating

- Integration updates every 60 minutes
- Force update: **Settings → Devices & Services → Clear Dark Sky → Reload**

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### For Maintainers: Creating a Release

See [RELEASE.md](RELEASE.md) for detailed release instructions.

**Quick release:**
```powershell
# Windows
.\release.ps1 1.2.1
git push origin main --tags

# Linux/Mac/WSL
./release.sh 1.2.1
git push origin main --tags
```

GitHub Actions will automatically create the release and notify HACS.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/mavproductions/cleardarksky_hacs/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/mavproductions/cleardarksky_hacs/issues)
- 📖 **Documentation**: [GitHub Wiki](https://github.com/mavproductions/cleardarksky_hacs/wiki)

## Important Attribution ⚠️

This integration is entirely dependent on the free service provided by [ClearDarkSky.com](https://www.cleardarksky.com/).

**Please support ClearDarkSky:**
- Consider [donating to ClearDarkSky](https://www.cleardarksky.com/csk/donate.html) if you find this integration useful
- The service is provided free by Attilla Danko and relies on community support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Created with 💖 for the Home Assistant Community by [@mavproductions](https://github.com/mavproductions)
