# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .work import *
from .configuration import *


def register():
    Pool.register(
        Configuration,
        ConfigurationCompany,
        Project,
        ProjectMilestoneGroup,
        ProjectSaleLine,
        Sale,
        ShipmentWork,
        MilestoneGroup,
        module='work_project', type_='model')
