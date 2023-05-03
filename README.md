# Requirements
- Python and packages, see `pyproject.toml`
- `firewalld` installed and running

# Configuration
- `python-consul2` might require configuration
- `firewall-cmd` might requre `root` access

# Running
- Run by `cron` with access to run `firewall-cmd` (`root` or any better way)

# Debug / Testing
- Can test without Consul with test file provided. See:
  - `DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL`
  - `DEBUG_CONSUL_CURRENT_HOST_ENV_OVERRIDE`
- Can test `firewall-cmd` commands without running (see `DEBUG_DRY_RUN`)

# TODO
- Some `firewall-cmd` will fail and should not be treated as failure
- Error Handling in general
- Documentation strings & comments if needed
- Configuration and/or arguments for debug, logging
- Tests
- Find a firewall lib or extract `firewalld` methods to a module
- Extract mapping rules from `add_services_to_rules` to configuration file

# Better ways (need research)
- [Consul Watches](https://developer.hashicorp.com/consul/docs/dynamic-app-config/watches): subscribe for Consul catalog updates
- [Network Infrastructure Automation (NIA) with Terraform and Consul](https://www.hashicorp.com/resources/introduction-to-network-infrastructure-automation-nia-with-hashicorp-terraform-an)