# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
