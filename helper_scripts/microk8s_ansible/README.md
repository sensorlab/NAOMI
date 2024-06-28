# Microk8s Ansible script

Configure 'ansible.cfg' and 'inventory.yml' files.

```bash
# health check
ansible-playbook health_check.yml

# install microk8s
ansible-playbook install_microk8s.yml

# remove microk8s
ansible-playbook remove_microk8s.yml
```

This installs a non HA microk8s cluster with head and worker nodes.
The installation include coredns, flannel and etcd as a db.

Removing `microk8s disable ha-cluster --force` command from script installs a HA ready cluster with calico as CNI and dqlite.
