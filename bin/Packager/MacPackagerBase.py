from Packager.CollectionPackagerBase import *
from Blueprints.CraftPackageObject import CraftPackageObject
from Utils import CraftHash
from pathlib import Path
import contextlib
import io
import subprocess
import stat
import glob
import utils

class MacPackagerBase(CollectionPackagerBase):
    def _setDefaults(self):
        # TODO: Fix defaults
        self.defines.setdefault("apppath", "")
        self.defines.setdefault("appname", self.package.name.lower())

    def createPackage(self):
        CraftCore.log.debug("packaging using the MacPackagerBase")

        if not self.internalCreatePackage():
            return False

        self._setDefaults()

        archive = os.path.normpath(self.archiveDir())
        appPath = self.defines['apppath']
        if not appPath:
            apps = glob.glob(os.path.join(archive, f"**/{self.defines['appname']}.app"), recursive=True)
            if len(apps) != 1:
                CraftCore.log.error(f"Failed to detect {self.defines['appname']}.app for {self}, please provide a correct self.defines['apppath'] or a relative path to the app as self.defines['apppath']")
                return False
            appPath = apps[0]
        appPath = os.path.join(archive, appPath)
        appPath = os.path.normpath(appPath)


        CraftCore.log.info(f"Packaging {appPath}") # "9B5WD74GWJ"

        self.appPath = appPath

        targetLibdir = os.path.join(appPath, "Contents", "Frameworks")
        utils.createDir(targetLibdir)

        moveTargets = [
            (os.path.join(archive, "lib", "plugins"), os.path.join(appPath, "Contents", "PlugIns")),
            (os.path.join(archive, "plugins"), os.path.join(appPath, "Contents", "PlugIns")),
            (os.path.join(archive, "lib"), targetLibdir),
            (os.path.join(archive, "share"), os.path.join(appPath, "Contents", "Resources"))]

        if not appPath.startswith(archive):
            moveTargets += [(os.path.join(archive, "bin"), os.path.join(appPath, "Contents", "MacOS"))]

        for src, dest in moveTargets:
            if os.path.exists(src):
                if not utils.mergeTree(src, dest):
                    return False

        dylibbundler = MacDylibBundler(appPath)
        CraftCore.log.info("Bundling main binary dependencies...")
        mainBinary = Path(appPath, "Contents", "MacOS", "%s" % self.defines['appname'])
        if not dylibbundler.bundleLibraryDependencies(mainBinary):
            return False

        if not utils.system(["install_name_tool", "-add_rpath", "@executable_path/../Frameworks", "-delete_rpath", "/Users/administrator/CraftMaster/macos-64-clang/lib", mainBinary], logCommand=False):
            CraftCore.log.error("failed to add rpath to '%s'",
                                mainBinary)
            return False
        #if not utils.system(["install_name_tool", "-add_rpath", "@executable_path/.", mainBinary], logCommand=False):
            #CraftCore.log.error("failed to add rpath to '%s'",
                                #mainBinary)
            #return False

        sideBinary = Path(appPath, "Contents", "MacOS", "%scmd" % self.defines['appname'])
        if not utils.system(["install_name_tool", "-add_rpath", "@executable_path/../Frameworks", "-delete_rpath", "/Users/administrator/CraftMaster/macos-64-clang/lib", sideBinary], logCommand=False):
            CraftCore.log.error("failed to add rpath to '%s'",
                                sideBinary)
            return False

        #sideBinary = Path(appPath, "Contents", "MacOS", "%scmd" % self.defines['appname'])
        #if not utils.system(["install_name_tool", "-add_rpath", "@executable_path/.", sideBinary], logCommand=False):
            #CraftCore.log.error("failed to add rpath to '%s'",
                                #sideBinary)
            #return False


        #if not utils.system("install_name_tool -change libz.1.dylib @rpath/libz.1.dylib /Users/administrator/CraftMaster/macos-64-clang/build/owncloud/owncloud-client/archive/bin/owncloud.app/Contents/MacOS/owncloudcmd", logCommand=False):
            #CraftCore.log.error("HACK FAILED")
            #return False



        # Fix up the library dependencies of files in Contents/Frameworks/
        CraftCore.log.info("Bundling library dependencies...")
        if not dylibbundler.fixupAndBundleLibsRecursively("Contents/Frameworks"):
            return False
        CraftCore.log.info("Bundling plugin dependencies...")
        if not dylibbundler.fixupAndBundleLibsRecursively("Contents/PlugIns"):
            return False

        if not utils.system(["macdeployqt", appPath, "-verbose=1"]):
            return False

        # macdeployqt might just have added some explicitly blacklisted files
        blackList = Path(self.packageDir(), "mac_blacklist.txt")
        if blackList.exists():
            blackList = [self.read_blacklist(str(blackList))]
            # use it as whitelist as we want only matches, ignore all others
            matches = self.traverse(appPath, whitelist=lambda x:self.blacklisted(x, blackList), blacklist=lambda x:True)
            for f in matches:
                CraftCore.log.info(f"Remove blacklisted file: {f}")
                utils.deleteFile(f)

        # macdeployqt adds some more plugins so we fix the plugins after calling macdeployqt
        dylibbundler.checkedLibs = set()  # ensure we check all libs again (but
        # we should not need to make any changes)
        CraftCore.log.info("Fixing plugin dependencies after macdeployqt...")
        if not dylibbundler.fixupAndBundleLibsRecursively("Contents/PlugIns"):
            return False
        CraftCore.log.info("Fixing library dependencies after macdeployqt...")
        if not dylibbundler.fixupAndBundleLibsRecursively("Contents/Frameworks"):
            return False

        if not self.signPackage():
            return False

        return self.createPackageFoo()

    def signPackage(self):
        CraftCore.log.error("signing not implemented yet in MacPackagerBase")


                # if signing is enabled ....

        if not utils.system("rm -rvf /Users/administrator/CraftMaster/macos-64-clang/build/owncloud/owncloud-client/archive/bin/owncloud.app/Contents/Frameworks/engines-1.1 /Users/administrator/CraftMaster/macos-64-clang/build/owncloud/owncloud-client/archive/bin/owncloud.app/Contents/Frameworks/python2.7"):
            return False

        developerId = "Developer ID Application"
        # Sign .app
        if not utils.system(["codesign", "-s", developerId, "--force", "--preserve-metadata=entitlements", "--verbose=4", "--deep", self.appPath]):
            return False
        ## Verify signature
        if not utils.system(["codesign", "-dv", self.appPath]):
            return False
        if not utils.system(["codesign", "--verify", "-v", self.appPath]):
            return False
        if not utils.system(["spctl", "-a", "-t", "exec", "-vv", self.appPath]):
            return False

        ## Validate that the key used for signing the binary matches the expected TeamIdentifier
        ## needed to pass the SocketApi through the sandbox
        #if not utils.system("codesign -dv %s 2>&1 | grep 'TeamIdentifier=%s'" % (self.appPath, "9B5WD74GWJ")):

            #return False

        return True



@contextlib.contextmanager
def makeWritable(targetPath: Path):
    originalMode = targetPath.stat().st_mode
    try:
        # ensure it is writable
        targetPath.chmod(originalMode | stat.S_IWUSR)
        yield targetPath
    finally:
        targetPath.chmod(originalMode)


class MacDylibBundler(object):
    """ Bundle all .dylib files that are not provided by the system with the .app """
    def __init__(self, appPath: str):
        # Avoid processing the same file more than once
        self.checkedLibs = set()
        self.appPath = appPath

    def _addLibToAppImage(self, libPath: Path) -> bool:
        print("addLibToAppImage: %s" % libPath)
        #assert libPath.is_absolute(), libPath
        libBasename = libPath.name
        targetPath = Path(self.appPath, "Contents/Frameworks/", libBasename)
        if targetPath.exists() and targetPath in self.checkedLibs:
            return True
        # Handle symlinks (such as libgit2.27.dylib -> libgit2.0.27.4.dylib):
        if libPath.is_symlink():
            linkTarget = os.readlink(str(libPath))
            CraftCore.log.info("Library dependency %s is a symlink to '%s'", libPath, linkTarget)
            if os.path.isabs(linkTarget):
                CraftCore.log.error("%s: Cannot handle absolute symlinks: '%s'", libPath, linkTarget)
                return False
            if ".." in linkTarget:
                CraftCore.log.error("%s: Cannot handle symlinks containing '..': '%s'", libPath, linkTarget)
                return False
            if libPath.resolve().parent != libPath.parent.resolve():
                CraftCore.log.error("%s: Cannot handle symlinks to other directories: '%s' (%s vs %s)",
                                    libPath, linkTarget, libPath.resolve().parent, libPath.parent.resolve())
                return False

            # copy the symlink and add the real file:
            print("BLA: %s : %s" % (str(libPath), str(targetPath)))
            utils.copyFile(str(libPath), str(targetPath), linkOnly=False)
            CraftCore.log.info("Added symlink '%s' (%s) to bundle -> %s", libPath,
                               os.readlink(str(targetPath)), targetPath)
            self.checkedLibs.add(targetPath)
            symlinkTarget = libPath.with_name(os.path.basename(linkTarget))
            CraftCore.log.info("Processing symlink target '%s'", symlinkTarget)
            if not self._addLibToAppImage(symlinkTarget):
                self.checkedLibs.remove(targetPath)
                return False
            # If the symlink target was processed, the symlink itself is also fine
            return True

        if not libPath.exists():
            CraftCore.log.error("Library dependency '%s' does not exist", libPath)
            return False
        CraftCore.log.debug("Handling library dependency '%s'", libPath)
        if not targetPath.exists():
            utils.copyFile(str(libPath), str(targetPath), linkOnly=False)
            CraftCore.log.info("Added library dependency '%s' to bundle -> %s", libPath, targetPath)

        if not self._fixupLibraryId(targetPath):
            return False
        for path in utils.getLibraryDeps(str(targetPath)):
            # check there aren't any references to the original location:
            if path == str(libPath):
                CraftCore.log.error("%s: failed to fix reference to original location for '%s'", targetPath, path)
                return False

        if not self.bundleLibraryDependencies(targetPath):
            CraftCore.log.error("%s: UNKNOWN ERROR adding '%s' into bundle", targetPath, libPath)
            return False
        if not os.path.exists(targetPath):
            CraftCore.log.error("%s: Library dependency '%s' doesn't exist after copying... Symlink error?",
                                targetPath, libPath)
            return False
        self.checkedLibs.add(targetPath)
        return True

    @staticmethod
    def _updateLibraryReference(fileToFix: Path, oldRef: str, newRef: str = None) -> bool:
        if newRef is None:
            newRef = "@rpath/" + os.path.basename(oldRef)

        CraftCore.log.info("%s: update library dependency path from '%s' to '%s'",
                                    fileToFix, oldRef, newRef)
        with makeWritable(fileToFix):
            if not utils.system(["install_name_tool", "-change", oldRef, newRef, str(fileToFix)], logCommand=False):
                CraftCore.log.error("%s: failed to update library dependency path from '%s' to '%s'",
                                    fileToFix, oldRef, newRef)
                return False
        return True

    @staticmethod
    def _getLibraryNameId(fileToFix: Path) -> str:
        #print("PATH: %s" % fileToFix)
        libraryIdOutput = io.StringIO(
            subprocess.check_output(["otool", "-D", str(fileToFix)]).decode("utf-8"))
        lines = libraryIdOutput.readlines()
        # DOMME: FWIW ... executables have only one line here ... apparently
        if len(lines) == 1:
            return ""
        # Should have exactly one line with the id now
        assert len(lines) == 2, lines
        return lines[1].strip()

    @classmethod
    def _fixupLibraryId(cls, fileToFix: Path):
        libraryId = cls._getLibraryNameId(fileToFix)
        if libraryId and os.path.isabs(libraryId):
            CraftCore.log.debug("Fixing library id name for %s", libraryId)
            with makeWritable(fileToFix):
                if not utils.system(["install_name_tool", "-id", "@rpath/%s" % os.path.basename(libraryId), str(fileToFix)],
                                    logCommand=False):
                    CraftCore.log.error("%s: failed to fix absolute library id name for", fileToFix)
                    return False
        return True

    def bundleLibraryDependencies(self, fileToFix: Path) -> bool:
        assert not fileToFix.is_symlink(), fileToFix
        if fileToFix.stat().st_nlink > 1:
            CraftCore.log.error("More than one hard link to library %s found! "
                                "This might modify another accidentally.", fileToFix)
        CraftCore.log.info("Fixing library dependencies for %s", fileToFix)
        if not self._fixupLibraryId(fileToFix):
            return False


        # Ensure we have the current library ID since we need to skip it in the otool -L output
        libraryId = self._getLibraryNameId(fileToFix)

        print("LibraryId: %s" % libraryId)

        for path in utils.getLibraryDeps(str(fileToFix)):
            #print("%s: fix dep: %s" % (fileToFix, path))
            if path == libraryId:
                # The first line of the otool output is (usually?) the library itself:
                # $ otool -L PlugIns/printsupport/libcocoaprintersupport.dylib:
                # PlugIns/printsupport/libcocoaprintersupport.dylib:
                #         libcocoaprintersupport.dylib (compatibility version 0.0.0, current version 0.0.0)
                #         /System/Library/Frameworks/AppKit.framework/Versions/C/AppKit (compatibility version 45.0.0, current version 1561.40.112)
                #         @rpath/QtPrintSupport.framework/Versions/5/QtPrintSupport (compatibility version 5.11.0, current version 5.11.1)
                # ....
                CraftCore.log.info("%s: ignoring library name id %s in %s", fileToFix, path,
                                    os.path.relpath(str(fileToFix), self.appPath))
                continue
            if path.startswith("@executable_path/"):
                continue  # already fixed
            if path.startswith("@rpath/.."):
                # CraftCore.log.info("%s: can't handle @rpath library dep of yet: '%s'", fileToFix, path)
                relpath = os.path.relpath(str(fileToFix), self.appPath)
                relrpath =  path[7:]
                print("******")
                print("fileToFix: %s" % fileToFix)
                print("fileToFix dirname: %s" % os.path.dirname(fileToFix))
                print("path: %s" % path)
                print("relpath: %s" % relpath)
                print("relrpath: @rpath/%s" % relrpath) # this is what needs to be replaced ... with?
                print("relrpath dirname: %s" % os.path.dirname(relrpath)) # this is what needs to be replaced ... with?
                print("self.appPath: %s" % self.appPath)
                rpath = "/Users/administrator/CraftMaster/macos-64-clang/lib" # ARGH... need to parse
                print("rpath: %s" % rpath)
                print("abs path of library: %s" % os.path.join(rpath, relrpath))
                print("abs path in Frameworks: %s" % os.path.join(self.appPath, "Contents", "Frameworks"))
                print("%s: can't handle @rpath library dep of yet: '%s': %s: %s" % (fileToFix, path, relpath, self.appPath))
                # TODO: run otool -l and verify that we pick the right file?
                # assume app Frameworks and lib folder are the rpath
                #rpath =

                newPath = path.replace(os.path.dirname(relrpath), "")
                newPath = newPath.replace("//", "/")
                #newPath = os.path.realpath(newPath)
                #newPath = path.replace("bar", os.path.dirname(relpath))
                print("relrpath dir: %s" % os.path.dirname(relrpath))
                print("relpath: %s" % relpath)
                print("relrpath: @rpath/%s" % relrpath) # this is what needs to be replaced ... with?
                print("NEW PATH  %s" % newPath)
                print("******")

                if not self._updateLibraryReference(fileToFix, path, newPath):
                    return False

                return True
            elif path.startswith("@rpath/"):
                continue
            elif path.startswith("/usr/lib/") or path.startswith("/System/Library/Frameworks/"):
                CraftCore.log.debug("%s: allowing dependency on system library '%s'", fileToFix, path)
            elif path.startswith("@loader_path/"):
                if not self._updateLibraryReference(fileToFix, path):
                    return False
            elif path.startswith("/"):
                if not path.startswith(CraftStandardDirs.craftRoot()):
                    # TODO: should this be an error?
                    CraftCore.log.warning("%s: reference to absolute library path outside craftroot: %s",
                                          fileToFix, path)
                    # return False
                # file installed by craft -> bundle it into the .app if it doesn't exist yet
                if not self._addLibToAppImage(Path(path)):
                    CraftCore.log.error("%s: Failed to add library dependency '%s' into bundle", fileToFix, path)
                    return False
                if not self._updateLibraryReference(fileToFix, path):
                    return False
            elif "/" not in path and path.startswith("lib"):
                # library reference without absolute path -> try to find the library
                # First check if it exists in Contents/Frameworks already
                guessedPath = Path(self.appPath, "Frameworks", path)
                if guessedPath.exists():
                    CraftCore.log.info("%s: relative library dependency is alreayd bundled: %s", fileToFix, guessedPath)
                else:
                    guessedPath = Path(CraftStandardDirs.craftRoot(), "lib", path)
                    if not guessedPath.exists():
                        CraftCore.log.error("%s: Could not find library dependency '%s' in craftroot", fileToFix, path)
                        return False
                CraftCore.log.debug("%s: Found relative library reference %s in '%s'", fileToFix, path, guessedPath)
                if not self._addLibToAppImage(guessedPath):
                    CraftCore.log.error("%s: Failed to add library dependency '%s' into bundle", fileToFix,
                                        guessedPath)
                    return False
                if not self._updateLibraryReference(fileToFix, path):
                    return False
            else:
                CraftCore.log.error("%s: don't know how to handle otool -L output: '%s'", fileToFix, path)
                return False
        return True

    def fixupAndBundleLibsRecursively(self, subdir: str):
        """Remove absolute references and budle all depedencies for all dylibs under :p subdir"""
        assert not subdir.startswith("/"), "Must be a relative path"
        for dirpath, dirs, files in os.walk(os.path.join(self.appPath, subdir)):
            for filename in files:
                fullpath = Path(dirpath, filename)
                if fullpath.is_symlink():
                    continue  # No need to update symlinks since we will process the target eventually.
                if (filename.endswith(".so")
                        or filename.endswith(".dylib")
                        or ".so." in filename
                        or f"{fullpath.name}.framework" in str(fullpath)):
                    if not self.bundleLibraryDependencies(fullpath):
                        CraftCore.log.info("Failed to bundle dependencies for '%s'", os.path.join(dirpath, filename))
                        return False
        return True

    def areLibraryDepsOkay(self, fullPath: Path):
        CraftCore.log.debug("Checking library dependencies of %s", fullPath)
        found_bad_lib = False
        libraryId = self._getLibraryNameId(fullPath)
        relativePath = os.path.relpath(str(fullPath), self.appPath)
        for dep in utils.getLibraryDeps(str(fullPath)):
            if dep == libraryId and not os.path.isabs(libraryId):
                continue  # non-absolute library id is fine
            # @rpath and @executable_path is fine FIXME: it's not. it's the old relative path, but it can be changed now because of the location we copied libraries to
            if dep.startswith("@rpath") or dep.startswith("@executable_path"):
                print("RPATH DEP: %s: %s" % (relativePath, dep))
                return False
            # Also allow /System/Library/Frameworks/ and /usr/lib:
            if dep.startswith("/usr/lib/") or dep.startswith("/System/Library/Frameworks/"):
                continue
            if dep.startswith(CraftStandardDirs.craftRoot()):
                CraftCore.log.error("ERROR: %s references absolute library path from craftroot: %s", relativePath,
                                    dep)
            elif dep.startswith("/"):
                CraftCore.log.error("ERROR: %s references absolute library path: %s", relativePath, dep)
            else:
                CraftCore.log.error("ERROR: %s has bad dependency: %s", relativePath, dep)
            found_bad_lib = True
        return not found_bad_lib

    def checkLibraryDepsRecursively(self, subdir: str):
        """Check that all  absolute references and budle all depedencies for all dylibs under :p subdir"""
        assert not subdir.startswith("/"), "Must be a relative path"
        foundError = False
        for dirpath, dirs, files in os.walk(os.path.join(self.appPath, subdir)):
            for filename in files:
                fullpath = Path(dirpath, filename)
                if fullpath.is_symlink() and not fullpath.exists():
                    CraftCore.log.error("Found broken symlink '%s' (%s)", fullpath,
                                        os.readlink(str(fullpath)))
                    foundError = True
                    continue

                if filename.endswith(".so") or filename.endswith(".dylib") or ".so." in filename:
                    if not self.areLibraryDepsOkay(fullpath):
                        CraftCore.log.error("Found library dependency error in '%s'", fullpath)
                        foundError = True
        return not foundError


if __name__ == '__main__':
    print("Testing MacDMGPackager.py")
    defaultFile = CraftStandardDirs.craftRoot() + "/lib/libKF5TextEditor.5.dylib"
    sourceFile = defaultFile if len(sys.argv) else sys.argv[1]
    utils.system(["otool", "-L", sourceFile])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        source = os.path.realpath(sourceFile)
        target = os.path.join(td, os.path.basename(source))
        utils.copyFile(source, target, linkOnly=False)
        bundler = MacDylibBundler(td)
        bundler.bundleLibraryDependencies(Path(target))
        print("Checked libs:", bundler.checkedLibs)
        utils.system(["find", td])
        utils.system(["ls", "-laR", td])
        if not bundler.areLibraryDepsOkay(Path(target)):
            print("Error")
        if not bundler.checkLibraryDepsRecursively("Contents/Frameworks"):
            print("Error 2")
        # utils.system(["find", td, "-type", "f", "-execdir", "otool", "-L", "{}", ";"])
