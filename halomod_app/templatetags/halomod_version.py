"""
Created on Apr 10, 2013

@author: Steven
"""

import halomod
from django import template

register = template.Library()


def current_halomod_version():
    return halomod.__version__


register.simple_tag(current_halomod_version)
