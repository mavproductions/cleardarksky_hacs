# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2025-12-06

### Fixed
- **Critical**: Fixed "Clear Hours Tonight" calculation showing incorrect values (was showing 22+ hours)
  - Now correctly counts only hours within tonight's darkness period (astronomical dusk → dawn)
  - During daytime: Counts full upcoming darkness period
  - During nighttime: Counts only remaining hours until dawn
  - Only focuses on current night cycle, not future nights
  - Added helpful debug logging showing exact counting window

### Technical
- Added `_calculate_clear_hours_tonight()` method that uses sun data to determine darkness window
- Moved clear hours calculation from chart parsing to after sun data is available
- Enhanced logging shows whether counting "remaining hours" or "full darkness period"

## [1.3.0] - 2025-12-06

### Added
- **Discrete color matching**: Chart parsing now uses exact ClearDarkSky color palettes with Euclidean distance matching
  - Cloud Cover: 11 discrete colors (0% to 100% in 10% increments)
  - Transparency: 6 discrete levels (Too cloudy to forecast, Poor, Below average, Average, Above average, Excellent)
  - Seeing: 6 discrete levels (Too cloudy to forecast, Bad 1/5, Poor 2/5, Average 3/5, Good 4/5, Excellent 5/5)
  - Darkness: 15 discrete levels (magnitude scale from -4 daylight to 6.5 darkest)
- **New sensor**: "Current Observing Quality" - Real-time quality based on current cloud cover, transparency, and seeing
  - Provides numeric quality score (0-100) in attributes
  - Ignores time of day/darkness - purely current conditions
  - Quality ratings: Excellent (80+), Good (60-79), Fair (40-59), Poor (<40)

### Changed
- **BREAKING**: Renamed "Observing Quality" sensor to "Tonight's Observing Forecast" for clarity
  - Entity ID changed from `observing_quality` to `observing_quality_tonight`
  - Same forecast-based logic (clear hours vs darkness hours)
  - Icon changed to `mdi:weather-night` to indicate forecast nature
- **Major accuracy improvement**: Replaced continuous gradient color calculations with discrete color palette matching
  - Now matches ClearDarkSky's actual discrete color system instead of interpolating
  - Uses RGB color distance algorithm for precise color identification
  - Significantly more accurate readings matching actual chart colors

### Removed
- **BREAKING**: Removed wind sensors per user request
  - Removed "Wind (Current)" sensor
  - Removed "Wind (Average Forecast)" sensor
  - Wind data no longer calculated or stored
  - Sensor count reduced from 15 to 14 regular sensors

### Technical
- Color matching uses Euclidean distance in RGB space to find nearest palette color
- All ClearDarkSky discrete color values now defined as constants for maintainability
- Chart parsing code simplified with removal of complex gradient calculations

## [1.2.8] - 2025-12-06

### Fixed
- **Critical**: Fixed sun data calculation crash that prevented integration from loading
  - Changed from deprecated `get_astral_location()` to `sun.get_astral_event_next()`
  - Fixed "'tuple' object has no attribute 'sunset'" error
  - Integration now properly loads and updates
  - Added better error handling and logging for sun calculations

## [1.2.6] - 2025-12-06

### Fixed
- **Critical**: Fixed math overflow in cloud cover calculation (reported 175% on clear days)
- **Critical**: Fixed math overflow in transparency calculation (reported 120% during nighttime)
- **Critical**: Fixed math overflow in seeing calculation (same issue as transparency)
- **Critical**: All condition values now properly capped at 0-100% range with min/max guards
- Added `async_reload_entry` to support integration reloading without full HA restart

### Added
- Enhanced debug logging with exact pixel positions (X, Y coordinates)
- Warning messages when calculated values are out of valid range
- Brightness values shown in logs for easier troubleshooting
- INFO level logging for easier diagnosis without debug mode

### Changed
- Improved error detection and reporting for chart parsing issues

## [1.2.0] - 2025-12-06

### Added
- Comprehensive debug logging for RGB color sampling and condition calculations
- Summary logging of current conditions after each chart update
- Detailed logging of first 3 hours for troubleshooting

### Changed
- **Major improvement**: Completely rewritten color-to-value mapping algorithm
  - Now uses blue saturation (`b / (r + g + b)`) instead of simple blue dominance
  - Gradual/continuous transitions instead of discrete threshold jumps
  - More accurate detection of dark blue (clear) vs white/gray (cloudy) pixels
- Cloud cover calculation now uses combined brightness and blue saturation
- Transparency and seeing calculations improved with better color detection
- All condition mappings now use continuous gradients for smoother, more accurate readings

### Fixed
- Fixed issue where clear dark blue skies were incorrectly interpreted as cloudy/poor conditions
- Improved accuracy of cloud cover percentage matching actual sky conditions
- Better differentiation between excellent and poor transparency/seeing conditions

## [1.1.0] - Previous Release

### Added
- Initial support for 15 sensor entities
- 3 binary sensors for observing conditions
- Camera entity displaying ClearDarkSky chart
- Configurable chart key and location
- Automatic sun/darkness calculations

### Features
- Cloud cover (current and average)
- Transparency (current and average)
- Seeing (current and average)
- Darkness hours and twilight times
- Wind conditions
- Clear hours counting
- Observing quality rating

## [1.0.0] - Initial Release

### Added
- Basic ClearDarkSky chart parsing
- Integration with Home Assistant config flow
- Core sensor platform
- Chart image fetching and display
