# Clear Dark Sky for Home Assistant

{% if installed %}
## Changes in v1.3.1

### Fix
- **"Clear Hours Tonight" sensor logic**: Was incorrectly showing 22+ hours
  - Now correctly counts only hours within tonight's darkness period
  - During daytime: Shows full upcoming darkness period
  - During nighttime: Shows remaining hours until dawn
  - Only focuses on current night cycle

### From v1.3.0

### Major Improvements
- **Discrete Color Matching**: Completely rewritten chart parsing using exact ClearDarkSky color palettes
  - Cloud Cover: 11 discrete colors for precise readings
  - Transparency/Seeing: 6 discrete levels matching actual chart values
  - Darkness: 15 discrete levels on magnitude scale
  - Uses Euclidean distance algorithm for accurate color identification

### New Sensor
- **Current Observing Quality**: Real-time quality based on current conditions
  - Combines cloud cover, transparency, and seeing
  - Includes numeric quality score (0-100) in attributes
  - Ignores time of day - purely current conditions

### Other Changes
- **Renamed**: "Observing Quality" → "Tonight's Observing Forecast" (entity ID changed)
- **Removed**: Wind sensors (Wind Current and Wind Average) no longer available

### From v1.2.8

### Critical Fix
- **Fixed integration crash**: Resolved sun calculation error that prevented the integration from loading
- Integration now properly loads and updates chart data

### From v1.2.6

### Critical Bug Fixes
- **Fixed math overflow**: Cloud cover can no longer exceed 100% (was reporting values like 175%)
- **Added value capping**: All calculations now properly limited to 0-100% range
- **Reload support**: Integration can now be reloaded without full Home Assistant restart

### Improvements
- **Enhanced diagnostics**: Logs now show exact pixel coordinates and RGB values
- **Better error detection**: Warnings when values are out of expected range
- **Easier troubleshooting**: INFO level logging without needing debug mode

### From v1.2.0
- **Enhanced Color Mapping**: Completely rewritten chart parsing logic with gradual/continuous color-to-value mapping for more accurate readings
- **Better Clear Sky Detection**: Improved blue saturation algorithm to correctly identify dark blue (clear) vs gray (cloudy) pixels
- **Debug Logging**: Added comprehensive debug logging to help troubleshoot parsing issues
{% endif %}

## About

This integration brings ClearDarkSky astronomy forecasts directly into Home Assistant, providing essential data for stargazers and amateur astronomers.

### 🌌 Perfect Aurora Viewing Companion!

**Pairs perfectly with Home Assistant's [Aurora Integration](https://www.home-assistant.io/integrations/aurora/)!**

- **Aurora Integration** tells you **IF** aurora will be visible (NOAA geomagnetic forecast)
- **Clear Dark Sky** tells you **CAN YOU SEE IT** (cloud cover, transparency, darkness)

Combine both for intelligent aurora alerts that only notify when aurora is active AND skies are clear!

### Features
- **Real-time astronomy forecasts** from ClearDarkSky.com
- **15 sensor entities** tracking cloud cover, transparency, seeing, darkness, and wind conditions
- **3 binary sensors** for quick "is it good for observing?" checks
- **Chart display** via camera entity showing the full ClearDarkSky forecast chart
- **Hourly forecasts** for up to 48 hours ahead
- **Aurora viewing support** when paired with the Aurora integration

### What You Get
- Cloud cover percentage (current and average)
- Atmospheric transparency ratings
- Seeing conditions (for planetary/lunar observation)
- Darkness hours and astronomical twilight times
- Wind conditions
- Clear hours count for planning observing sessions

Perfect for:
- **Aurora chasing** (when combined with Aurora integration)
- Planning stargazing sessions
- Astrophotography scheduling
- Telescope setup decisions
- Observatory automation

Data is sourced from ClearDarkSky.com, a trusted resource for astronomical weather forecasting.
