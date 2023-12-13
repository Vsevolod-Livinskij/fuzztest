"""A Docker container for running an external image with centipede."""

import geni.portal as portal
import geni.rspec.pg as rspec
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a Request object to start building the RSpec.
request = portal.context.makeRequestRSpec()

for j in range(0,2):
    host = request.RawPC("host-%d" % (j))
    # Select a specific hardware type for the container host.
    host.hardware_type = "d430"

    # Create a container.
    node = request.DockerContainer("node-%d" % (j))

    # Load the image
    node.docker_extimage = "vlivinsk/centipede-eval:latest"
    #node.docker_extimage = "ubuntu:22.04"


    # Select host and occupy it
    #node.docker_ptype = host.client_id
    node.InstantiateOn(host.client_id)
    node.exclusive = True
    node.docker_privileged = True

    # SSH hack
    node.docker_ssh_style = "exec"
    node.docker_exec_shell = "/bin/bash"

    # For some reason, we can't allocate more than 150GB with this apporoach
    # The solution is to use the volume in docker
    #node.Desire('?+disk_nonsysvol','1')
    #bs = node.Blockstore("temp-bs-%d" % (j),"/testing/result")
    #bs = node.Blockstore("temp-bs-%d" % (j), "/mnt/tmp")
    #bs.size = "200GB"
    #bs.placement = "NONSYSVOL"

request.setRoutingStyle('static')

# Print the RSpec to the enclosing page.
portal.context.printRequestRSpec()
