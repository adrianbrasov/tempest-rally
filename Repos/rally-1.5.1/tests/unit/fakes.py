# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import itertools
import multiprocessing
import random
import re
import string
import uuid

import mock

from rally import api
from rally.common import utils as rally_utils
from rally import consts
from rally.task import context
from rally.task import scenario


def generate_uuid():
    return str(uuid.uuid4())


def generate_name(prefix="", length=12, choices=string.ascii_lowercase):
    """Generate pseudo-random name.

    :param prefix: str, custom prefix for genertated name
    :param length: int, length of autogenerated part of result name
    :param choices: str, chars that accurs in generated name
    :returns: str, pseudo-random name
    """
    return prefix + "".join(random.choice(choices) for i in range(length))


def generate_mac():
    """Generate pseudo-random MAC address.

    :returns: str, MAC address
    """
    rand_str = generate_name(choices="0123456789abcdef", length=12)
    return ":".join(re.findall("..", rand_str))


def setup_dict(data, required=None, defaults=None):
    """Setup and validate dict scenario_base. on mandatory keys and default data.

    This function reduces code that constructs dict objects
    with specific schema (e.g. for API data).

    :param data: dict, input data
    :param required: list, mandatory keys to check
    :param defaults: dict, default data
    :returns: dict, with all keys set
    :raises IndexError, ValueError: If input data is incorrect
    """
    required = required or []
    for i in set(required) - set(data):
        raise IndexError("Missed: %s" % i)

    defaults = defaults or {}
    for i in set(data) - set(required) - set(defaults):
        raise ValueError("Unexpected: %s" % i)

    defaults.update(data)
    return defaults


def fake_credential(**config):
    m = mock.Mock()
    m.to_dict.return_value = config
    for key, value in config.items():
        setattr(m, key, value)
    return m


class FakeResource(object):

    def __init__(self, manager=None, name=None, status="ACTIVE", items=None,
                 deployment_uuid=None, id=None):
        self.name = name or generate_uuid()
        self.status = status
        self.manager = manager
        self.uuid = generate_uuid()
        self.id = id or self.uuid
        self.items = items or {}
        self.deployment_uuid = deployment_uuid or generate_uuid()

    def __getattr__(self, name):
        # NOTE(msdubov): e.g. server.delete() -> manager.delete(server)
        def manager_func(*args, **kwargs):
            return getattr(self.manager, name)(self, *args, **kwargs)
        return manager_func

    def __getitem__(self, key):
        return self.items[key]


class FakeManager(object):

    def __init__(self):
        super(FakeManager, self).__init__()
        self.cache = {}
        self.resources_order = []

    def get(self, resource_uuid):
        return self.cache.get(resource_uuid)

    def delete(self, resource_uuid):
        cached = self.get(resource_uuid)
        if cached is not None:
            cached.status = "DELETED"
            del self.cache[resource_uuid]
            self.resources_order.remove(resource_uuid)

    def _cache(self, resource):
        self.resources_order.append(resource.uuid)
        self.cache[resource.uuid] = resource
        return resource

    def list(self, **kwargs):
        return [self.cache[key] for key in self.resources_order]

    def find(self, **kwargs):
        for resource in self.cache.values():
            match = True
            for key, value in kwargs.items():
                if getattr(resource, key, None) != value:
                    match = False
                    break
            if match:
                return resource


class FakeRunner(object):

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "type": {
                "type": "string",
                "enum": ["fake"]
            },

            "a": {
                "type": "string"
            },

            "b": {
                "type": "number"
            }
        },
        "required": ["type", "a"]
    }


class FakeScenario(scenario.Scenario):

    def idle_time(self):
        return 0

    def do_it(self, **kwargs):
        pass

    def with_output(self, **kwargs):
        return {"data": {"a": 1}, "error": None}

    def with_add_output(self):
        self.add_output(additive={"title": "Additive",
                                  "description": "Additive description",
                                  "data": [["a", 1]],
                                  "chart_plugin": "FooPlugin"},
                        complete={"title": "Complete",
                                  "description": "Complete description",
                                  "data": [["a", [[1, 2], [2, 3]]]],
                                  "chart_plugin": "BarPlugin"})

    def too_long(self, **kwargs):
        pass

    def something_went_wrong(self, **kwargs):
        raise Exception("Something went wrong")

    def raise_timeout(self, **kwargs):
        raise multiprocessing.TimeoutError()


@scenario.configure(name="classbased.fooscenario")
class FakeClassBasedScenario(FakeScenario):
    """Fake class-based scenario."""

    def run(self, *args, **kwargs):
        pass


class FakeTimer(rally_utils.Timer):

    def duration(self):
        return 10

    def timestamp(self):
        return 0

    def finish_timestamp(self):
        return 3


@context.configure(name="fake", order=1)
class FakeContext(context.Context):

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "test": {
                "type": "integer"
            },
        },
        "additionalProperties": False
    }

    def __init__(self, context_obj=None):
        context_obj = context_obj or {}
        context_obj.setdefault("config", {})
        context_obj["config"].setdefault("fake", None)
        context_obj.setdefault("task", mock.MagicMock())
        super(FakeContext, self).__init__(context_obj)

    def setup(self):
        pass

    def cleanup(self):
        pass


@context.configure(name="fake_hidden_context", order=1, hidden=True)
class FakeHiddenContext(FakeContext):
    pass


class FakeDeployment(dict):

    def __init__(self, **kwargs):
        platform = kwargs.pop("platform", "openstack")
        kwargs["credentials"] = {
            platform: [{"admin": kwargs.pop("admin", None),
                        "users": kwargs.pop("users", [])}],
            "default": [{"admin": None, "users": []}]}
        dict.__init__(self, **kwargs)
        self.update_status = mock.Mock()
        self.env_obj = mock.Mock()

    def get_platforms(self):
        return [platform for platform in self["credentials"]]

    def get_credentials_for(self, platform):
        return self["credentials"][platform][0]

    def verify_connections(self):
        pass

    def get_validation_context(self):
        return {}


class FakeTask(dict, object):

    def __init__(self, task=None, temporary=False, **kwargs):
        self.is_temporary = temporary
        self.update_status = mock.Mock()
        self.set_failed = mock.Mock()
        self.set_validation_failed = mock.Mock()
        task = task or {}
        for k, v in itertools.chain(task.items(), kwargs.items()):
            self[k] = v
        self.task = self

    def to_dict(self):
        return self


class FakeAPI(object):

    def __init__(self):
        self._deployment = mock.create_autospec(api._Deployment)
        self._task = mock.create_autospec(api._Task)
        self._verifier = mock.create_autospec(api._Verifier)
        self._verification = mock.create_autospec(api._Verification)

    @property
    def deployment(self):
        return self._deployment

    @property
    def task(self):
        return self._task

    @property
    def verifier(self):
        return self._verifier

    @property
    def verification(self):
        return self._verification