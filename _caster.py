'''
main Caster module
Created on Jun 29, 2014
'''

from subprocess import Popen
import time

try:
    from caster.lib import settings# requires nothing
    settings.WSR = __name__ == "__main__"
    from caster.lib import utilities# requires settings
    from caster.lib import control# requires settings
    from caster.lib.dfplus.state.stack import CasterState# requires control
    control.nexus().inform_state(CasterState())
    
    from caster.apps import *
    from caster.asynch import *
    from caster.lib import ccr, context, recording
    from caster.asynch import auto_com
    import caster.dev#, caster.wsr
    from caster.lib.dfplus.hint import _nodes
    try:
        import caster.w
    except Exception:
        pass
    from caster.asynch.hmc import h_launch
    from caster.asynch.hmc import vocabulary_processing
    from caster.asynch.sikuli import sikuli
    from caster.lib import navigation, password
    from caster.lib.pita import scanner
    from caster.lib.dfplus.state.short import R
    
    
    ccr.initialize_ccr()
    recording.load_alias_rules()
    recording.load_recorded_rules()
except:
    print "\nAttempting to load CCR anyway..."
    from caster.lib import ccr, utilities
    utilities.simple_log()
    ccr.initialize_ccr()

from dragonfly import (Key, Function, Grammar, Playback, IntegerRef, Dictation, Choice, Pause, MappingRule)
        


def change_monitor():
    if settings.SETTINGS["miscellaneous"]["sikuli_enabled"]:
        Playback([(["monitor", "select"], 0.0)]).execute()
    else:
        utilities.report("This command requires SikuliX to be enabled in the settings file")
       
class MainRule(MappingRule):
    
    @staticmethod
    def generate_CCR_choices():
        choices = {}
        for ccr_choice in settings.get_list_of_ccr_config_files():
            choices[settings.get_ccr_config_file_pronunciation(ccr_choice)] = ccr_choice
        return Choice("ccr_mode", choices)
    
    mapping = {
    # Dragon NaturallySpeaking commands moved to dragon.py
    
    # hardware management
    "volume <volume_mode> [<n>]":   R(Function(navigation.volume_control, extra={'n', 'volume_mode'}), rdescript="Volume Control"),
    "change monitor":               R(Key("w-p") + Pause("100") + Function(change_monitor), rdescript="Change Monitor"),
    
    # window management
    'minimize':                     Playback([(["minimize", "window"], 0.0)]),
    'maximize':                     Playback([(["maximize", "window"], 0.0)]),
    "remax":                        R(Key("a-space/10,r/10,a-space/10,x"), rdescript="Force Maximize"),
        
    # passwords
    'hash password <text> <text2> <text3>':                    R(Function(password.hash_password), rdescript="Get Hash Password"),
    'get password <text> <text2> <text3>':                     R(Function(password.get_password), rdescript="Get Seed Password"),
    'get restricted password <text> <text2> <text3>':          R(Function(password.get_restricted_password), rdescript="Get Char-Restricted Password"),
    'quick pass <text> <text2> <text3>':                       R(Function(password.get_simple_password), rdescript="Get Crappy Password"),
    
    # mouse alternatives
    "legion":                       R(Function(navigation.mouse_alternates, mode="legion"), rdescript="Activate Legion"),
    "rainbow":                      R(Function(navigation.mouse_alternates, mode="rainbow"), rdescript="Activate Rainbow Grid"),
    "douglas":                      R(Function(navigation.mouse_alternates, mode="douglas"), rdescript="Activate Douglas Grid"),
    
    # pita (fuzzy string matching)
    "scan directory":               R(Function(scanner.scan_directory), rdescript="Scan Directory For PITA"),
    "rescan current":               R(Function(scanner.rescan_current_file), rdescript="Rescan Current File For PITA"),
    
    # macro recording and automation
    "record from history":          R(Function(recording.record_from_history), rdescript="Create Macro From Spoken"),
    "delete recorded macros":       R(Function(recording.delete_recorded_rules), rdescript="Delete Recorded Macros"),
    "wait sec [<n>]":               R(Pause("%(n)d00"), rdescript="Wait (Macro Recording)"),
    
    # aliasing
    "alias <text>":                 R(Function(recording.add_alias), rdescript="Create Alias Command"),
    "delete aliases":               R(Function(recording.delete_alias_rules), rdescript="Delete All Alias Commands"),
    "chain alias":                  R(Function(recording.get_chain_alias_spec), rdescript="Create CCR Alias Command"), 
    
    # miscellaneous
    "<enable_disable> <ccr_mode>":  R(Function(ccr.set_active_command), rdescript="Enable CCR Module"),
    "refresh <ccr_mode>":           R(Function(ccr.refresh_from_files), rdescript="Refresh CCR Module"), 
    "again (<n> [(times|time)] | do)":R(Function(recording.repeat_that), rdescript="Repeat Last Action"),
#     "edit settings":                R(Function(), rdescript="Edit Caster Settings"), 
    
    }
    extras = [
              IntegerRef("n", 1, 50),
              Dictation("text"),
              Dictation("text2"),
              Dictation("text3"),
              Choice("enable_disable",
                    {"enable": 1, "disable": 0
                    }),
              Choice("volume_mode",
                    {"mute": "mute", "up":"up", "down":"down"
                     }),
              generate_CCR_choices.__func__()
             ]
    defaults = {"n": 1, "nnv": 1,
               "text": "", "volume_mode": "setsysvolume",
               "enable":-1
               }


grammar = Grammar('general')
grammar.add_rule(MainRule())
grammar.load()

def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None
    ccr.unload()
    sikuli.unload()

if settings.SETTINGS["miscellaneous"]["status_window_enabled"]:
    utilities.report("\nWARNING: Status Window is an experimental feature, and there is a known freezing glitch with it.\n")
utilities.report("*- Starting " + settings.SOFTWARE_NAME + " -*")


if __name__ == "__main__":
    import pythoncom
    print "Windows Speech Recognition is garbage; it is " \
        +"recommended that you not run Caster this way. " \
        + ""
    while True:
        pythoncom.PumpWaitingMessages()  # @UndefinedVariable
        time.sleep(.1)