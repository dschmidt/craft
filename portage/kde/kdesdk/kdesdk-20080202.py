import info

class subinfo(info.infoclass):
    def setTargets( self ):
        self.svnTargets['svnHEAD'] = 'branches/KDE/4.7/kdesdk'
        for ver in ['0', '1', '2', '3', '4']:
            self.targets['4.7.' + ver] = 'ftp://ftp.kde.org/pub/kde/stable/4.7.' + ver + '/src/kdesdk-4.7.' + ver + '.tar.bz2'
            self.targetInstSrc['4.7.' + ver] = 'kdesdk-4.7.' + ver
        self.patchToApply['4.7.0'] = ("kdesdk-4.7.0-20110822.diff", 1)
        self.defaultTarget = 'svnHEAD'

    def setDependencies( self ):
        self.dependencies['kde/kde-baseapps'] = 'default'
        self.dependencies['win32libs-bin/boost'] = 'default'
        self.dependencies['dev-util/zip'] = 'default'
        self.shortDescription = "KDE software development package (umbrello, okteta)"

from Package.CMakePackageBase import *

class Package(CMakePackageBase):
    def __init__( self ):
        self.subinfo = subinfo()
        CMakePackageBase.__init__( self )

if __name__ == '__main__':
    Package().execute()
