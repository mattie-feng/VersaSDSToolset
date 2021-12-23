import execute as ex
import sundry as sd


class Usage():
    # host部分使用手册
    disk = '''
    disk(d) {show(s)}'''

    disk_show = '''
    disk(d) show(s) [DISK]'''


class DiskCommands():
    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the disk management:create,delete,show
        """
        disk_parser = parser.add_parser(
            'disk', aliases='d', help='disk operation', usage=Usage.disk)
        disk_parser.set_defaults(func=self.print_disk_help)

        disk_subp = disk_parser.add_subparsers(dest='subargs_disk')

        """
        Show disk
        """

        p_show_disk = disk_subp.add_parser(
            'show', aliases='s', help='disk show', usage=Usage.disk_show)

        p_show_disk.add_argument(
            'disk',
            action='store',
            help='disk show [disk_name]',
            nargs='?',
            default='all')

        self.disk_parser = disk_parser
        self.p_show_disk = p_show_disk
        p_show_disk.set_defaults(func=self.show)

    @sd.deco_record_exception
    def show(self, args):
        disk = ex.Disk()
        disk.show(args.disk)

    def print_disk_help(self, *args):
        self.disk_parser.print_help()
