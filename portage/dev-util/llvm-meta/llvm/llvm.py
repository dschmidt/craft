# -*- coding: utf-8 -*-
import info

class subinfo(info.infoclass):
    def setTargets( self ):
        self.versionInfo.setDefaultValues( )
        self.targetDigests['3.7.0'] = '0355c2fe01a8d17c3315069e6f2ef80c281e7dad'

        for ver in self.svnTargets.keys() | self.targets.keys():
            if ver in ["3.7.0", "3.7.1", "release_37"]:
                self.patchToApply[ ver ] = [("0002-use-DESTDIR-on-windows.patch", 1)]
            if ver in ["release_38"]:
                self.patchToApply[ver] = [("use-DESTDIR-on-windows-3.8.patch", 1)]


    def setDependencies( self ):
        self.buildDependencies['virtual/base'] = 'default'
        self.buildDependencies['dev-util/lld'] = 'default'
        self.buildDependencies['dev-util/clang'] = 'default'

from Package.CMakePackageBase import *

class Package(CMakePackageBase):
    def __init__( self, **args ):
        CMakePackageBase.__init__(self)
        self.subinfo.options.configure.defines = '-DLLVM_TARGETS_TO_BUILD="X86"'
        self.subinfo.options.configure.defines += " -DLLVM_EXTERNAL_LLD_SOURCE_DIR=\"%s\"" % portage.getPackageInstance('dev-util', 'lld').sourceDir().replace("\\", "/")
        self.subinfo.options.configure.defines += " -DLLVM_EXTERNAL_CLANG_SOURCE_DIR=\"%s\"" % portage.getPackageInstance('dev-util', 'clang').sourceDir().replace("\\", "/")
        if compiler.isMinGW():
            self.subinfo.options.configure.defines += " -DBUILD_SHARED_LIBS=ON"

    def configureOptions(self, defines=""):
        options = CMakePackageBase.configureOptions(self, defines)
        # just expect that we don't want to debug our compiler
        options += ' -DCMAKE_BUILD_TYPE=Release'
        return options

    def install(self):
        if not CMakePackageBase.install(self):
            return False
        if compiler.isMinGW():
            files = os.listdir(os.path.join(self.buildDir(), "lib"))
            for f in files:
                if f.endswith("dll.a"):
                    src = os.path.join(self.buildDir(), "lib", f)
                    dest = os.path.join(self.imageDir(), "lib", f)
                    if not os.path.exists(dest):
                        utils.copyFile(src, dest, False)
        return True