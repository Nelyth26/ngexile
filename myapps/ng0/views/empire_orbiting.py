from .base import *

class View(BaseView):

    def dispatch(self, request, *args, **kwargs):

        response = super().pre_dispatch(request, *args, **kwargs)
        if response: return response

        self.selectedMenu = "fleets"

        content = getTemplateContext(self.request, "empire-orbiting")

        query = "SELECT nav_planet.id, nav_planet.name, nav_planet.galaxy, nav_planet.sector, nav_planet.planet," + \
                " fleets.id, fleets.name, users.username, alliances.tag, sp_relation(fleets.ownerid, nav_planet.ownerid), fleets.signature" + \
                " FROM nav_planet" + \
                "    INNER JOIN fleets ON fleets.planetid=nav_planet.id" + \
                "    INNER JOIN users ON fleets.ownerid=users.id" + \
                "    LEFT JOIN alliances ON users.alliance_id=alliances.id" + \
                " WHERE nav_planet.ownerid=" + str(self.profile['id']) + " AND fleets.ownerid != nav_planet.ownerid AND action != 1 AND action != -1" + \
                " ORDER BY nav_planet.id, upper(alliances.tag), upper(fleets.name)"
        oRss = oConnExecuteAll(query)

        if oRss == None:
            content.parse("nofleets")
        else:
            lastplanetid=-1

            planets = []
            content.assignValue("planets", planets)
            
            for oRs in oRss:
                
                if oRs[0] != lastplanetid:
                    planet = { "fleets":[] }
                    planets.append(planet)
                    
                    planet["planetid"] = oRs[0]
                    planet["planetname"] = oRs[1]
                    planet["g"] = oRs[2]
                    planet["s"] = oRs[3]
                    planet["p"] = oRs[4]
                    
                    lastplanetid = oRs[0]

                item = {}
                planet["fleets"].append(item)

                if (oRs[8]):
                    item["tag"] = oRs[8]
                    item["alliance"] = True

                if oRs[9] == -1:
                    item["enemy"] = True
                elif oRs[9] == 0:
                    item["friend"] = True
                elif oRs[9] == 1:
                    item["ally"] = True

                item["fleetname"] = oRs[6]
                item["fleetowner"] = oRs[7]
                item["fleetsignature"] = oRs[10]

        return self.display(content)
