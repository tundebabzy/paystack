import frappe
import paystakk


def make_payment_entry(docname):
	doc = frappe.get_doc("Payment Request", docname)
	if doc.status == 'Initiated':
		return doc.create_payment_entry(submit=True)


def update_paid_requests():
	paystack_profiles = frappe.get_list('Paystack Settings', fields=['name'])

	for profile in paystack_profiles:
		doc = frappe.get_doc('Paystack Settings', profile['name'])
		secret_key = doc.get_password(fieldname='secret_key', raise_exception=False)
		api = paystakk.Invoice(secret_key=secret_key, public_key=doc.public_key)
		invoices = api.list_invoices(status='success')

		if invoices['status']:
			gen = (item for item in invoices['data'])
			for item in gen:
				if item['metadata']:
					docname = item['metadata']['payment_request']
					make_payment_entry(docname=docname)

