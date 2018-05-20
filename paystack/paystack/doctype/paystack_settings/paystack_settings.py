# -*- coding: utf-8 -*-
# Copyright (c) 2018, XLevel Retail Systems Nigeria Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.integrations.utils import create_payment_gateway
from frappe.model.document import Document
from frappe.utils import call_hook_method
from requests import RequestException


SUPPORTED_CURRENCIES = ['NGN']


class PaystackSettings(Document):
	def validate(self):
		create_payment_gateway("Paystack")
		call_hook_method('payment_gateway_enabled', gateway="Paystack")
		if not self.flags.ignore_mandatory:
			self.validate_credentials()

	def validate_credentials(self):
		import paystakk
		try:
			paystack = paystakk.TransferControl(secret_key=self.secret_key, public_key=self.public_key)
			paystack.get_balance()
		except RequestException:
			frappe.throw(
				_('Verification of your credentials failed. Please ensure you '
				  'have a working internet connection and that your '
				  'credentials are correct')
			)
