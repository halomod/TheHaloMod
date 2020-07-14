"""
Defines custom meta-forms and other utilities to make forms easier.
"""

import logging
import re
from collections import OrderedDict

from crispy_forms.bootstrap import Tab
from crispy_forms.layout import Div, Field
from django import forms
from django.utils.safestring import mark_safe

from halomod import TracerHaloModel

logger = logging.getLogger(__name__)


DEFAULTS = TracerHaloModel.get_all_parameter_defaults()


class RangeSlider(forms.TextInput):
    def __init__(self, minimum, maximum, step, elem_name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.minimum = str(minimum)
        self.maximum = str(maximum)
        self.step = str(step)
        self.elem_name = str(elem_name)

    def get_initial(self, val):
        try:
            rg = val.split(" - ")
            return """[ """ + rg[0] + "," + rg[1] + """ ]"""
        except IndexError:
            return """[ """ + self.minimum + """,""" + self.maximum + """ ]"""

    def render(self, name, value, attrs=None, renderer=None):

        s = super(RangeSlider, self).render(name, value, attrs)
        elem_id = re.findall(r'id_([A-Za-z0-9_\./\\-]*)"', s)[0]
        val = self.get_initial(value)

        html = (
            """<div id="slider-range-"""
            + elem_id
            + """"></div>
        <script>
        $('#id_"""
            + elem_id
            + """').attr("readonly", true)
        $( "#slider-range-"""
            + elem_id
            + """" ).slider({
        range: true,
        min: """
            + self.minimum
            + """,
        max: """
            + self.maximum
            + """,
        step: """
            + self.step
            + """,
        values: """
            + val
            + """,
        slide: function( event, ui ) {
          $( "#id_"""
            + elem_id
            + """" ).val(" """
            + self.elem_name
            + """ "+ ui.values[ 0 ] + " - " + ui.values[ 1 ] );
        }
        });
        $( "#id_"""
            + elem_id
            + """" ).val(" """
            + self.elem_name
            + """ "+ $( "#slider-range-"""
            + elem_id
            + """" ).slider( "values", 0 ) +
        " - " + $( "#slider-range-"""
            + elem_id
            + """" ).slider( "values", 1 ) );
        </script>
        """
        )

        return mark_safe(s + html)


class FloatListField(forms.CharField):
    """
    Defines a form field that accepts comma-separated real values and returns a list of floats.
    """

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_val, self.max_val = min_value, max_value
        super(FloatListField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)

        final_list = []
        if value:
            numbers = value.split(",")
            for number in numbers:
                try:
                    final_list.append(float(number))
                except ValueError:
                    raise forms.ValidationError("%s is not a float" % number)
            for number in final_list:
                if self.min_val is not None and number < self.min_val:
                    raise forms.ValidationError(
                        f"Must be greater than {self.min_val} ({number})"
                    )
                if self.max_val is not None and number > self.max_val:
                    raise forms.ValidationError(
                        f"Must be smaller than {self.max_val} ({number})"
                    )

        return final_list


class RangeSliderField(forms.CharField):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", "")
        self.minimum = kwargs.pop("minimum", 0)
        self.maximum = kwargs.pop("maximum", 100)
        self.step = kwargs.pop("step", 1)

        kwargs["widget"] = RangeSlider(self.minimum, self.maximum, self.step, self.name)

        if "label" not in kwargs.keys():
            kwargs["label"] = False

        super(RangeSliderField, self).__init__(*args, **kwargs)

    def clean(self, value):
        super().clean(value)

        items = value.split(" - ")
        return [float(i) for i in items]


class CompositeForm(forms.Form):
    """
    Helper class to handle form composition.
    Usage::
      class ProfileForm(CompositeForm):
          form_list = [ProfileAddressForm, ProfileBirthDayForm]

    Ripped from https://github.com/t0ster/django-composite-form
    """

    form_list = None  # Form classes

    def __init__(self, data=None, files=None, field_order=None, *args, **kwargs):
        super().__init__(data, files, field_order=None, *args, **kwargs)

        self._form_instances = OrderedDict()  # Form instances
        for form in self.form_list:
            kw = kwargs.copy()
            self._form_instances[form] = form(data, files, *args, **kw)

        for form in self.forms:
            self.fields.update({f"{name}": val for name, val in form.fields.items()})

        self.order_fields(self.field_order if field_order is None else field_order)
        #
        # for form in self.forms:
        #     self.initial.update(form.initial)

    @property
    def forms(self):
        """
        Returns list of form instances
        """
        # Preserving forms ordering
        return [self._form_instances[form_class] for form_class in self.form_list]

    def get_form(self, form_class):
        """
        Returns form instance by its class
        ``form_class``: form class from ``forms_list``
        """
        return self._form_instances[form_class]

    def non_field_errors(self):
        _errors = super().non_field_errors()
        for form in self.forms:
            _errors.extend(form.non_field_errors())
        return _errors

    def full_clean(self):
        super().full_clean()

        if not self.is_bound:
            return

        for form in self.forms:
            form.full_clean()
            self.cleaned_data.update(form.cleaned_data)
            self._errors.update(form._errors)


class ComponentModelForm(forms.Form):
    """Base class for forms that define input to Components."""

    label = None  # The text that shows on the form's tab
    kind = None  # What it's called in the hmf framework, eg "hmf" for "hmf_model"
    choices = None
    _initial = None
    multi = False

    module = None

    ignore_fields = []
    add_fields = {}
    field_kwargs = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.label is None:
            self.label = self.__class__.__name__.split("Form")[0] + " Model"

        if self.kind is None:
            self.kind = self.__class__.__name__.split("Form")[0].lower()

        # Get initial model choice based on defaults of TracerHaloModel.
        if self._initial is None:
            df = DEFAULTS.get(self.kind + "_model")
            if isinstance(df, str):
                self._initial = df
            elif df is None:
                self._initial = "None"
            else:
                self._initial = df.__name__

        # Fill the fields
        if not self.multi:
            self.fields[f"{self.kind}_model"] = forms.ChoiceField(
                label=self.label,
                choices=self.choices,
                initial=self._initial,
                required=True,
            )
        else:
            self.fields[f"{self.kind}_model"] = forms.MultipleChoiceField(
                label=self.label,
                choices=self.choices,
                initial=[self._initial],
                required=True,
            )

        # Add all the possible parameters for this model
        for choice in self.choices:
            self._add_default_model(choice[0])

        for fieldname, field in self.add_fields.items():
            name = f"{self.kind}_{fieldname}"
            self.fields[name] = field
            self.fields[name].component = self.kind
            self.fields[name].paramname = fieldname

        # Make layout a simple Tab with a model chooser and model parameters.
        self._layout = Tab(
            self.label,
            Div(
                Div(
                    Field(
                        f"{self.kind}_model",
                        css_class="hmf_model",
                        data_component=self.kind,
                    ),
                    css_class="col",
                ),
                self._get_model_param_divs(),
                css_class="mt-4 row",
            ),
        )

    def _add_default_model(self, model):
        # Allow a "None" class
        if model == "None" or model is None:
            return

        cls = getattr(self.module, model)

        for key, val in getattr(cls, "_defaults", {}).items():
            name = f"{self.kind}_{model}_{key}"

            if (
                key in self.ignore_fields
                or model + "_" + key in self.ignore_fields
                or isinstance(val, dict)
                or val is None
            ):
                continue

            field_types = {
                float: forms.FloatField,
                bool: forms.BooleanField,
                str: forms.ChoiceField,
            }

            fkw = self.field_kwargs.get(key, {})
            thisfield = fkw.pop("type", field_types.get(type(val), forms.FloatField))

            self.fields[name] = thisfield(
                label=fkw.pop("label", key), initial=str(val), required=False, **fkw
            )

            self.fields[name].component = self.kind
            self.fields[name].model = model
            self.fields[name].paramname = key

    def _get_model_param_divs(self):
        param_div = Div()
        for name, field in self.fields.items():
            if name == f"{self.kind}_model":
                continue

            if hasattr(field, "model"):
                param_div.append(
                    Div(
                        name,
                        css_class="col",
                        data_component=self.kind,
                        data_model=field.model,
                    )
                )
            else:
                param_div.append(Div(name, css_class="col"))
        return param_div


class FrameworkForm(forms.Form):
    """Base class for forms that define inputs to Frameworks."""

    label = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.label is None:
            self.label = self.__class__.__name__

        self._layout = Tab(self.label, Div(*self.fields.keys(), css_class="mt-4 col"))
