"""All the forms on TheHaloMod"""

import logging

import hmf
import numpy as np
from crispy_forms.bootstrap import TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML, Field
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
from . import utils
from copy import copy

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
            localize=True,
        ),
        Ob0=forms.FloatField(
            label=mark_safe("&#937<sub>b</sub>"),
            initial=str(hmf.cosmo.Planck15.Ob0),
            min_value=0.005,
            max_value=0.65,
            localize=True,
        ),
        Om0=forms.FloatField(
            label=mark_safe("&#937<sub>m</sub>"),
            initial=str(hmf.cosmo.Planck15.Om0),
            min_value=0.02,
            max_value=2.0,
            localize=True,
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
        label="Redshift",
        initial=str(DEFAULT_MODEL["z"]),
        min_value=0,
        max_value=1100,
        localize=True,
    )

    # Power spectral index
    n = forms.FloatField(
        label=mark_safe("n<sub>s</sub> "),
        initial=f"{DEFAULT_MODEL['n']}",
        min_value=-4,
        max_value=3,
        help_text="Spectral Index",
        localize=True,
    )

    # Mass variance on a scale of 8Mpc
    sigma_8 = forms.FloatField(
        label=mark_safe("&#963<sub>8</sub>"),
        initial=f"{DEFAULT_MODEL['sigma_8']}",
        min_value=0.1,
        help_text="RMS Mass Fluctuations",
        localize=True,
    )

    lnk_range = RangeSliderField(
        label="lnk range",
        minimum=np.log(1e-10),
        maximum=np.log(2e6),
        initial=f"{DEFAULT_MODEL['lnk_min']} - {DEFAULT_MODEL['lnk_max']}",
        step=0.1,
    )

    dlnk = forms.FloatField(
        label="lnk Step Size",
        initial=0.05,
        min_value=0.005,
        max_value=0.5,
        localize=True,
    )

    takahashi = forms.BooleanField(
        label="Use Takahashi (2012) nonlinear P(k)?",
        required=False,
        initial=str(DEFAULT_MODEL["takahashi"]),
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
    label = "HMF"


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
        localize=True,
    )

    delta_c = forms.FloatField(
        label=mark_safe("&#948<sub>c</sub>"),
        initial=f"{DEFAULT_MODEL['delta_c']}",
        min_value=1,
        max_value=3,
        localize=True,
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
    label = "Mass Definition"


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
        label="WDM Particle Mass (keV)",
        initial=0,
        min_value=0,
        max_value=1000.0,
        localize=True,
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


class TracerConcentrationForm(HaloConcentrationForm):
    kind = "tracer_concentration"


class HaloProfileForm(ComponentModelForm):
    module = profiles
    choices = [
        ("NFW", "NFW (1997)"),
        ("Hernquist", "Hernquist"),
        ("Moore", "Moore"),
        ("GeneralizedNFW", "Generalized NFW"),
        ("Einasto", "Einasto"),
        ("CoredNFW", "Cored NFW"),
    ]
    kind = "halo_profile"


class TracerProfileForm(HaloProfileForm):
    kind = "tracer_profile"


class ExclusionForm(ComponentModelForm):
    module = halo_exclusion
    choices = [
        ("NoExclusion", "No Exclusion"),
        ("Sphere", "Spherical Halos"),
        ("DblSphere_", "Spherical Overlapping Halos"),
        ("DblEllipsoid_", "Ellipsoidal Haloes"),
        ("NgMatched_", "Density-Matched (Tinker 2005)"),
    ]
    label = "Halo Exclusion"


class HODForm(ComponentModelForm):
    module = hod
    choices = [
        ("Zehavi05", "Zehavi (3-param), 2005"),
        ("Zheng05", "Zheng (5-param), 2005"),
        ("Contreras13", "Contreras (9-param), 2013"),
        ("Geach12", "Geach (8-param), 2012"),
        ("Tinker05", "Tinker (3-param), 2005"),
        ("Zehavi05WithMax", "Zehavi (2005) with max"),
        ("Zehavi05Marked", "Zehavi (2005) dimensional"),
        ("ContinuousPowerLaw", "Continuous Power Law"),
        ("Constant", "Constant Occupancy"),
    ]


class TracerHaloModelFramework(FrameworkForm):
    label = "Halo Model"

    # Setting the initial here just has to correspond to the default TracerHaloModel.
    # If the value is updated, it will get automatically reflected in its descendent models.
    log_r_range = RangeSliderField(
        label="Scale Range (log10)",
        minimum=-3,
        maximum=3,
        initial=f"{np.log10(DEFAULT_MODEL['rmin'])} - {np.log10(DEFAULT_MODEL['rmax'])}",
        step=0.05,
    )

    rnum = forms.IntegerField(
        label="Number of r bins",
        min_value=5,
        max_value=100,
        initial=f"{DEFAULT_MODEL['rnum']}",
    )

    log_k_range = RangeSliderField(
        label="Wavenumber Range (log10)",
        minimum=-3,
        maximum=3,
        initial=f"{DEFAULT_MODEL['hm_logk_min']} - {DEFAULT_MODEL['hm_logk_max']}",
        step=0.05,
    )

    hm_dlog10k = forms.FloatField(
        label="Halo Model k bin size",
        min_value=0.01,
        max_value=1,
        initial=f"{DEFAULT_MODEL['hm_dlog10k']}",
        localize=True,
    )

    hc_spectrum = forms.ChoiceField(
        choices=[
            ("linear", "linear"),
            ("nonlinear", "nonlinear"),
            ("filtered-lin", "filtered linear"),
            ("filtered-nl", "filtered non-linear"),
        ],
        label="Halo Centre Spectrum",
        initial=str(DEFAULT_MODEL["hc_spectrum"]),
    )

    force_1halo_turnover = forms.BooleanField(
        label="Force 1-halo turnover?",
        required=False,
        initial=str(DEFAULT_MODEL["force_1halo_turnover"]),
    )


class FrameworkInput(CompositeForm):
    """Input parameters to the overall framework."""

    form_list = [
        CosmoForm,
        MassDefinitionForm,
        TransferForm,
        TransferFramework,
        FilterForm,
        GrowthForm,
        HMFForm,
        TracerHaloModelFramework,
        HODForm,
        MassFunctionFramework,
        BiasForm,
        HaloConcentrationForm,
        TracerConcentrationForm,
        HaloProfileForm,
        TracerProfileForm,
        ExclusionForm,
        WDMFramework,
        WDMForm,
        WDMAlterForm,
    ]

    label = forms.CharField(
        label="Label",
        initial="default",
        help_text="A name for the model",
        max_length=25,
    )

    def __init__(
        self, model_label=None, current_models=None, edit=False, *args, **kwargs,
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

        # Here we modify some of the tab layouts because they are more obvious this way.
        extras = {
            CosmoForm: ("z", "n", "sigma_8"),
            TransferForm: ("lnk_range", "dlnk", "takahashi"),
            HMFForm: ("logm_range", "dlog10m"),
            FilterForm: ("delta_c",),
            WDMForm: ("wdm_mass", WDMAlterForm),
        }
        omit = [TransferFramework, MassFunctionFramework, WDMFramework, WDMAlterForm]

        print(
            self.forms[self.form_list.index(WDMAlterForm)]._layout().fields[-1].fields
        )

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
            TabHolder(
                *[
                    form._layout(
                        extra=[
                            x
                            for x in extras.get(self.form_list[i], ())
                            if isinstance(x, str)
                        ],
                        appended_rows=[
                            self.forms[self.form_list.index(x)]._layout().fields[-1]
                            for x in extras.get(self.form_list[i], ())
                            if not isinstance(x, str)
                        ],
                    )
                    for i, form in enumerate(self.forms)
                    if self.form_list[i] not in omit
                ]
            ),
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

        cls, frmwk_dict = self.cleaned_data_to_framework_dict(cleaned_data)
        logger.info(f"Constructed hmf_dct: {frmwk_dict}")

        try:
            self.halomod_obj = utils.hmf_driver(
                previous=self.derivative_model, cls=cls, **frmwk_dict
            )
        except Exception as e:
            logger.info(f"cls={cls}, previous={self.derivative_model}")
            logger.error(f"Got form error: {e}")
            raise forms.ValidationError(str(e))

        self.halomod_cls = cls
        self.halomod_dct = frmwk_dict

        return cleaned_data

    def cleaned_data_to_framework_dict(self, cleaned_data):
        # get all the _params out
        out = {}
        for k, v in cleaned_data.items():
            # label is not a halo model argument
            if k == "label":
                continue
            elif k == "lnk_range":
                out["lnk_min"] = v[0]
                out["lnk_max"] = v[1]
                continue
            elif k == "logm_range":
                out["Mmin"] = v[0]
                out["Mmax"] = v[1]
                continue
            elif k == "log_r_range":
                out["rmin"] = 10 ** v[0]
                out["rmax"] = 10 ** v[1]
                continue
            elif k == "log_k_range":
                out["hm_logk_min"] = v[0]
                out["hm_logk_max"] = v[1]
                continue

            component = getattr(self.fields[k], "component", None)

            if component:
                form_model = cleaned_data[component + "_model"]
                # the model could be empty if component is, say, cosmo
                model = getattr(self.fields[k], "model", form_model)

                # Ignore params that don't belong to the chosen model
                if model != form_model:
                    continue

                dctkey = component + "_params"
                paramname = self.fields[k].paramname

                if dctkey not in out:
                    out[dctkey] = {paramname: v}
                else:
                    out[dctkey][paramname] = v
            else:
                out[k] = v

        if out["wdm_mass"] > 0:
            cls = hm_wdm.HaloModelWDM
        else:
            # Remove all WDM stuff
            # TODO: probably a better way about this.
            cls = TracerHaloModel
            del out["wdm_mass"]
            del out["wdm_model"]
            del out["wdm_params"]
            del out["alter_model"]

            # have to check because it won't be there if alter_model is None
            if "alter_params" in out:
                del out["alter_params"]

        return cls, out


class PlotChoice(forms.Form):
    plot_choices = [
        (
            "Mass Function",
            (
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
            ),
        ),
        (
            "Linear Structure",
            (
                ("transfer_function", "Transfer Function"),
                ("power", "Power Spectrum"),
                ("delta_k", "Dimensionless Power Spectrum"),
                (
                    "nonlinear_delta_k",
                    "Non-linear dimensionless power spectrum (HALOFIT)",
                ),
                ("nonlinear_power", "Non-linear power spectrum (HALOFIT)"),
                ("corr_linear_mm", "Linear matter correlation function"),
            ),
        ),
        (
            "Halos and HODs",
            (
                ("halo_bias", "Halo Bias"),
                ("cmz_relation", "Halo Concentration-Mass Relation"),
                ("total_occupation", "Tracer occupation"),
                ("central_occupation", "Occupation of central component"),
                ("satellite_occupation", "Occupation of satellite component"),
                ("radii", "Radii of spherical regions"),
                ("tracer_cmz_relation", "Tracer conentration-mass relation"),
            ),
        ),
        (
            "Halo Model Spectra",
            (
                # Matter power
                ("power_auto_matter", "Matter-matter power spectrum"),
                ("power_2h_auto_matter", "2-halo matter-matter power spectrum"),
                ("power_1h_auto_matter", "1-halo matter-matter power spectrum"),
                # Tracer Power
                ("power_auto_tracer", "Tracer power spectrum"),
                ("power_2h_auto_tracer", "2-halo tracer-tracer power spectrum"),
                ("power_1h_auto_tracer", "2-halo tracer-tracer power spectrum"),
                (
                    "power_1h_cs_auto_tracer",
                    "1-halo central-satellite tracer power spectrum",
                ),
                (
                    "power_1h_ss_auto_tracer",
                    "1-halo satellite-satellite tracer power spectrum",
                ),
                # Cross Power
                ("power_cross_tracer_matter", "Matter-tracer power spectrum"),
                (
                    "power_1h_cross_tracer_matter",
                    "1-halo tracer-matter power spectrum",
                ),
                (
                    "power_2h_cross_tracer_matter",
                    "2-halo matter-tracer power spectrum",
                ),
            ),
        ),
        (
            "Halo Model Correlations",
            (
                # Matter
                ("corr_auto_matter", "Matter-matter correlation function"),
                ("corr_2h_auto_matter", "2-halo matter-matter correlation function",),
                ("corr_1h_auto_matter", "1-halo matter-matter correlation function",),
                # Tracer
                ("corr_auto_tracer", "Tracer-tracer correlation function"),
                ("corr_2h_auto_tracer", "2-halo tracer-tracer correlation function",),
                ("corr_1h_auto_tracer", "1-halo tracer-tracer correlation function",),
                (
                    "corr_1h_cs_auto_tracer",
                    "1-halo central-satellite tracer correlation function",
                ),
                (
                    "corr_1h_ss_auto_tracer",
                    "1-halo satellite-satellite tracer correlation function",
                ),
                # Cross
                ("corr_cross_tracer_matter", "Matter-tracer correlation function"),
                (
                    "corr_1h_cross_tracer_matter",
                    "1-halo matter-tracer correlation function",
                ),
                (
                    "corr_2h_cross_tracer_matter",
                    "2-halo matter-tracer correlation function",
                ),
                ("sd_bias_correction", "Scale-dependent bias correction"),
            ),
        ),
    ]

    def __init__(self, request, *args, **kwargs):
        super(PlotChoice, self).__init__(*args, **kwargs)
        # Add in extra plot choices if they are required by the form in the session.
        # There have been a lot of errors coming through here -- not really sure why,
        # probably something to do with a session dying or something. I'm just wrapping
        # it in a try-except block for now so that people don't get errors at least.

        objects = request.session["objects"]

        plot_choices = copy(self.plot_choices)
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
            '<a href="plot/power_auto_tracer.pdf" id="plot_download">Download </a>'
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
        super().__init__(*args, **kwargs)


class UserErrorForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)
    name = forms.CharField(required=False, label_suffix="optional")
    email = forms.EmailField(required=False)

    def __init__(self, objects, current_quantity, model, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

        super().__init__(*args, **kwargs)

        self.fields["quantity"] = forms.MultipleChoiceField(
            label="Which quantities showed the problem?",
            choices=PlotChoice.plot_choices,
            initial=[current_quantity],
            required=False,
        )

        self.fields["models"] = forms.MultipleChoiceField(
            label="Models with Bugs",
            required=False,
            choices=list(zip(objects.keys(), objects.keys())),
            initial=[model],
        )

        self.helper.layout = Div(
            Div(Field("quantity")),
            Div(Field("models")),
            Div(Field("message")),
            Div(
                Div(Field("name"), css_class="mt-6 col"),
                Div(Field("email"), css_class="mt-6 col"),
                css_class="mt-12 row",
            ),
        )
