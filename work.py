# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
from sql.aggregate import Max, Sum, Avg
from sql.operators import NotIn

from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

from trytond.modules.product import price_digits

__all__ = ['ProjectSaleLine', 'Project', 'ShipmentWork', 'Sale']

_ZERO = Decimal('0.0')


class ProjectSaleLine(ModelSQL, ModelView):
    'Project Sale Line'
    __name__ = 'work.project.sale.line'
    project = fields.Many2One('work.project', 'Project', required=True)
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Float('Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    unit = fields.Many2One('product.uom', 'Unit')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    currency = fields.Many2One('currency.currency', 'Currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    unit_price = fields.Numeric('Unit Price', digits=price_digits)
    amount = fields.Function(fields.Numeric('Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amount')

    def get_amount(self, name):
        return self.currency.round(
            Decimal(str(self.quantity)) * self.unit_price)

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        return self.currency.digits

    @classmethod
    def table_query(cls):
        pool = Pool()
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')
        table = SaleLine.__table__()
        sale = Sale.__table__()

        columns = []
        for name in ('id', 'create_uid', 'write_uid', 'create_date',
                'write_date'):
            columns.append(Max(getattr(table, name)).as_(name))

        columns.extend([sale.work_project, table.product, sale.currency, table.unit,
                Sum(table.quantity).as_('quantity'),
            Avg(table.unit_price).as_('unit_price')])

        return table.join(sale, condition=(sale.id == table.sale)).select(
            *columns,
            where=((table.type == 'line') &
                (sale.work_project != None) &
                (NotIn(sale.state, ['cancel', 'draft', 'quotation']))
                ),
            group_by=(sale.work_project, sale.currency, table.product, table.unit))


class Project(ModelSQL, ModelView):
    'Work Project'
    __name__ = 'work.project'
    _rec_name = 'code'

    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    code = fields.Char('Code', required=True, select=True,
        states={
            'readonly': Eval('code_readonly', True),
            },
        depends=['code_readonly'])
    code_readonly = fields.Function(fields.Boolean('Code Readonly'),
        'get_code_readonly')
    party = fields.Many2One('party.party', 'Party', required=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    maintenance = fields.Boolean('Maintenance')
    work_shipments = fields.One2Many('shipment.work', 'work_project',
        'Shipment Works',
        domain=[
            ('party', '=', Eval('party')),
            ],
        depends=['party'])
    sales = fields.One2Many('sale.sale', 'work_project', 'Sales',
        domain=[
            ('party', '=', Eval('party', -1))
            ],
        add_remove=[
            ('state', 'in', ['quotation', 'confirmed', 'processing']),
            ],
        depends=['party'])
    sale_lines = fields.One2Many('work.project.sale.line', 'work_project',
        'Sale Lines', readonly=True)
    supplier_invoice_lines = fields.One2Many('account.invoice.line',
        'work_project', 'Supplier Invoice Lines', domain=[
            ('invoice.type', 'in', ['in_invoice', 'in_credit_note']),
            ])
    amount_to_invoice = fields.Function(fields.Numeric('Amount To Invoice',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amount_to_invoice')
    invoiced_amount = fields.Function(fields.Numeric('Invoiced Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amount_to_invoice')
    shipments = fields.Function(fields.One2Many('stock.shipment.out',
            None, 'Shipments'), 'get_shipments')
    shipment_returns = fields.Function(fields.One2Many(
            'stock.shipment.out.return', None, 'Shipment Returns'),
        'get_shipment_returns')
    moves = fields.Function(fields.One2Many('stock.move', None, 'Moves'),
        'get_moves')
    income_labor = fields.Function(fields.Numeric('Income Labor',
        digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_income_labor')
    income_material = fields.Function(fields.Numeric('Income Material',
        digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_income_material')
    income_other = fields.Function(fields.Numeric('Income Other',
        digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_income_other')
    expense_labor = fields.Function(fields.Numeric('Expense Labor',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_expense_labor')
    expense_material = fields.Function(fields.Numeric('Expense Material',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_expense_material')
    expense_other = fields.Function(fields.Numeric('Expense Other',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_expense_other')
    margin_labor = fields.Function(fields.Numeric('Margin Labor',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_margins')
    margin_material = fields.Function(fields.Numeric('Margin Material',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_margins')
    margin_other = fields.Function(fields.Numeric('Margin Other',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_margins')
    margin_percent_labor = fields.Function(fields.Numeric('Margin(%) Labor',
            digits=(16, 4)),
        'get_margins')
    margin_percent_material = fields.Function(fields.Numeric(
            'Margin (%) Material', digits=(16, 4)),
        'get_margins')
    margin_percent_other = fields.Function(fields.Numeric('Margin (%) Other',
            digits=(16, 4)),
        'get_margins')
    note = fields.Text('Note')
    invoices = fields.Function(fields.One2Many('account.invoice', None,
        'Invoices'), 'get_invoices')


    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_code_readonly():
        Configuration = Pool().get('work.project.configuration')
        config = Configuration(1)
        return bool(config.project_sequence)

    @fields.depends('company')
    def on_change_with_currency_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    def is_labour_line(self, line):
        'Returns True if the sale line is of labour type'
        return line.product and line.product.type == 'service'

    def is_other_line(self, line):
        'Returns True if the sale line is of other type'
        return not line.product

    def get_income_labor(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if not self.is_other_line(line) and self.is_labour_line(line):
                    amount += line.amount
        return amount

    def get_income_material(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if (not self.is_other_line(line) and
                        not self.is_labour_line(line)):
                    amount += line.amount
        return amount

    def get_income_other(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if self.is_other_line(line):
                    amount += line.amount
        return amount

    def get_expense_labor(self, name):
        amount = _ZERO
        # for shipment_work in self.work_shipments:
        #     for line in shipment_work.timesheet_lines:
        #         amount += line.compute_cost()
        return amount

    def get_expense_material(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if line.product and line.product.type != 'service':
                    qty = Decimal(str(line.quantity or 0))
                    # Compatibility with sale_margin
                    if hasattr(line, 'cost_price'):
                        cost_price = line.cost_price or _ZERO
                    else:
                        cost_price = line.product.cost_price
                    amount += sale.currency.round(cost_price * qty)
        return amount

    def get_expense_other(self, name):
        amount = _ZERO
        return amount

    @classmethod
    def get_margins(cls, projects, names):
        res = {}
        for name in names:
            res[name] = dict((p.id, _ZERO) for p in projects)
        for project in projects:
            for name in names:
                field_name = name.split('_')[-1]
                income = getattr(project, 'income_%s' % field_name)
                expense = getattr(project, 'expense_%s' % field_name)
                if 'percent' in name:
                    if not expense:
                        value = Decimal('1.0')
                    else:
                        value = (income - expense) / expense
                    digits = getattr(cls, name).digits[1]
                else:
                    value = income - expense
                    digits = project.currency_digits
                value = value.quantize(Decimal(str(10 ** - digits)))
                res[name][project.id] = value
        return res

    @classmethod
    def get_amount_to_invoice(cls, projects, names):
        res = {}
        for name in names:
            res[name] = dict((p.id, _ZERO) for p in projects)

        for project in projects:
            amount_to_invoice = Decimal('0.00')
            invoiced_amount = Decimal('0.00')
            for sale in project.sales:
                amount_to_invoice += sale.amount_to_invoice()
                invoiced_amount += sale.invoiced_amount()
            res['amount_to_invoice'][project.id] = amount_to_invoice
            res['invoiced_amount'][project.id] = invoiced_amount
        return res

    def get_code_readonly(self, name):
        return True

    def get_moves(self, name):
        return [m.id for s in self.sales for m in s.moves]

    def get_shipments(self, name):
        return [m.id for s in self.sales for m in s.shipments]

    def get_shipment_returns(self, name):
        return [m.id for s in self.sales for m in s.shipment_returns]

    def get_invoices(self, name):
        return [m.id for s in self.sales for m in s.invoices]

    @classmethod
    def create(cls, vlist):
        'Fill the reference field with the sale sequence'
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('work.project.configuration')

        config = Config(1)
        for value in vlist:
            if not value.get('code'):
                if config.project_sequence:
                    code = Sequence.get_id(config.project_sequence.id)
                else:
                    code = None
                value['code'] = code
        return super(Project, cls).create(vlist)

    @classmethod
    def copy(cls, projects, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(Project, cls).copy(projects, default=default)


class ShipmentWork:
    __name__ = 'shipment.work'
    __metaclass__ = PoolMeta

    work_project = fields.Many2One('work.project', 'Project',
        domain=[
            ('party', '=', Eval('party')),
            ],
        states={
            'readonly': Eval('state').in_(['checked', 'cancel']),
            },
        depends=['state', 'party'])

    def get_sale(self, invoice_method):
        sale = super(ShipmentWork, self).get_sale(invoice_method)
        sale.work_project = self.work_project
        return sale


class Sale:
    __name__ = 'sale.sale'
    __metaclass__ = PoolMeta

    work_project = fields.Many2One('work.project', 'Project', domain=[
            ('party', '=', Eval('party')),
            ])

    def invoiced_amount(self):
        amount = Decimal('0.00')
        for invoice in self.invoices:
            amount += invoice.untaxed_amount
        return amount

    def amount_to_invoice(self):
        return self.untaxed_amount - self.invoiced_amount()
