# -*- coding: utf-8 -*-

import re

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

from myapps.s03.lib.exile import *
from myapps.s03.lib.template import *

from myapps.s03.views.cache import *

class View(ExileMixin, View):

    def dispatch(self, request, *args, **kwargs):

        response = super().pre_dispatch(request, *args, **kwargs)
        if response: return response

        if maintenance and not request.user.is_superuser : return HttpResponseRedirect("/")

        self.UserId = ToInt(request.session.get(sUser), 0)
        if self.UserId == 0: return HttpResponseRedirect("/")

        action = request.GET.get("a")

        # change category of a fleet
        if action == "setcat":
            fleetid = ToInt(request.GET.get("id"), 0)
            oldCat = ToInt(request.GET.get("old"), 0)
            newCat = ToInt(request.GET.get("new"), 0)

            oRs = oConnExecute("SELECT sp_fleets_set_category(" + str(self.UserId) + "," + str(fleetid) + "," + str(oldCat) + "," + str(newCat) + ")")
            if oRs and oRs[0]:
                content = GetTemplate(self.request, "s03/fleets-handler")

                content.AssignValue("id", fleetid)
                content.AssignValue("old", oldCat)
                content.AssignValue("new", newCat)
                content.Parse("fleet_category_changed")

                return render(self.request, content.template, content.data)

        # create a new category
        if action == "newcat":
            name = request.GET.get("name")

            content = GetTemplate(self.request, "s03/fleets-handler")

            if self.isValidCategoryName(name):
                oRs = oConnExecute("SELECT sp_fleets_categories_add(" + str(self.UserId) + "," + dosql(name) + ")")

                if oRs:
                    content.AssignValue("id", oRs[0])
                    content.AssignValue("label", name)
                    content.Parse("category")

                    return render(self.request, content.template, content.data)

            else:
                content.Parse("category_name_invalid")

                return render(self.request, content.template, content.data)

        # rename a category
        if action == "rencat":
            name = request.GET.get("name")
            catid = ToInt(request.GET.get("id"), 0)

            content = GetTemplate(self.request, "s03/fleets-handler")

            if name == "":
                oRs = oConnExecute("SELECT sp_fleets_categories_delete(" + str(self.UserId) + "," + str(catid) + ")")
                if oRs:
                    content.AssignValue("id", catid)
                    content.AssignValue("label", name)
                    content.Parse("category")

                    return render(self.request, content.template, content.data)

            elif self.isValidCategoryName(name):
                oRs = oConnExecute("SELECT sp_fleets_categories_rename(" + str(self.UserId) + "," + str(catid) + "," + dosql(name) + ")")

                if oRs:
                    content.AssignValue("id", catid)
                    content.AssignValue("label", name)
                    content.Parse("category")

                    return render(self.request, content.template, content.data)

            else:
                content.Parse("category_name_invalid")

                return render(self.request, content.template, content.data)

    def getPlanetName(self, relation, radar_strength, ownerName, planetName):
        if relation == rSelf:
            return planetName
        elif relation == rAlliance:
            return ownerName
        elif relation == rFriend:
            return ownerName
        else:
            if radar_strength > 0:
                return ownerName if ownerName else ""
            else:
                return ""

    # return if the given name if valid for a fleet, a planet
    def isValidCategoryName(self, name):
        name = name.strip()

        if name == "" or len(name) < 2 or len(name) > 32:
            return False
        else:
            p = re.compile("^[a-zA-Z0-9\- ]+$")
            return p.match(name)
            