import os
import info

class subinfo( info.infoclass ):
    def setTargets( self ):
        for ver in ['0', '1', '2', '3', '4']:
          self.targets['4.7.' + ver] = 'ftp://ftp.kde.org/pub/kde/stable/4.7.' + ver + '/src/kde-l10n/kde-l10n-%s-4.7.' + ver + '.tar.bz2'
          self.targetInstSrc['4.7.' + ver] = 'kde-l10n-%s-4.7.' + ver

        # Checking out from SVN is currently broken. The fetch
        # Action is not made for it (see hasSVNTargets) and also
        # The checkoutDir override will not work correctly
        # Please see the master branch for svnHEAD
        # self.svnTargets['svnHEAD'] = 'branches/stable/l10n-kde4/%s'
        self.defaultTarget = '4.7.0'

    def setDependencies( self ):
        self.buildDependencies['dev-util/cmake'] = 'default'
        self.buildDependencies['kde/kdelibs'] = 'default'
        self.buildDependencies['dev-util/gettext-tools'] = 'default'
   

from Package.CMakePackageBase import *

class Package( CMakePackageBase ):
    def __init__( self  ):
        self.subinfo = subinfo()
        CMakePackageBase.__init__( self )
        self.language = None
        # because of the large amount of packages
        # it is very annoying to restart the build, 
        # wasting several hours, so ignore any errors 
        # for now
        self.subinfo.options.make.ignoreErrors = True
        self.subinfo.options.exitOnErrors = False
        # overwrite the workDir function that is inherited from SourceBase
        self.source.workDir = self.workDir.__get__( self, Package )
        self.source.localFileNames = self.localFileNames.__get__( self, Package )

    def localFileNames( self ):
        filenames = []
        for i in range( self.repositoryUrlCount() ):
            filenames.append( os.path.basename( self.repositoryUrl( i ) ) )
        return filenames

    def configureSourceDir( self ):
        return CMakePackageBase.configureSourceDir( self ) % self.language
        
    def sourceDir( self ):
        return CMakePackageBase.sourceDir( self ) % self.language
        
    def imageDir( self ):
        return os.path.join( CMakePackageBase.imageDir( self ), self.language )

    def repositoryUrl( self, index=0 ):
        # \todo we cannot use CMakePackageBase here because repositoryPath 
        # then is not be overrideable for unknown reasons 
        url = CMakePackageBase.repositoryUrl( self, index ) % self.language
        return url

    def workDir( self ):
        dir = os.path.join( CMakePackageBase.workDir( self ), self.language )
        return dir

    def fetch( self ):
        filenames = self.localFileNames()

        if ( self.source.noFetch ):
            utils.debug( "skipping fetch (--offline)" )
            return True

        self.source.setProxy()
        if self.subinfo.hasTarget():
            return utils.getFiles( self.subinfo.target() % self.language, self.downloadDir() )
        else:
            return utils.getFiles( "", self.downloadDir() )

    def unpack( self ):
        autogen = os.path.join( self.packageDir() , "autogen.py" )

        filenames = self.localFileNames()

        # the following code is taken from ArchiveSource::unpack() function
        # it will not remove already existing files
        destdir = self.workDir()
        utils.debug( "unpacking files into work root %s" % destdir, 1 )

        if not utils.unpackFiles( self.downloadDir(), filenames, destdir ):
            return False

        return True

        # execute autogen.py and generate the CMakeLists.txt files
#        cmd = "cd %s && python %s %s %s" % \
#              ('..', autogen, self.sourceDir(), self.language )
#        return self.system( cmd )

    def install( self ):
        self.subinfo.options.install.useMakeToolForInstall = False
        CMakePackageBase.install( self )
        #ignore errors
        return True

    def createPackage( self ):
        self.subinfo.options.package.packageName = 'kde4-l10n-%s' % self.language
        self.subinfo.options.package.withCompiler = False
        return CMakePackageBase.createPackage(self)
        
        
class MainInfo( info.infoclass ):
    def setTargets( self ):
        self.svnTargets['svnHEAD'] = 'trunk/l10n-kde4/scripts'
        self.defaultTarget = 'svnHEAD'
        self.languages = dict()
        
        self.languages['svnHEAD'] = 'ar bg ca ca@valencia cs csb da de el en_GB eo es et eu fi fr fy ga'
        self.languages['svnHEAD'] += ' gl gu he hi hr hu id is it ja kk km kn ko lt lv mai mk ml nb nds' 
        self.languages['svnHEAD'] += ' nl nn pa pl pt pt_BR ro ru si sk sl sr sv tg tr uk wa zh_CN zh_TW'

        self.languages['4.7.0'] = 'ar bg bs ca ca@valencia cs da de el en_GB es et eu fi fr ga gl he hr hu ia id is it ja kk km kn ko lt lv nb nds nl nn pa pl pt pt_BR ro ru sk sl sr sv th tr ug uk wa zh_CN zh_TW'
        self.languages['4.7.4'] = 'ar bg bs ca ca@valencia cs da de el en_GB es et eu fi fr ga gl he hr hu ia id is it ja kk km kn ko lt lv nb nds nl nn pa pl pt pt_BR ro ru si sk sl sr sv th tr ug uk wa zh_CN zh_TW'
        for ver in ['0', '1', '2', '3']:
            self.languages['4.7.' + ver] = self.languages['4.7.0']

     #for testing
        #self.languages['svnHEAD']  = 'de'
    
    def setDependencies( self ):
        self.buildDependencies['dev-util/cmake'] = 'default'
        self.buildDependencies['dev-util/gettext-tools'] = 'default'
    
class MainPackage( CMakePackageBase ):
    def __init__( self  ):
        self.subinfo = MainInfo()
        CMakePackageBase.__init__( self )
        self.kde4_l10n = Package()

        # set to any language to start building from 
        ## \todo when emerge.py is able to provide command line options to us
        # it would be possible to set this from command line 
        self.startLanguage = None
        
    def execute( self ):
        ( command, option ) = self.getAction()
        self.errors = dict()
        ## \todo does not work yet see note in PackageBase::getAction()
#        if option <> None:
#            languages = option.split()
#        else:

        # build target is not set here for unknown reasons, set manually for now
        self.buildTarget='4.7.0'
        if self.subinfo.languages[self.buildTarget]: 
            languages = self.subinfo.languages[self.buildTarget].split()
        else:
            languages = self.subinfo.languages['svnHEAD'].split()
        
        found=None
        for language in languages:
            if not found and self.startLanguage:
                if self.startLanguage <> language:
                    continue
                else:
                    found = True
            
            self.kde4_l10n.language = language
            utils.debug( "current language: %s current command: %s" % ( self.kde4_l10n.language, command ), 1 )
            self.kde4_l10n.runAction( command )
#                self.errors["%s-%s" % ( language, command )] = 1

        if self.errors:
            utils.debug( "Errors that happened while executing last command: %s" % self.errors, 2 )
        return True    
        
if __name__ == '__main__':
    MainPackage().execute()

