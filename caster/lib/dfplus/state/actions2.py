import time

from dragonfly import Function, Key
import win32gui, win32con

from caster.asynch.hmc import h_launch
from caster.lib import settings, control, utilities
from caster.lib.dfplus.monkeypatch import Window
from caster.lib.dfplus.state.actions import AsynchronousAction, ContextSeeker
from caster.lib.dfplus.state.short import L, S

'''CB's solution for focus window failure'''
win32gui.SystemParametersInfo(win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 1)

class ConfirmAction(AsynchronousAction):
    '''
    Similar to AsynchronousAction, but the repeated action is always
    checking on the Homunculus response.
    -
    Homunculus response guide:
    0: no response yet
    1: True
    2: False
    '''
    def __init__(self, base, rspec="default", rdescript="unnamed command (RA)"):
        mutable_integer = {"value": 0}
        def check_response(): # signals to the stack to cease waiting, return True terminates
            return mutable_integer["value"]!=0
        self.mutable_integer = mutable_integer
        AsynchronousAction.__init__(self, 
                                    [L(S(["cancel"], check_response, None))], 
                                    1, 60, rdescript, False)# cannot block, if it does, it'll block its own confirm command
        self.base = base
        self.rspec = rspec
    def _execute(self, data=None):
        confirm_stack_item = self.state.generate_confirm_stack_item(self, data)
        self.mutable_integer["value"] = 0
        mutable_integer = self.mutable_integer
        def hmc_closure(data):
            '''
            receives response from homunculus, uses it to
            stop the stack and tell the ConfirmAction how
            to execute
            '''
            mutable_integer["value"] = data["confirm"]
            confirm_stack_item.receive_hmc_response(data["confirm"])
                    
        h_launch.launch(settings.QTYPE_CONFIRM, hmc_closure, "_".join(self.rdescript.split(" ")))
        self.state.add(confirm_stack_item)

class FuzzyMatchAction(ContextSeeker):
    '''
    list_function: provides a list of strings to filter
        ; takes no parameters, returns a list
    filter_function: reduces the size of the list from list_function
        ; can be null, takes dragonfly data and list from  list_function
    selection_function: what to do with the result that the user chooses
        ; takes a string, does something with it, returns nothing
    default_1: speaking a next command other than a number or cancel activates the first choice in the list
        ; 
    '''
    TEN = ["numb one", "numb two", "numb three", "numb four", "numb five", 
       "numb six", "numb seven", "numb eight", "numb nine", "numb ten"]
    def __init__(self, list_function, filter_function, selection_function, default_1=True, rspec="default", rdescript="unnamed command (FM)"):
        def get_choices(data):
            choices = list_function()
            if filter_function:
                choices = filter_function(data, choices) # the filter function is responsible for using the data to filter the choices
            while len(choices)<len(FuzzyMatchAction.TEN):
                choices.append("") # this is questionable
            return choices
        self.choice_generator = get_choices
        
        mutable_list = {"value": None} # only generate the choices once, and show them between the action and the stack item
        self.mutable_list = mutable_list
        
        def execute_choice(spoken_words=[]):
            n = -1
            while len(spoken_words)>2:# in the event the last words spoken were a command chain,
                spoken_words.pop()    # get only the number trigger
            j = ""
            if len(spoken_words)>0:
                j = " ".join(spoken_words)
            if j in FuzzyMatchAction.TEN:
                n = FuzzyMatchAction.TEN.index(j)
            if n == -1: n = 0
            selection_function(mutable_list["value"][n])
        def cancel_message():
            control.nexus().intermediary.text("Cancel ("+rdescript+")")
        forward = [L(S([""], execute_choice, consume=False),
                     S(["number"], execute_choice, use_spoken=True), 
                     S(["cancel", "clear"], cancel_message)
                    )
                  ]
        if not default_1: # make cancel the default
            context_level = forward[0]
            a = context_level.sets[0]
            context_level.sets[0] = context_level.sets[2]
            context_level.sets[2] = a
        ContextSeeker.__init__(self, None, forward, rspec, rdescript)
    
    def _execute(self, data=None):
        choices = self.choice_generator(data)
        display_string = ""
        for i in range(0, 10):
            display_string += str(i+1)+" - "+choices[i]
            if i+1<10: display_string += "\n"
        control.nexus().intermediary.hint(display_string)
        self.mutable_list["value"] = choices
        self.state.add(self.state.generate_context_seeker_stack_item(self, data))


class SuperFocusWindow(AsynchronousAction):
    '''
    Workaround class for Dragonfly's FocusWindow, which only works on titles and 
    32-bit executables, and sometimes fails to work at all. 
    '''
    @staticmethod
    def focus_was_success(title, executable):
        w=Window.get_foreground()
        success=True
        if title!=None:
            success=title in w.title
        if success and executable!=None:
            success=executable in w.executable
        return success
    
    @staticmethod
    def path_from_executable(executable):
        for win in Window.get_all_windows():
            if executable in win.executable:
                return win.executable
    
    def __init__(self, executable=None, title=None, time_in_seconds=1, repetitions=15, 
        rdescript="unnamed command (SFW)", blocking=False):
        assert executable!=None or title!=None, "SuperFocusWindow needs executable or title"
        def attempt_focus():
            for win in Window.get_all_windows():
                w=win
                found_match=True
                if title!=None:
                    found_match=title in w.title
                if found_match and executable!=None:
                    found_match=executable in w.executable
                if found_match:
                    try:
                        # this is still broken
                        win32gui.SetWindowPos(w.handle,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)  
                        win32gui.SetWindowPos(w.handle,win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)  
                        win32gui.SetWindowPos(w.handle,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
                        Key("alt").execute()
                        time.sleep(0.5)
                        win32gui.SetForegroundWindow(w.handle)
                        w.set_foreground()
                    except Exception:
                        utilities.report("Unable to set focus:\ntitle: "+w.title+"\nexe: "+w.executable)
                    break
             
            # do not assume that it worked
            success = SuperFocusWindow.focus_was_success(title, executable)
            if not success:
                if title!=None:
                    print "title failure: ", title, w.title
                if executable!=None:
                    print "executable failure: ", executable, w.executable, executable in w.executable
            return success
            
        forward=[L(S(["cancel"], attempt_focus))]
        AsynchronousAction.__init__(self, forward, time_in_seconds=time_in_seconds, repetitions=repetitions, 
                                    rdescript=rdescript, blocking=blocking, 
                                    finisher=Function(control.nexus().intermediary.text, message="SuperFocus Complete")+Key("escape"))
        self.show = False
        