from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(
        r"favicon\.ico",
        RedirectView.as_view(url="http://hmfstatic.appspot.com/img/favicon.ico"),
    ),
    path("", views.home.as_view(), name="home"),
    path("halomod/create/", views.CalculatorInputCreate.as_view(), name="calculate"),
    path(
        "halomod/create/<label>/",
        views.CalculatorInputCreate.as_view(),
        name="calculate",
    ),
    path(
        "halomod/edit/<label>/", views.CalculatorInputEdit.as_view(), name="calculate"
    ),
    path("halomod/delete/<label>/", views.delete_plot, name="delete"),
    path("halomod/restart/", views.complete_reset, name="restart"),
    path("help/", views.help.as_view(), name="help"),
    # path(
    #     'hmf_resources/',
    #     views.resources.as_view(),
    #     name='resources'
    # ),
    # path(
    #     'hmf_acknowledgments/',
    #     views.acknowledgments.as_view(),
    #     name='acknowledgments'
    # ),
    path("halomod/", views.ViewPlots.as_view(), name="image-page"),
    path("halomod/<plottype>.<filetype>", views.plots, name="images"),
    path("halomod/download/allData.zip", views.data_output, name="data-output"),
    path("halomod/download/parameters.txt", views.header_txt, name="header-txt"),
    path("emailme/", views.ContactFormView.as_view(), name="contact-email"),
    path("email-sent/", views.EmailSuccess.as_view(), name="email-success"),
    path("halomod/download/halogen.zip", views.halogen, name="halogen-output"),
    path("halomod/report/", views.UserErrorReport.as_view(), name="report_model"),
]
