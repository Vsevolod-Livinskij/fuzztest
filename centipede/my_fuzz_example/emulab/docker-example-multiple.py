# Copied from https://www.emulab.net/portal/show-profile.php?project=PortalProfiles&profile=docker-lan-parameterized
# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the InstaGENI library.
import geni.rspec.igext as ig
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal object,
pc = portal.Context()

#
# Define a boatload of parameters.
#
pc.defineParameter(
    "vnodesPerPhost","Containers per Host",portal.ParameterType.INTEGER,1,
    longDescription="Number of containers per physical host.")
pc.defineParameter(
    "hosts","Physical Hosts",portal.ParameterType.INTEGER,1,
    longDescription="Number of physical hosts.  If 0, your containers will be allocated in shared mode instead of dedicated, if a shared container host is available.")
pc.defineParameter(
    "hostType","Physical Host Node Type",portal.ParameterType.NODETYPE,"",
    longDescription="Node type of physical host nodes.")
pc.defineParameter(
    "images","Container Images",portal.ParameterType.STRING,
    "urn:publicid:IDN+emulab.net+image+emulab-ops//docker-ubuntu18-std",
    longDescription="A list of images your containers will run, separated by whitespace.  If more than one, we will alternate through the list as we create containers.")
pc.defineParameter(
    "imageSource","Image Source",portal.ParameterType.STRING,
    'urn',[('urn','Testbed Image'),('external','External Repository'),
           ('dockerfile','Dockerfile')],
    longDescription="Specifies the type of image referenced by the images parameter; read the help for the image parameter!")
pc.defineParameter(
    "dockerTbAugmentation","Image Augmentation Level",
    portal.ParameterType.STRING,"core",
    [("default","Default"),("none","None"),("basic","Basic"),
     ("core","Core"),("buildenv","BuildEnv"),("full","Full")],
    longDescription="Your image will be augmented with testbed binaries and a simple init daemon to support the testbed per-node services, and other generally useful packages.  The value of this parameter determines how many modifications we will make to your image.  This value may be either none (no changes: no testbed binaries/services installed); basic (init, sshd, syslogd; no testbed binaries/services); core (basic + testbed binaries/services and dependencies); buildenv (core + build environment to rebuild testbed binaries); full (buildenv + packages to make the image as similar as possible to a normal testbed disk image).")
pc.defineParameter(
    "dockerTbAugmentationUpdate","Update Image Augmentation",
    portal.ParameterType.BOOLEAN,False,
    longDescription="If the image is already augmented, re-augment with the current testbed binaries/services.  You can increase the augmentation level; but you cannot decrease it.")
pc.defineParameter(
    "dockerSshStyle","SSH Style",portal.ParameterType.STRING,
    "default",[("default","Default"),("direct","Direct"),("exec","Exec")],
    longDescription="Specify what happens when you ssh to your node; may be direct or exec.  If your container is augmented > basic, and you do not specify this, it defaults to direct.  If your container is not augmented to that level and you do not specify this, it defaults to exec.  direct means that the container is running an sshd inside, and an incoming ssh connection will be handled by the container.  exec means that when you connection, sshd will exec a shell inside your container.  You can change that shell by specifying the docker_exec_shell value.")
pc.defineParameter(
    "dockerExecShell","Docker Exec Shell",portal.ParameterType.STRING,"",
    longDescription="The shell to run if your Docker ssh_style is direct; otherwise ignored")
pc.defineParameter(
    "startupCmd","Startup Command",portal.ParameterType.STRING,"",
    longDescription="A command the container will run at startup.  This is separate from the Docker CMD/ENTRYPOINT functionality (see the Docker Command and Docker Environment Variables options for that stuff); this is a testbed service.")
pc.defineParameter(
    "dockerCmd","Docker Command",portal.ParameterType.STRING,"",
    longDescription="As specified in the Docker documentation, this value will either be concatenated with the value of entrypoint in the docker image file; or it will replace it.  Note: we emulate entrypoint/command as a boot service, because we run a real init as the entrypoint.")
pc.defineParameter(
    "dockerEnv","Docker Environment Variables",portal.ParameterType.STRING,"",
    longDescription="These environment variables will be placed in a shell script and source by the entrypoint/command emulation.  Shells accept whitespace-separated variable assigment statements; you could also separate them by semicolons if you prefer.  Either way, this value will be placed into a one-line file that will be sourced by another shell script.")
pc.defineParameter(
    "numberLans","Number of LANs",portal.ParameterType.INTEGER,0,
    longDescription="Number of LANs to which each container is connected.")
pc.defineParameter(
    "buildSnakeLink","Build Snake of Links",portal.ParameterType.BOOLEAN,False,
    longDescription="Build a snake of links from container to container.")
pc.defineParameter(
    "linkSpeed","LAN/Link Speed",portal.ParameterType.INTEGER, 1000000,
    [(0,"Any"),(100000,"100Mb/s"),(1000000,"1Gb/s"),(10000000,"10Gb/s")],
    longDescription="A specific link speed to use for each LAN and link.")
pc.defineParameter(
    "linkLatency","LAN/Link Latency",portal.ParameterType.LATENCY, 0,
    longDescription="A specific latency to use for each LAN and link.")
#pc.defineParameter(
#   "linkLoss", "LAN/Link Loss",portal.ParameterType.FLOAT, 0.0,
#   longDescription="A specific loss rate to use for each LAN and link.")

pc.defineParameter(
    "cores","Cores per container",portal.ParameterType.INTEGER,0,
    longDescription="Number of cores each container will get.",
    advanced=True)
pc.defineParameter(
    "ram","RAM per container",portal.ParameterType.INTEGER,0,
    longDescription="Amount of RAM each container will get.",
    advanced=True)
pc.defineParameter(
    "storageDriver","Docker Storage Driver",portal.ParameterType.STRING,'',
    [('',''),('devicemapper','devicemapper'),
     ('overlay2','overlay2'),('aufs','aufs')],
    longDescription="The Docker storage driver the host machines will use; currently defaults to overlay2.",
    advanced=True)
pc.defineParameter(
    "hostImage","Host Image",portal.ParameterType.STRING,'',
    longDescription="The image your container host nodes will run; best to let the system pick this for you unless you know what you are doing.",
    advanced=True)
pc.defineParameter(
    "multiplex", "Multiplex Networks",portal.ParameterType.BOOLEAN,True,
    longDescription="Multiplex all LANs and links.",
    advanced=True)
pc.defineParameter(
    "bestEffort", "Best Effort Link Bandwidth",portal.ParameterType.BOOLEAN,True,
    longDescription="Do not require guaranteed bandwidth throughout switch fabric.",
    advanced=True)
pc.defineParameter(
    "trivialOk", "Trivial Links Ok",portal.ParameterType.BOOLEAN, True,
    longDescription="Maybe use trivial links.",
    advanced=True)
#pc.defineParameter(
#   "forceVlanLinkType", "Force VLAN Link Type",portal.ParameterType.BOOLEAN, False,
#   longDescription="Force the type of each LAN/Link to vlan.",
#   advanced=True)
pc.defineParameter(
    "ipAllocationStrategy","IP Addressing",portal.ParameterType.STRING,
    "script",[("cloudlab","CloudLab"),("script","This Script")],
    longDescription="Either let CloudLab auto-generate IP addresses for the nodes in your networks, or let this script generate them.  If you include nodes at multiple sites, you must choose this script!  The default is this script, because the subnets CloudLab generates for flat networks are sized according to the number of physical nodes in your topology.  If the script IP address generation is buggy or otherwise insufficient, you can fall back to CloudLab and see if that improves things.",
    advanced=True)
pc.defineParameter(
    "ipAllocationUsesCIDR","Script IP Addressing Uses CIDR",
    portal.ParameterType.BOOLEAN,False,
    longDescription="If this script is generating the IP addresses for your nodes, and this button is checked, we will generate a minimal set of subnets that are just large enough to contain the hosts in each subnet.  If it is not checked, we will generate class B/C subnets inside the 10.0.0.0/8 class A unrouted subnet, for each separate link/lan.",
    advanced=True)
pc.defineParameter(
    "clientsideUpdate","Update Clientside",portal.ParameterType.STRING,'no',
    [('no','No'),('yes','Yes'),('each','Each Boot')],
    longDescription="If set to Yes, the clientside will be updated on first boot for each vhost prior to booting vnodes.  If set to Each Boot, the clientside will be updated for each boot for each vhost.",
    advanced=True)
pc.defineParameter(
    "clientsideUpdateRepo","Clientside Update Source Repo",
    portal.ParameterType.STRING,"",
    longDescription="If set, the updater will clone this git repo; default is https://gitlab.flux.utah.edu/emulab/emulab-devel.git",
    advanced=True)
pc.defineParameter(
    "clientsideUpdateRef","Clientside Update Source Ref",
    portal.ParameterType.STRING,"",
    longDescription="If set, the updater will checkout this branch or tag instead of master; note that it must be a branch or tag, so that we can see its latest commit hash via ls-remote.",
    advanced=True)

params = pc.bindParameters()

if params.hosts < 0:
    pc.reportError(portal.ParameterError("Must specify 0 or more physical hosts",['hosts']))
if params.vnodesPerPhost < 1:
    pc.reportError(portal.ParameterError("Must specify at least one container per host",['vnodesPerPhost']))
if not params.images:
    params.images = "urn:publicid:IDN+emulab.net+image+emulab-ops//docker-ubuntu16-std"
if params.cores < 0:
    pc.reportError(portal.ParameterError("Must specify at least one core per container",['cores']))
if params.ram < 0:
    pc.reportError(portal.ParameterError("Must specify at least one core per container",['ram']))

#
# Give the library a chance to return nice JSON-formatted exception(s) and/or
# warnings; this might sys.exit().
#
pc.verifyParameters()

#
# Build some parameter auto-documentation for the instructions.
#
detailedParamAutoDocs = ''
for param in pc._parameterOrder:
    if not pc._parameters.has_key(param):
        continue
    detailedParamAutoDocs += \
      """
  - *%s*

    %s
    (default value: *%s*)
      """ % (pc._parameters[param]['description'],
             pc._parameters[param]['longDescription'],
             pc._parameters[param]['defaultValue'])
    pass


# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

tour = ig.Tour()
tour.Description(
    ig.Tour.TEXT,
    "Instantiate one or many dedicated or shared containers, configured with many different parameters.")
tour.Instructions(
    ig.Tour.MARKDOWN,
    "### Detailed Parameter Documentation\n%s" % (detailedParamAutoDocs))
request.addTour(tour)

lans = list()
for i in range(0,params.numberLans):
    lan = pg.LAN('lan-%d' % (i,))
    if params.trivialOk is True:
        lan.trivial_ok = True
    else:
        lan.trivial_ok = False
    if params.bestEffort is True:
        lan.best_effort = True
    else:
        lan.best_effort = False
    if params.multiplex is True:
        lan.link_multiplexing = True
    else:
        lan.link_multiplexing = False
    #if params.forceVlanLinkType:
    #    lan.type = "vlan"
    lan.vlan_tagging = True
    if params.linkSpeed > 0:
        lan.bandwidth = params.linkSpeed
    if params.linkLatency > 0:
        lan.latency = params.linkLatency
    #if params.linkLoss > 0:
    #    lan.loss = params.linkLoss
    lans.append(lan)
    pass

vhosts = list()
vnodes = list()
links = list()
lastSnakeLink = None
lastSnakeLinkNum = 0
imageList = []
if params.images:
    imageList = params.images.split(" ")
    pass

for i in range(0,params.hosts):
    host = pg.RawPC('vhost-%d' % (i,))
    host.exclusive = True
    if params.hostType:
        host.hardware_type = params.hostType
    if params.hostImage:
        host.disk_image = params.hostImage
        pass
    if params.clientsideUpdate == "yes" or params.clientsideUpdate == "each":
        host.Attribute("CLIENTSIDE_UPDATE","1")
        if params.clientsideUpdate == "each":
            host.Attribute("CLIENTSIDE_UPDATE_EACHBOOT","1")
        if params.clientsideUpdateRepo:
            host.Attribute("CLIENTSIDE_UPDATE_REPO",params.clientsideUpdateRepo)
        if params.clientsideUpdateRef:
            host.Attribute("CLIENTSIDE_UPDATE_REF",params.clientsideUpdateRef)
    if params.storageDriver:
        host.Attribute("DOCKER_STORAGE_DRIVER",params.storageDriver)
        pass

    vhosts.append(host)

for i in range(-1,params.hosts):
    if i == -1 and params.hosts > 0:
        continue
    for j in range(0,params.vnodesPerPhost):
        node = None
        if i > -1:
            name = 'node-%d-%d' % (i,j)
        else:
            name = 'node-%d' % (j,)
        node = ig.DockerContainer(name)
        if params.cores > 0:
            node.cores = params.cores
        if params.ram:
            node.ram = params.ram
        if params.hostType:
            node.docker_ptype = '%s-vm' % (params.hostType,)
        if i > -1:
            node.InstantiateOn('vhost-%d' % (i,))
            node.exclusive = True
        else:
            node.exclusive = False
        if params.imageSource == "external":
            if len(imageList) > 0:
                node.docker_extimage = imageList[j % len(imageList)]
        elif params.imageSource == "dockerfile":
            if len(imageList) > 0:
                node.docker_dockerfile = imageList[j % len(imageList)]
        elif len(imageList) > 0:
            node.disk_image = imageList[j % len(imageList)]
        if params.dockerTbAugmentation != 'default':
            node.docker_tbaugmentation = params.dockerTbAugmentation
        if params.dockerTbAugmentationUpdate:
            node.docker_tbaugmentation_update = params.dockerTbAugmentationUpdate
        if params.dockerSshStyle != 'default':
            node.docker_ssh_style = params.dockerSshStyle
        if params.dockerExecShell:
            node.docker_exec_shell = params.dockerExecShell
        if params.startupCmd:
            node.addService(pg.Execute(shell="sh",command=params.startupCmd))
        for k in range(0,params.numberLans):
            iface = node.addInterface('if%d' % (k,))
            lans[k].addInterface(iface)
            pass
        if params.buildSnakeLink:
            if not lastSnakeLink:
                lastSnakeLink = pg.Link("slink-%d" % (lastSnakeLinkNum,))
                if params.trivialOk:
                    lastSnakeLink.trivial_ok = True
                else:
                    lastSnakeLink.trivial_ok = False
                if params.bestEffort:
                    lastSnakeLink.best_effort = True
                if params.multiplex:
                    lastSnakeLink.link_multiplexing = True
                lastSnakeLink.vlan_tagging = True
                #if params.forceVlanLinkType:
                #    lastSnakeLink.type = "vlan"

                if params.linkSpeed > 0:
                    lastSnakeLink.bandwidth = params.linkSpeed
                if params.linkLatency > 0:
                    lastSnakeLink.latency = params.linkLatency
                #if params.linkLoss > 0:
                #    lastSnakeLink.loss = params.linkLoss

                siface = node.addInterface('ifS%d' % (lastSnakeLinkNum,))
                lastSnakeLink.addInterface(siface)
            else:
                siface = node.addInterface('ifS%d' % (lastSnakeLinkNum,))
                if params.trivialOk:
                    lastSnakeLink.trivial_ok = True
                else:
                    lastSnakeLink.trivial_ok = False
                if params.bestEffort:
                    lastSnakeLink.best_effort = True
                if params.multiplex:
                    lastSnakeLink.link_multiplexing = True
                lastSnakeLink.vlan_tagging = True
                #if params.forceVlanLinkType:
                #    lastSnakeLink.type = "vlan"
                if params.linkSpeed > 0:
                    lastSnakeLink.bandwidth = params.linkSpeed
                if params.linkLatency > 0:
                    lastSnakeLink.latency = params.linkLatency
                #if params.linkLoss > 0:
                #    lastSnakeLink.loss = params.linkLoss

                lastSnakeLink.addInterface(siface)
                links.append(lastSnakeLink)

                lastSnakeLinkNum += 1
                lastSnakeLink = pg.Link("slink-%d" % (lastSnakeLinkNum,))
                siface = node.addInterface('ifS%d' % (lastSnakeLinkNum,))
                lastSnakeLink.addInterface(siface)
            pass
        if params.dockerCmd:
            node.docker_cmd = params.dockerCmd
            #node.Attribute("DOCKER_CMD",params.dockerCmd)
        if params.dockerEnv:
            node.docker_env = params.dockerEnv
            #node.Attribute("DOCKER_ENV",params.dockerEnv)
        vnodes.append(node)
        pass
    pass

baseaddr = [10,0,0,0]
basebits = 8
minsubnetbits = basebits + 1
maxsubnetbits = 32 - 2
networks = dict()
netmasks = dict()
lastaddr = dict()
# The list of allowed subnet bit sizes.
ALLOWED_SUBNETS = []
# An ordered (increasing bit size) list of (bitsize,networkname) tuples.
REQUIRED_SUBNETS = []
# A dict of key networkname and value { 'bits':bitsize,'network':networkint,
#   'hostnum':hostint,'maxhosts':maxhostsint,'netmaskstr':'x.x.x.x' }
SUBNETS = {}

if params.ipAllocationUsesCIDR:
    subbits = basebits + 1
    while subbits <= maxsubnetbits:
        ALLOWED_SUBNETS.append(subbits)
        subbits += 1
else:
    ALLOWED_SUBNETS = [ 16,24 ]

def __htoa(h):
    return "%d.%d.%d.%d" % (
        (h >> 24) & 0xff,(h >> 16) & 0xff,(h >> 8) & 0xff,h & 0xff)

def ipassign_request_network(name,numhosts):
    #
    # Here, we just reserve each network's bitspace, in increasing
    # bitsize.  This makes eventual assignment trivial; we just pick the
    # next hole out of the previous (larger or equiv size) subnet.
    #
    _sz = numhosts + 1
    i = 0
    while _sz > 0:
        i += 1
        _sz = _sz >> 1
    # The minimum network size is a 255.255.255.252 (a /30).
    if i < 2:
        i = 2
    # Change the host bitsize to a network bitsize.
    i = 32 - i
    sn = None
    for _sn in ALLOWED_SUBNETS:
        if i < _sn:
            break
        sn = _sn
    if sn == None:
        raise Exception("network of bitsize %d (%d hosts) cannot be supported"
                        " with basebits %d" % (i,numhosts,basebits))
    ipos = 0
    for (bitsize,_name) in REQUIRED_SUBNETS:
        if sn < bitsize:
            break
        ipos += 1
    REQUIRED_SUBNETS.insert(ipos,(sn,name))
    return

def ipassign_assign_networks():
    basenum = baseaddr[0] << 24 | baseaddr[1] << 16 \
        | baseaddr[2] << 8 | baseaddr[3]
    # If any of our network broadcast addrs exceed this address, we've
    # overallocated.
    nextbasenum = basenum + 2 ** (32 - basebits)

    #
    # Process REQUIRED_SUBNETS list into SUBNETS dict, and setup the
    # next host number.  Again, we assume that REQUIRED_SUBNETS is
    # ordered in increasing number of network bits required.
    #
    lastbitsize = None
    lastnetnum = None
    for i in range(0,len(REQUIRED_SUBNETS)):
        (bitsize,name) = REQUIRED_SUBNETS[i]
        if lastbitsize != bitsize and lastbitsize != None:
            # Need to get into the next lastbitsize subnet to allocate
            # for the bitsize subnet.
            lastnetnum += 2 ** (32 - lastbitsize)

        if lastnetnum != None:
            netnum = lastnetnum + 2 ** (32 - bitsize)
        else:
            netnum = basenum
        if netnum >= nextbasenum:
            raise Exception("out of network space in /%d at network %s (/%d)"
                            % (basebits,name,bitsize))
        netmask = 0xffffffff ^ (2 ** (32 - bitsize) - 1)
        SUBNETS[name] = {
            'bits':bitsize,'networknum':netnum,'networkstr':__htoa(netnum),
            'hostnum':0,'maxhosts':2 ** (32 - bitsize) - 1,'netmask':netmask,
            'netmaskstr':__htoa(netmask),'addrs':[]
        }
        lastnetnum = netnum
        lastbitsize = bitsize

def ipassign_assign_host(lan):
    #
    # Assign an IP address in the given lan.  If you call this function
    # more times than you effectively promised (by calling
    # ipassign_add_network with a requested host size), you will be
    # handed an Exception.
    #
    bitsize = None
    for (_bitsize,_name) in REQUIRED_SUBNETS:
        if _name == lan:
            bitsize = _bitsize
    if not bitsize:
        raise Exception("unknown network name %s" % (lan,))
    if not _name in SUBNETS:
        raise Exception("unknown network name %s" % (lan,))

    maxhosts = (2 ** bitsize - 1)
    if SUBNETS[lan]['hostnum'] >= maxhosts:
        raise Exception("no host space left in network name %s (max hosts %d)"
                        % (lan,maxhosts))

    SUBNETS[lan]['hostnum'] += 1

    addr = __htoa(SUBNETS[lan]['networknum'] + SUBNETS[lan]['hostnum'])
    if True:
        SUBNETS[lan]['addrs'].append(addr)
    return (addr,SUBNETS[lan]['netmaskstr'])

#
# Assign IP addresses if necessary.
#
if params.ipAllocationStrategy == 'script':
    for lan in lans:
        name = lan.client_id
        ipassign_request_network(name,len(lan.interfaces))
    for link in links:
        name = link.client_id
        ipassign_request_network(name,len(link.interfaces))
    ipassign_assign_networks()
    for lan in lans:
        name = lan.client_id
        for iface in lan.interfaces:
            (address,netmask) = ipassign_assign_host(name)
            iface.addAddress(pg.IPv4Address(address,netmask))
    for link in links:
        name = link.client_id
        for iface in link.interfaces:
            (address,netmask) = ipassign_assign_host(name)
            iface.addAddress(pg.IPv4Address(address,netmask))
    pass

#
# If this is a LAN-only experiment, turn off ddjikstra routing; we don't
# need it, and it explodes on huge LANs (i.e., on a 5k topo, 30s per vnode).
#
if not params.buildSnakeLink:
    request.setRoutingStyle("none")

for x in vhosts:
    request.addResource(x)
for x in vnodes:
    request.addResource(x)
for x in lans:
    request.addResource(x)
for x in links:
    request.addResource(x)

pc.printRequestRSpec(request)
