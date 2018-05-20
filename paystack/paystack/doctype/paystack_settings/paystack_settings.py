# -*- coding: utf-8 -*-
# Copyright (c) 2018, XLevel Retail Systems Nigeria Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import paystakk
from frappe import _
from frappe.integrations.utils import create_payment_gateway
from frappe.model.document import Document
from frappe.utils import call_hook_method, nowdate
from requests import RequestException

SUPPORTED_CURRENCIES = ['NGN']


class PaystackSettings(Document):
	supported_currencies = SUPPORTED_CURRENCIES

	def validate(self):
		if not self.flags.ignore_mandatory:
			self.validate_credentials()

	def on_update(self):
		name = 'Paystack-{0}'.format(self.gateway_name)
		create_payment_gateway(
			name,
			settings='Paystack Settings',
			controller=self.gateway_name
		)
		call_hook_method('payment_gateway_enabled', gateway=name)

	def validate_credentials(self):
		try:
			paystack = paystakk.TransferControl(secret_key=self.secret_key, public_key=self.public_key)
			paystack.get_balance()
		except RequestException:
			frappe.throw(
				_('Verification of your credentials failed. Please ensure you '
				  'have a working internet connection and that your '
				  'credentials are correct')
			)

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(
				_('{currency} is not supported by Paystack at the moment.').format(currency))

	def get_payment_url(self, **kwargs):
		amount = kwargs.get('amount')
		description = kwargs.get('description')
		slug = kwargs.get('reference_docname')
		email = kwargs.get('payer_email')

		secret_key = self.get_password(fieldname='secret_key', raise_exception=False)

		customer_api = paystakk.Customer(secret_key=secret_key, public_key=self.public_key)

		try:
			customer_api.fetch_customer(email)
			if not customer_api.customer_code:
				customer_api.create_customer(email=email)
		except RequestException as e:
			frappe.throw(_(e.message))

		invoice_api = paystakk.Invoice(secret_key=secret_key, public_key=self.public_key)

		try:
			identifier = hash('{0}{1}{2}'.format(amount, description, slug))
			invoice_api.create_invoice(
				customer=customer_api.customer_code, amount=amount,
				due_date=nowdate(), description=description, invoice_number=identifier
			)
		except RequestException as e:
			frappe.throw(_(e.message))

		payment_url = 'https://api.paystack.co/paymentrequest/notify/{invoice_code}'.format(
			invoice_code=invoice_api.invoice_code)

		return payment_url
