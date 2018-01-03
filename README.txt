PagerDuty Addon
========================
Provides modular inputs & framework to ingest data from PagerDuty APIs for reporting or automation.

APIs supported:
- Log Entries (https://v2.developer.pagerduty.com/v2/page/api-reference#!/Log_Entries/get_log_entries)
- Incidents (https://v2.developer.pagerduty.com/v2/page/api-reference#!/Incidents/get_incidents)

## Release Notes:

v1.0.1
- Fixed bug in incidents collection logic not removed from development testing.
- Fixed bug in log entries collection logic when retrieving paginated responses.
- Updated input UI defaults not populating as expected & set default pagination to 25 (vs. 10).
- Enabled kvstore (collection) replication by default.
- Set default index in inputs.conf.
- Updated sourcetypes to index as JSON and removed KV_MODE causing duplicate values in UI (props.conf).
- Added lookup definition for retrieving input checkpointers (transforms.conf). 

v1.0.0
- Initial release. Documentation will be included in future releases.

## Submit issues or requests via Github:
TA-PagerDuty: https://github.com/pentestfail/TA-PagerDuty