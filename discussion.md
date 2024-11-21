## Deployment Decisions
I ended up going with k3s and a python script to deploy a kubernetes compliant cluster locally to VMs. This uses multipass 
to stand up the vms and then includes them into a k3s cluster.

Originally, I had planned to use Ansible to do this because I'm a lot more familiar with that tool, and it's fairly straight 
forward to provision on prem resources using roles / playbooks. The issue I ran into was running containers inside the VMs
I stood up using Ansible. Ansible's Molecule module usually lets you create vms for local testing, and then you can simply point 
the ansible playbook to your real hosts inventory when you are ready to deploy to on-prem instead the molecule defined hosts. 
However, in this case conditioning the vms for k8s using podman or docker was challenging. Maybe this is because I wasn't 
using the correct image or maybe this sort of nested virtualization isn't well-supported on arm macs, but either way I 
got bogged down in the details of setting up these vms correctly rather than working on the actual problem of deploying 
a cluster and then provisioning a high availability mysql solution. 

I decided to use minikube to create a local cluster that I could more easily test with. That way I could get a basic mysql 
solution up and running. I went with Bitnami's mysql helm chart because of it's ease of use in standing up a basic mysql instance. 

I used both the K3s and the digital ocean high availability docs, to decide on the architecture for this, and they provided
the arch blueprint that I ultimately followed. Even though I didn't use any of the DO stuff in my solution, it helped me 
understand what was going on. 

## Architecture Improvements
The fail-over system doesn't work as stated in the diagram in the readme. I think this is a limitation with the bitnami solution.
In a real deployment I don't think I would pick this because the details of what kind of high availability we want are relevant.
The system depicted is node tolerant, but the deployed system doesn't behave this way. The LoadBalancer doesn't re-distribute
the read/write loads to secondary pods.

With some more time I'd roll my own helm chart solution that does actually work the described in the diagram. 

If MariaDB was an okay stand in I'd  opt to use Galera instead of both of those options; from reading their docs they 
designed the system from the ground up to be high availability. 


## Improvements
There are many things I didn't get to in this solution:
1. The system should be connected up some sort of monitoring solution, I think Prometheus is the right choice.
2. The helm should have better authentication management instead of a single plain text password
3. Handle the network configuration correctly. This tends to be the most challenging part of an on-prem deployment is 
making sure the network interfaces are all correctly setup.
4. The secrets.yaml templating should get rid of the need to manually copy in you AWS scret and access key.

This was an interesting project, I went from never having deployed k8s before to a working cluster running an application.
I'm excited to learn more about how kubernetes works at a base level, and see how I can leverage more components. 

In a real world deployment, I'd strongly encourage looking at a managed solution. The tooling to handle a managed solution 
through something like terraform is much better supported, and you are able to create something with a much higher standard
for availability as you can distribute across more zones and regions. 
