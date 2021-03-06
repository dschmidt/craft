import info
import glob

class subinfo(info.infoclass):
    def setTargets(self):
        # not used  yet only for reference
        ver = str(CraftCore.compiler.getVersion())
        self.patchLevel[ver] = 1
        self.targets[ver] = ""
        self.description = "The compiler runtime package"
        self.defaultTarget = ver

    def setDependencies(self):
        self.buildDependencies["virtual/base"] = "default"
        if CraftCore.compiler.isMinGW():
            self.buildDependencies["dev-utils/mingw-w64"] = "default"


from Package.BinaryPackageBase import *


class PackageWin(BinaryPackageBase):
    def __init__(self):
        BinaryPackageBase.__init__(self)
        self.subinfo.options.package.disableBinaryCache = CraftCore.compiler.isMSVC()

    def fetch(self):
        return True

    def unpack(self):
        return True

    def install(self):
        destdir = os.path.join(self.installDir(), "bin")
        utils.createDir(destdir)

        files = []
        if CraftCore.compiler.isMinGW():
            files = ['libgomp-1.dll', 'libstdc++-6.dll', 'libwinpthread-1.dll']
            if CraftCore.compiler.isMinGW_W32():
                files.append('libgcc_s_sjlj-1.dll')
                srcdir = os.path.join(self.rootdir, "mingw", "bin")
            elif CraftCore.compiler.isMinGW_W64():
                files.append('libgcc_s_seh-1.dll')
                srcdir = os.path.join(self.rootdir, "mingw64", "bin")
        elif CraftCore.compiler.isMSVC():
            if self.buildType() != "Debug":
                if CraftCore.compiler.isMSVC2017():
                    redistDir = os.environ["VCTOOLSREDISTDIR"]
                elif CraftCore.compiler.isMSVC2015():
                    redistDir = os.path.join(os.environ["VCINSTALLDIR"], "redist")
                if redistDir:
                    files = glob.glob(os.path.join(redistDir, CraftCore.compiler.architecture, "**/*.dll"), recursive=True)
                else:
                    CraftCore.log.error("Unsupported Compiler")
                    return False
        for f in files:
            if not os.path.isabs(f):
                f = os.path.join(srcdir, f)
            utils.copyFile(f, os.path.join(destdir, os.path.basename(f)), linkOnly=False)
        return True


from Package.Qt5CorePackageBase import *


class Package(Qt5CoreSdkPackageBase):
    def __init__(self):
        Qt5CoreSdkPackageBase.__init__(self, condition=OsUtils.isWin(), classA=PackageWin)
