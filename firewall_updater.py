import subprocess
import consul
# import requests

custom_services = {
    'node_exporter': ['9100/tcp'],
    'mysqld_exporter': ['9104/tcp'],
    'logstash_syslog': ['5141/udp', '5141/tcp']
}

def apply_firewall_rules(rules):
    for zone, zone_rules in rules.items():
        if 'services' in zone_rules:
            # print(f'firewall-cmd --permanent --new-zone={zone}')
            subprocess.run(['firewall-cmd',
                            '--permanent',
                            f'--new-zone={zone}'], check=False)

            for service in zone_rules['services']:
                # print(f'firewall-cmd --permanent --new-service={service}')
                subprocess.run(['firewall-cmd',
                                '--permanent',
                                f'--new-service={service}'], check=False)

                add_ports_arguments = " ".join([
                    f'--add-port={a}' for a in custom_services['logstash_syslog']])

                # print(f'firewall-cmd --permanent --service={service} {add_ports_arguments}')
                subprocess.run(['firewall-cmd',
                                '--permanent',
                                f'--service={service}', add_ports_arguments], check=False)

                # print(f'firewall-cmd --permanent --zone={zone} --add-service={service}')
                subprocess.run(['firewall-cmd',
                                '--permanent',
                                f'-zone={zone}',
                                f'--add-service={service}'], check=False)

            # print(f'firewall-cmd --permanent --zone={zone} --remove-source=ipset:{zone}')
            subprocess.run(['firewall-cmd',
                            '--permanent',
                            f'-zone={zone}',
                            f'--remove-source=ipset:{zone}'], check=False)

            # print(f'firewall-cmd --permanent --delete-ipset={zone}')
            subprocess.run(['firewall-cmd',
                            '--permanent',
                            f'--delete-ipset={zone}'], check=False)

            # print(f'firewall-cmd --permanent --new-ipset={zone} --type=hash:ip')
            subprocess.run(['firewall-cmd',
                            '--permanent',
                            f'--new-ipset={zone}',
                            '--type=hash:ip'], check=False)

            for ip in zone_rules['ips']:
                # print(f'firewall-cmd --permanent --ipset={zone} --add-entry={ip}')
                subprocess.run(['firewall-cmd',
                                '--permanent',
                                f'--ipset={zone}',
                                f'--add-entry={ip}'], check=False)

            # print(f'firewall-cmd --permanent --zone={zone} --zone={zone}')
            subprocess.run(['firewall-cmd',
                            '--permanent',
                            f'--zone={zone}',
                            f'--zone={zone}'], check=False)

    # print(f'firewall-cmd --reload')
    subprocess.run(['firewall-cmd', '--reload'], check=False)

def add_service_to_zone_rules(rules, zone, service):
    if 'services' in rules[zone]:
        rules[zone]['services'].append(service)
    else:
        rules[zone]['services'] = [service]

c = consul.Consul()
agent_info = c.agent.self()
current_node_env = agent_info['Config']['NodeMeta']['env']
# current_node_env = 'metrics'
rules = {}

# Test file
# services = requests.get('https://gist.githubusercontent.com/jakubgs/dbf1df154f2d94541dc01baf1116d69f/raw/e2cccda0fba8988bc0af8a710ba5c5b4413d7558/services.json').json()
services = c.catalog.service('wireguard')[1]
for service in services:
    service_env = service['NodeMeta']['env']
    ip = service['ServiceAddress']
    if service_env in rules:
        rules[service_env]['ips'].append(ip)
    else:
        rules[service_env] = {'ips': []}

add_service_to_zone_rules(rules, 'metrics', 'node_exporter')

if current_node_env == 'app':
    add_service_to_zone_rules(rules, 'metrics', 'mysqld_exporter')
    add_service_to_zone_rules(rules, 'backups', 'mysql')

if current_node_env == 'logs':
    add_service_to_zone_rules(rules, 'metrics', 'logstash_syslog')
    add_service_to_zone_rules(rules, 'backups', 'logstash_syslog')
    add_service_to_zone_rules(rules, 'app', 'logstash_syslog')

apply_firewall_rules(rules)
