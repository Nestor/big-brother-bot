#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
from ConfigParser import NoOptionError
import os
from mock import Mock, sentinel, patch, call
import unittest2 as unittest

from b3.plugins.tk import TkPlugin, TkInfo
from b3.config import XmlConfigParser

from tests import B3TestCase


default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../b3/conf/plugin_tk.xml"))


class Test_Tk_plugin(B3TestCase):

    def setUp(self):
        super(Test_Tk_plugin, self).setUp()
        self.console.gameName = 'f00'
        self.conf = XmlConfigParser()
        self.p = TkPlugin(self.console, self.conf)

    def test_onLoadConfig_minimal(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
        </configuration>
        """)
        # WHEN
        self.p = TkPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        # THEN
        self.assertEqual(400, self.p._maxPoints)
        self.assertDictEqual({
            0: (2.0, 1.0, 2),
            1: (2.0, 1.0, 2),
            2: (1.0, 0.5, 1),
            20: (1.0, 0.5, 0),
            40: (0.75, 0.5, 0)
        }, self.p._levels)
        self.assertEqual(40, self.p._maxLevel)
        self.assertEqual(7, self.p._round_grace)
        self.assertEqual("sfire", self.p._issue_warning)
        self.assertTrue(self.p._grudge_enable)
        self.assertTrue(self.p._private_messages)
        self.assertEqual(100, self.p._damage_threshold)
        self.assertEqual(2, self.p._warn_level)
        self.assertEqual(0, self.p._tkpointsHalflife)
        self.assertEqual('1h', self.p._tk_warn_duration)

    def test_onLoadConfig(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="max_points">350</set>
                <set name="levels">0,1,2</set>
                <set name="round_grace">3</set>
                <set name="issue_warning">foo</set>
                <set name="grudge_enable">no</set>
                <set name="private_messages">off</set>
                <set name="damage_threshold">99</set>
                <set name="warn_level">10</set>
                <set name="halflife">3</set>
                <set name="warn_duration">3h</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">3</set>
            </settings>
            <settings name="level_1">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">4</set>
            </settings>
            <settings name="level_2">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">0.5</set>
                <set name="ban_length">5</set>
            </settings>
        </configuration>
        """)
        self.p = TkPlugin(self.console, self.conf)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual(350, self.p._maxPoints)
        self.assertDictEqual({
            0: (2.0, 1.0, 3),
            1: (2.0, 1.0, 4),
            2: (1.0, 0.5, 5),
        }, self.p._levels)
        self.assertEqual(2, self.p._maxLevel)
        self.assertEqual(3, self.p._round_grace)
        self.assertEqual("foo", self.p._issue_warning)
        self.assertFalse(self.p._grudge_enable)
        self.assertFalse(self.p._private_messages)
        self.assertEqual(99, self.p._damage_threshold)
        self.assertEqual(10, self.p._warn_level)
        self.assertEqual(3, self.p._tkpointsHalflife)
        self.assertEqual('3h', self.p._tk_warn_duration)


class Test_get_config_for_levels(Test_Tk_plugin):

    def setUp(self):
        Test_Tk_plugin.setUp(self)
        self.error_patcher = patch.object(self.p, 'error')
        self.error_mock = self.error_patcher.start()

    def tearDown(self):
        Test_Tk_plugin.tearDown(self)
        self.error_patcher.stop()

    def test_missing_level(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting NoOptionError")
        except NoOptionError:
            pass
        # THEN
        self.assertListEqual([], self.error_mock.mock_calls)

    def test_nominal_one_level(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length">3</set>
            </settings>
        </configuration>
        """)
        # WHEN
        levels = self.p.load_config_for_levels()
        # THEN
        self.assertDictEqual({
            0: (1.3, 1.1, 3),
        }, levels)
        self.assertListEqual([], self.error_mock.mock_calls)

    def test_nominal_many_levels(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0,20,80</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length">3</set>
            </settings>
            <settings name="level_20">
                <set name="kill_multiplier">1.8</set>
                <set name="damage_multiplier">1.3</set>
                <set name="ban_length">2</set>
            </settings>
            <settings name="level_80">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">1</set>
            </settings>
        </configuration>
        """)
        # WHEN
        levels = self.p.load_config_for_levels()
        # THEN
        self.assertDictEqual({
            0: (1.3, 1.1, 3),
            20: (1.8, 1.3, 2),
            80: (1.0, 1.0, 1),
        }, levels)
        self.assertListEqual([], self.error_mock.mock_calls)

    def test_level_junk(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">f00</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([call("'f00' is not a valid level number")], self.error_mock.mock_calls)

    def test_missing_section(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0,20,80</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length">3</set>
            </settings>
            <settings name="level_80">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">1</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([call("section 'level_20' is missing from the config file")], self.error_mock.mock_calls)

    def test_missing_kill_multiplier(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length">3</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call('option kill_multiplier is missing in section level_0'),
        ], self.error_mock.mock_calls)

    def test_missing_damage_multiplier(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="ban_length">3</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call('option damage_multiplier is missing in section level_0'),
        ], self.error_mock.mock_calls)

    def test_missing_ban_length(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">1.1</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call('option ban_length is missing in section level_0'),
        ], self.error_mock.mock_calls)

    def test_bad_kill_multiplier(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">f00</set>
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length">3</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call('value for kill_multiplier is invalid. could not convert string to float: f00'),
        ], self.error_mock.mock_calls)

    def test_bad_damage_multiplier(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">f00</set>
                <set name="ban_length">3</set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call('value for damage_multiplier is invalid. could not convert string to float: f00'),
        ], self.error_mock.mock_calls)

    def test_bad_ban_length(self):
        # GIVEN
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="levels">0</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">1.3</set>
                <set name="damage_multiplier">1.1</set>
                <set name="ban_length"></set>
            </settings>
        </configuration>
        """)
        # WHEN
        try:
            self.p.load_config_for_levels()
            self.fail("expecting ValueError")
        except ValueError:
            pass
        # THEN
        self.assertListEqual([
            call("value for ban_length is invalid. invalid literal for int() with base 10: ''"),
        ], self.error_mock.mock_calls)


@unittest.skipUnless(os.path.exists(default_plugin_file), reason="cannot get default plugin config file at %s" % default_plugin_file)
class Test_Tk_default_config(B3TestCase):

    def setUp(self):
        super(Test_Tk_default_config, self).setUp()
        self.console.gameName = 'f00'
        self.conf = XmlConfigParser()
        self.conf.load(default_plugin_file)
        self.p = TkPlugin(self.console, self.conf)
        self.p.onLoadConfig()

    def test_settings(self):
        self.assertEqual(400, self.p._maxPoints)
        self.assertEqual(40, self.p._maxLevel)
        self.assertEqual({
                0: (2.0, 1.0, 2),
                1: (2.0, 1.0, 2),
                2: (1.0, 0.5, 1),
                20: (1.0, 0.5, 0),
                40: (0.75, 0.5, 0)
        }, self.p._levels)
        self.assertEqual(7, self.p._round_grace)
        self.assertEqual("sfire", self.p._issue_warning)
        self.assertTrue(self.p._grudge_enable)
        self.assertTrue(self.p._private_messages)
        self.assertEqual(100, self.p._damage_threshold)
        self.assertEqual(2, self.p._warn_level)
        self.assertEqual(0, self.p._tkpointsHalflife)
        self.assertEqual('1h', self.p._tk_warn_duration)

    def test_messages(self):
        self.assertEqual("^7team damage over limit", self.p.config.get('messages', 'ban'))
        self.assertEqual("^7$vname^7 has forgiven $aname [^3$points^7]", self.p.config.get('messages', 'forgive'))
        self.assertEqual("^7$vname^7 has a ^1grudge ^7against $aname [^3$points^7]", self.p.config.get('messages', 'grudged'))
        self.assertEqual("^7$vname^7 has forgiven $attackers", self.p.config.get('messages', 'forgive_many'))
        self.assertEqual("^1ALERT^7: $name^7 auto-kick if not forgiven. Type ^3!forgive $cid ^7to forgive. [^3damage: $points^7]", self.p.config.get('messages', 'forgive_warning'))
        self.assertEqual("^7no one to forgive", self.p.config.get('messages', 'no_forgive'))
        self.assertEqual("^7Forgive who? %s", self.p.config.get('messages', 'players'))
        self.assertEqual("^7$name^7 has ^3$points^7 TK points", self.p.config.get('messages', 'forgive_info'))
        self.assertEqual("^7$name^7 cleared of ^3$points^7 TK points", self.p.config.get('messages', 'forgive_clear'))
        self.assertEqual("^3Do not attack teammates, ^1Attacked: ^7$vname ^7[^3$points^7]", self.p.config.get('messages', 'tk_warning_reason'))

    def test__default_messages(self):
        conf_items = self.p.config.items('messages')
        for conf_message_id, conf_message in conf_items:
            if conf_message_id not in self.p._default_messages:
                self.fail("%s should be added to the _default_messages dict" % conf_message_id)
            if conf_message != self.p._default_messages[conf_message_id]:
                self.fail("default message in the _default_messages dict for %s does not match the message from the config file" % conf_message_id)
        for default_message_id in self.p._default_messages:
            if default_message_id not in zip(*conf_items)[0]:
                self.fail("%s exists in the _default_messages dict, but not in the config file" % default_message_id)


class Test_TkInfo(unittest.TestCase):

    def setUp(self):
        self.my_cid = 1
        self.mock_plugin = Mock(name="plugin", spec=TkPlugin)
        self.info = TkInfo(self.mock_plugin, self.my_cid)

    def test_construct(self):
        self.assertIsNone(self.info.lastAttacker)
        self.assertEqual({}, self.info.attackers)
        self.assertEqual({}, self.info.attacked)
        self.assertEqual(0, self.info.points)

    def test_damage(self):
        self.assertNotIn(2, self.info._attacked)
        self.info.damage(cid=2, points=5)
        self.assertTrue(self.info._attacked[2])

    def test_damaged(self):
        cidA = 3
        self.assertNotIn(cidA, self.info._attackers)
        self.info.damaged(cidA, points=15)
        self.assertEqual(15, self.info._attackers[cidA])

        self.info.damaged(cidA, points=5)
        self.assertEqual(20, self.info._attackers[cidA])

        cidB = 2
        self.info.damaged(cidB, points=7)
        self.assertEqual(20, self.info._attackers[cidA])
        self.assertEqual(7, self.info._attackers[cidB])

    def test_grudge(self):
        cid = 4
        self.assertNotIn(cid, self.info._grudged)
        self.assertFalse(self.info.isGrudged(cid))
        self.info.grudge(cid=cid)
        self.assertIn(cid, self.info._grudged)
        self.assertTrue(self.info.isGrudged(cid))

    def test_getAttackerPoints(self):
        cidA = 2
        s = sentinel
        self.info._attackers[cidA] = s
        self.assertEqual(s, self.info.getAttackerPoints(cidA))

        cidB = 3
        self.assertEqual(0, self.info.getAttackerPoints(cidB))

    def test_points(self):
        self.assertEqual(0, self.info.points)

        cid2 = 2
        cid3 = 3
        infos = {
            cid2: TkInfo(self.mock_plugin, cid2),
            cid3: TkInfo(self.mock_plugin, cid3)
        }
        self.mock_plugin.console.clients.getByCID = Mock(side_effect=lambda cid:cid)
        self.mock_plugin.getClientTkInfo = Mock(side_effect=lambda cid:infos[cid])

        points_2 = 45
        self.info.damage(cid2, points_2)
        infos[cid2].damaged(self.my_cid, points_2)
        self.assertEqual(points_2, self.info.points)

        points_3 = 21
        self.info.damage(cid3, points_3)
        infos[cid3].damaged(self.my_cid, points_3)
        self.assertEqual(points_2 + points_3, self.info.points)

    def test_lastAttacker(self):
        self.assertIsNone(self.info.lastAttacker)
        cid2 = 2
        self.info.damaged(cid2, 32)
        self.assertEqual(cid2, self.info.lastAttacker)

    def test_forgive(self):
        cid2 = 2
        cid3 = 3
        self.info.damaged(cid2, 75)
        self.info.damaged(cid3, 47)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))
        self.info.forgive(cid2)
        self.assertEqual(0, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))

    def test_forgive_last_attacker(self):
        cid2 = 2
        cid3 = 3
        self.info.damaged(cid2, 75)
        self.info.damaged(cid3, 47)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))
        self.assertEqual(cid3, self.info.lastAttacker)
        self.info.forgive(cid3)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(0, self.info.getAttackerPoints(cid3))
        self.assertNotEqual(cid3, self.info.lastAttacker)

    def test_forgiven(self):
        self.mock_plugin.console = Mock()
        cid2 = 2
        self.info._attacked[cid2] = True
        self.info._warnings[cid2] = mock_warn = Mock()

        self.info.forgiven(cid2)

        self.assertNotIn(cid2, self.info._attacked)
        self.assertEqual(1, mock_warn.inactive)
        mock_warn.save.assert_called_once_with(self.mock_plugin.console)


if __name__ == '__main__':
    unittest.main()