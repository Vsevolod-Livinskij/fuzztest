# Copied from https://www.emulab.net/portal/show-profile.php?project=PortalProfiles&profile=docker-one-node

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

# Define some parameters related to image augmentation/onboarding.
pc.defineParameter(
    "image","Image Reference",portal.ParameterType.STRING,
    "urn:publicid:IDN+emulab.net+image+emulab-ops//docker-ubuntu16-std",
    longDescription="An image URN pointing to an existing testbed Docker image; or a publicly-accessible Docker registry/repo:tag; or publicly-accessible URL pointing to a Dockerfile (in this case, we will build a new image from the Dockerfile).  Be sure to change the Image Type parameter just below in accordance with one of these options!")
pc.defineParameter(
    "imageSource","Image Type",portal.ParameterType.STRING,
    "urn",[("urn","Testbed Image"),("external","External Repository"),
           ("dockerfile","Dockerfile")],
    longDescription="Specifies the type of image referenced by the image parameter; read the help for the image parameter!")
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
    "dockerEntrypoint","Docker Entrypoint",portal.ParameterType.STRING,"",
    longDescription="As specified in the Docker documentation, this value will replace the image's builtin entrypoint.  Note: we emulate entrypoint/command as a boot service in augmented images, because we run a real init as the entrypoint.")
pc.defineParameter(
    "dockerCmd","Docker Command",portal.ParameterType.STRING,"",
    longDescription="As specified in the Docker documentation, this value will either be concatenated with the value of entrypoint in the docker image file; or it will replace it.  Note: we emulate entrypoint/command as a boot service in augmented images, because we run a real init as the entrypoint.")
pc.defineParameter(
    "dockerEnv","Docker Environment Variables",portal.ParameterType.STRING,"",
    longDescription="These environment variables will be placed in a shell script and source by the entrypoint/command emulation.  Shells accept whitespace-separated variable assigment statements; you could also separate them by semicolons if you prefer.  Either way, this value will be placed into a one-line file that will be sourced by another shell script.")
pc.defineParameter(
    "dockerPrivileged","Docker Privileged Mode",
    portal.ParameterType.BOOLEAN,False,
    longDescription="If enabled, your container will be privileged (i.e., the ability to use full root privileges on the container host machine).  If you select this option, you must also enable exclusive mode.")
pc.defineParameter(
    "startupCmd","Startup Command",portal.ParameterType.STRING,"",
    longDescription="A command the container will run at startup.  This is separate from the Docker CMD/ENTRYPOINT functionality (see the Docker Command and Docker Environment Variables options for that stuff); this is a testbed service.")
pc.defineParameter(
    "exclusive","Exclusive Mode",portal.ParameterType.BOOLEAN,False,
    longDescription="If checked, your container will be run in dedicated mode, meaning that the underlying physical host will be dedicated to your experiment (and thus you can login to it, run Docker commands, etc.).  If unchecked (the default in this profile), your node will be created atop a shared physical host (potentially shared with containers from other experiments).  When containers are run in shared mode, they are deprivileged, so they have no visibility to the physical host machine, nor to other containers from other experiments.")
pc.defineParameter(
    "routableControlIP","Allocate Routable Control IP",
    portal.ParameterType.BOOLEAN,False,
    longDescription="Virtual nodes in Emulab by default do not have public IP addresses; this option allocates one.")

# Bind parameter values from the Web Interface (etc).
params = pc.bindParameters()

# A couple parameter checks.
if not params.image:
    pc.reportError(
        portal.ParameterError("Must specify an image value!",["image"]))
if params.dockerPrivileged and not params.exclusive:
    pc.reportError(portal.ParameterError(
        "Privileged containers *must* be exclusive (not shared)!",
        ["dockerPrivileged","exclusive"]))

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

# Describe this profile.
tour = ig.Tour()
tour.Description(
    ig.Tour.TEXT,
    "Create one Docker container running a testbed image; an external image; or a Dockerfile built on-demand.  Also supports updating an existing testbed-augmented image.")
tour.Instructions(
    ig.Tour.MARKDOWN,
    "### Detailed Parameter Documentation\n%s" % (detailedParamAutoDocs))
request.addTour(tour)

# Create the container node.
node = ig.DockerContainer("node")
# Put the container into "shared" mode, meaning it will be hosted on a
# shared container host, potentially shared amongst users from multiple
# projects.  Your container's data is not accessible to other containers
# on the shared host, and your container is unprivileged.  This results
# in the fastest-possible experiment creation time, since the testbed
# does not have to take the additional step of provisioning a dedicated
# physical node to host your one container.
node.exclusive = params.exclusive
if params.imageSource == "external":
    node.docker_extimage = params.image
elif params.imageSource == "dockerfile":
    node.docker_dockerfile = params.image
else:
    node.disk_image = params.image
if params.dockerTbAugmentation != "default":
    node.docker_tbaugmentation = params.dockerTbAugmentation
if params.dockerTbAugmentationUpdate:
    node.docker_tbaugmentation_update = params.dockerTbAugmentationUpdate
if params.dockerSshStyle != "default":
    node.docker_ssh_style = params.dockerSshStyle
if params.dockerExecShell:
    node.docker_exec_shell = params.dockerExecShell
if params.dockerEntrypoint:
    node.docker_entrypoint = params.dockerEntrypoint
if params.dockerCmd:
    node.docker_cmd = params.dockerCmd
if params.dockerEnv:
    node.docker_env = params.dockerEnv
if params.dockerPrivileged:
    node.docker_privileged = params.dockerPrivileged
if params.startupCmd:
    node.addService(pg.Execute(shell="sh",command=params.startupCmd))
if params.routableControlIP:
    node.routable_control_ip = True

# Add the node to our resource request.
request.addResource(node)

# Dump the request as an XML RSpec.
pc.printRequestRSpec(request)
