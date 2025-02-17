# -*- coding: utf-8 -*-

from myapps.s03.views._global import *

from myapps.s03.lib.accounts import *

class View(GlobalView):

    def dispatch(self, request, *args, **kwargs):

        response = super().pre_dispatch(request, *args, **kwargs)
        if response: return response

        self.selected_menu = "planet"

        self.showHeader = True

        e_no_error = 0
        self.e_rename_bad_name = 1

        self.planet_error = e_no_error

        if request.POST.get("action") == "assigncommander":
            if ToInt(request.POST.get("commander"), 0) != 0: # assign selected commander
                query = "SELECT * FROM sp_commanders_assign(" + str(self.UserId) + "," + str(ToInt(request.POST.get("commander"), 0)) + "," + str(self.CurrentPlanet) + ",null)"
                oConnDoQuery(query)
            else:
                # unassign current planet commander
                query = "UPDATE nav_planet SET commanderid=null WHERE ownerid=" + str(self.UserId) + " AND id=" + str(self.CurrentPlanet)
                oConnDoQuery(query)

        elif request.POST.get("action") == "rename":
            if not isValidObjectName(request.POST.get("name")):
                self.planet_error = self.e_rename_bad_name
            else:
                query = "UPDATE nav_planet SET name=" + dosql(request.POST.get("name")) + \
                        " WHERE ownerid=" + str(self.UserId) + " AND id=" + str(self.CurrentPlanet)

                oConnDoQuery(query)

                self.InvalidatePlanetList()

        elif request.POST.get("action") == "firescientists":
            amount = ToInt(request.POST.get("amount"), 0)
            oConnExecute("SELECT sp_dismiss_staff(" + str(self.UserId) + "," + str(self.CurrentPlanet) + "," + str(amount) + ",0,0)")
        elif request.POST.get("action") == "firesoldiers":
            amount = ToInt(request.POST.get("amount"), 0)
            oConnExecute("SELECT sp_dismiss_staff(" + str(self.UserId) + "," + str(self.CurrentPlanet) + "," + "0," + str(amount) + ",0)")
        elif request.POST.get("action") == "fireworkers":
            amount = ToInt(request.POST.get("amount"), 0)
            oConnExecute("SELECT sp_dismiss_staff(" + str(self.UserId) + "," + str(self.CurrentPlanet) + "," + "0,0," + str(amount) + ")")

        elif request.POST.get("action") == "abandon":
            oConnExecute("SELECT sp_abandon_planet(" + str(self.UserId) + "," + str(self.CurrentPlanet) + ")")
            self.InvalidatePlanetList()
            return HttpResponseRedirect("/s03/overview/")

        elif request.POST.get("action") == "resources_price":
            query = "UPDATE nav_planet SET" + \
                    " buy_ore = GREATEST(0, LEAST(1000, " + str(ToInt(request.POST.get("buy_ore"), 0)) + "))" + \
                    " ,buy_hydrocarbon = GREATEST(0, LEAST(1000, " + str(ToInt(request.POST.get("buy_hydrocarbon"), 0)) + "))" + \
                    " WHERE ownerid=" + str(self.UserId) + " AND id=" + str(self.CurrentPlanet)
            oConnDoQuery(query)

        if request.GET.get("a") == "suspend":
            oConnExecute("SELECT sp_update_planet_production(" + str(self.CurrentPlanet) + ")")
            oConnDoQuery("UPDATE nav_planet SET mod_production_workers=0, recruit_workers=False WHERE ownerid=" + str(self.UserId) + " AND id=" + str(self.CurrentPlanet) )
        elif request.GET.get("a")== "resume":
            oConnDoQuery("UPDATE nav_planet SET recruit_workers=True WHERE ownerid=" + str(self.UserId) + " AND id=" + str(self.CurrentPlanet) )
            oConnExecute("SELECT sp_update_planet(" + str(self.CurrentPlanet) + ")")

        return self.DisplayPlanet()

    def DisplayPlanet(self):

        content = GetTemplate(self.request, "s03/planet")

        CmdReq=""

        query = "SELECT id, name, galaxy, sector, planet, " + \
                "floor_occupied, floor, space_occupied, space, workers, workers_capacity, mod_production_workers," + \
                "scientists, scientists_capacity, soldiers, soldiers_capacity, commanderid, recruit_workers," + \
                "planet_floor, COALESCE(buy_ore, 0), COALESCE(buy_hydrocarbon, 0)" + \
                " FROM vw_planets WHERE id=" + str(self.CurrentPlanet)

        oRs = oConnExecute(query)

        if oRs:
            content.AssignValue("planet_id", oRs[0])
            content.AssignValue("planet_name", oRs[1])
            content.AssignValue("planet_img", self.planetimg(oRs[0], oRs[18]))

            content.AssignValue("pla_g", oRs[2])
            content.AssignValue("pla_s", oRs[3])
            content.AssignValue("pla_p", oRs[4])

            content.AssignValue("floor_occupied", oRs[5])
            content.AssignValue("floor", oRs[6])

            content.AssignValue("space_occupied", oRs[7])
            content.AssignValue("space", oRs[8])

            content.AssignValue("workers", oRs[9])
            content.AssignValue("workers_capacity", oRs[10])

            content.AssignValue("scientists", oRs[12])
            content.AssignValue("scientists_capacity", oRs[13])

            content.AssignValue("soldiers", oRs[14])
            content.AssignValue("soldiers_capacity", oRs[15])

            content.AssignValue("growth", oRs[11]/10)

            if oRs[17]:
                content.Parse("suspend")
            else:
                content.Parse("resume")

            content.AssignValue("buy_ore", oRs[19])
            content.AssignValue("buy_hydrocarbon", oRs[20])

            # retrieve commander assigned to this planet
            if oRs[16]:
                oCmdRs = oConnExecute("SELECT name FROM commanders WHERE ownerid="+str(self.UserId)+" AND id="+str(oRs[16]))
                content.AssignValue("commandername", oCmdRs[0])
                CmdId = oRs[16]
                content.Parse("commander")
            else:
                content.Parse("nocommander")
                CmdId = 0

        if CmdId == 0: # display "no commander" or "fire commander"
            content.Parse("none")
        else:
            content.Parse("unassign")

        # display commmanders

        query = " SELECT id, name, fleetname, planetname, fleetid " + \
                " FROM vw_commanders" + \
                " WHERE ownerid="+str(self.UserId) + \
                " ORDER BY fleetid IS NOT NULL, planetid IS NOT NULL, fleetid, planetid "
        oRss = oConnExecuteAll(query)

        lastItem = ""
        item = ""
        ShowGroup = False

        cmd_groups = []
        content.AssignValue("optgroups", cmd_groups)
        
        cmd_nones = {'typ':'none', 'cmds':[]}
        cmd_fleets = {'typ':'fleet', 'cmds':[]}
        cmd_planets = {'typ':'planet', 'cmds':[]}
        
        for oRs in oRss:
            item = {}

            if oRs[2] == None and oRs[3] == None:
                typ = "none"
                cmd_nones['cmds'].append(item)
            elif oRs[2] == None:
                typ = "planet"
                cmd_planets['cmds'].append(item)
            else:
                typ = "fleet"
                cmd_fleets['cmds'].append(item)

            if CmdId == oRs[0]: item["selected"] = True
            item["cmd_id"] = oRs[0]
            item["cmd_name"] = oRs[1]
            if typ == "planet":
                item["name"] = oRs[3]
                item["assigned"] = True

            if item == "fleet":
                item["name"] = oRs[2]
                activityRs = oConnExecute("SELECT dest_planetid, engaged, action FROM fleets WHERE ownerid="+str(self.UserId)+" AND id="+str(oRs[4]))
                if activityRs[0] == None and (not activityRs[1]) and activityRs[2]==0:
                    item["assigned"] = True
                else:
                    item["unavailable"] = True
                    
        if len(cmd_nones['cmds']) > 0: cmd_groups.append(cmd_nones)
        if len(cmd_fleets['cmds']) > 0: cmd_groups.append(cmd_fleets)
        if len(cmd_planets['cmds']) > 0: cmd_groups.append(cmd_planets)

        # view current buildings constructions
        query = "SELECT buildingid, remaining_time, destroying" + \
                " FROM vw_buildings_under_construction2 WHERE planetid="+str(self.CurrentPlanet) + \
                " ORDER BY remaining_time DESC"

        oRss = oConnExecuteAll(query)

        i = 0
        list = []
        content.AssignValue("buildings", list)
        for oRs in oRss:
            item = {}
            list.append(item)
            
            item["buildingid"] = oRs[0]
            item["building"] = getBuildingLabel(oRs[0])
            item["time"] = oRs[1]

            if oRs[2]: item["destroy"] = True

            i = i + 1

        if i==0: content.Parse("nobuilding")

        query = "SELECT shipid, remaining_time, recycle" + \
                " FROM vw_ships_under_construction" + \
                " WHERE ownerid=" + str(self.UserId) + " AND planetid=" + str(self.CurrentPlanet) + " AND end_time IS NOT NULL" + \
                " ORDER BY remaining_time DESC"

        # view current ships constructions
        oRss = oConnExecuteAll(query)

        i = 0

        list = []
        content.AssignValue("ships", list)
        for oRs in oRss:
            item = {}
            list.append(item)
            
            item["shipid"] = oRs[0]
            item["ship"] = getShipLabel(oRs[0])
            item["time"] = oRs[1]

            if oRs[2]: item["recycle"] = True

            i = i + 1

        if i==0: content.Parse("noship")

        # list the fleets near the planet
        query = "SELECT id, name, attackonsight, engaged, size, signature, commanderid, (SELECT name FROM commanders WHERE id=commanderid) as commandername," + \
                " action, sp_relation(ownerid, " + str(self.UserId) + ") AS relation, sp_get_user(ownerid) AS ownername" + \
                " FROM fleets" + \
                " WHERE action != -1 AND action != 1 AND planetid=" + str(self.CurrentPlanet) + \
                " ORDER BY upper(name)"

        oRss = oConnExecuteAll(query)

        i = 0

        list = []
        content.AssignValue("fleets", list)
        for oRs in oRss:
            item = {}
            list.append(item)
            
            item["id"] = oRs[0]
            item["size"] = oRs[4]
            item["signature"] = oRs[5]

            if oRs[9] > rFriend:
                item["name"] = oRs[1]
            else:
                item["name"] = oRs[10]

            if oRs[6]:
                item["commanderid"] = oRs[6]
                item["commandername"] = oRs[7]
                item["commander"] = True
            else:
                item["nocommander"] = True

            if oRs[3]:
                item["fighting"] = True
            elif oRs[8] == 2:
                item["recycling"] = True
            else:
                item["patrolling"] = True

            if oRs[9] in [rHostile, rWar]:
                item["enemy"] = True
            elif oRs[9] == rFriend:
                item["friend"] = True
            elif oRs[9] == rAlliance:
                item["ally"] = True
            elif oRs[9] == rSelf:
                item["owner"] = True

            i = i + 1

        if i==0: content.Parse("nofleet")

        if self.planet_error == self.e_rename_bad_name:
                content.Parse("rename_bad_name")

        content.Parse("ondev")

        return self.Display(content)
