import info

class subinfo(info.infoclass):
    def setTargets( self ):
        self.versionInfo.setDefaultValues( )

        self.shortDescription = "KTextEditor provides an advanced embeddable text editor"

    def setDependencies( self ):
        self.buildDependencies["virtual/base"] = "default"
        self.buildDependencies["dev-util/extra-cmake-modules"] = "default"
        self.dependencies["kde/karchive"] = "default"
        self.dependencies["kde/kconfig"] = "default"
        self.dependencies["kde/kguiaddons"] = "default"
        self.dependencies["kde/ki18n"] = "default"
        self.dependencies["kde/kio"] = "default"
        self.dependencies["kde/kparts"] = "default"
        self.dependencies["kde/sonnet"] = "default"

from Package.CMakePackageBase import *

class Package(CMakePackageBase):
    def __init__( self ):
        CMakePackageBase.__init__( self )