from Packager.MacPackagerBase import *

class MacDMGPackager( MacPackagerBase ):

    @InitGuard.init_once
    def __init__(self, whitelists=None, blacklists=None):
        CollectionPackagerBase.__init__(self, whitelists, blacklists)

    def _setDefaults(self):
        # TODO: Fix defaults
        self.defines.setdefault("apppath", "")
        self.defines.setdefault("appname", self.package.name.lower())

    def createPackageFoo(self):
        """ create a package """

        # Finally sanity check that we don't depend on absolute paths from the builder
        CraftCore.log.info("Checking for absolute library paths in package...")
        found_bad_dylib = False  # Don't exit immeditately so that we log all the bad libraries before failing:
        if not dylibbundler.areLibraryDepsOkay(mainBinary):
            found_bad_dylib = True
            CraftCore.log.error("Found bad library dependency in main binary %s", mainBinary)
        if not dylibbundler.checkLibraryDepsRecursively("Contents/Frameworks"):
            CraftCore.log.error("Found bad library dependency in bundled libraries")
            found_bad_dylib = True
        if not dylibbundler.checkLibraryDepsRecursively("Contents/PlugIns"):
            CraftCore.log.error("Found bad library dependency in bundled plugins")
            found_bad_dylib = True
        if found_bad_dylib:
            CraftCore.log.error("Cannot not create .dmg since the .app contains a bad library depenency!")
            return False

        name = self.binaryArchiveName(fileType="", includeRevision=True)
        dmgDest = os.path.join(self.packageDestinationDir(), f"{name}.dmg")
        if os.path.exists(dmgDest):
            utils.deleteFile(dmgDest)
        appName = self.defines['appname'] + ".app"
        if not utils.system(["create-dmg", "--volname", name,
                                # Add a drop link to /Applications:
                                "--icon", appName, "140", "150", "--app-drop-link", "350", "150",
                                dmgDest, appPath]):
            return False

        CraftHash.createDigestFiles(dmgDest)

        return True
