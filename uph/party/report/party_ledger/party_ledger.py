# Copyright (c) 2025, Abdo Ruzaqi and contributors
# For license information, please see license.txt

from collections import OrderedDict,defaultdict

import frappe
from frappe import _, qb, query_builder, scrub

from frappe.query_builder import Criterion
from frappe.query_builder.functions import Date, Substring, Sum
from frappe.utils import cint, cstr, flt, getdate, nowdate, money_in_words

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from ruzaqi_app.ruzaqi_app.report.sub_accounts_gl_summary.sub_accounts_gl_summary import get_sales_invoice_count,get_purchase_invoice_count
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children

from erpnext.accounts.utils import get_currency_precision, get_party_types_from_account_type


def execute(filters=None):
	columns, data = [], []
	return columns, data
def execute(filters=None):
	return PartyLedger(filters).run()


class PartyLedger(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.selected_fields=""
		self.list_selected_fields=[]
		self.sub_acc_parties= []
		self.parties_gl_entries=OrderedDict()
		self.data = []
		self.message=''

	def run(self):
		self.set_defaults()
		self.validate_filters()
		self.get_parties()
		self.get_conditions()
		self.get_columns()
		self.get_data()
		# self.get_chart_data()
		return self.columns, self.data,self.message


	def validate_filters(self):
		if self.filters.get("to_date") < self.filters.get("from_date"):
			frappe.throw(_("Set From Date Must be priore Dates to To current Date"))

		
	def set_defaults(self):
		if not self.filters.get("company"):
			frappe.throw(_("Set Company Otherwise Select company wise accounting"))
		self.company_currency = frappe.get_cached_value(
			"Company", self.filters.get("company"), "default_currency"
		)
		self.accounting_dimensions =[]
		if self.filters.get("include_dimensions"):
			self.accounting_dimensions = get_accounting_dimensions()
		self.dimension_fields = ""
		if self.accounting_dimensions:
			self.dimension_fields = ", ".join(self.accounting_dimensions) + ","
		self.selected_fields = """, gle.debit as coc_debit, gle.credit as coc_credit, gle.debit_in_account_currency as debit,
		credit_in_account_currency as credit, remarks """

	def get_conditions(self):
		conditions=[]
		voucher_no_not_in=[]
		if self.filters.get("ignore_err"):
			err_journals = frappe.db.get_all(
			"Journal Entry",
			filters={
				"company": self.filters.get("company"),
				"docstatus": 1,
				"voucher_type": ("in", ["Exchange Rate Revaluation", "Exchange Gain Or Loss"]),
			},
			as_list=True,)
			if err_journals:
				voucher_no_not_in= [x[0] for x in err_journals]
		if self.filters.get("not_include_voucher_no"):
				vnolist= self.filters.get("not_include_voucher_no").split(",")
				voucher_no_not_in.extend(vnolist)
		if voucher_no_not_in:
			self.filters.update({"voucher_no_not_in":voucher_no_not_in})
		if not self.filters.get("show_cancelled_entries"):
			conditions.append("is_cancelled = 0")
		if self.filters.get("voucher_no_not_in"):
			conditions.append("voucher_no not in %(voucher_no_not_in)s")
		#if self.filters.get("party"):
		#	conditions.append("party in %(party)s")
	#	if self.filters.get("party_type"):
		#	conditions.append("party_type=%(party_type)s")
		if self.filters.get("cost_center"):
			self.filters.cost_center = get_cost_centers_with_children(self.filters.cost_center)
			conditions.append("cost_center in %(cost_center)s")
		accounting_dimensions = get_accounting_dimensions(as_list=False)
		if accounting_dimensions:
			for dimension in accounting_dimensions:
				# Ignore 'Finance Book' set up as dimension in below logic, as it is already handled in above section
				if not dimension.disabled and dimension.document_type != "Finance Book":
					if self.filters.get(dimension.fieldname):
						if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
							self.filters[dimension.fieldname] = get_dimension_with_children(
								dimension.document_type, self.filters.get(dimension.fieldname)
							)
							conditions.append("{0} in %({0})s".format(dimension.fieldname))
						else:
							conditions.append("{0} in %({0})s".format(dimension.fieldname))

		self.conditions = "and {}".format(" and ".join(conditions)) if conditions else ""

	def get_parties(self):
		order=[]
		where =[]
		if self.filters.get("order_by_full_name"):
			order.extend(["p.full_name", "p.name", "c.party_type"])
		else:
			order.extend(["p.name", "c.party_type"])

		if self.filters.get("party_parent"):
			where.append("p.name = %(party_parent)s")
		if not self.filters.all_currency and self.filters.presentation_currency:
			where.append("c.currency = %(presentation_currency)s")      
		elif self.filters.all_currency:
			order.append('c.currency desc')
		self.parties= OrderedDict()
		where_claus="{0} {1}".format("where" if where else ""," and ".join(where))
		order_claus="order by {}".format(" , ".join(order))
		query =frappe.db.sql(
				"""
				select c.account as name, c.party_type as party_type, c.currency as default_currency, p.name as party_parent, p.full_name as full_name, has_accounting_issues,warning_message
				from `tabProfile Accounts` c
				join `tabParty Profile` p on c.parent = p.name
				{where}
				{order}		
            	""".format(where=where_claus,order=order_claus),self.filters,as_dict=1)
		if not query and self.filters.party_parent and self.filters.presentation_currency:
			frappe.msgprint(_('Party Profile {0} Not Activate Currency {1}').format(self.filters.party_parent,self.filters.presentation_currency))
		self.parties=query
		self.filters.update({"party":[d.get("name") for d in self.parties]})
# This will get Total Counts of Sales invoice and Purchase Invoice with DocStatus
		if self.filters.get("show_documents_summary"):
			customer=[d.name for d in self.parties if d.party_type=="Customer"]
			supplier=[d.name for d in self.parties if d.party_type=="Supplier"]
			filt= {"company":self.filters.get("company"),"all_customer":0,"all_supplier":0,"customer":customer,"supplier":supplier}
			if customer:
				self.sales_invoice= get_sales_invoice_count(filters=filt)
			if supplier:			
				self.purchase_invoice= get_purchase_invoice_count(filters=filt)
   
	def get_data(self):
		parties_data= self.calculate_balance()
		parent_dict= frappe._dict()
		for party in self.parties:
			if gl:= parties_data.get(party.name):
				pb=""
				pr=party.get("parent") 
				if pr not in parent_dict.keys():
					parent_dict[pr]=1
					if len(parent_dict.keys())>1:
						pb+='<p class="page-break"></p>'
					self.data.append({"indent":2,"html":pb})
				self.data.append({
						"party_parent":party.get("party_parent"),
						"remarks":"{0} {1}".format(party.get("full_name"),"" if not party.get("warning_message") else party.get("warning_message")),
						"indent":0,
						"bold":1,
						"party_type":party.get("party_type"),
						"party":party.get("name"),
					})
				self.data.extend(gl)
				if self.filters.get("show_documents_summary"):
					remark=[]
					if party.party_type =="Customer" and self.sales_invoice and self.sales_invoice.get(party.name):
						remark.append(self.get_doctype_summary("Sales Invoice", self.sales_invoice.get(party.name)))
					if party.party_type =="Supplier" and self.purchase_invoice and self.purchase_invoice.get(party.name):
						remark.append(self.get_doctype_summary("Purchase Invoice", self.purchase_invoice.get(party.name)))
					if remark:
						self.data.append({"row_type":"colspan","indent":1,"op_en":"Yes","remarks":"{}".format(" /n ".join(remark))
									})
				self.data.append({"empty":1,"indent":2})

	def calculate_balance(self):
		parties_gl_data = self.prepare_data()
		for party,data in parties_gl_data.items():
			if len(data)>0:
				balance,tc_debit,tc_credit=0,0,0
				currency=data[0].get("currency")
				for d in data:
					tc_debit+=d.get("debit",0)
					tc_credit+=d.get("credit",0)
					balance+=d.get("debit",0)-d.get("credit",0)
					d["balance"]=balance
					d["balance_statues"]= "{}".format(_("Dr") if d.get("balance")>0 else  _("Cr"))
					d["indent"]=1
				balance_word=0
				if balance<0:
					balance_word+=balance*-1
				else:
					balance_word=balance
				balance_in_word ="{0}  {1}".format("" if balance_word==0 else _("Dr") if balance>0 else  _("Cr"), money_in_words(balance_word,currency))
				parties_gl_data[party].append({"op_en":"Yes","totals":"Yes","currency":currency,"debit":tc_debit, "credit": tc_credit,"indent":1,"bold":1,"remarks":_("Total Current Period")})
				parties_gl_data[party].append({"op_en":"Yes","ending":1,"remarks": "{0} {1}".format(_("The End Balance"),balance_in_word),"currency":currency,"balance":balance,"bold":1,"indent":1,})    
      
		return parties_gl_data

	def prepare_data(self):
		opening_balance = self.get_opening()
		current_gl_entries=self.get_current_period_trans()
		gl_entries=defaultdict(list)
		for party in self.parties:
			if op:=opening_balance.get(party.name):
				gl_entries[party.name].append(op)
			if gl_tx:= current_gl_entries.get(party.name):
				if self.filters.get("group_by_voucher_consolidate"):
					gl_tx= self.group_by_voucher(current_gl_entries.get(party.name))
					gl_entries[party.name].extend(gl_tx)
				else:
					gl_entries[party.name].extend(gl_tx)
		return gl_entries
	
	def group_by_voucher(self,gl_entries):
		new_list=[]
		voucher_dict=OrderedDict()
		if isinstance(gl_entries,list):
			for d in gl_entries:
				voucher_no=d.get("voucher_no")
				voucher_type=d.get("voucher_type")
				if voucher_no not in voucher_dict.keys():
					voucher_dict[voucher_no]=d
				else:
					if voucher_type==voucher_dict[voucher_no].get("voucher_type"):
						credit= d.get("credit",0)+voucher_dict[voucher_no].get("credit",0)
						debit=d.get("debit",0)+voucher_dict[voucher_no].get("debit",0)
						voucher_dict[voucher_no].update({"credit":credit,"debit":debit})
			
		for v in voucher_dict.values():
			new_list.append(v)

		#Removing Equals transiction : So return list without equal debit and credit after grouping by voucher no.
		if self.filters.hide_equals_dr_cr_tx:
			nlist=[x for x in new_list if x.get('debit')!=x.get('credit')]
			return nlist
			

		return new_list
	def get_doctype_summary(self,doctype,value):
		liststatus=[]
		for k,v in value.items():
			liststatus.append("{0} {1} {2} ".format(_("Submitted") if k==1 else _("Cancel") if k==2  else _("Draft"),_("Counts"),v))
		return "{0} :[ {1} ]".format(_(doctype)," , ".join(liststatus))
	
	def get_opening(self):
		query = frappe.db.sql(
		"""
		select 
			gle.party as party, gle.party_type, gle.account_currency as currency,gle.account, p.parent as party_parent, gle.branch, gle.cost_center,
			SUM(gle.debit_in_account_currency-gle.credit_in_account_currency) as balance 
		from `tabGL Entry` gle
		join `tabProfile Accounts` p on gle.party = p.account
		where company= %(company)s and posting_date < %(from_date)s {conditions}
		group by 
			gle.party
		order by 
			p.parent		
		""".format(
			conditions= self.conditions,
		),self.filters, 
		as_dict=1,
		)
		result =[b for b in query if b.get("balance") !=0] # type: ignore
		opening= frappe._dict()
		for r in result:
			credit,debit=0,0
			if r.get("balance")>0:
				debit+=r.get("balance",0)
			else:
				credit+=r.get("balance",0)*-1
			r.update({"balance":0,"debit":debit,"credit":credit,"remarks":_("Opening"),"is_opening":"Yes","op_en":"Yes","bold":1})
			opening.setdefault(r.get("party"), r)
		return opening

	def get_current_period_trans(self):
		gl_entries = frappe.db.sql(
		"""
		select
			gle.name as gl_entry, gle.posting_date as posting_date, gle.account, gle.party_type, gle.party as party,
			gle.voucher_type, gle.voucher_subtype, gle.voucher_no, gle.branch, 
			gle.cost_center, gle.project, p.parent as party_parent,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency as currency,
			gle.against, gle.is_opening, gle.creation {select_fields}
		from `tabGL Entry` gle
		join `tabProfile Accounts` p on gle.party = p.account
		where company=%(company)s and posting_date between %(from_date)s and %(to_date)s {conditions}
		order by gle.party, gle.posting_date, gle.creation
	""".format(
			select_fields=self.selected_fields,
			conditions=self.conditions,
		),
		self.filters,
		as_dict=1,)
		gle_tx=defaultdict(list)
		for gl in gl_entries:
			gle_tx[gl.get("party")].append(gl)
		return gle_tx


	def get_columns(self):
		self.columns = [
			{
				"label": "GL Entry",
				"fieldname": "gl_entry",
				"hidden": 1,
			},
			{
				"label":_("Account No"),
				"fieldname": "party_parent",
				"fieldtype": "Link",
    			"options": "Party Profile",
				"align": "left",
				"width": 80,
    			"hidden": 1,

			},
			{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
			{
				"label": _("Remarks"),
				"fieldname": "remarks",
				"fieldtype": "Data",
				"align":"right",
				"width": 200,
			},
   			{
				"label": _("Voucher No"),
				"fieldname": "voucher_no",
				"fieldtype": "Dynamic Link",
				"options": "voucher_type",
				"width": 150,
			},	
			{
				"label":_("Currency"),
				"fieldname":"currency",
				"fieldtype":"Data",
				"width": 50,	
				"hidden": 0,
			},
			{
				"label": _("Debit"),
				"fieldname": "debit",
				"fieldtype": "Float",
				"width": 110,
				"precision": 2,
			},
			{
				"label": _("Credit"),
				"fieldname": "credit",
				"fieldtype": "Float",
				"width": 110,
				"precision": 2,
			},
			{
				"label": _("The Balance"),
				"fieldname": "balance",
				"fieldtype": "Currency",
				"width": 130,
				"options":"currency",
			},
				
  			{
				"label": _("Voucher Type"),
				"fieldname": "voucher_type",
				"fieldtype": "Data",
				"width": 100,
			},
		]
		if self.filters.get("include_dimensions"):
			for dim in get_accounting_dimensions(as_list=False):
				self.columns.append(
				{"label": _(dim.label), "fieldname": dim.fieldname, "width": 100}
			)
		self.columns.append(
			{"label": _("Cost Center"),  "fieldname": "cost_center", "width": 100}
		)

		self.columns += [
		
			{
				"label":_("Party Type"),
				"fieldname": "party_type",
				"fieldtype": "Data",
				"hidden":0,
			},
			
			{
				"label": _("Account"),
				"fieldname": "account",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Party"),
				"fieldname": "party",
				"fieldtype": "Dynamic Link",
				"options": "party_type",
				"align": "left",
				"width": 20,
			},
   			{
			"label": _("Voucher Subtype"),
			"fieldname": "voucher_subtype",
			"fieldtype": "Data",
			"width": 180,
			},
			{"label": _("Against Account"), "fieldname": "against", "width": 120},]
	
		self.columns.extend(
		[
			{"label": _("Against Voucher Type"), "fieldname": "against_voucher_type", "width": 100},
			{
				"label": _("Against Voucher"),
				"fieldname": "against_voucher",
				"fieldtype": "Dynamic Link",
				"options": "against_voucher_type",
				"width": 100,
			},
			{"label": _("Supplier Invoice No"), "fieldname": "bill_no", "fieldtype": "Data", "width": 100},
		]
	)
		
	