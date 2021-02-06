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
from requests import RequestException, ConnectionError

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
		api = paystakk.TransferControl(secret_key=self.secret_key, public_key=self.public_key)
		try:
			api.get_balance()
		except ConnectionError:
			frappe.throw('There was a connection problem. Please ensure that'
						 ' you have a working internet connection.')

		if not api.ctx.status:
			frappe.throw(api.ctx.message, title=_("Failed Credentials Validation"))

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(
				_('{currency} is not supported by Paystack at the moment.').format(currency))

	def get_payment_url(self, **kwargs):
		amount = kwargs.get('amount')
		description = kwargs.get('description')
		slug = kwargs.get('reference_docname')
		email = kwargs.get('payer_email')
		metadata = {
			'payment_request': kwargs.get('order_id'),
			'customer_name': kwargs.get('payer_name')
		}

		secret_key = self.get_password(fieldname='secret_key', raise_exception=False)

		customer_api = paystakk.Customer(secret_key=secret_key, public_key=self.public_key)

		customer_api.fetch_customer(email)
		if not customer_api.ctx.status:
			customer_api.create_customer(email=email)

		if not customer_api.ctx.status:
			frappe.throw(customer_api.ctx.message)

		invoice_api = paystakk.Invoice(secret_key=secret_key, public_key=self.public_key)

		identifier = hash('{0}{1}{2}'.format(amount, description, slug))
		invoice_api.create_invoice(customer=customer_api.customer_code,
								   amount=amount, due_date=nowdate(),
								   description=description,
								   invoice_number=identifier, metadata=metadata)

		if not invoice_api.ctx.status:
			frappe.throw(invoice_api.ctx.message)
		else:
			payment_url = 'https://paystack.com/pay/{invoice_code}'.format(
				invoice_code=invoice_api.request_code)
			return payment_url
