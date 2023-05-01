# Requirements
- Python and `python-consul2`
- `firewalld` installed and running
# Configuration
- `python-consul2` might require configuration
- `firewall-cmd` might requre `root` access
# Running
- Run by `cron` with access to run `firewall-cmd` (`root` or any better way)
# Debug / Testing
- Can test without Consul with test file provided (see code)
- Can test `firewall-cmd` commands without running (see code)
# TODO
- Some `firewall-cmd` will fail and should not be treated as failure
# Better ways (need research)
- [Consul Watches](https://developer.hashicorp.com/consul/docs/dynamic-app-config/watches): subscribe for Consul catalog updates
- [Network Infrastructure Automation (NIA) with Terraform and Consul](https://www.hashicorp.com/resources/introduction-to-network-infrastructure-automation-nia-with-hashicorp-terraform-an)