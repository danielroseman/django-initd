from optparse import make_option
import signal
from django.core.management.base import NoArgsCommand
from initd import Initd

class DaemonCommand(NoArgsCommand):
    """
    Run a management command as a daemon.

    Subclass this and override the `loop_callback` method with the code the 
    daemon process should run. Optionally, override `exit_callback` with 
    code to run when the process is stopped.

    Alternatively, if your code has more complex setup/shutdown requirements,
    override `handle_noargs` along the lines of the basic version here. 
    
    Pass one of --start, --stop, --restart or --status to work as a daemon.
    Otherwise, the command will run as a standard application.
    """
    requires_model_validation = True
    WORKDIR = '.'
    UMASK = 0
    PID_FILE = 'daemon_command.pid'
    LOGFILE = 'daemon_command.log'
    STDOUT = '/dev/null'
    STDERR = STDOUT

    option_list = NoArgsCommand.option_list + (
        make_option('--start', action='store_const', const='start', dest='action',
                    help='Start the daemon'),
        make_option('--stop', action='store_const', const='stop', dest='action',
                    help='Stop the daemon'),
        make_option('--restart', action='store_const', const='restart', dest='action',
                    help='Stop and restart the daemon'),
        make_option('--status', action='store_const', const='status', dest='action',
                    help='Report whether the daemon is currently running or stopped'),
        make_option('--workdir', action='store', dest='workdir', default=WORKDIR,
            help='Full path of the working directory to which the process should '
            'change on daemon start.'),
        make_option('--umask', action='store', dest='umask', default=UMASK, type="int",
            help='File access creation mask ("umask") to set for the process on '
            'daemon start.'),
        make_option('--pidfile', action='store', dest='pid_file', 
                    default=PID_FILE, help='PID filename.'),
        make_option('--logfile', action='store', dest='log_file',
                    default=LOGFILE, help='Path to log file'),
        make_option('--stdout', action='store', dest='stdout', default=STDOUT,
                    help='Destination to redirect standard out'),
        make_option('--stderr', action='store', dest='stderr', default=STDERR,
                    help='Destination to redirect standard error'),
    )


    def loop_callback(self):
        raise NotImplementedError

    def exit_callback(self):
        pass

    def handle_noargs(self, **options):
        action = options.pop('action', None)
        
        if action:
            # daemonizing so set up functions to call while running and at close
            daemon = Initd(**options)
            daemon.execute(action, run=self.loop_callback, exit=self.exit_callback)
        else:
            # running in console, so set up signal to call on ctrl-c
            signal.signal(signal.SIGINT, lambda sig, frame: self.exit_callback())
            self.loop_callback()
