import info

from emerge_config import *

class subinfo(info.infoclass):
    def setTargets( self ):
        self.versionInfo.setDefaultVersions("http://download.kde.org/unstable/frameworks/${VERSION}/${PACKAGE_NAME}-${VERSION}.tar.xz",
                                            "http://download.kde.org/unstable/frameworks/${VERSION}/${PACKAGE_NAME}-${VERSION}.tar.xz.sha1",
                                            "${PACKAGE_NAME}-${VERSION}",
                                            "[git]kde:${PACKAGE_NAME}" )

        self.shortDescription = "Extra widgets for easier configuration support"
        

    def setDependencies( self ):
        self.buildDependencies["virtual/base"] = "default"
        self.buildDependencies["dev-util/extra-cmake-modules"] = "default"
        self.buildDependencies["win32libs/automoc"] = "default"
        self.buildDependencies["kde/kauth"] = "default"
        self.buildDependencies["kde/kcoreaddons"] = "default"
        self.buildDependencies["kde/kcodecs"] = "default"
        self.buildDependencies["kde/kconfig"] = "default"
        self.buildDependencies["kde/kdoctools"] = "default"
        self.buildDependencies["kde/kguiaddons"] = "default"
        self.buildDependencies["kde/ki18n"] = "default"
        self.buildDependencies["kde/kwidgetsaddons"] = "default"

from Package.CMakePackageBase import *

class Package(CMakePackageBase):
    def __init__( self ):
        CMakePackageBase.__init__( self )


    

