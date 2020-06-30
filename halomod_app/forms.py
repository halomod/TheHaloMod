"""All the forms on TheHaloMod"""

import logging

import hmf
import numpy as np
from crispy_forms.bootstrap import TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML
from django import forms
from django.utils.safestring import mark_safe
from hmf import growth_factor, transfer_models, fitting_functions, filters, wdm
from hmf.halos import mass_definitions
from .form_utils import (
    CompositeForm,
    ComponentModelForm,
    FrameworkForm,
    RangeSliderField,
)
from halomod import bias
from halomod import concentration
from halomod import profiles
from halomod import halo_exclusion
from halomod import hod
from halomod import wdm as hm_wdm
from halomod import TracerHaloModel

logger = logging.getLogger(__name__)


DEFAULT_MODEL = TracerHaloModel.get_all_parameter_defaults()


class CosmoForm(ComponentModelForm):
    choices = [
        ("Planck15", "Planck15"),
        ("Planck13", "Planck13"),
        ("WMAP9", "WMAP9"),
        ("WMAP7", "WMAP7"),
        ("WMAP5", "WMAP5"),
    ]

    label = "Cosmology"
    _initial = "Planck15"
    module = hmf.cosmo

    add_fields = dict(
        H0=forms.FloatField(
            label=mark_safe("H<sub>0</sub>"),
            initial=str(hmf.cosmo.Planck15.H0.value),
            min_value=10,
            max_value=500.0,
        ),
        Ob0=forms.FloatField(
            label=mark_safe("&#937<sub>b</sub>"),
            initial=str(hmf.cosmo.Planck15.Ob0),
            min_value=0.005,
            max_value=0.65,
        ),
        Om0=forms.FloatField(
            label=mark_safe("&#937<sub>m</sub>"),
            initial=str(hmf.cosmo.Planck15.Om0),
            min_value=0.02,
            max_value=2.0,
        ),
    )


class GrowthForm(ComponentModelForm):
    choices = [
        ("GrowthFactor", "Integral"),
        ("GenMFGrowth", "GenMF"),
        ("Carroll1992", "Carroll (1992)"),
        # ("CAMB", "CambGrowth")
    ]
    module = growth_factor


class TransferForm(ComponentModelForm):
    choices = [
        ("CAMB", "CAMB"),
        ("EH_BAO", "Eisenstein-Hu (1998) (with BAO)"),
        ("EH_NoBAO", "Eisenstein-Hu (1998) (no BAO)"),
        ("BBKS", "BBKS (1986)",),
        ("BondEfs", "Bond-Efstathiou"),
    ]
    module = transfer_models
    ignore_fields = ["camb_params"]

    field_kwargs = {"fname": {"type": forms.FileField, "label": "",}}

    def clean_transfer_fname(self):
        thefile = self.cleaned_data.get("transfer_fname", None)
        if thefile is not None:
            try:
                np.genfromtxt(thefile)
            except Exception:
                raise forms.ValidationError(
                    "Uploaded transfer file is of the wrong format"
                )
        return thefile


class TransferFramework(FrameworkForm):
    label = "Transfer Function"

    # Redshift at which to calculate the mass variance.
    z = forms.FloatField(
        label="Redshift", initial=str(DEFAULT_MODEL["z"]), min_value=0, max_value=1100
    )

    # Power spectral index
    n = forms.FloatField(
        label=mark_safe("n<sub>s</sub> "),
        initial=f"{DEFAULT_MODEL['n']}",
        min_value=-4,
        max_value=3,
        help_text="Spectral Index (note: modified by Base Cosmology)",
    )

    # Mass variance on a scale of 8Mpc
    sigma_8 = forms.FloatField(
        label=mark_safe("&#963<sub>8</sub>"),
        initial=f"{DEFAULT_MODEL['sigma_8']}",
        min_value=0.1,
        help_text="RMS Mass Fluctuations (note: modified by Base Cosmology)",
    )

    lnk_range = RangeSliderField(
        label="lnk range",
        minimum=np.log(1e-10),
        maximum=np.log(2e6),
        initial=f"{DEFAULT_MODEL['lnk_min']} - {DEFAULT_MODEL['lnk_max']}",
        step=0.1,
    )

    dlnk = forms.FloatField(
        label="lnk Step Size", initial=0.05, min_value=0.005, max_value=0.5,
    )

    takahashi = forms.BooleanField(
        label="Use Takahashi (2012) nonlinear P(k)?", required=False
    )


class HMFForm(ComponentModelForm):
    choices = [
        ("PS", "Press-Schechter (1974)"),
        ("SMT", "Sheth-Mo-Tormen (2001)"),
        ("Jenkins", "Jenkins (2001)"),
        ("Reed03", "Reed (2003)"),
        ("Warren", "Warren (2006)"),
        ("Reed07", "Reed (2007)"),
        ("Peacock", "Peaock (2007)"),
        ("Tinker08", "Tinker (2008)"),
        ("Crocce", "Crocce (2010)"),
        ("Courtin", "Courtin (2010)"),
        ("Tinker10", "Tinker (2010)"),
        ("Bhattacharya", "Bhattacharya (2011)"),
        ("Angulo", "Angulo (2012)"),
        ("AnguloBound", "Angulo (Subhaloes) (2012)"),
        ("Watson_FoF", "Watson (FoF Universal) (2012)"),
        ("Watson", "Watson (Redshift Dependent) (2012)"),
        ("Behroozi", "Behroozi (Tinker Extension to High-z) (2013)"),
        ("Pillepich", "Pillepich (2010)"),
        ("Manera", "Manera (2010)"),
        ("Ishiyama", "Ishiyama (2015)"),
    ]
    module = fitting_functions


class FilterForm(ComponentModelForm):
    module = filters
    choices = [
        ("TopHat", "Top-hat"),
        ("Gaussian", "Gaussian"),
        ("SharpK", "Sharp-k"),
        ("SharpKEllipsoid", "Sharp-k with ellipsoidal correction"),
    ]


class MassFunctionFramework(FrameworkForm):
    label = "Mass Function"

    # Setting the initial here just has to correspond to the default TracerHaloModel.
    # If the value is updated, it will get automatically reflected in its descendent models.
    logm_range = RangeSliderField(
        label="Mass Range (log10)",
        minimum=0,
        maximum=20,
        initial=f"{DEFAULT_MODEL['Mmin']} - {DEFAULT_MODEL['Mmax']}",
        step=0.1,
    )

    dlog10m = forms.FloatField(
        label="Mass Resolution (log10)",
        min_value=0.005,
        max_value=1,
        initial=f"{DEFAULT_MODEL['dlog10m']}",
    )

    delta_c = forms.FloatField(
        label=mark_safe("&#948<sub>c</sub>"),
        initial=f"{DEFAULT_MODEL['delta_c']}",
        min_value=1,
        max_value=3,
    )


class MassDefinitionForm(ComponentModelForm):
    module = mass_definitions
    choices = [
        ("None", "Use native definition of mass function"),
        ("SOMean", "Spherical Overdensity wrt mean"),
        ("SOCritical", "Spherical Overdensity wrt critical"),
        ("SOVirial", "Virial Spherical Overdensity (Bryan and Norman)"),
        ("FOF", "Friends-of-Friends"),
    ]
    kind = "mdef"


class WDMAlterForm(ComponentModelForm):
    module = wdm
    choices = [
        ("None", "No recalibration"),
        ("Schneider12_vCDM", "Schneider (2012) recalibration of CDM"),
        ("Schneider12", "Schneider (2012) recalibration of WDM"),
        ("Lovell14", "Lovell (2014) recalibration of WDM"),
    ]
    label = "WDM Recalibration"
    kind = "alter"

    def clean_alter_model(self):
        if self.cleaned_data["alter_model"] == "None":
            self.cleaned_data["alter_model"] = None


class WDMForm(ComponentModelForm):
    module = wdm
    choices = [("Viel05", "Viel (2005)")]


class WDMFramework(FrameworkForm):
    wdm_mass = forms.FloatField(
        label="WDM Particle Mass (keV)", initial=0, min_value=0, max_value=1000.0
    )


class BiasForm(ComponentModelForm):
    module = bias
    choices = [
        ("Tinker10", "Tinker (2010)"),
        ("UnityBias", "Unbiased"),
        ("Mo96", "Mo (1996)"),
        ("Jing98", "Jing (1998)"),
        ("ST99", "Sheth-Tormen (1999)"),
        ("SMT01", "Sheth-Mo-Tormen (2001)"),
        ("Seljak04", "Seljak (2004) Without Cosmo"),
        ("Seljak04Cosmo", "Seljak (2004) With Cosmo"),
        ("Mandelbaum05", "Mandelbaum (2005)"),
        ("Pillepich10", "Pillepich (2010)"),
        ("Manera10", "Manera (2010)"),
        ("Tinker10PBSplit", "Tinker (2010) Peak-Background Split"),
    ]
    field_kwargs = {"use_nu": {"label": r"Use $\nu$?"}}


class HaloConcentrationForm(ComponentModelForm):
    module = concentration
    choices = [
        ("Bullock01", "Bullock (2001) Physical Form"),
        ("Bullock01Power", "Bullock (2001) Power-Law"),
        ("Duffy08", "Duffy (2008) Power-Law"),
        ("Zehavi11", "Zehavi (2011) Power-Law"),
        ("Ludlow16", "Ludlow (2016)"),
        ("Ludlow16Empirical", "Ludlow (2016) Empirical"),
    ]

    field_kwargs = {"sample": {"choices": [("relaxed", "relaxed"), ("full", "full")]}}
    kind = "halo_concentration"


class FrameworkInput(CompositeForm):
    """Input parameters to the overall framework."""

    form_list = [
        MassFunctionFramework,
        CosmoForm,
        TransferForm,
        HMFForm,
        MassDefinitionForm,
        TransferFramework,
        FilterForm,
        GrowthForm,
        WDMFramework,
        WDMForm,
        WDMAlterForm,
        BiasForm,
        HaloConcentrationForm,
    ]

    label = forms.CharField(
        label="Label",
        initial="default",
        help_text="A name for the model",
        max_length=25,
    )

    def __init__(
        self, model_label=None, current_models=None, edit=False, *args, **kwargs
    ):

        self.current_models = current_models
        self.derivative_model_label = model_label
        if current_models:
            self.derivative_model = current_models.get(model_label, None)
        else:
            self.derivative_model = None
        self.edit = edit

        super().__init__(*args, **kwargs)

        # Add form.modules to fields (useful for getting which ones are necessary)
        for form in self.forms:
            if not hasattr(form, "module"):
                continue

            for field in form.fields:
                self.fields[field].module = form.module

        # If this is not an edit, we can't use the same label!
        if not edit and model_label:
            self.fields["label"].initial = model_label + "-new"

        self.helper = FormHelper()
        self.helper.form_id = "input_form"
        self.helper.form_class = "form-horizontal"
        self.helper.form_method = "post"

        self.helper.help_text_inline = True
        self.helper.label_class = "col-3 control-label"
        self.helper.field_class = "col-8"

        self.helper.layout = Layout(
            Div(
                Div("label", css_class="col"),
                Div(
                    HTML(  # use HTML for button, to get icon in there :-)
                        '<button type="submit" class="btn btn-primary">'
                        '<i class="fas fa-calculator"></i> Calculate'
                        "</button>"
                    ),
                    css_class="col",
                ),
                Div(
                    HTML(  # use HTML for button, to get icon in there :-)
                        '<a class="btn btn-warning" href="../..">'
                        '<i class="fas fa-ban"></i> Cancel</a>'
                    ),
                    css_class="col",
                ),
                css_class="row",
            ),
            TabHolder(*[form._layout for form in self.forms]),
        )
        self.helper.form_action = ""

    def clean_label(self):
        label = self.cleaned_data["label"]
        label = label.replace("_", "-")

        if not self.edit and self.current_models and label in self.current_models:
            raise forms.ValidationError("Label must be unique")
        return label

    def clean(self):
        """
        Clean the form for things that need to be cross-referenced between fields.
        """
        cleaned_data = super().clean()

        # Check k limits
        krange = cleaned_data.get("lnk_range")
        dlnk = cleaned_data.get("dlnk")

        if dlnk > (float(krange[1]) - float(krange[0])) / 2:
            raise forms.ValidationError(
                "Wavenumber step-size must be less than the k-range."
            )

        # Check mass limits
        mrange = cleaned_data.get("logm_range")
        dlogm = cleaned_data.get("dlog10m")
        if dlogm > (float(mrange[1]) - float(mrange[0])) / 2:
            raise forms.ValidationError("Mass step-size must be less than its range.")

        return cleaned_data


class PlotChoice(forms.Form):
    def __init__(self, request, *args, **kwargs):
        super(PlotChoice, self).__init__(*args, **kwargs)
        # Add in extra plot choices if they are required by the form in the session.
        # There have been a lot of errors coming through here -- not really sure why,
        # probably something to do with a session dying or something. I'm just wrapping
        # it in a try-except block for now so that people don't get errors at least.

        objects = request.session["objects"]

        plot_choices = [
            ("dndm", "dn/dm"),
            ("dndlnm", "dn/dln(m)"),
            ("dndlog10m", "dn/dlog10(m)"),
            ("fsigma", mark_safe("f(&#963)")),
            ("sigma", mark_safe("&#963 (mass variance)")),
            ("lnsigma", mark_safe("ln(1/&#963)")),
            ("n_eff", "Effective Spectral Index"),
            ("ngtm", "n(>m)"),
            ("rho_ltm", mark_safe("&#961(&#60m)")),
            ("rho_gtm", mark_safe("&#961(>m)")),
            ("transfer_function", "Transfer Function"),
            ("power", "Power Spectrum"),
            ("delta_k", "Dimensionless Power Spectrum"),
            # Halo Model
            ("halo_bias", "Halo Bias"),
            ("cmz_relation", "Halo Concentration-Mass Relation"),
            ("corr_2h_auto_tracer", "2-halo tracer-tracer correlation function"),
            ("corr_auto_tracer", "Tracer-tracer correlation function"),
            ("power_2h_auto_matter", "2-halo matter-matter power spectrum"),
            ("power_1h_auto_matter", "1-halo matter-matter power spectrum"),
            ("corr_linear_mm", "Linear matter correlation function"),
            ("total_occupation", "Tracer occupation"),
            ("corr_1h_auto_tracer", "1-halo tracer-tracer correlation function"),
            ("sd_bias_correction", "Scale-dependent bias correction"),
            ("central_occupation", "Occupation of central component"),
            ("satellite_occupation", "Occupation of satellite component"),
            ("corr_1h_auto_matter", "1-halo matter-matter correlation function"),
            (
                "corr_1h_cross_tracer_matter",
                "1-halo matter-tracer correlation function",
            ),
            (
                "corr_1h_cs_auto_tracer",
                "1-halo central-satellite tracer correlation function",
            ),
            (
                "corr_1h_ss_auto_tracer",
                "1-halo satellite-satellite tracer correlation function",
            ),
            ("corr_2h_auto_matter", "2-halo matter-matter correlation function"),
            (
                "corr_2h_cross_tracer_matter",
                "2-halo matter-tracer correlation function",
            ),
            ("corr_auto_matter", "Matter-matter correlation function"),
            ("corr_cross_tracer_matter", "Matter-tracer correlation function"),
            # ("halo_profile_rho", )
            ("nonlinear_delta_k", "Non-linear dimensionless power spectrum (HALOFIT)"),
            ("nonlinear_power", "Non-linear power spectrum (HALOFIT)"),
            ("power_1h_auto_tracer", "2-halo tracer-tracer power spectrum"),
            ("power_1h_cross_tracer_matter", "1-halo tracer-matter power spectrum"),
            (
                "power_1h_cs_auto_tracer",
                "1-halo central-satellite tracer power spectrum",
            ),
            (
                "power_1h_ss_auto_tracer",
                "1-halo satellite-satellite tracer power spectrum",
            ),
            ("power_2h_auto_tracer", "2-halo tracer-tracer power spectrum"),
            ("power_2h_cross_tracer_matter", "2-halo matter-tracer power spectrum"),
            ("power_auto_tracer", "Tracer power spectrum"),
            ("power_cross_tracer_matter", "Matter-tracer power spectrum"),
            ("radii", "Radii of spherical regions"),
            ("tracer_concentration", "Tracer conentration-mass relation"),
        ]

        if len(objects) > 1:
            show_comps = True
            for i, o in enumerate(objects.values()):
                if i == 0:
                    comp_obj = o
                else:
                    if (
                        o.Mmin != comp_obj.Mmin
                        or o.Mmax != comp_obj.Mmax
                        or len(o.m) != len(comp_obj.m)
                    ):
                        show_comps = False

            if show_comps:
                plot_choices += [
                    ("comparison_dndm", "Comparison of Mass Functions"),
                    ("comparison_fsigma", "Comparison of Fitting Functions"),
                ]

        self.fields["plot_choice"] = forms.ChoiceField(
            label="Plot: ",
            choices=plot_choices,
            initial="power_auto_tracer",
            required=False,
        )

        self.helper = FormHelper()
        self.helper.form_id = "plotchoiceform"
        self.helper.form_class = "form-horizontal"
        self.helper.form_method = "post"
        self.helper.form_action = ""
        self.helper.help_text_inline = True
        self.helper.label_class = "col-md-3 control-label"
        self.helper.field_class = "col-md-8"
        self.helper.layout = Layout(
            Div("plot_choice", "download_choice", css_class="col-md-6")
        )

    download_choices = [
        ("pdf-current", "PDF of Current Plot"),
        # ("pdf-all", "PDF's of All Plots"),
        ("ASCII", "All ASCII data"),
        ("parameters", "List of parameter values"),
        ("halogen", "HALOgen-ready input"),
    ]

    download_choice = forms.ChoiceField(
        label=mark_safe(
            '<a href="power_auto_tracer.pdf" id="plot_download">Download </a>'
        ),
        choices=download_choices,
        initial="pdf-current",
        required=False,
    )


class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super(ContactForm, self).__init__(*args, **kwargs)
