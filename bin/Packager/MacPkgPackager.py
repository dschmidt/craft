from Packager.MacPackagerBase import *

import utils

class MacPkgPackager(MacPackagerBase):
    def _setDefaults(self):
        # TODO: Fix defaults
        self.defines.setdefault("apppath", "")
        self.defines.setdefault("appname", self.package.name.lower())

    def createPackageFoo(self):
        pkgprojFile = "%s/admin/osx/macosx.pkgproj" % self.buildDir()

        installer = '%s-1.2.3.4' % self.package.name
        print(installer)
        installer_file = "%s.pkg" % installer
        print(installer_file)
        installer_file_tar="%s.pkg.tar" % installer_file
        print(installer_file_tar)
        installer_file_tar_bz2="%s.tar.bz2" % installer_file_tar
        print(installer_file_tar_bz2)
        installer_file_tbz="%s.pkg.tbz" % installer_file
        print(installer_file_tbz)

        # TODO: why not set it when configuring the pkg file cmake?
        # set the installer name to the copied prj config file
        utils.system(['packagesutil', '--file', pkgprojFile, 'set', 'project', 'name', 'installer'])
        utils.system(['packagesbuild', '--reference-folder', os.path.join(self.archiveDir(), 'bin'), '--build-folder', self.packageDestinationDir(), pkgprojFile])

        return True
