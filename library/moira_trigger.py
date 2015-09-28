#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# SKB Kontur
#
# This file is part of Ansible
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: moira_trigger
short_description: Moira trigger create/edit/delete
description:
    - Create trigger if they do not exist.
    - Edit trigger
    - Delete trigger
author:
    - me
 requirements:
    - "python >= 2.6"
options:
    server_url:
        description:
            - Url of Moira API, with protocol (http or https)
              C(url) is an aliaz for C(server_url).
        required: false
        default: http://localhost:6060
        aliases: ["url"]
    state:
        description:
            - Create or delete host group.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
    name:
    targets:
    warn:
    error:
    expression: 
    ttl:
        description:
            - Time to live
        required: false
        default: 600
    ttl_state:
        description:
            - Set status after ttl
        required: false
        default: nodata
        choises: ["nodata", "ok", "warn", "error"]
    tags:

'''

try:
    import json
except ImportError:
    import simplejson as json
import requests

def moira_get_trigger(module):
    name = module.params['name']
    url = module.params['server_url'] + "/worker/trigger"
    r = requests.get(url)
    if r.status_code != 200:
        module.fail_json(msg="unable to connect moira api %s" % module.params['server_url'])
    triggers = r.json()
    for trigger in triggers['list']:
        if trigger['name'] == name:
            return trigger
    return None

def moira_delete_trigger(module, trigger):
    if trigger == None:
        module.exit_json(msg="OK", changed=False)
    else:
        url = module.params['server_url'] + "/worker/trigger/" + trigger['id']
        r = requests.delete(url)
        if r.status_code != 200:
            module.fail_json(msg="failed delete trigger, status code %d" % r.status_code)
        module.exit_json(msg="OK", changed=True)


def moira_need_update_trigger(trigger, new_trigger):
    if trigger == None:
        return True
    for h in ['name', 'targets', 'warn_value', 'error_value', 'ttl', 'ttl_state', 'expression']:
        if h not in trigger:
            return True
        if trigger[h] != new_trigger[h]:
            return True
    if len(trigger['tags']) != len(new_trigger['tags']):
        return True
    for t in new_trigger['tags']:
        if t not in trigger['tags']:
            return True
    return False

def moira_create_trigger(module, trigger, new_trigger):
    if moira_need_update_trigger(trigger, new_trigger):
        if trigger == None:
            trigger_id = ''
        else:
            trigger_id = trigger['id']
        url = module.params['server_url'] + "/worker/trigger/" + trigger_id
        r = requests.put(url, data=json.dumps(new_trigger))
        if r.status_code != 200:
            module.fail_json(msg="unable to update trigger, status code %d" % r.status_code)
        module.exit_json(msg="OK", changed=True)
    else:
        module.exit_json(msg="OK", changed=False)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            server_url  = dict(type='str', required=False, default='http://localhost'),
            name        = dict(type='str', required=True),
            target      = dict(type='str', required=False, default=''),
            targets     = dict(type='list', required=False, default=[]),
            warn        = dict(type='int', required=False, default=None),
            error       = dict(type='int', required=False, default=None),
            expression  = dict(type='str', required=False, default=''),
            ttl         = dict(type='int', required=False, default=600),
            state       = dict(type='str', required=False, default='present', choices=['present', 'absent']),
            ttl_state   = dict(type='str', required=False, default='NODATA', choises=['nodata', 'ok', 'warn', 'error', 'NODATA', 'OK', 'WARN', 'ERROR']),
            tags        = dict(type='list', required=False, default=[])
        )
    )
    
    state = module.params['state']
    trigger = moira_get_trigger(module)
    new_trigger = {}
    new_trigger['name'] = module.params['name']
    new_trigger['warn_value'] = module.params['warn']
    new_trigger['error_value'] = module.params['error']
    new_trigger['ttl'] = module.params['ttl']
    new_trigger['ttl_state'] = module.params['ttl_state'].upper()
    new_trigger['expression'] = module.params['expression']
    new_trigger['tags'] = module.params['tags']
    if module.params['target'] != '':
        new_trigger['targets'] = [module.params['target']]
    else:
        new_trigger['targets'] = module.params['targets']

    if state == "absent":
        moira_delete_trigger(module, trigger)
    else:
        if len(new_trigger['targets']) == 0:
            module.fail_json(msg="'target' or 'targets' param required")
        if new_trigger['warn_value'] == None or new_trigger['error_value'] == None:
            module.fail_json(msg="warn and error required") 
        moira_create_trigger(module, trigger, new_trigger)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()



