"""Constants for the Clear Dark Sky integration."""

DOMAIN = "cleardarksky"

# Configuration
CONF_CHART_KEY = "chart_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

# Update interval
UPDATE_INTERVAL_MINUTES = 60

# Chart parameters - based on Clear Dark Sky image structure
FORECAST_HOURS = 48  # Clear Dark Sky provides ~48 hours of hourly forecasts

# Condition thresholds
CLOUD_CLEAR_THRESHOLD = 25  # Less than 25% cloud cover is "clear"
TRANSPARENCY_GOOD_THRESHOLD = 3  # Transparency levels (lower is better, scale 1-5)
SEEING_GOOD_THRESHOLD = 3  # Seeing levels (lower is better, scale 1-5)

# Chart URL template
CHART_URL_TEMPLATE = "https://www.cleardarksky.com/c/{chart_key}csk.gif"
CHART_PAGE_TEMPLATE = "https://www.cleardarksky.com/c/{chart_key}key.html"
