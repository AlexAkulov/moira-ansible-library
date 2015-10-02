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
              C(url) is an alias for C(server_url).
        required: false
        default: http://localhost
        aliases: ["url"]
    state:
        description:
            - Create or delete trigger.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
    name:
        description:
            - Trigger name
        required: true
    target:
        description:
            - Target
        required: false
        default: ""
    targets:
        description:
            - Target lists
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
    try:
        r = requests.get(url)
    except:
        module.fail_json(msg="unable to connect moira api %s" % module.params['server_url'])
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
        try:
            r = requests.delete(url)
        except:
            module.fail_json(msg="unable to connect moira api %s" % module.params['server_url'])
        if r.status_code != 200:
            module.fail_json(msg="failed delete trigger, status code %d" % r.status_code)
        module.exit_json(msg="OK", changed=True)

def moira_create_trigger(module, old_trigger, new_trigger):
    if old_trigger != new_trigger:
        if old_trigger == None:
            trigger_id = ''
        else:
            trigger_id = old_trigger['id']
        url = module.params['server_url'] + "/worker/trigger/" + trigger_id
        try:
            r = requests.put(url, data=json.dumps(new_trigger))
        except:
            module.fail_json(msg="unable to connect moira api %s" % module.params['server_url'])
        if r.status_code != 200:
            module.fail_json(msg="unable to update trigger, status code %d" % r.status_code)
        module.exit_json(msg="OK", changed=True)
    else:
        module.exit_json(msg="OK", changed=False)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            server_url  = dict(type='str',aliases=['url'], required=False, default='http://localhost'),
            name        = dict(type='str', required=True),
            target      = dict(type='str', required=False, default=''),
            targets     = dict(type='list', required=False, default=[]),
            warn        = dict(type='float', required=False, default=None),
            error       = dict(type='float', required=False, default=None),
            expression  = dict(type='str', required=False, default=None),
            ttl         = dict(type='int', required=False, default=600),
            state       = dict(type='str', required=False, default='present', choices=['present', 'absent']),
            ttl_state   = dict(type='str', required=False, default='NODATA', choises=['nodata', 'ok', 'warn', 'error', 'NODATA', 'OK', 'WARN', 'ERROR']),
            tags        = dict(type='list', required=False, default=[])
        )
    )
    
    state = module.params['state']
    old_trigger = moira_get_trigger(module)
    if old_trigger is not None:
        new_trigger = old_trigger.copy()
    else:
        new_trigger = {}

    if state == "absent":
        moira_delete_trigger(module, old_trigger)
    else:
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
        if len(new_trigger['targets']) == 0:
            module.fail_json(msg="'target' or 'targets' param required")
        if len(new_trigger['targets']) > 1:
            if new_trigger['expression'] is None:
                module.fail_json(msg="expression required") 
        else:
            if new_trigger['warn_value'] is None or new_trigger['error_value'] is None:
                module.fail_json(msg="warn and error required") 
        moira_create_trigger(module, old_trigger, new_trigger)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()



