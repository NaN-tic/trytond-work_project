# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import work
from . import configuration
from . import invoice


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationCompany,
        work.Project,
        work.ProjectSaleLine,
        work.Sale,
        invoice.InvoiceLine,
        module='work_project', type_='model')
