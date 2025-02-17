# -*- coding: utf-8 -*-

from myapps.s03.views._global import *

class View(GlobalView):

    def dispatch(self, request, *args, **kwargs):

        response = super().pre_dispatch(request, *args, **kwargs)
        if response: return response

        self.selected_menu = "invasion"

        invasionid = ToInt(request.GET.get("id"), 0)

        if invasionid == 0:
            return HttpResponseRedirect("/s03/overview/")

        self.fleetid = ToInt(request.GET.get("fleetid"), 0)

        return self.DisplayReport(invasionid, self.UserId)

    def DisplayReport(self, invasionid, readerid):

        content = GetTemplate(self.request, "s03/invasion")

        query = "SELECT i.id, i.time, i.planet_id, i.planet_name, i.attacker_name, i.defender_name, " + \
                "i.attacker_succeeded, i.soldiers_total, i.soldiers_lost, i.def_soldiers_total, " + \
                "i.def_soldiers_lost, i.def_scientists_total, i.def_scientists_lost, i.def_workers_total, " + \
                "i.def_workers_lost, galaxy, sector, planet, sp_get_user("+str(readerid)+") " + \
                "FROM invasions AS i INNER JOIN nav_planet ON nav_planet.id = i.planet_id WHERE i.id = "+str(invasionid)
        oRs = oConnExecute(query)

        if oRs == None:
            return HttpResponseRedirect("/s03/overview/")

        viewername = oRs[18]

        # compare the attacker name and defender name with the name of who is reading this report
        if oRs[4] != viewername and oRs[5] != viewername and self.AllianceId:
            # if we are not the attacker or defender, check if we can view this invasion as a member of our alliance of we are ambassador
            if self.oAllianceRights["can_see_reports"]:
                # find the name of the member that did this invasion, either the attacker or the defender
                query = "SELECT username" + \
                        " FROM users" + \
                        " WHERE (username="+dosql(oRs[4])+" OR username="+dosql(oRs[5])+") AND alliance_id="+str(self.AllianceId)+" AND alliance_joined <= (SELECT time FROM invasions WHERE id="+str(invasionid)+")"
                oRs2 = oConnExecute(query)
                if oRs2 == None:
                    return HttpResponseRedirect("/s03/overview/")
                viewername = oRs2[0]
            else:
                return HttpResponseRedirect("/s03/overview/")

        content.AssignValue("planetid", oRs[2])
        content.AssignValue("planetname", oRs[3])
        content.AssignValue("g", oRs[15])
        content.AssignValue("s", oRs[16])
        content.AssignValue("p", oRs[17])
        content.AssignValue("planet_owner", oRs[5])
        content.AssignValue("fleet_owner", oRs[4])
        content.AssignValue("date", oRs[1])
        content.AssignValue("soldiers_total", oRs[7])
        content.AssignValue("soldiers_lost", oRs[8])
        content.AssignValue("soldiers_alive", oRs[7] - oRs[8])
        content.AssignValue("def_soldiers_total", oRs[9])
        content.AssignValue("def_soldiers_lost", oRs[10])
        content.AssignValue("def_soldiers_alive", oRs[9] - oRs[10])
        def_total = oRs[9]
        def_losts = oRs[10]

        if oRs[4] == viewername: #we are the attacker
            content.AssignValue("relation", rWar)
            # display only troops encountered by the attacker's soldiers
            if oRs[9]-oRs[10] == 0:
                # if no workers remain, display the scientists
                if oRs[13]-oRs[14] == 0:
                    def_total = def_total + oRs[11]
                    def_losts = def_losts + oRs[12]
                    content.AssignValue("def_scientists_total", oRs[11])
                    content.AssignValue("def_scientists_lost", oRs[12])
                    content.AssignValue("def_scientists_alive", oRs[11] - oRs[12])
                    content.Parse("scientists")

                # if no soldiers remain, display the workers
                def_total = def_total + oRs[13]
                def_losts = def_losts + oRs[14]
                content.AssignValue("def_workers_total", oRs[13])
                content.AssignValue("def_workers_lost", oRs[14])
                content.AssignValue("def_workers_alive", oRs[13] - oRs[14])
                content.Parse("workers")

            content.AssignValue("planetname", oRs[5])

            content.AssignValue("def_alive", def_total - def_losts)
            content.AssignValue("def_total", def_total)
            content.AssignValue("def_losts", def_losts)

            content.Parse("ally")
            content.Parse("attacker")
            content.Parse("enemy")
            content.Parse("defender")
        else: # ...we are the defender
            content.AssignValue("relation", rFriend)
            def_total = def_total + oRs[11]
            def_losts = def_losts + oRs[12]
            content.AssignValue("def_scientists_total", oRs[11])
            content.AssignValue("def_scientists_lost", oRs[12])
            content.AssignValue("def_scientists_alive", oRs[11] - oRs[12])
            content.Parse("scientists")
            def_total = def_total + oRs[13]
            def_losts = def_losts + oRs[14]
            content.AssignValue("def_workers_total", oRs[13])
            content.AssignValue("def_workers_lost", oRs[14])
            content.AssignValue("def_workers_alive", oRs[13] - oRs[14])
            content.Parse("workers")

            content.AssignValue("def_alive", def_total - def_losts)
            content.AssignValue("def_total", def_total)
            content.AssignValue("def_losts", def_losts)

            content.Parse("ally")
            content.Parse("defender")
            content.Parse("enemy")
            content.Parse("attacker")

        if self.fleetid != 0:
            # if a fleetid is specified, parse a link to redirect the user to the fleet
            content.AssignValue("fleetid", self.fleetid)
            content.Parse("justdone")

        if oRs[6]:
            content.Parse("succeeded")
        else:
            content.Parse("not_succeeded")

        content.Parse("report")
        content.Parse("invasion_report")

        return self.Display(content)
