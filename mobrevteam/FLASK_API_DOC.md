# Flask API Documentaion

## Endpoints:

### 1. '/frontend_campaigns'

**Methods:**

a. **'GET'** _(READ)_ [FrontendCampaign]
* headers: {}
* input_data_type: None
* input: {}
* ouput_data_type: json
* success_output: **{"campaigns": [{"id":*(INTEGER)*, "name":*(STRING)*, "all_day_notification": *(BOOLEAN)*, "from_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "to_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "time_zone": *(STRING(UTC +/- INTEGER))*, "locations": [ {"id":*(INTEGER)*, "name":*(BOOLEAN)*, "checked": *(BOOLEAN)*}], "status": *(INTEGER)* }], "locations": [ {"id":*(INTEGER)*, "name":*(STRING)*, "checked": *(BOOLEAN)*}], "status": *(INTEGER)*}**
* falure_outputs: **[
	{"failure": "retreiving campaigns", "error": *error_message*, "status": 404 }
	{"failure": "retreiving geos", "error": *error_message*, "status": 404 }
	]**

b. **'PUT'** _(DELETE)_ [FrontendCampaign]
* headers: {}
* input_data_type: json
* input: **{"delete_id": *(INTEGER)*}**
* ouput_data_type: json
* success_output: **{"success": "deleteing campaign id *(INTEGER)*", "status": 200}**
* falure_outputs: **[{ "failure": "deleting campaign (id:*(INTEGER)*)", "error":  *error_message*, "status": 404 }]**
*notes: *the input "delete_id" is the id wher $rootScope.campaigns[delete_id] is the campaign you wish to delete*

c. **'POST'** _(CREATE/UPDATE)_ [FrontendCampaign]
* headers: **{'Custom-Status': 'save_campaign'}**
* input_data_type: json
* input: **{"id":*(INTEGER)*, "name":*(STRING)*, "all_day_notification": *(BOOLEAN)*, "from_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "to_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "time_zone": *(STRING(UTC +/- INTEGER))*, "locations": [ {"id":*(INTEGER)*, "name":*(STRING)*, "checked": *(BOOLEAN)*}], "status": *(BOOLEAN)* }**
* ouput_data_type: json
* success_output: **{"success": "saving campaign id *(INTEGER)*', "status": 200}**
* falure_outputs: **[{ "failure": "saving campaign (id:*(INTEGER)*)", "error": " *error_message*, "status": 404 }]**
*notes: *the input is one of the $rootScope.campaigns*

d. **'POST'** _(UPDATE)_ [FrontendCampaign.status]
* headers: **{"Custom-Status": "update_status"}**
* input_data_type: json
* input: **{"campaign": {"id":*(INTEGER)*, "name":*(STRING)*, "all_day_notification": *(BOOLEAN)*, "from_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "to_time": {"hh": *(STRING_OF_INTEGER)*, "mins": *(STRING_OF_INTEGER)*, "m": *(STRING)*}, "time_zone": *(STRING(UTC +/- INTEGER))*, "locations": [ {"id":*(INTEGER)*, "name":*(STRING)*, "checked": *(BOOLEAN)*}], "status": *(BOOLEAN)* }}**
* ouput_data_type: json
* success_output: **{"success": "updateing status of campaign id *(INTEGER)*", "status": 200}**
* falure_outputs: **[{ "failure": "updating campaign status", "error": *error_message*, "status": 404 }]**