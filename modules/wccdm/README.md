python3 app/station_metadata/station_metadata/utils/initialise_db.py ; python3 app/station_metadata/station_metadata/utils/cache_code_tables.py ; python3 app/wccdm/wccdm/utils/initialise_wccdm.py

curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/A/%23&target=AWS_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/I/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/M/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/N/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/S/%23&target=marine_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/B/%23&target=buoy_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/R/%23&target=sea_surface_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/T/%23&target=sea_surface_temperature_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/W/%23&target=wave_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/I/%23&target=sea_ice"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/%2B/data/core/weather/surface-based-observations/synop&target=wis2_synop"
curl "http://subscription_manager:5001/wis2/subscriptions/add?topic=cache/a/wis2/%2B/%2B/data/core/weather/surface-based-observations/synop&target=wis2_synop"


curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/A/%23&target=AWS_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/I/%23&target=synop_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/M/%23&target=synop_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/N/%23&target=synop_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/S/%23&target=marine_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/B/%23&target=buoy_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/R/%23&target=sea_surface_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/T/%23&target=sea_surface_temperature_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/W/%23&target=wave_reports"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/I/%23&target=sea_ice"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/%2B/data/core/weather/surface-based-observations/synop&target=wis2_synop"
curl "http://localhost:5002/wis2/subscriptions/add?topic=cache/a/wis2/%2B/%2B/data/core/weather/surface-based-observations/synop&target=wis2_synop"

curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/A/%23&target=AWS_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/I/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/M/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/N/%23&target=synop_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/S/S/%23&target=marine_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/B/%23&target=buoy_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/R/%23&target=sea_surface_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/T/%23&target=sea_surface_temperature_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/W/%23&target=wave_reports"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/de-dwd-gts-to-wis2/data/core/I/O/I/%23&target=sea_ice"
curl "http://subscription_manager:5001/wis2/subscriptions/delete?topic=cache/a/wis2/%2B/data/core/weather/surface-based-observations/synop&target=wis2_synop"



SELECT pg_reload_conf();