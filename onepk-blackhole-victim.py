#!/usr/bin/python

# Written by Patrick Ogenstad (@networklore)
# For more information visit:
# http://networklore.com/onepk-prank/

import sys
import argparse
import getpass



from onep.element.NetworkElement import NetworkElement
from onep.element.SessionConfig import SessionConfig
from onep.core.util import tlspinning

from onep.element import CLIListener
from onep.element import CLIEvent
from onep.element import CLIFilter
from onep.vty import VtyService

from onep.interfaces import NetworkPrefix
from onep.routing import AppRouteTable
from onep.routing import L3UnicastNextHop
from onep.routing import L3UnicastRouteOperation
from onep.routing import L3UnicastScope
from onep.routing import Routing
from onep.routing import L3UnicastRoute

class PinningHandler(tlspinning.TLSUnverifiedElementHandler):
    
    def __init__(self, pinning_file):
        self.pinning_file = pinning_file
        
    def handle_verify(self, host,hashtype, finger_print, changed):
    	return tlspinning.DecisionType.ACCEPT_ONCE


class MyCliListener(CLIListener):
    
    name = ''

    def __init__(self, name):        
        super(MyCliListener, self).__init__()
        self.name = name

    def handle_event(self,event,clientData):
    	
        print "-----"
        print "Caught: " + event.message
        print "-----"

        blackhole = False


        vtyService = VtyService(router)
        vtyService.open()
        TEST_CMD1 = "who";
        cli_result = vtyService.write(TEST_CMD1)
        vtyService.close()
        victim_string = " " + victim + " "
        
        lines = cli_result.split("\n")
        for line in lines:
            if " vty " and victim_string in line:
                print "-----"
                print "User is on the system: " + victim
                entries = line.split()
                for entry in entries:
                    if is_ip_address(entry):
                        blackhole = True
                        blackhole_ip = entry

        if blackhole:
            print "Blackholing ip: " + blackhole_ip
            out_if = router.get_interface_by_name("Null0")

            routing = Routing.get_instance(router)
            approutetable = routing.app_route_table
            route_scope = L3UnicastScope("", L3UnicastScope.AFIType.IPV4 , L3UnicastScope.SAFIType.UNICAST, "")
            aL3UnicastNextHop = L3UnicastNextHop(out_if, "")

            aL3UnicastNextHopList = list()
            aL3UnicastNextHopList.append(aL3UnicastNextHop)

            
            destNetworkPrefix = NetworkPrefix(blackhole_ip, 32)

            aRoute = L3UnicastRoute(destNetworkPrefix, aL3UnicastNextHopList)
            aRoute.admin_distance = 1

            routeOperation = L3UnicastRouteOperation(0, aRoute)

            routeOperationList = list()
            routeOperationList.append(routeOperation)
            mylist = approutetable.update_routes(route_scope, routeOperationList)
        print "-----"
        print "Type a key to exit script"


def is_ip_address(ip_teststring):
    ip_octets = ip_teststring.split(".")

    try:
        o4 = int(ip_octets[3])
    except:
        return False

    return True
 


parser = argparse.ArgumentParser(description='''Used to black hole the\
        ip address of a specific user when he/she issues a specified command.''', epilog='''REMEMBER: With
        great power comes great responsibility.''')
parser.add_argument('-t', help="Target router")
parser.add_argument('-u', help="Your username")
parser.add_argument('-c', help="Command to trigger event on")
parser.add_argument('-v', help="The victims username")



args = parser.parse_args()


if args.t:
    host = args.t
else:
    print "You have to specify a target (-t)"
    sys.exit()

if args.u:
    user = args.u
else:
    print "You have to specify a user (-u)"
    sys.exit()

if args.c:
    command = args.c
else:
    print "You have to specify a command (-c)"
    sys.exit()

if args.v:
    victim = args.v
else:
    print "You have to specify a victim (-u)"
    sys.exit()


password = getpass.getpass("Please enter your password: ")

sc = SessionConfig(None)
sc.set_tls_pinning('', PinningHandler(''))
sc.transportMode = SessionConfig.SessionTransportMode.TLS

router = NetworkElement(host, 'App_Name')
router.connect(user, password, sc)
cliListener = MyCliListener("Prank Listener")
cliFilter = CLIFilter(command)
clientData = None 
eventHandle = router.add_cli_listener(cliListener, cliFilter, clientData)


print "-----"
print router
print "-----"
print "Waiting for command: " + command

try:
    print "-----"
    wait_for_it = raw_input("Type a key to exit script")
    router.remove_cli_listener(eventHandle)
    router.disconnect()
except KeyboardInterrupt:
    router.remove_cli_listener(eventHandle)
    router.disconnect()
