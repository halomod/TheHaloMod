from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("halomod_app/img/favicon.ico"), permanent=False
        ),
        name="favicon",
    ),
    path("create/", views.CalculatorInputCreate.as_view(), name="calculate"),
    path("create/<label>/", views.CalculatorInputCreate.as_view(), name="calculate",),
    path("edit/<label>/", views.CalculatorInputEdit.as_view(), name="calculate"),
    path("delete/<label>/", views.delete_plot, name="delete"),
    path("restart/", views.complete_reset, name="restart"),
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
    path("", views.ViewPlots.as_view(), name="image-page"),
    path("plot/<plottype>.<filetype>", views.plots, name="images"),
    path("download/allData.zip", views.data_output, name="data-output"),
    path("download/parameters.txt", views.header_txt, name="header-txt"),
    path("download/halogen.zip", views.halogen, name="halogen-output"),
    path("contact/", views.ContactFormView.as_view(), name="contact-email"),
    path("email-sent/", views.EmailSuccess.as_view(), name="email-success"),
    path("report/", views.UserErrorReport.as_view(), name="report_model"),
    path("report/<model>/", views.UserErrorReport.as_view(), name="report_model"),
    path("about/", views.about.as_view(), name="about"),

    # api
    path("api/", include(router.urls))
]
