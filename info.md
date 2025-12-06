# Clear Dark Sky for Home Assistant

{% if installed %}
## Changes in v1.2.0

### Improvements
- **Enhanced Color Mapping**: Completely rewritten chart parsing logic with gradual/continuous color-to-value mapping for more accurate readings
- **Better Clear Sky Detection**: Improved blue saturation algorithm to correctly identify dark blue (clear) vs gray (cloudy) pixels
- **Debug Logging**: Added comprehensive debug logging to help troubleshoot parsing issues

### Bug Fixes
- Fixed issue where clear skies were incorrectly reported as poor/cloudy conditions
- Improved transparency and seeing calculations for better accuracy
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
