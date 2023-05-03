import subprocess
import consul
import requests
import logging

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

CUSTOM_SERVICES = {
    'node_exporter': ['9100/tcp'],
    'mysqld_exporter': ['9104/tcp'],
    'logstash_syslog': ['5141/udp', '5141/tcp']
}

DEBUG_DRY_RUN = True
DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL = 'https://gist.githubusercontent.com/jakubgs/dbf1df154f2d94541dc01baf1116d69f/raw/e2cccda0fba8988bc0af8a710ba5c5b4413d7558/services.json'
DEBUG_CONSUL_CURRENT_HOST_ENV_OVERRIDE = 'app'

c = consul.Consul()


def create_firewall_zone(zone_name: str):
    cmd = ['firewall-cmd',
           '--permanent',
           f'--new-zone={zone_name}']

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def create_new_service(service_name: str):
    if service_name not in CUSTOM_SERVICES:
        return

    cmd = ['firewall-cmd',
           '--permanent',
           f'--new-service={service_name}']

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)

    add_ports_arguments = " ".join([
        f'--add-port={a}' for a in CUSTOM_SERVICES[service_name]])

    cmd = ['firewall-cmd',
           '--permanent',
           f'--service={service_name}',
           add_ports_arguments]

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def add_service_to_zone(service_name: str, zone_name: str):
    cmd = ['firewall-cmd',
           '--permanent',
           f'-zone={zone_name}',
           f'--add-service={service_name}']

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def remove_source_from_zone(ipset_name: str, zone_name: str):
    cmd = ['firewall-cmd',
           '--permanent',
           f'-zone={zone_name}',
           f'--remove-source=ipset:{ipset_name}']

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def delete_ipset(ipset_name: str):
    cmd = ['firewall-cmd',
           '--permanent',
           f'--delete-ipset={ipset_name}']

    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def create_new_ipset(ipset_name: str, ips: str):
    delete_ipset(ipset_name)

    cmd = ['firewall-cmd',
           '--permanent',
           f'--new-ipset={ipset_name}',
           '--type=hash:ip']
    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)

    for ip in ips:
        cmd = ['firewall-cmd',
               '--permanent',
               f'--ipset={ipset_name}',
               f'--add-entry={ip}']
        if DEBUG_DRY_RUN:
            logging.debug(cmd)
        else:
            subprocess.run(cmd, check=False)


def add_ipset_to_zone(ipset_name: str, zone_name: str):
    cmd = ['firewall-cmd',
           '--permanent',
           f'--zone={zone_name}',
           f'--add-source=ipset:{ipset_name}']
    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def reload_firewall():
    cmd = ['firewall-cmd',
           '--reload']
    if DEBUG_DRY_RUN:
        logging.debug(cmd)
    else:
        subprocess.run(cmd, check=False)


def apply_firewall_rules(rules: dict):
    logging.info('Applying firewalld rules')
    for zone_name, zone_rules in rules.items():
        if 'services' in zone_rules:
            create_firewall_zone(zone_name)

            for service_name in zone_rules['services']:
                create_new_service(service_name)
                add_service_to_zone(service_name, zone_name)

            ipset_name = zone_name
            remove_source_from_zone(ipset_name, zone_name)
            create_new_ipset(ipset_name, zone_rules['ips'])
            add_ipset_to_zone(ipset_name, zone_name)

            reload_firewall()


def add_service_to_zone_rules(rules, zone, service):
    logging.info(f'Adding rule to open {service} for {zone}')
    if 'services' in rules[zone]:
        rules[zone]['services'].append(service)
    else:
        rules[zone]['services'] = [service]


def get_current_host_env() -> str:
    if DEBUG_CONSUL_CURRENT_HOST_ENV_OVERRIDE:
        logging.info('Using DEBUG_CONSUL_CURRENT_HOST_ENV_OVERRIDE')
        env = DEBUG_CONSUL_CURRENT_HOST_ENV_OVERRIDE
    else:
        agent_info = c.agent.self()
        env = agent_info['Config']['NodeMeta']['env']
    logging.info(f'Current host env: {env}')

    return env


def get_env_node_ips() -> dict:
    env_node_ips = {}
    if DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL:
        logging.info('Getting Consul Services from DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL:')
        logging.info(DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL)
        services = requests.get(DEBUG_CONSUL_SERVICES_OVERRIDE_JSON_URL).json()
    else:
        services = c.catalog.service('wireguard')[1]

    for service in services:
        service_env = service['NodeMeta']['env']
        ip = service['ServiceAddress']
        if service_env in env_node_ips:
            env_node_ips[service_env]['ips'].append(ip)
        else:
            env_node_ips[service_env] = {'ips': []}

    return env_node_ips


def add_services_to_rules(rules: dict, env: str) -> dict:
    add_service_to_zone_rules(rules, 'metrics', 'node_exporter')

    if env == 'app':
        add_service_to_zone_rules(rules, 'metrics', 'mysqld_exporter')
        add_service_to_zone_rules(rules, 'backups', 'mysql')

    if env == 'logs':
        add_service_to_zone_rules(rules, 'metrics', 'logstash_syslog')
        add_service_to_zone_rules(rules, 'backups', 'logstash_syslog')
        add_service_to_zone_rules(rules, 'app', 'logstash_syslog')

    return rules


if __name__ == '__main__':
    current_node_env = get_current_host_env()
    env_node_ips = get_env_node_ips()
    firewall_rules = add_services_to_rules(env_node_ips, current_node_env)
    apply_firewall_rules(firewall_rules)
