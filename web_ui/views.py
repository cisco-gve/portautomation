from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import traceback
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from web_ui.controllers.apic import ApicController, SNAPSHOT_PATH
from django.utils.encoding import smart_str
from . import envs

PREFIX = "ssDeployer"


# ====================>>>>>>>> Utils <<<<<<<<====================
class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


# ====================>>>>>>>> Templates <<<<<<<<====================

def login(request):
    return render(request, 'web_app/login.html')


def index(request):
    return render(request, 'web_app/index.html')


def home(request):
    return render(request, 'web_app/home.html')


# ====================>>>>>>>> APIs <<<<<<<<====================
@csrf_exempt
def api_get_token(request):
    """
    Return an APIC token to be used by the web client
    :param request:
    :return:
    """
    if request.method == 'POST':
        try:

            # Parse the json
            payload = json.loads(request.body)
            apic = ApicController()
            apic.url = payload["apic"]["url"]
            request.session['apic_url'] = payload["apic"]["url"]
            payload["apic"]["token"] = apic.get_token(username=payload["apic"]["username"],
                                                      password=payload["apic"]["password"])

            return JSONResponse(payload)
        except Exception as e:
            print(traceback.print_exc())
            # return the error to web client
            return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
    else:
        return JSONResponse("Bad request. " + request.method + " is not supported", status=400)


@csrf_exempt
def api_pod(request):
    """
       Return a list of pods
       :param request:
       :return:
       """
    if 'HTTP_AUTHORIZATION' in request.META:
        apic_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        apic_url = request.META['HTTP_AUTHORIZATION'].split(' ')[2]
        if request.method == 'GET':
            try:
                apic = ApicController()
                apic.url = apic_url
                apic.token = apic_token
                pods = apic.getPods()
                return JSONResponse(pods)
            except Exception as e:
                print(traceback.print_exc())
                # return the error to web client
                return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
        else:
            return JSONResponse("Bad request. " + request.method + " is not supported", status=400)

    else:
        return JSONResponse("Bad request. HTTP_AUTHORIZATION header is required", status=400)


@csrf_exempt
def api_switch(request):
    """
       Return a list of switches
       :param request:
       :return:
       """
    if 'HTTP_AUTHORIZATION' in request.META:
        apic_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        apic_url = request.META['HTTP_AUTHORIZATION'].split(' ')[2]
        if request.method == 'POST':
            try:
                payload = json.loads(request.body)
                apic = ApicController()
                apic.url = apic_url
                apic.token = apic_token
                switches = apic.getLeafs(pod_dn=payload["pod"]["fabricPod"]["attributes"]["dn"])
                return JSONResponse(switches)
            except Exception as e:
                print(traceback.print_exc())
                # return the error to web client
                return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
        else:
            return JSONResponse("Bad request. " + request.method + " is not supported", status=400)
    else:
        return JSONResponse("Bad request. HTTP_AUTHORIZATION header is required", status=400)


@csrf_exempt
def api_interface(request):
    """
       Return a list of interfaces
       :param request:
       :return:
       """
    if 'HTTP_AUTHORIZATION' in request.META:
        apic_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        apic_url = request.META['HTTP_AUTHORIZATION'].split(' ')[2]
        if request.method == 'POST':
            try:
                payload = json.loads(request.body)
                apic = ApicController()
                apic.url = apic_url
                apic.token = apic_token
                interfaces = apic.getInterfaces(switch_dn=payload["switch"]["fabricNode"]["attributes"]["dn"])
                return JSONResponse(interfaces)
            except Exception as e:
                print(traceback.print_exc())
                # return the error to web client
                return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
        else:
            return JSONResponse("Bad request. " + request.method + " is not supported", status=400)
    else:
        return JSONResponse("Bad request. HTTP_AUTHORIZATION header is required", status=400)


@csrf_exempt
def api_epg(request):
    """
       Return a list of EPG for a given tenant
       :param request:
       :return:
       """
    if 'HTTP_AUTHORIZATION' in request.META:
        apic_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        apic_url = request.META['HTTP_AUTHORIZATION'].split(' ')[2]
        if request.method == 'GET':
            try:
                apic = ApicController()
                apic.url = apic_url
                apic.token = apic_token
                tenants = apic.getTenants(query_filter='eq(fvTenant.name,"' + PREFIX + '")')
                if len(tenants) == 0:
                    return JSONResponse([])
                aps = apic.getAppProfiles(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                          query_filter='eq(fvAp.name,"' + PREFIX + '")')
                if len(aps) == 0:
                    return JSONResponse([])
                epgs = apic.getEPGs(ap_dn=aps[0]["fvAp"]["attributes"]["dn"])
                return JSONResponse(epgs)
            except Exception as e:
                print(traceback.print_exc())
                # return the error to web client
                return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
        else:
            return JSONResponse("Bad request. " + request.method + " is not supported", status=400)
    else:
        return JSONResponse("Bad request. HTTP_AUTHORIZATION header is required", status=400)


@csrf_exempt
def api_deploy(request):
    """
   Creates if does not exist:
   - EPG
   - App Profile
   - BD
   - VRF
   - Tenant
   :param request:
   :return:
   """
    if 'HTTP_AUTHORIZATION' in request.META:
        apic_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        apic_url = request.META['HTTP_AUTHORIZATION'].split(' ')[2]
        if request.method == 'POST':
            try:
                payload = json.loads(request.body)
                apic = ApicController()
                apic.url = apic_url
                apic.token = apic_token

                print("Creating tenant if not present")
                tenants = apic.getTenants(query_filter='eq(fvTenant.name,"' + PREFIX + '")')
                if len(tenants) == 0:
                    tenants = apic.createTenant(PREFIX)

                print("Creating application profile if not present")
                aps = apic.getAppProfiles(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                          query_filter='eq(fvAp.name,"' + PREFIX + '")')
                if len(aps) == 0:
                    aps = apic.createAppProfile(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                                app_prof_name=PREFIX)

                print("Creating VRF if not present")
                vrfs = apic.getVRFs(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                    query_filter='eq(fvCtx.name,"' + PREFIX + '")')

                if len(vrfs) == 0:
                    vrfs = apic.createVRF(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                          vrf_name=PREFIX)

                print("Creating Bridge Domain if not present")
                bds = apic.getBridgeDomains(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                            query_filter='eq(fvBD.name,"' + PREFIX + '")')

                if len(bds) == 0:
                    bds = apic.createBridgeDomain(tenant_dn=tenants[0]["fvTenant"]["attributes"]["dn"],
                                                  bd_name=PREFIX,
                                                  vrf_name=vrfs[0]["fvCtx"]["attributes"]["name"])

                print("Creating Endpoint Group if not present")
                if payload["deployment"]["epgAction"] == "new":
                    epgName = payload["deployment"]["epgVlan"]
                else:
                    epgName = payload["deployment"]["selectedEpg"]["fvAEPg"]["attributes"]["name"]
                # Check if EPG already exists
                epgs = apic.getEPGs(ap_dn=aps[0]["fvAp"]["attributes"]["dn"],
                                    query_filter='eq(fvAEPg.name,"' + epgName + '")')
                if len(epgs) == 0:
                    # Create only if does not exist
                    epgs = apic.createEPG(ap_dn=aps[0]["fvAp"]["attributes"]["dn"],
                                          bridge_domain_name=bds[0]["fvBD"]["attributes"]["name"],
                                          epg_name=epgName)

                print("Creating VLAN Pool if not present")
                vpools = apic.getVlanPools(query_filter='eq(fvnsVlanInstP.name,"' + PREFIX + '")')

                if len(vpools) == 0:
                    # Create vlan pool
                    vpools = apic.createVlanPool(name=PREFIX)

                print("Add selected VLANs to pool if not present")
                apic.addVlansToPool(pool_name=vpools[0]["fvnsVlanInstP"]["attributes"]["name"],
                                    from_vlan=epgName, to_vlan=epgName)

                print("Creating Physical Domain if not present")
                phyDoms = apic.getPhysicalDomains(query_filter='eq(physDomP.name,"' + PREFIX + '")')
                if len(phyDoms) == 0:
                    phyDoms = apic.createPhysicalDomain(name=PREFIX,
                                                        vlan_pool_dn=vpools[0]["fvnsVlanInstP"]["attributes"]["dn"])

                print("Creating Attachable Entity Profile if not present")
                atthEntProfiles = apic.getAttachEntityProfile(query_filter='eq(infraAttEntityP.name,"' + PREFIX + '")')
                if len(atthEntProfiles) == 0:
                    atthEntProfiles = apic.createAttachEntityProfile(name=PREFIX,
                                                                     phy_domain_dn=phyDoms[0]["physDomP"]["attributes"][
                                                                         "dn"])
                port1 = payload["deployment"]["selectedInterface1"]["l1PhysIf"]["attributes"]["id"].replace(
                    "eth1/", "")

                leaf1_id = payload["deployment"]["selectedSwitch1"]["fabricNode"]["attributes"]["id"]

                if payload["deployment"]["portType"] == "access":
                    # ## Access ##
                    # Create Policy Group default options with attachable entity profile
                    print("**** Deployment Port Type: Access *****")
                    intPolGroups = apic.createAccessInterfacePolicyGroup(
                        name=PREFIX + "-access",
                        attEntPro_dn=atthEntProfiles[0]["infraAttEntityP"]["attributes"]["dn"])

                    print("Creating Interface Policy if not present")
                    # Create access interface policy
                    intAccessProfiles = apic.createAccessInterfaceProfile(name=PREFIX + "-access-" + port1)

                    print("Creating Interface Selector if not present")
                    # Add selected port
                    apic.createInterfaceSelector(
                        name=payload["deployment"]["selectedInterface1"]["l1PhysIf"]["attributes"]["id"].replace(
                            "/", "-"),
                        from_port=port1,
                        to_port=port1,
                        interface_profile_dn=intAccessProfiles[0]["infraAccPortP"]["attributes"]["dn"],
                        interface_policy_group_dn=intPolGroups[0]["infraAccPortGrp"]["attributes"]["dn"])

                    print("Creating Switch Profile if not present")
                    # Create switch profile
                    sProfile = apic.createSwitchProfile(name=PREFIX, leaf_id=leaf1_id)

                    print("Associating interface profiles to switch profile if not present")
                    # Associate interface profiles to switch profile sw_prof_dn, int_prof_dn
                    apic.associateIntProfToSwProf(
                        sw_prof_dn=sProfile["infraNodeP"]["attributes"]["dn"],
                        int_prof_dn=intAccessProfiles[0]["infraAccPortP"]["attributes"]["dn"])

                    print("Associating port to EPG if not present")
                    # Associate port to EPG
                    apic.addStaticPortToEpg(
                        vlan=epgName,
                        leaf_id=leaf1_id,
                        port_id=payload["deployment"]["selectedInterface1"]["l1PhysIf"]["attributes"]["id"],
                        epg_dn=epgs[0]["fvAEPg"]["attributes"]["dn"])

                elif payload["deployment"]["portType"] == "portChannel":

                    print("**** Deployment Port Type: PortChannel *****")
                    # ## Port Channel ##
                    port2 = payload["deployment"]["selectedInterface2"]["l1PhysIf"]["attributes"]["id"].replace(
                        "eth1/", "")

                    print("Creating LACP Profile if not present")
                    # make sure lacp_profile exists
                    lapc_prof = apic.addLacpProf(name=PREFIX + '-LACP-ACTIVE')

                    print("Creating port channel policy group if not present")
                    # make sure portchannel policy group exists
                    portchannel_policy = apic.addPortchannelIntPolicyGroup(
                        name=PREFIX + '-portchannel',
                        att_ent_prof_dn=atthEntProfiles[0]["infraAttEntityP"]["attributes"]["dn"],
                        lacp_prof_name=lapc_prof["lacpLagPol"]["attributes"]["name"])

                    print("Creating port channel profile if not present")
                    # make sure portchannel profile exists for port 1
                    portchannel_profile = apic.addPortchannelIntProfile(
                        name=PREFIX + '-portchannel-' + port1 + '-' + port2)

                    print("Creating Interface Selector for interfaces if not present")
                    # Add selected port1
                    apic.createInterfaceSelector(
                        name=payload["deployment"]["selectedInterface1"]["l1PhysIf"]["attributes"]["id"].replace(
                            "/", "-"),
                        from_port=port1,
                        to_port=port1,
                        interface_profile_dn=portchannel_profile["infraAccPortP"]["attributes"]["dn"],
                        interface_policy_group_dn=portchannel_policy["infraAccBndlGrp"]["attributes"]["dn"])

                    # Add selected port2
                    apic.createInterfaceSelector(
                        name=payload["deployment"]["selectedInterface2"]["l1PhysIf"]["attributes"]["id"].replace(
                            "/", "-"),
                        from_port=port2,
                        to_port=port2,
                        interface_profile_dn=portchannel_profile["infraAccPortP"]["attributes"]["dn"],
                        interface_policy_group_dn=portchannel_policy["infraAccBndlGrp"]["attributes"]["dn"])

                    print("Creating Switch Profile if not present")
                    # Create switch Profile
                    sProfile = apic.createSwitchProfile(name=PREFIX, leaf_id=leaf1_id)

                    print("Associating interface profiles to switch profile if not present")
                    # Associate interface profiles to switch profile sw_prof_dn, int_prof_dn
                    apic.associateIntProfToSwProf(
                        sw_prof_dn=sProfile["infraNodeP"]["attributes"]["dn"],
                        int_prof_dn=portchannel_profile["infraAccPortP"]["attributes"]["dn"])

                    print("Associating port to EPG if not present")
                    # Associate port to EPG
                    apic.addStaticPortchannelToEpg(
                        vlan=epgName,
                        leaf_id=leaf1_id,
                        portchannel_pol_grp_name=portchannel_policy["infraAccBndlGrp"]["attributes"]["name"],
                        epg_dn=epgs[0]["fvAEPg"]["attributes"]["dn"])

                print("Deployment Done!")
                return JSONResponse("ok")
            except Exception as e:
                print(traceback.print_exc())
                # return the error to web client
                return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
        else:
            return JSONResponse("Bad request. " + request.method + " is not supported", status=400)
    else:
        return JSONResponse("Bad request. HTTP_AUTHORIZATION header is required", status=400)


def downloads(request, file_name):
    """
    Downloads a requested file
    :param request:
    :param file_name:
    :return:
    """
    try:
        response = HttpResponse(
            content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name + '.txt')
        with open(SNAPSHOT_PATH + "/" + file_name, 'r') as config_file:
            data = config_file.read()
            response.write(data)
        return response
    except Exception as e:
        # return the error to web client
        return JSONResponse({'error': e.__class__.__name__, 'message': str(e)}, status=500)
