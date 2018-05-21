# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "paystack"
app_title = "Paystack"
app_publisher = "XLevel Retail Systems Nigeria Ltd"
app_description = "App that integrates Paystack into ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "olamide@xlevelretail.com"
app_license = "MIT"

scheduler_events = {
	"hourly": ['paystack.paystack.utils.update_paid_requests']
}
