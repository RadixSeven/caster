from subprocess import Popen

from dragonfly import (Function, Grammar, IntegerRef, MappingRule, AppContext, Choice)

from caster.asynch.hmc import h_launch
from caster.lib import  settings, control, utilities
from caster.lib.dfplus.state.short import R


def kill():
    control.nexus().comm.get_com("hmc").kill()

def complete():
    control.nexus().comm.get_com("hmc").complete()

def hmc_checkbox(n):
    # can easily check multiple boxes, use a comma-separated list of numbers instead of str(n)
    control.nexus().comm.get_com("hmc").do_action("check", [int(n)])

def hmc_focus(field):
    # can easily check multiple boxes, use a comma-separated list of numbers instead of str(n)
    control.nexus().comm.get_com("hmc").do_action("focus", str(field))

def hmc_recording_check_range(n, n2):
    control.nexus().comm.get_com("hmc").do_action("check_range", [int(n), int(n2)])

def hmc_recording_exclude(n):
    control.nexus().comm.get_com("hmc").do_action("exclude", int(n))
    
def hmc_recording_repeatable():
    control.nexus().comm.get_com("hmc").do_action("repeatable")

def hmc_directory_browse():
    control.nexus().comm.get_com("hmc").do_action("dir")

def hmc_confirm(value):
    control.nexus().comm.get_com("hmc").do_action(value)
    
def hmc_settings_complete():
    control.nexus().comm.get_com("hmc").complete()
    
class HMCRule(MappingRule):
    mapping = {
        "kill homunculus":              R(Function(kill), rdescript="Kill Helper Window"),
        "complete":                     R(Function(complete), rdescript="Complete Input"),
        "check <n>":                    R(Function(hmc_checkbox, extra="n"), rdescript="Check Checkbox"),
        "focus <field> [box]":          R(Function(hmc_focus, extra="field"), rdescript="Focus Field"),
        # specific to macro recorder
        "check from <n> to <n2>":       R(Function(hmc_recording_check_range, extra={"n", "n2"}), rdescript="Check Range"),
        "exclude <n>":                  R(Function(hmc_recording_exclude, extra="n"), rdescript="Uncheck Checkbox"),
        "[make] repeatable":            R(Function(hmc_recording_repeatable), rdescript="Make Macro Repeatable"),
        # specific to directory browser
        "browse":                       R(Function(hmc_directory_browse), rdescript="Browse Computer"),
        # specific to confirm
        "confirm":                      R(Function(hmc_confirm, value=True), rdescript="HMC: Confirm Action"),
        "cancel":                       R(Function(hmc_confirm, value=False), rdescript="HMC: Cancel Action"),
    }   
    extras = [
              IntegerRef("n", 1, 25),
              IntegerRef("n2", 1, 25),
              Choice("field",
                    {"vocabulary": "vocabulary", "word": "word"
                    }),
             ]
    defaults = {
               
               }


c = AppContext(title=settings.HOMUNCULUS_VERSION)
grammar = Grammar("hmc", context=c)
grammar.add_rule(HMCRule())
grammar.load()

class HMCRuleSettings(MappingRule):
    mapping = {
        "kill homunculus":              R(Function(kill), rdescript="Kill Settings Window"),
        "complete":                     R(Function(hmc_settings_complete), rdescript="Complete Input"),
    }


sc = AppContext(title=settings.SETTINGS_WINDOW_TITLE+settings.SOFTWARE_VERSION_NUMBER)
grammar_settings = Grammar("hmc2", context=sc)
grammar_settings.add_rule(HMCRuleSettings())
grammar_settings.load()



def get_settings_from_settings_window(data):
    settings.SETTINGS = data
    settings.save_config()
    # TODO: apply new settings

def launch_status():
    if not utilities.window_exists(None, settings.STATUS_WINDOW_TITLE):
        Popen(["pythonw", settings.SETTINGS["paths"]["STATUS_WINDOW_PATH"]])
    
def toggle_status():
    enabled = settings.SETTINGS["miscellaneous"]["status_window_enabled"]
    if enabled:
        control.nexus().intermediary.kill()
    else:
        launch_status()
    settings.SETTINGS["miscellaneous"]["status_window_enabled"] = not enabled
    settings.save_config()

def settings_window():
#     if control.nexus().dep.WX:
    if not utilities.window_exists(None, settings.STATUS_WINDOW_TITLE + settings.SOFTWARE_VERSION_NUMBER):
        h_launch.launch(settings.WXTYPE_SETTINGS, get_settings_from_settings_window)
#     else:
#         utilities.availability_message("Settings Window", "wxPython")

class LaunchRule(MappingRule):

    mapping = {
        "toggle status window":     R(Function(toggle_status), rdescript="Toggle Status Window"), 
        "launch settings window":   R(Function(settings_window), rdescript="Launch Settings Window"), 
        }
    extras = []
    defaults = {}

#---------------------------------------------------------------------------


grammarw = Grammar("Caster Windows")
grammarw.add_rule(LaunchRule())
grammarw.load()

if settings.SETTINGS["miscellaneous"]["status_window_enabled"]:
    launch_status()

def unload():
    global grammar, grammar_settings, grammarw
    if grammar: grammar.unload()
    if grammar_settings: grammar_settings.unload()
    if grammarw: grammarw.unload()
    grammar = None
    grammar_settings = None
    grammarw = None
