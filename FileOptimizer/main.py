'''
Based on https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/Source/cppMain.cpp
and https://sourceforge.net/p/nikkhokkho/code/HEAD/tree/trunk/FileOptimizer/Source/clsUtil.cpp
commit ver [r1613] 2021-03-19
Author of original cpp code: Nikkho
'''
import os
import multiprocessing
import subprocess
import shutil
from configparser import RawConfigParser, ConfigParser
from send2trash import send2trash
import re
import imghdr
import fleep
import mimetypes
import random
import tempfile
import time
import sys
import pathlib
from .extensions import *

__all__ = [
  "FileOptimiser", "FileOptimizer",
  "optimise", "optimize",
  "optimiseDir", "optimizeDir"
]

if sys.platform == "win32":
   pluginExt = ".exe"
   winePrefix = ""
else:
   pluginExt = ""
   winePrefix = "wine "

def getPathPluginsRegistry():
   try:
      import winreg
      with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as areg:
         try:
            with winreg.OpenKey(areg, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\FileOptimizer') as akey:
               pathFO = winreg.QueryValueEx(akey, 'InstallDir')[0].strip("()");
         except FileNotFoundError:
            try:
               with winreg.OpenKey(areg, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\FileOptimizer') as akey:
                  pathFO = winreg.QueryValueEx(akey, 'InstallDir')[0].strip("()");
            except FileNotFoundError:
               pathFO = r"C:\Program Files\FileOptimizer";
   except:
      pathFO = r"C:\Program Files\FileOptimizer";

   if os.path.exists(pathFO):
      if os.path.exists(os.path.join(pathFO,"Plugins32")):
         pluginsDirectory = os.path.join(pathFO,"Plugins32");
      elif os.path.exists(os.path.join(pathFO,"Plugins64")):
         pluginsDirectory = os.path.join(pathFO,"Plugins64");
      else:
         return None;
   else:
      return None;
   return pluginsDirectory;

def createSettings(settings_file):
   """Create a new settings file with default options.

   `settings_file` is a path string to this file.
   """
   settings = ConfigParser(allow_no_value=True);
   settings.add_section('Paths');
   pluginsDirectory = getPathPluginsRegistry();
   if pluginsDirectory:
      settings.set('Paths','PluginsDirectory',pluginsDirectory);
   else:
      if sys.platform == "win32":
         settings.set('Paths','PluginsDirectory',r'C:\Program Files\FileOptimizer\Plugins64');
      else:
         settings.set('Paths','PluginsDirectory',os.path.join(os.path.expanduser('~'),'FileOptimizerPlugins'));
   settings.add_section('Options');
   settings.set('Options','ForceWine','false		; Force running Wine. UNIX-only option.');
   settings.set('Options','BMPCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'CSSEnableTidy', "false		; Boolean. Default: false. Enable tidy. Results in smaller files, but can happen they are not editable anymore.");
   settings.set('Options', 'CSSTemplate', "low		; String. Default 'low'. Compression template, from safer and worse compression, to highest compression.");
   settings.set('Options', 'EXEDisablePETrim', "false		; Boolean. Default: false. Disable PETrim. When enabled, PETrim will not be used, resulting in less EXE corruption at the cost of larger file size.");
   settings.set('Options', 'EXEEnableUPX', "false		; Boolean. Default: false. Enable UPX executable compression. When enabled, UPX will be used, resulting EXE and DLL size reduction at the cost of runtime decompression.");
   settings.set('Options', 'GIFCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'GIFAllowLossy', "false		; Boolean. Default: false. Allowing lossy optimizations will get higher files reduction at the cost of some quality loss, even if visually unnoticeable or not.");
   settings.set('Options', 'GZCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'HTMLEnableTidy', "false		; Boolean. Default: false. Enable Tidy. Results in smaller files, but can happen they are not editable anymore. Note that this applies to both SVG and HTML file types.");
   settings.set('Options', 'JPEGCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information");
   settings.set('Options', 'JPEGUseArithmeticEncoding', "false		; Boolean. Default: false. Arithmetic encoding gives additional saving reductions, but is incompatible with most programs.");
   settings.set('Options', 'JPEGAllowLossy', "false		; Boolean. Default: false. Allowing lossy optimizations will get higher files reduction at the cost of some quality loss, even if visually unnoticeable or not.");
   settings.set('Options', 'JSEnableJSMin', "false		; Boolean. Default: false. Enable jsmin. Results in smaller files, but can happen they are not editable anymore.");
   settings.set('Options', 'JSAdditionalExtensions', "		; String. Default: ''. Add extra extensions to be threated as JS/JSON.");
   settings.set('Options', 'LUAEnableLeanify', "false		; Boolean. Default: false. Enable Leanify. Results in smaller files, but can happen they are not editable anymore.");
   settings.set('Options', 'MiscDisable', "false		; Boolean. Default: false. Disable processing of other file types. This could imply lossing some edit capabilities such as PSD/PSB where text layers will be rasterized.");
   settings.set('Options', 'MiscCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'MP3CopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'MP4CopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'PCXCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'PDFProfile', "none		; String. Default 'none'. Compression profile, from less size, to best quality.");
   settings.set('Options', 'PDFCustomDPI', "150		; Number. Default: 150. When custom profile is choosen, it allows you to specify a custom DPI for downsampling images.");
   settings.set('Options', 'PDFSkipLayered', "false		; Boolean. Default: false. Skip processing of PDF files containing layered objects. Results in more compatible files with higher size.");
   settings.set('Options', 'PNGCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'PNGAllowLossy', "false		; Boolean. Default: false. Allowing lossy optimizations will get higher files reduction at the cost of some quality loss, even if visually unnoticeable or not.");
   settings.set('Options', 'TGACopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'TIFFCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'WAVCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'WAVStripSilence', "false		; Boolean. Default: false. Strip start and end silences if any.");
   settings.set('Options', 'WEBPAllowLossy', "false		; Boolean. Default: false. Allowing lossy optimizations will get higher files reduction at the cost of some quality loss, even if visually unnoticeable or not.");
   settings.set('Options', 'XMLEnableLeanify', "false		; Boolean. Default: false. Enable Leanify. Results in smaller files, but can happen they are not editable anymore.");
   settings.set('Options', 'ZIPCopyMetadata', "false		; Boolean. Default: false. Copy file metadata. Else strip all unneeded information.");
   settings.set('Options', 'ZIPRecurse', "false		; Boolean. Default: false. Enable optimization inside archives (recursive optimization).");
   settings.set('Options', 'KeepAttributes', "false		; Boolean. Default: false. Keep original readonly, system, hidden and archive attributes as well as creation and modification timestamps.");
   settings.set('Options', 'DoNotUseRecycleBin', "false		; Boolean. Default: false. When checked original files will not be backed up in the system trashcan.");
   settings.set('Options', 'DoNotCreateBackups', "false		; Boolean. Default: false. When checked original files will not be backed up in the current folder as a .BAK files.");
   settings.set('Options', 'IncludeMask', "		; String. Default: ''. If not empty, only files containing this mask (substring) on name or path will be included from optimization. You can use semicolon to specify more than one substring being included.");
   settings.set('Options', 'ExcludeMask', "		; String. Default: ''. Files containing this mask (substring) on name or path will be excluded from optimization. You can use semicolon to specify more than one substring being excluded.");
   settings.set('Options', 'DisablePluginMask', "		; String. Default: ''. Allow excluding execution of certain plugins. It is case insensitive, and allows more than one item to be specified by using semicolon as separator.");
   settings.set('Options', 'BeepWhenDone', "false		; Boolean. Default: false. Beep the speaker when optimization completes.");
   settings.set('Options', 'Debug', "false		; Boolean. Default: false. Enable internal debugging mode. Temporary files will not be deleted.");
   settings.set('Options', 'Level', "9		; Number. Default: 5. Optimization level from best speed to best compression.");
   settings.set('Options', 'ProcessPriority', "32		; Number. Default: 2 (Normal). Process priority from most conservative to best performance.");
   settings.set('Options', 'LogLevel', "0		; Number. Default: 0. Debugging level to output on program log.");
   settings.set('Options', 'FilenameFormat', "0		; Number. Default: 0. Specify the format to display filenames in the list.");
   settings.set('Options', 'LeanifyIterations', "-1		; Number. Default: -1. If specified, number of trial iterations in all Leanify executions will use this value. If not, iterations are calculated depending on the Optimization level.");
   settings.set('Options', 'PNGWolfIterations', "-1		; Number. Default: -1. If specified, number of trial iterations in all PNGWolf executions will use this value. If not, iterations are calculated depending on the Optimization level.");
   settings.set('Options', 'TempDirectory', "		; String. Default: ''. If not empty specified directory will be used for temporary storage instead of system's %%TEMP%%.");
   with open(settings_file,'w') as f:
      settings.write(f);

settings = RawConfigParser(allow_no_value=True);

# Search settings file in current path
if os.path.exists("FileOptimizerPy.ini"):
   settings_file = "FileOptimizerPy.ini";
# Search settings file in home path
elif os.path.exists(os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini")):
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
# Search settings file of original FileOptimizer in FileOptimizer path
elif getPathPluginsRegistry() and os.path.exists(os.path.join(os.path.split(getPathPluginsRegistry())[0], "FileOptimizer.ini")):
   pluginsDirectory = getPathPluginsRegistry();
   settings.read(os.path.join(os.path.split(pluginsDirectory)[0], "FileOptimizer.ini"));
   settings.add_section('Paths');
   if pluginsDirectory:
      settings.set('Paths','PluginsDirectory',pluginsDirectory);
   else:
      settings.set('Paths','PluginsDirectory',r'C:\Program Files\FileOptimizer\Plugins64');
   settings.set('Options','ForceWine','false		; Force running Wine. UNIX-only option.');
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
   with open(settings_file,'w') as f:
      settings.write(f);
# Search settings file of original FileOptimizer64 in FileOptimizer64 path
elif getPathPluginsRegistry() and os.path.exists(os.path.join(os.path.split(getPathPluginsRegistry())[0], "FileOptimizer64.ini")):
   pluginsDirectory = getPathPluginsRegistry();
   settings.read(os.path.join(os.path.split(pluginsDirectory)[0], "FileOptimizer64.ini"));
   settings.add_section('Paths');
   if pluginsDirectory:
      settings.set('Paths','PluginsDirectory',pluginsDirectory);
   else:
      settings.set('Paths','PluginsDirectory',r'C:\Program Files\FileOptimizer\Plugins64');
   settings.set('Options','ForceWine','false		; Force running Wine. UNIX-only option.');
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
   with open(settings_file,'w') as f:
      settings.write(f);
# Search settings file of original FileOptimizer in home path
elif os.path.exists(os.path.join(os.path.expanduser('~'), "FileOptimizer.ini")):
   settings.read(os.path.join(os.path.expanduser('~'), "FileOptimizer.ini"));
   settings.add_section('Paths');
   pluginsDirectory = getPathPluginsRegistry();
   if pluginsDirectory:
      settings.set('Paths','PluginsDirectory',pluginsDirectory);
   else:
      settings.set('Paths','PluginsDirectory',r'C:\Program Files\FileOptimizer\Plugins64');
   settings.set('Options','ForceWine','false		; Force running Wine. UNIX-only option.');
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
   with open(settings_file,'w') as f:
      settings.write(f);
# Search settings file of original FileOptimizer64 in home path
elif os.path.exists(os.path.join(os.path.expanduser('~'), "FileOptimizer64.ini")):
   settings.read(os.path.join(os.path.expanduser('~'), "FileOptimizer64.ini"));
   settings.add_section('Paths');
   pluginsDirectory = getPathPluginsRegistry();
   if pluginsDirectory:
      settings.set('Paths','PluginsDirectory',pluginsDirectory);
   else:
      settings.set('Paths','PluginsDirectory',r'C:\Program Files\FileOptimizer\Plugins64');
   settings.set('Options','ForceWine','false		; Force running Wine. UNIX-only option.');
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
   with open(settings_file,'w') as f:
      settings.write(f);
# Create settings file in home path
else:
   settings_file = os.path.join(os.path.expanduser('~'), "FileOptimizerPy.ini");
   createSettings(settings_file);

settings.read(settings_file);
# ConfigParser can't split comment from option string
s = dict(settings.items())
ini = {x:{y:s[x][y].rsplit(";",1)[0].strip() for y in dict(s[x])} for x in s}
settings = ConfigParser(allow_no_value=True);
settings.read_dict(ini);

if sys.platform == "win32" or not settings.getboolean('Options','ForceWine'):
   winePrefixForced = ""
else:
   winePrefixForced = "wine "

# Получение короткого пути в Windows
def GetShortName(psLongName):
   '''Returns a short path form in Windows.
   For non-Win systems returns path itself.

   `psLongName` is a path string.
   '''
   try:
      import win32api
      import pywintypes
      try:
         acShortName = win32api.GetShortPathName(psLongName);
      except pywintypes.error:
         enum = 1;
         spl = psLongName.rsplit(os.sep,enum)
         while os.sep in spl[0]:
            try:
               short = win32api.GetShortPathName(spl[0]);
               acShortName = os.sep.join([short, *spl[1:]]);
               break;
            except pywintypes.error:
               enum += 1;
               spl = psLongName.rsplit(os.sep,enum)
      return acShortName;
   except:
      return psLongName;

sPluginsDirectory = GetShortName(os.path.join(os.path.normpath(settings.get('Paths','PluginsDirectory')), ""))

# Function name refers to similar function from cppMain.cpp
def SetCellFileValue(psValue):
   '''Returns a path string in form chosen in settings option "FilenameFormat":
   0: only filename;
   1: path+filename in short form;
   2: driveletter + :\+partial path if fits+... last part of filename;
   3: full path+filename.

   `psValue` is a path string.
   '''
   FilenameFormat = settings.getint('Options','FilenameFormat');
   # only filename
   if FilenameFormat == 1:
      sRes = os.path.basename(psValue);
   # ToDo: driveletter + :\+partial path + filename
   elif FilenameFormat == 2:
      sRes = GetShortName(os.path.abspath(psValue));
   # ToDo: driveletter + :\+partial path if fits+... last part of filename
   elif FilenameFormat == 3:
      sRes = GetShortName(os.path.abspath(psValue));
      if len(sRes)>25:
         sRes = sRes[:20].rsplit(os.sep,1)[0] + f'{os.sep} ... {os.sep}' + sRes[-20:].split(os.sep,1)[-1]
   # full path+filename
   else:
      sRes = os.path.abspath(psValue);
   return sRes;

def GetFileAttributes(filename):
   '''Returns file system attributes for a specified file or directory as int.

   `filename` is a path string.

   Retuns None if can't get attributes.
   '''
   try:
      import win32api
      return win32api.GetFileAttributes(filename);
   except:
      return None;

def SetFileAttributes(filename, hexattributes):
   '''Sets the attributes for a file or directory.

   `filename` is a path string.

   `hexattributes` is file attributes to set for the file in int form.

   If succeeds returns True, if fails returns False.
   '''
   try:
      import win32api
      win32api.SetFileAttributes(filename, hexattributes);
      return True;
   except:
      return False;

# Определение типа файла
def GetExtensionByContent(filename):
   '''Returns list of extensions with dot.
   Extension determines by content file.
   If can't determine gets extension from filename.

   `filename` is a file path string.
   '''
   # Для изображений (rgb, gif, pbm, pgm, ppm, tiff, rast, xbm, jpeg, bmp, png, webp, exr) достаточно imghdr
   Extension = imghdr.what(filename)
   # fleep распознаёт большинство файлов по содержимому
   if not Extension:
      with open(filename,'rb') as f:
         fleep_info = fleep.get(f.read(128))
      if fleep_info.extension:
         Extension = fleep_info.extension
   # Файлы, содержимое которых не знает fleep (mng ogg ole pcx tar tga tif), проверяем сами
   if not Extension:
      with open(filename,'rb') as f:
         acBuffer = f.read()
      # Check MNG
      if acBuffer[:8] == b"\x8A\x4D\x4E\x47\x0D\x0A\x1A\x0A":
         Extension = ".mng";
      # Check OGG / Check OGV
      elif b"OggS" in acBuffer[:7]:
         Extension = ".ogg";
      # Check OLE/OLE Beta
      elif (acBuffer[:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1") \
        or (acBuffer[:8] == b"\x0E\x11\xFC\x0D\xD0\xCF\x11\x0E"):
         Extension = ".ole";
      # Check PCX
      elif (acBuffer[0] == 10) \
       and (acBuffer[2] == 1) \
       and (acBuffer[64] == 0) \
       and (acBuffer[74] == 0):
         Extension = ".pcx";
      # Check TAR
      elif acBuffer[257:262] == b"\x75\x73\x74\x61\x72":
         Extension = ".tar";
      # Check TGA
      elif acBuffer[-18:-8] == b"TRUEVISION":
         Extension = ".tga";
      # Check TIF
      elif (acBuffer[:2] == b"\x0C\xED") \
        or (acBuffer[:3] == b"\x49\x20\x49") \
        or (acBuffer[:4] == b"\x49\x49\x2A\x00") \
        or (acBuffer[:4] == b"\x4D\x4D\x00\x2B"):
         Extension = ".tif";
   # Пробуем определить тип из mime по названию
   if not Extension:
      mime = mimetypes.guess_type(filename)
      if mime and mime[0]:
         Extension = mimetypes.guess_all_extensions(mime[0])
   # В крайнем случае берём расширение файла
   if not Extension:
      Extension = os.path.splitext(filename)[-1].lower()
   # Запаковываем
   if isinstance(Extension, str):
      Extension = [Extension if Extension[0]=='.' else f".{Extension}"]
   else:
      Extension = [ext if ext[0]=='.' else f".{ext}" for ext in Extension]
   return Extension

# Получение пути к логам
def GetLogPath():
   '''Returns a path string to log file.
   '''
   acPath = GetShortName(os.path.join(os.path.expanduser('~'), "FileOptimizer.log"));
   return acPath;

# Запись в логи
def Log(piLevel, pacValue, piDesiredLevel):
   '''Writing to end of log file.

   `piLevel` is level of this message.

   `pacValue` is string message for adding to file.

   `piDesiredLevel` is desired level for logging, usually from settings option "Level".
   '''
   if piDesiredLevel > piLevel:
      acPath = GetLogPath();
      with open(acPath, "at", encoding="utf-8") as pLog:
         # dteDate = time.time();
         pLog.write(f"{pacValue}\n");

# Проверка разрядности системы
def IsWindows64():
   '''Checking system bitness.'''
   return sys.maxsize > 2**32;

# Запуск плагина оптимизации
def RunPlugin(psStatus, psCommandLine, psInputFile, psOutputFile, piErrorMin, piErrorMax, ErrorsList=[], Extension="", KI_GRID_ORIGINAL=0, KI_GRID_OPTIMIZED=0, KI_GRID_STATUS="", silentMode=False):
   '''Running optimisation plugin.

   `psStatus` is message contains status of optimisation: index and plugin name.

   `psCommandLine` is a command string for running process.

   `psInputFile` is a path string of input file.

   `psOutputFile` is a path string of output file.

   `piErrorMin`, `piErrorMax`, are range of acceptable exit codes.

   `ErrorsList` is list of acceptable exit codes.

   `Extension`, `KI_GRID_ORIGINAL`, `KI_GRID_OPTIMIZED`, `KI_GRID_STATUS` are parameters for output print.

   `silentMode` is a flag of running without output print.

   Returns tuple with exit code, optimised size and status string.
   '''
   # Check if it is an excluded plugins
   PluginMask = settings.get('Options','DisablePluginMask').upper().split(";");
   for Token in PluginMask:
      if Token and Token in psCommandLine.upper():
         KI_GRID_STATUS = "Skipped";
         return 0, KI_GRID_OPTIMIZED, KI_GRID_STATUS;

   if not os.path.exists(psInputFile):
      KI_GRID_OPTIMIZED = 0;
      KI_GRID_STATUS = "Skipped";
      return 0, KI_GRID_OPTIMIZED, KI_GRID_STATUS;

   sInputFile = psInputFile;
   sOutputFile = psOutputFile;
   sCommandLine = psCommandLine;

   # Avoid temporary name collisions across different instances
   iRandom = random.randint(0, 9999);

   # Use specified option temp directory if exists
   if settings.get('Options','TempDirectory'):
      TempPath = os.path.normpath(settings.get('Options','TempDirectory'))
      if not os.access(TempPath,os.F_OK):
         os.makedirs(TempPath);
   else:
      TempPath = tempfile.gettempdir()

   basename = os.path.basename(sInputFile)
   sTmpInputFile = os.path.join(TempPath, f"FileOptimizer_Input_{iRandom}_{basename}");
   sTmpOutputFile = os.path.join(TempPath, f"FileOptimizer_Output_{iRandom}_{basename}");

   if not settings.getboolean('Options','Debug'):
      if os.path.exists(sTmpInputFile):
         os.remove(sTmpInputFile);
      if os.path.exists(sTmpOutputFile):
         os.remove(sTmpOutputFile);

   # Required indirection
   sCaption = f"Running {psStatus}...";
   KI_GRID_STATUS = sCaption
   lSize = os.stat(sInputFile).st_size;
   lSizeNew = lSize;
   KI_GRID_OPTIMIZED = lSize

   # Handle copying original file, if there is not Output nor Tmp for commands that only accept 1 file
   if ("%OUTPUTFILE%" not in psCommandLine) and ("%TMPOUTPUTFILE%" not in psCommandLine):
      shutil.copy2(sInputFile,sTmpInputFile, follow_symlinks=False)
      # sInputFile = sTmpOutputFile;
   sCommandLine = sCommandLine.replace("%INPUTFILE%", os.path.abspath(sInputFile) if sInputFile else sInputFile);
   sCommandLine = sCommandLine.replace("%OUTPUTFILE%", os.path.abspath(sOutputFile) if sOutputFile else sOutputFile);
   sCommandLine = sCommandLine.replace("%TMPINPUTFILE%", sTmpInputFile);
   sCommandLine = sCommandLine.replace("%TMPOUTPUTFILE%", sTmpOutputFile);

   fixInput = False;
   presInputFile = sInputFile;
   presTmpInputFile = sTmpInputFile;
   presTmpOutputFile = sTmpOutputFile;
   if lSize > 0:
      dteStart = time.time();
      iError = RunProcess(sCommandLine, True);

      if not ((iError >= piErrorMin and iError <= piErrorMax) or iError in ErrorsList):
         sInputFile = f"{os.path.splitext(psInputFile)[0]}";
         basename = os.path.basename(sInputFile)
         sInputFile = os.path.join(TempPath, f"FileOptimizer_sInput_{iRandom}_{basename}{Extension}");
         shutil.copy2(psInputFile,sInputFile, follow_symlinks=False);
         fixInput = True;
         if not settings.getboolean('Options','Debug'):
            if os.path.exists(sTmpInputFile):
               os.remove(sTmpInputFile);
            if os.path.exists(sTmpOutputFile):
               os.remove(sTmpOutputFile);
         sTmpInputFile = os.path.join(TempPath, f"FileOptimizer_Input_{iRandom}_{basename}{Extension}");
         sTmpOutputFile = os.path.join(TempPath, f"FileOptimizer_Output_{iRandom}_{basename}{Extension}");
         if not settings.getboolean('Options','Debug'):
            if os.path.exists(sTmpInputFile):
               os.remove(sTmpInputFile);
            if os.path.exists(sTmpOutputFile):
               os.remove(sTmpOutputFile);
         sCommandLine = psCommandLine;
         if ("%OUTPUTFILE%" not in psCommandLine) and ("%TMPOUTPUTFILE%" not in psCommandLine):
            shutil.copy2(sInputFile,sTmpInputFile, follow_symlinks=False)
            # sInputFile = sTmpOutputFile;
         sCommandLine = sCommandLine.replace("%INPUTFILE%", os.path.abspath(sInputFile) if sInputFile else sInputFile);
         sCommandLine = sCommandLine.replace("%OUTPUTFILE%", os.path.abspath(sOutputFile) if sOutputFile else sOutputFile);
         sCommandLine = sCommandLine.replace("%TMPINPUTFILE%", sTmpInputFile);
         sCommandLine = sCommandLine.replace("%TMPOUTPUTFILE%", sTmpOutputFile);
         iError = RunProcess(sCommandLine, True);

      dteEnd = time.time();

      # Check exit errorlevel
      if (iError >= piErrorMin and iError <= piErrorMax) or iError in ErrorsList:
         # We did get a TMP output file, so if smaller, make it overwrite input file
         if "%TMPOUTPUTFILE%" in psCommandLine:
            if not os.path.exists(sTmpOutputFile):
               sTmpOutputFile = f"{sTmpOutputFile}{Extension}"
            try:
               lSizeNew = os.stat(sTmpOutputFile).st_size;
            except FileNotFoundError:
               lSizeNew = 0;
            if lSizeNew >= 8 and lSizeNew < lSize:
               shutil.copy2(sTmpOutputFile,presInputFile, follow_symlinks=False);
         elif ("%OUTPUTFILE%" not in psCommandLine) and ("%TMPOUTPUTFILE%" not in psCommandLine):
            lSizeNew = os.stat(sTmpInputFile).st_size;
            if lSizeNew >= 8 and lSizeNew < lSize:
               shutil.copy2(sTmpInputFile,presInputFile, follow_symlinks=False)
               # sInputFile = sTmpOutputFile;
   else:
      iError = -9999;
      dteStart = dteEnd = time.time();

   if not settings.getboolean('Options','Debug'):
      if os.path.exists(sTmpInputFile):
         os.remove(sTmpInputFile);
      if os.path.exists(sTmpOutputFile):
         os.remove(sTmpOutputFile);
      if fixInput and os.path.exists(sInputFile):
         os.remove(sInputFile);
         sInputFile = presInputFile;
      if os.path.exists(presTmpOutputFile):
         os.remove(presTmpOutputFile);
      if os.path.exists(presTmpInputFile):
         os.remove(presTmpInputFile);
      if os.path.exists(f"{presTmpOutputFile}{Extension}"):
         os.remove(f"{presTmpOutputFile}{Extension}");
      if os.path.exists(f"{presTmpInputFile}{Extension}"):
         os.remove(f"{presTmpInputFile}{Extension}");

   if (lSizeNew <= 8) or (lSizeNew >= lSize):
      lSizeNew = lSize;
   else:
      KI_GRID_OPTIMIZED = lSizeNew

   if not silentMode:
      print(f"{SetCellFileValue(sInputFile)} ", f" {Extension} ", f" {KI_GRID_ORIGINAL} ", f" {KI_GRID_OPTIMIZED} ", f" {KI_GRID_STATUS} ", sep="\t", end="\r");
   Log(3, f"Start: {time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(dteStart))}\t" \
          f"End: {time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(dteEnd))}\t" \
          f"Level: {settings.get('Options','Level')}\t" \
          f"Original: {lSize}\t" \
          f"Optimized: {lSizeNew}\t" \
          f"Errorlevel: {iError}\t" \
          f"Input: {os.path.abspath(sInputFile) if sInputFile else sInputFile}\t" \
          f"Output: {os.path.abspath(sOutputFile) if sOutputFile else sOutputFile}\t" \
          f"Plugin: {psStatus}\t" \
          f"Commandline: {sCommandLine}",
       settings.getint('Options','LogLevel'));

   return iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS;

# Запуск подпроцесса с помощью команды pacProcess
def RunProcess(pacProcess, pbWait):
   '''Running subprocess.

   `pacProcess` is a command string.

   `pbWait` is a flag for waiting exit process.

   Returns exit code of process.
   '''
   if sys.platform == "win32":
      udtSI = subprocess.STARTUPINFO(
                 dwFlags=subprocess.STARTF_USESHOWWINDOW,
                 wShowWindow=subprocess.SW_HIDE
              )

      proc = subprocess.Popen(
                GetShortName(pacProcess),
                cwd=sPluginsDirectory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=not False,
                creationflags=settings.getint('Options','ProcessPriority'),
                startupinfo=udtSI
             )
   else:
      udtSI = None
      proc = subprocess.Popen(
                GetShortName(pacProcess),
                cwd=sPluginsDirectory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=not False,
                shell=True,
                preexec_fn=lambda : os.nice(settings.getint('Options','ProcessPriority')),
                startupinfo=udtSI
             )

   if pbWait:
      lExitCode = proc.wait();
   else:
      lExitCode = proc.poll();

   return lExitCode;

# Распознание APNG
def IsAPNG(pacFile):
   '''Determine APNG.

   `pacFile` is a path to file.

   Returns True if file is animated PNG.
   '''
   bRes = False;
   if os.stat(pacFile).st_size > 0:
      with open(pacFile,'rb') as f:
         acBuffer = f.read(8);
      if acBuffer and acBuffer[:8] == b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A":
         with open(pacFile,'rb') as f:
            acBuffer = f.read();
         iLength = acBuffer.find(b'IDAT');
         if iLength>0:
            acBuffer = acBuffer[:iLength];
            if (b"fcTL" in acBuffer) or (b"acTL" in acBuffer) or (b"fdAT" in acBuffer):
               bRes = True;
   return bRes;

# Распознание .exe
def IsEXESFX(pacFile):
   '''Determine SFX EXE.

   `pacFile` is a path to file.

   Returns True if file is self-extracting archive EXE.
   '''
   bRes = False;
   with open(pacFile,'rb') as f:
      acBuffer = f.read(2);

   # Check if it is EXE
   if (acBuffer == b"MZ") or (acBuffer == b"ZM"):
      with open(pacFile,'rb') as f:
         acBuffer = f.read();
      # Check if it is an Inno Setup Installer
      if b"Inno Setup" in acBuffer:
         bRes = True;
      # Check if it is an InstallShield Wizard
      elif b"InstallShield" in acBuffer:
         bRes = True;
      # Check if it is an NSIS
      elif b"Nullsoft Install System" in acBuffer:
         bRes = True;
      # Check if it is an RTPatch Updater
      elif b"RTPatch" in acBuffer:
         bRes = True;
      # Check if it is a RAR SFX
      elif b"\x52\x61\x72\x21\x1A\x07" in acBuffer:
         bRes = True;
      # Check if it is a ZIP SFX
      elif b"\x50\x4B\x03\x04" in acBuffer:
         bRes = True;
      # Check if it is a 7-ZIP SFX
      elif b"\x37\x7A\xBC\xAF\x27\x1C" in acBuffer:
         bRes = True;
   return bRes;

# Распознание PDF со слоями
def IsPDFLayered(pacFile):
   '''Determine layered PDF.

   `pacFile` is a path to file.

   Returns True if file is PDF with layers.
   '''
   bRes = False;
   with open(pacFile,'rb') as f:
      acBuffer = f.read();
   # Look for a OCG (Optional Content Groups)
   if b"<< /Type /OCG /Name" in acBuffer:
      bRes = True;
   return bRes;

def optimise(sInputFile, silentMode=False, res={}):
   '''Single file optimisation.

   `sInputFile` is a path to file needs for optimisation.

   `silentMode` is a flag of running without output print.

   `res` is returns dict with result.

   Returns `res`.
   '''
   basename = os.path.basename(sInputFile);
   KI_GRID_OPTIMIZED = KI_GRID_ORIGINAL = 0;
   thisExt = ""

   # Required indirection
   sCaption = f"Processing {sInputFile}...";
   KI_GRID_STATUS = "Pending";

   iStartTicks = time.perf_counter();

   # Проверка файла на исключение из оптимизации
   excluded = False
   # Если название файла соотвествует непустой маске, то оптимизируем его
   IncludeMask = settings.get('Options','IncludeMask')
   if IncludeMask != '':
      if re.search(IncludeMask, basename):
         excluded = False
      else:
         excluded = True
   # Если название файла соотвествует маске, то не оптимизируем его
   ExcludeMask = settings.get('Options','ExcludeMask')
   if ExcludeMask != '':
      if re.search(ExcludeMask, basename):
         excluded = True

   if os.path.exists(sInputFile) and not excluded:
      KI_GRID_OPTIMIZED = KI_GRID_ORIGINAL = os.stat(sInputFile).st_size
      # Создаём в корзине копию
      if not settings.getboolean('Options','DoNotUseRecycleBin'):
         KI_GRID_STATUS = "Copying to Recyclebin...";
         shutil.copy2(sInputFile,f"{sInputFile}.tmp", follow_symlinks=False)
         send2trash(sInputFile)
         shutil.move(f"{sInputFile}.tmp",sInputFile)
      # Создаём бэкап
      if not settings.getboolean('Options','DoNotCreateBackups'):
         KI_GRID_STATUS = "Creating backup...";
         shutil.copy2(sInputFile,f"{sInputFile}.bak", follow_symlinks=False)
      # Сохранение атрибутов
      KeepAttributes = settings.getboolean('Options','KeepAttributes')
      if KeepAttributes:
         statFile = os.stat(sInputFile);
         udtFileCreated = (statFile.st_atime, statFile.st_mtime);
         FileAttributes = GetFileAttributes(GetShortName(sInputFile));
      # Определяем тип файла
      Extension = GetExtensionByContent(sInputFile)
      # Each extension can correspond to more than one engine, so use if instead of elif
      # BMP: ImageMagick, ImageWorsener
      if set(Extension) & set(KS_EXTENSION_BMP):
         thisExt = list(set(Extension) & set(KS_EXTENSION_BMP))[0];
         sFlags = "";
         if not settings.getboolean('Options','BMPCopyMetadata'):
            sFlags += "-strip ";
         if sys.platform == "win32" or winePrefixForced:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -compress RLE {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -compress RLE {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageWorsener (2/2)",
                   f"{winePrefixForced}{sPluginsDirectory}imagew{pluginExt} -noresize -zipcmprlevel 9 -outfmt bmp -compress \"rle\" \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # CSS: CSSTidy, Minify
      if set(Extension) & set(KS_EXTENSION_CSS):
         thisExt = list(set(Extension) & set(KS_EXTENSION_CSS))[0];
         if settings.getboolean('Options','CSSEnableTidy'):
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("CSSTidy (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}csstidy{pluginExt} \"%INPUTFILE%\" --template={settings.get('Options','CSSTemplate')} \"\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Minify (2/2)",
                      f"{winePrefixForced}{sPluginsDirectory}minify.exe \"%INPUTFILE%\" --output \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # DLL: PETrim, strip, UPX
      if set(Extension) & set(KS_EXTENSION_DLL):
         thisExt = list(set(Extension) & set(KS_EXTENSION_DLL))[0];
         if not settings.getboolean('Options','EXEDisablePETrim'):
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PETrim (1/3)",
                      f"{winePrefix}{sPluginsDirectory}petrim.exe \"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("strip (2/3)",
                   f"{winePrefixForced}{sPluginsDirectory}strip{pluginExt} --strip-all -o \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         if settings.getboolean('Options','EXEEnableUPX'):
            sFlags = "";
            if settings.getint('Options','Level') < 3:
               sFlags += "-1 ";
            elif settings.getint('Options','Level') < 5:
               sFlags += "-9 ";
            elif settings.getint('Options','Level') < 7:
               sFlags += "-9 --best ";
            elif settings.getint('Options','Level') < 9:
               sFlags += "-9 --best --lzma ";
            else:
               sFlags += "-9 --best --lzma --ultra-brute --crp-ms=999999 ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("UPX (3/3)",
                      f"{winePrefixForced}{sPluginsDirectory}upx{pluginExt} --no-backup --force {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # EXE: Leanify, PETrim, strip, UPX
      if set(Extension) & set(KS_EXTENSION_EXE):
         thisExt = list(set(Extension) & set(KS_EXTENSION_EXE))[0];
         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; #1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/4)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not IsEXESFX(sInputFile):
            if not settings.getboolean('Options','EXEDisablePETrim'):
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PETrim (2/4)",
                         f"{winePrefix}{sPluginsDirectory}petrim.exe /StripFixups:Y \"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("strip (3/4)",
                      f"{winePrefixForced}{sPluginsDirectory}strip{pluginExt} --strip-all -o \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            if settings.getboolean('Options','EXEEnableUPX'):
               sFlags = "--no-backup --force ";
               if settings.getint('Options','Level') < 3:
                  sFlags += "-1 ";
               elif settings.getint('Options','Level') < 5:
                  sFlags += "-9 ";
               elif settings.getint('Options','Level') < 7:
                  sFlags += "-9 --best ";
               elif settings.getint('Options','Level') < 9:
                  sFlags += "-9 --best --lzma ";
               else:
                  sFlags += "-9 --best --lzma --ultra-brute --crp-ms=999999 ";
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("UPX (4/4)",
                         f"{winePrefixForced}{sPluginsDirectory}upx{pluginExt} {sFlags}\"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # FLAC: FLAC, FLACOut
      if set(Extension) & set(KS_EXTENSION_FLAC):
         thisExt = list(set(Extension) & set(KS_EXTENSION_FLAC))[0];
         if not settings.getboolean('Options','WAVCopyMetadata'):
            sTmpOutputFile = sInputFile.replace(".flac", "-stripped.flac");
            # Prevent a bug in shntool with no lowercase extensions
            if sTmpOutputFile == sInputFile:
               sTmpOutputFile += "-stripped.flac";

            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("shntool (1/4)",
                      f"{winePrefixForced}{sPluginsDirectory}shntool{pluginExt} strip -q -O always \"%INPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            if os.path.exists(sTmpOutputFile) \
             and (os.stat(sTmpOutputFile).st_size > 0) \
             and (os.stat(sTmpOutputFile).st_size < KI_GRID_OPTIMIZED):
               shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False)
               KI_GRID_OPTIMIZED = os.stat(sInputFile).st_size;
            if not settings.getboolean('Options','Debug'):
               os.remove(sTmpOutputFile);
            if settings.getboolean('Options','WAVStripSilence'):
               sTmpOutputFile = sInputFile.replace(".flac", "-trimmed.flac");
               # Prevent a bug in shntool with no lowercase extensions
               if (sTmpOutputFile == sInputFile):
                  sTmpOutputFile += "-trimmed.flac";

               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("shntool (2/4)",
                         f"{winePrefixForced}{sPluginsDirectory}shntool{pluginExt} trim -q -O always \"%INPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               if os.path.exists(sTmpOutputFile) \
                and (os.stat(sTmpOutputFile).st_size > 0) \
                and (os.stat(sTmpOutputFile).st_size < KI_GRID_OPTIMIZED):
                  shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False)
                  KI_GRID_OPTIMIZED = os.stat(sInputFile).st_size;
               if not settings.getboolean('Options','Debug'):
                  os.remove(sTmpOutputFile);

         sFlags = "";
         if settings.getboolean('Options','MiscCopyMetadata'):
            sFlags += "--keep-foreign-metadata ";
         if settings.getint('Options','Level') < 3:
            sFlags += "-1 ";
         elif settings.getint('Options','Level') < 5:
            sFlags += "-8 --best ";
         elif settings.getint('Options','Level') < 7:
            sFlags += "-8 --best -e ";
         else:
            sFlags += "-8 --best -ep ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("FLAC (3/4)",
                   f"{winePrefixForced}{sPluginsDirectory}flac{pluginExt} --force -s {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if settings.getint('Options','Level') >= 9:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("FLACOut (4/4)",
                      f"{winePrefix}{sPluginsDirectory}flacout.exe /q /y \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # GIF: ImageMagick, gifsicle, flexiGIF
      if set(Extension) & set(KS_EXTENSION_GIF):
         thisExt = list(set(Extension) & set(KS_EXTENSION_GIF))[0];
         sFlags = "";
         if not settings.getboolean('Options','GIFCopyMetadata'):
            sFlags += "-strip ";
         if sys.platform == "win32" or winePrefixForced:
            # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick", f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -layers optimize -compress LZW {sFlags}\"%TMPOUTPUTFILE%\"", sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -set dispose background -layers optimize -compress -loop 0 LZW {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick", f"{winePrefixForced}{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -layers optimize -compress LZW {sFlags}\"%TMPOUTPUTFILE%\"", sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -set dispose background -layers optimize -compress -loop 0 LZW {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 3 // 9, 3);
         iLevel = 3;
         sFlags += f"-O{iLevel} ";
         if not settings.getboolean('Options','GIFCopyMetadata'):
            sFlags += "--no-comments --no-extensions --no-names ";
         if settings.getboolean('Options','GIFAllowLossy'):
            sFlags += "--lossy=85 ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("gifsicle (2/2)",
                   f"{winePrefixForced}{sPluginsDirectory}gifsicle{pluginExt} -w -j --no-conserve-memory -o \"%TMPOUTPUTFILE%\" {sFlags}\"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not settings.getboolean('Options','GIFCopyMetadata'):
            sFlags = "";
            '''if settings.getint('Options','Level') >= 8:
               sFlags += "-p ";'''
            # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("flexiGIF (4/4)", f"{winePrefixForced}{sPluginsDirectory}flexiGIF{pluginExt} -q {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"", sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # GZ: Libdeflate, Leanify, ect, advdef, zRecompress, deflopt, defluff, deflopt
      if set(Extension) & set(KS_EXTENSION_GZ):
         thisExt = list(set(Extension) & set(KS_EXTENSION_GZ))[0];
         if not settings.getboolean('Options','GZCopyMetadata'):
            if sys.platform == "win32" or winePrefixForced:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("libdeflate (1/8)",
                         f"{winePrefixForced}{sPluginsDirectory}libdeflate.bat \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("libdeflate (1/8)",
                         f"{sPluginsDirectory}gzip -cd \"%INPUTFILE%\" | gzip -12 -f > \"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            if settings.getboolean('Options','GZCopyMetadata'):
               sFlags += "--keep-exif ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (2/8)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 7 // 9, 7) + 1;
         iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("advdef (3/8)",
                   f"{winePrefixForced}{sPluginsDirectory}advdef{pluginExt} -z -q -4 {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("zRecompress (4/8)",
                   f"{winePrefix}{sPluginsDirectory}zRecompress.exe -tgz \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if not settings.getboolean('Options','GZCopyMetadata'):
            sFlags += "-strμp ";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Convert level 9 to level 90032 because it is faster and usually with higher savings
         if iLevel == 9:
            iLevel = 90032;
         sFlags += f"-{iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ECT (5/8)",
                   f"{winePrefixForced}{sPluginsDirectory}ECT{pluginExt} -quiet --mt-deflate --allfilters -gzip {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','GZCopyMetadata'):
            sFlags += "/c ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (6/8)",
                   f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         if sys.platform == "win32" or winePrefixForced: # defluff run from .bat
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (7/8)",
                      f"{winePrefixForced}{sPluginsDirectory}defluff.bat \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (7/8)",
                      f"{sPluginsDirectory}defluff <\"%INPUTFILE%\" >\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (8/8)",
                   f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # HTML: tidy-html5, Minify, Leanify
      if set(Extension) & set(KS_EXTENSION_HTML):
         thisExt = list(set(Extension) & set(KS_EXTENSION_HTML))[0];
         if settings.getboolean('Options','HTMLEnableTidy'):
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("tidy (1/3)",
                      f"{winePrefixForced}{sPluginsDirectory}tidy{pluginExt} -config tidy.config -quiet -output \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\" ",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);


            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Minify (2/3)",
                      f"{winePrefixForced}{sPluginsDirectory}minify.exe \"%INPUTFILE%\" --output \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (3/3)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # ICO: ImageMagick, Leanify
      if set(Extension) & set(KS_EXTENSION_ICO):
         thisExt = list(set(Extension) & set(KS_EXTENSION_ICO))[0];
         '''
         sFlags = "";
         if not settings.getboolean('Options','PNGCopyMetadata'):
            sFlags += "-strip ";
         if sys.platform == "win32" or winePrefixForced:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -compress ZIP {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/2)",
                      f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -compress ZIP {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         '''

         # Temporary disable Leanify because it removed IPTC metadata
         if not settings.getboolean('Options','PNGCopyMetadata'):
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (2/2)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # JPEG: Guetzli, jpeg-recompress, jhead, Leanify, ect, pingo, jpegoptim, jpegtran, mozjpegtran
      if set(Extension) & set(KS_EXTENSION_JPG):
         thisExt = list(set(Extension) & set(KS_EXTENSION_JPG))[0];
         if settings.getboolean('Options','JPEGAllowLossy') and not settings.getboolean('Options','JPEGCopyMetadata'):
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Guetzli (1/10)",
                      f"{winePrefixForced}{sPluginsDirectory}guetzli{pluginExt} --quality 90 {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if settings.getboolean('Options','JPEGAllowLossy'):
            sFlags = "";
            if not settings.getboolean('Options','JPEGCopyMetadata'):
               sFlags += "--strip ";
            if settings.getint('Options','Level') >= 5:
               sFlags += "--accurate ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jpeg-recompress (2/10)",
                      f"{winePrefixForced}{sPluginsDirectory}jpeg-recompress{pluginExt} --method smallfry --quality high --min 60 --subsample disable --quiet {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags += "-zt ";
         else:
            sFlags += "-purejpg -di -dx -dt -zt ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jhead (3/10)",
                   f"{winePrefixForced}{sPluginsDirectory}jhead{pluginExt} -q -autorot {sFlags} \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags += "--keep-exif --keep-icc --jpeg-keep-all ";
         if settings.getboolean('Options','JPEGUseArithmeticEncoding'):
            sFlags += "--jpeg-arithmetic ";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (4/10)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if settings.getboolean('Options','JPEGAllowLossy'):
            sFlags = "";
            if not settings.getboolean('Options','JPEGCopyMetadata'):
               sFlags += "-strip ";
            # Seems to cause some loss of quality
            if sys.platform == "win32" or winePrefixForced:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (5/10)",
                         f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -interlace Plane -define jpeg:optimize-coding=true {sFlags}\"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (5/10)",
                         f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -interlace Plane -define jpeg:optimize-coding=true {sFlags}\"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if not settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags += "--strip-all ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jpegoptim (6/10)",
                   f"{winePrefixForced}{sPluginsDirectory}jpegoptim{pluginExt} -o -q --all-progressive {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','JPEGUseArithmeticEncoding'):
            sFlags += "-arithmetic ";
         else:
            sFlags += "-optimize ";
         if settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags += "-copy all ";
         else:
            sFlags += "-copy none ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jpegtran (7/10)",
                   f"{winePrefixForced}{sPluginsDirectory}jpegtran{pluginExt} -progressive -optimize {sFlags} -outfile \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("mozjpegtran (8/10)",
                   f"{winePrefixForced}{sPluginsDirectory}mozjpegtran{pluginExt} -outfile \"%TMPOUTPUTFILE%\" -progressive -optimize -perfect {sFlags}\"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if not settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags += "-strip ";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Convert level 9 to level 90032 because it is faster and usually with higher savings
         if iLevel == 9:
            iLevel = 90032;
         sFlags += f"-{iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ECT (9/10)",
                   f"{winePrefixForced}{sPluginsDirectory}ECT{pluginExt} -quiet --mt-deflate --allfilters -progressive {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not settings.getboolean('Options','JPEGCopyMetadata'):
            sFlags = "";
            iLevel = min(settings.getint('Options','Level') * 8 // 9, 8);
            sFlags += f"-s{iLevel} ";
            if iLevel >= 8:
               sFlags += "-table=6 ";
            if settings.getboolean('Options','JPEGAllowLossy'):
               sFlags += "-x3 -lossy ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pingo (10/10)",
                      f"{winePrefix}{sPluginsDirectory}pingo.exe -progressive {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # JS: jsmin, minify
      if (set(Extension) & set(KS_EXTENSION_JS)) or (set(Extension) & set(settings.get('Options','JSAdditionalExtensions').replace(";", " ").split(" "))):
         # If JSMin is enabled or it is a custom extension (we assume custom extensions always enable it)
         if settings.getboolean('Options','JSEnableJSMin') or (set(Extension) & set(settings.get('Options','JSAdditionalExtensions').replace(";", " ").split(" "))):
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jsmin (1/2)",
                      f"python -m jsmin \"%INPUTFILE%\" >\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Minify (2/2)",
                      f"{winePrefixForced}{sPluginsDirectory}minify.exe \"%INPUTFILE%\" --output \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # LUA: Leanify
      if set(Extension) & set(KS_EXTENSION_LUA):
         thisExt = list(set(Extension) & set(KS_EXTENSION_LUA))[0];
         if settings.getboolean('Options','LUAEnableLeanify'):
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/1)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MIME: Leanify
      if set(Extension) & set(KS_EXTENSION_MIME):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MIME))[0];
         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MKV: ffmpeg, mkclean
      if set(Extension) & set(KS_EXTENSION_MKV):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MKV))[0];
         sFlags = "";
         if not settings.getboolean('Options','MP4CopyMetadata'):
            sFlags += "-map_metadata -1 ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ffmpeg (1/2)",
                   f"{winePrefixForced}{sPluginsDirectory}ffmpeg{pluginExt} -i \"%INPUTFILE%\" -vcodec copy -acodec copy -map 0 {sFlags}\"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("mkclean (2/2)",
                   f"{winePrefixForced}{sPluginsDirectory}mkclean{pluginExt} --optimize --unsafe --quiet \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MNG: advmng
      if set(Extension) & set(KS_EXTENSION_MNG):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MNG))[0];
         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 7 // 9, 7) + 1;
         iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("advmng (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}advmng{pluginExt} -z -r -q -4 {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MP3: MP3packer
      if set(Extension) & set(KS_EXTENSION_MP3):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MP3))[0];
         sFlags = "";
         if not settings.getboolean('Options','MP3CopyMetadata'):
            sFlags += "-t -s ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("MP3packer (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}mp3packer{pluginExt} {sFlags}-z -a \"\" -A -f \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MP4: ffmpeg, mp4v2
      if set(Extension) & set(KS_EXTENSION_MP4):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MP4))[0];
         sFlags = "";
         if not settings.getboolean('Options','MP4CopyMetadata'):
            sFlags += "-map_metadata -1 ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ffmpeg (1/2)",
                   f"{winePrefixForced}{sPluginsDirectory}ffmpeg{pluginExt} -i \"%INPUTFILE%\" -vcodec copy -acodec copy -map 0 {sFlags}\"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("mp4v2 (2/2)",
                   f"{winePrefixForced}{sPluginsDirectory}mp4file{pluginExt} --optimize -q \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # OBJ: strip
      if set(Extension) & set(KS_EXTENSION_OBJ):
         thisExt = list(set(Extension) & set(KS_EXTENSION_OBJ))[0];
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("strip (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}strip{pluginExt} --strip-all -o \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # OGG: rehuff
      if set(Extension) & set(KS_EXTENSION_OGG):
         thisExt = list(set(Extension) & set(KS_EXTENSION_OGG))[0];
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("rehuff (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}rehuff{pluginExt} \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # OGV: ffmpeg, rehuff_theora
      if set(Extension) & set(KS_EXTENSION_OGV):
         thisExt = list(set(Extension) & set(KS_EXTENSION_OGV))[0];
         sFlags = "";
         if not settings.getboolean('Options','MP4CopyMetadata'):
            sFlags += "-map_metadata -1 ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ffmpeg (1/2)",
                   f"{winePrefixForced}{sPluginsDirectory}ffmpeg{pluginExt} -i \"%INPUTFILE%\" -vcodec copy -acodec copy -map 0 {sFlags}\"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("rehuff_theora (2/2)",
                   f"{winePrefixForced}{sPluginsDirectory}rehuff_theora{pluginExt} \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # Microsoft OLE Compound Files: Document Press, Best CFBF
      if set(Extension) & set(KS_EXTENSION_OLE):
         thisExt = list(set(Extension) & set(KS_EXTENSION_OLE))[0];
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Document Press (1/2)",
                   f"{winePrefix}{sPluginsDirectory}docprc.exe -opt \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Best CFBF (2/2)",
                   f"{winePrefix}{sPluginsDirectory}bestcfbf.exe \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\" -v4",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # PCX: ImageMagick
      if set(Extension) & set(KS_EXTENSION_PCX):
         thisExt = list(set(Extension) & set(KS_EXTENSION_PCX))[0];
         sFlags = "";
         if not settings.getboolean('Options','PCXCopyMetadata'):
            sFlags += "-strip ";
         if sys.platform == "win32" or winePrefixForced:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                      f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -compress RLE {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                      f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -compress RLE {sFlags}\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # PDF: mutool, ghostcript, cpdfsqueeze
      if set(Extension) & set(KS_EXTENSION_PDF):
         thisExt = list(set(Extension) & set(KS_EXTENSION_PDF))[0];
         bIsPDFLayered = IsPDFLayered(sInputFile);

         # Skip Ghostcript on PDF with layers, or if no downsampling is selected, because GS always downsample images.
         if not bIsPDFLayered \
          or not settings.getboolean('Options','PDFSkipLayered') \
          or settings.get('Options','PDFProfile') == "none":
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("mutool (1/3)",
                      f"{winePrefixForced}{sPluginsDirectory}mutool{pluginExt} clean -ggg -z \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            # Do not use Ghoscript for Adobe Illustrator (AI) files
            if not sInputFile.endswith(".ai"):
               sFlags = "";
               # Custom mode
               if settings.get('Options','PDFProfile') == "Custom":
                  sFlags += f"-dPDFSETTINGS=/ebook -dDownsampleColorImages=true -dColorImageResolution={settings.getint('Options','PDFCustomDPI')} -dDownsampleGrayImages=true -dGrayImageResolution={settings.getint('Options','PDFCustomDPI')} -dDownsampleMonoImages=true -dMonoImageResolution={settings.getint('Options','PDFCustomDPI')} ";
               # No downsampling
               elif settings.get('Options','PDFProfile') == "none":
                  sFlags += "-dPDFSETTINGS=/default -c \".setpdfwrite <</ColorACSImageDict>[1 1 1 1] /VSamples [1 1 1 1] /Blend 1>> /GrayACSImageDict<</QFactor>[1 1 1 1] /VSamples [1 1 1 1] /Blend 1>>>> setdistillerparams\" ";
               # Built in downsample modes: screen, ebook, printer, prepress
               else:
                  sFlags += f"-dPDFSETTINGS=/{settings.get('Options','PDFProfile')} ";

               sFlags += "-dColorImageDownsampleType=/Bicubic -dGrayImageDownsampleType=/Bicubic -dMonoImageDownsampleType=/Bicubic -dOptimize=true -dConvertCMYKImagesToRGB=true -dColorConversionStrategy=/sRGB -dPrinted=false -q -dBATCH -dNOPAUSE -dSAFER -dDELAYSAFER -dNOPROMPT -sDEVICE=pdfwrite -dDetectDuplicateImages=true -dAutoRotatePages=/None -dCompatibilityLevel=1.4 ";

               acTmpFilePdf = f"{os.path.splitext(sInputFile)[0]}.tmp.pdf";
               acTmpFilePdf = GetShortName(acTmpFilePdf);

               # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Ghostcript",
               #          f"{winePrefixForced}{sPluginsDirectory}cwebp{pluginExt} -mt -quiet -lossless {sFlags}\"{acTmpFileWebp}\" -o \"%INPUTFILE%\" -o \"{acTmpFileWebp}\"",
               #          sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               if IsWindows64() and (sys.platform == "win32" or winePrefixForced):
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Ghostcript (2/3)",
                            f"{winePrefixForced}{sPluginsDirectory}gswin64c.exe {sFlags}-sOutputFile=\"{acTmpFilePdf}\" \"%INPUTFILE%\"",
                            sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               elif sys.platform == "win32" or winePrefixForced:
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Ghostcript (2/3)",
                            f"{winePrefixForced}{sPluginsDirectory}gswin32c.exe {sFlags}-sOutputFile=\"{acTmpFilePdf}\" \"%INPUTFILE%\"",
                            sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               else:
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Ghostcript (2/3)",
                            f"{sPluginsDirectory}gs {sFlags}-sOutputFile=\"{acTmpFilePdf}\" \"%INPUTFILE%\"",
                            sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               # If there is size reduction check it is not so high to detect corrupted encrypted PDF
               if os.path.exists(acTmpFilePdf) and os.stat(acTmpFilePdf).st_size < os.stat(sInputFile).st_size:
                  if os.stat(acTmpFilePdf).st_size > 3000 and os.stat(sInputFile).st_size > 20000:
                     shutil.copy2(acTmpFilePdf, sInputFile, follow_symlinks=False);
               if os.path.exists(acTmpFilePdf) and not settings.getboolean('Options','Debug'):
                  os.remove(acTmpFilePdf);

            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("cpdfsqueeze (3/3)",
                      f"{winePrefixForced}{sPluginsDirectory}cpdfsqueeze{pluginExt} \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # PNG: apngopt, pngquant, PngOptimizer, TruePNG, pngout, optipng, pngwolf, Leanify, ect, pingo, advpng, deflopt, defluff, deflopt
      if set(Extension) & set(KS_EXTENSION_PNG):
         thisExt = list(set(Extension) & set(KS_EXTENSION_PNG))[0];
         bIsAPNG = IsAPNG(sInputFile);
         bIsPNG9Patch = sInputFile.endswith(".9.png");

         # Android 9-patch images get broken with advpng, deflopt, optipng, pngoptimizer, pngout, pngrewrite and truepng. Only pngwolf, defluff and leanify seem to be safe. At the moment, detect them by extension .9.png.
         if bIsAPNG:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("apngopt (1/16)",
                      f"{winePrefixForced}{sPluginsDirectory}apngopt.exe \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not bIsPNG9Patch:
            if settings.getboolean('Options','PNGAllowLossy') and not bIsAPNG:
               sFlags = "";
               if not settings.getboolean('Options','PNGCopyMetadata'):
                  sFlags += "--strip ";
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pngquant (2/16)",
                         f"{winePrefixForced}{sPluginsDirectory}pngquant.exe {sFlags}--quality=85-95 --speed 1 --ext .png --force \"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            sFlags = "";
            if settings.getboolean('Options','PNGCopyMetadata'):
               sFlags += "-KeepPhysicalPixelDimensions ";
            if sys.platform == "win32" or winePrefixForced:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PngOptimizer (3/16)",
                         f"{winePrefixForced}{sPluginsDirectory}PngOptimizer.exe {sFlags}-file:\"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PngOptimizer (3/16)",
                         f"{sPluginsDirectory}pngoptimizercl{pluginExt} {sFlags}-file:\"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not bIsAPNG and not bIsPNG9Patch:
            # Disable TruePNG on ICO files because it crashes
            if not (set(Extension) & set(KS_EXTENSION_ICO)):
               sFlags = "";
               iLevel = min(settings.getint('Options','Level') * 3 // 9, 3) + 1;
               sFlags += f"-o{iLevel} ";
               if settings.getboolean('Options','PNGCopyMetadata'):
                  sFlags += "-md keep all ";
               else:
                  sFlags += "-tz -md remove all -a1 -g1 ";
               if settings.getboolean('Options','PNGAllowLossy'):
                  sFlags += "-l ";
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("TruePNG (4/16)",
                         f"{winePrefix}{sPluginsDirectory}TruePNG.exe {sFlags}/i0 /nc /tz /quiet /y /out \"%TMPOUTPUTFILE%\" \"%INPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            # Skip PNGOut when it is a JPEG renamed to PNG
            if not (set(GetExtensionByContent(sInputFile)) & set(KS_EXTENSION_JPG)):
               sFlags = "";
               if settings.getboolean('Options','PNGCopyMetadata'):
                  sFlags += "/k1 ";
               else:
                  sFlags += "/kacTL,fcTL,fdAT ";
               iLevel = max((settings.getint('Options','Level') * 3 // 9) - 3, 0);
               sFlags += f"/s{iLevel} ";
               if sys.platform == "win32" or winePrefixForced:
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PNGOut (5/16)",
                            f"{winePrefixForced}{sPluginsDirectory}pngout.exe /q /y /r /d0 /mincodes0 {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                            sInputFile, "", 0, 0, ErrorsList=(2,), Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               else:
                  sFlags = sFlags.replace("/","-")
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("PNGOut (5/16)",
                            f"{sPluginsDirectory}pngout{pluginExt} -q -y -r -d0 -mincodes0 {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                            sInputFile, "", 0, 0, ErrorsList=(2,), Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         iLevel = min(settings.getint('Options','Level') * 6 // 9, 6);
         sFlags += f"-o{iLevel} ";
         if bIsAPNG:
            # For some reason -strip all -protect acTL,fcTL,fdAT is not keeping APNG chunks
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("OptiPNG (6/16)",
                      f"{winePrefixForced}{sPluginsDirectory}optipng{pluginExt} -zw32k -protect acTL,fcTL,fdAT -quiet {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            if not settings.getboolean('Options','PNGCopyMetadata'):
               sFlags += "-strip all ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("OptiPNG (7/16)",
                      f"{winePrefixForced}{sPluginsDirectory}optipng{pluginExt} -zw32k -quiet {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not bIsAPNG:
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            # Temporary disable Leanify because it removed IPTC metadata
            if not settings.getboolean('Options','PNGCopyMetadata'):
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (8/16)",
                         f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 7 // 9, 7) + 1;
            if settings.getint('Options','PNGWolfIterations') != -1:
               iLevel = settings.getint('Options','PNGWolfIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"--out-deflate=zopfli,iter={iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pngwolf (9/16)",
                      f"{winePrefixForced}{sPluginsDirectory}pngwolf{pluginExt} {sFlags}--in=\"%INPUTFILE%\" --out=\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

            if not bIsPNG9Patch:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pngrewrite (10/16)",
                         f"{winePrefixForced}{sPluginsDirectory}pngrewrite{pluginExt} \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

               # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageWorsener",
               #                    f"{winePrefixForced}{sPluginsDirectory}imagew{pluginExt} -noresize -zipcmprlevel 9 \"" + grdFiles->Cells[0][iCount] + "\" \"{acTmpFile}\"",
               #                    acPluginsDirectory, acTmpFile);

               sFlags = "";
               # iLevel = min(settings.getint('Options','Level') * 7 // 9, 7) + 1;
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
               sFlags += f"-i {iLevel} ";
               if not settings.getboolean('Options','PNGCopyMetadata'):
                  iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("advpng (11/16)",
                            f"{winePrefixForced}{sPluginsDirectory}advpng{pluginExt} -z -q -4 {sFlags}\"%TMPINPUTFILE%\"",
                            sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         # ECT will preserve APNG compatibility when --reuse is used and -strip is not used
         if bIsAPNG:
            sFlags += "--reuse ";
         elif not settings.getboolean('Options','PNGCopyMetadata'):
            sFlags += "-strip ";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Convert level 9 to level 90032 because it is faster and usually with higher savings
         if iLevel == 9:
            iLevel = 90032;
         sFlags += f"-{iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ECT (12/16)",
                   f"{winePrefixForced}{sPluginsDirectory}ECT{pluginExt} -quiet --mt-deflate --allfilters {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8);
         sFlags += f"-s{iLevel} ";

         if not settings.getboolean('Options','PNGCopyMetadata'):
            sFlags += "-strip ";
         if settings.getboolean('Options','PNGAllowLossy'):
            sFlags += "-x3 -lossyfilter ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pingo (13/16)",
                   f"{winePrefix}{sPluginsDirectory}pingo.exe {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','PNGCopyMetadata'):
            sFlags += "/k ";

         if not bIsAPNG and not bIsPNG9Patch:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (14/16)",
                      f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if sys.platform == "win32" or winePrefixForced: # defluff run from .bat
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (15/16)",
                      f"{winePrefixForced}{sPluginsDirectory}defluff.bat \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (15/16)",
                      f"{sPluginsDirectory}defluff <\"%INPUTFILE%\" >\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         if not bIsAPNG and not bIsPNG9Patch:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (16/16)",
                      f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);


      # SWF: Leanfy, flasm, zRecompress
      if set(Extension) & set(KS_EXTENSION_SWF):
         thisExt = list(set(Extension) & set(KS_EXTENSION_SWF))[0];
         sTmpOutputFile = sInputFile.replace(".swf", ".$wf");
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("flasm (1/5)",
                   f"{winePrefixForced}{sPluginsDirectory}flasm{pluginExt} -x \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False);
         os.remove(sTmpOutputFile);

         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("flasm (2/5)",
                   f"{winePrefixForced}{sPluginsDirectory}flasm{pluginExt} -u \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False);
         os.remove(sInputFile.replace(".swf", ".$wf"));

         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("flasm (3/5)",
                   f"{winePrefixForced}{sPluginsDirectory}flasm{pluginExt} -z \"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         if os.stat(sTmpOutputFile).st_size < KI_GRID_OPTIMIZED:
            shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False);
            KI_GRID_OPTIMIZED = os.stat(sInputFile).st_size;
         os.remove(sInputFile.replace(".swf", ".$wf"));

         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("zRecompress (4/5)",
                   f"{winePrefix}{sPluginsDirectory}zRecompress.exe -tswf-lzma \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (5/5)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # SQLITE: sqlite
      if set(Extension) & set(KS_EXTENSION_SQLITE):
         thisExt = list(set(Extension) & set(KS_EXTENSION_SQLITE))[0];
         if sys.platform == "win32" or winePrefixForced:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("sqlite (1/1)",
                      f"{winePrefixForced}{sPluginsDirectory}sqlite.bat \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("sqlite (1/1)",
                      f"{sPluginsDirectory}sqlite.sh \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\" > /dev/null",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # TAR: Leanify
      if set(Extension) & set(KS_EXTENSION_TAR):
         thisExt = list(set(Extension) & set(KS_EXTENSION_TAR))[0];
         sFlags = "";
         if settings.getboolean('Options','GZCopyMetadata'):
            sFlags += "--keep-exif ";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/1)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # Tencent QQ: Leanify
      if set(Extension) & set(KS_EXTENSION_TENCENTQQ):
         thisExt = list(set(Extension) & set(KS_EXTENSION_TENCENTQQ))[0];
         if not settings.getboolean('Options','PNGCopyMetadata'):
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/1)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

      # TGA: ImageMagick
      if set(Extension) & set(KS_EXTENSION_TGA):
         thisExt = list(set(Extension) & set(KS_EXTENSION_TGA))[0];
         sFlags = "";
         if not settings.getboolean('Options','TGACopyMetadata'):
            sFlags += "-strip ";
         if sys.platform == "win32" or winePrefixForced:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                      f"{winePrefixForced}{sPluginsDirectory}magick.exe convert -quiet -compress RLE {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                      f"{sPluginsDirectory}convert -quiet -compress RLE {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # TIFF: jhead, ImageMagick, jpegoptim, jpegtran, mozjpegtran
      if set(Extension) & set(KS_EXTENSION_TIFF):
         thisExt = list(set(Extension) & set(KS_EXTENSION_TIFF))[0];
         sFlags = "";
         if settings.getboolean('Options','TIFFCopyMetadata'):
            sFlags += "-zt ";
         else:
            sFlags += "-purejpg -di -dx -dt -zt ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jhead (1/5)",
                   f"{winePrefixForced}{sPluginsDirectory}jhead{pluginExt} -q -autorot {sFlags} \"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         # ImageMagick does not keep metadata on TIFF images so disable it
         if not settings.getboolean('Options','TIFFCopyMetadata'):
            if sys.platform == "win32" or winePrefixForced:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (2/5)",
                         f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet -compress ZIP -strip \"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (2/5)",
                         f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet -compress ZIP -strip \"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if not settings.getboolean('Options','TIFFCopyMetadata'):
            sFlags += "--strip-all ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jpegoptim (3/5)",
                   f"{winePrefixForced}{sPluginsDirectory}jpegoptim{pluginExt} -o -q --all-progressive {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','TIFFCopyMetadata'):
            sFlags += "-arithmetic ";
         else:
            sFlags += "-optimize ";
         if settings.getboolean('Options','TIFFCopyMetadata'):
            sFlags += "-copy all ";
         else:
            sFlags += "-copy none ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("jpegtran (4/5)",
                   f"{winePrefixForced}{sPluginsDirectory}jpegtran{pluginExt} -progressive -optimize {sFlags}\"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("mozjpegtran (5/5)",
                   f"{winePrefixForced}{sPluginsDirectory}mozjpegtran{pluginExt} -outfile \"%TMPOUTPUTFILE%\" -progressive -optimize -perfect {sFlags}\"%INPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # WAV: shntool
      if set(Extension) & set(KS_EXTENSION_WAV):
         thisExt = list(set(Extension) & set(KS_EXTENSION_WAV))[0];
         if not settings.getboolean('Options','WAVCopyMetadata'):
            sTmpOutputFile = sInputFile.replace(".wav", "-stripped.wav");
            # Prevent a bug in shntool with no lowercase extensions
            if sTmpOutputFile == sInputFile:
               sTmpOutputFile += "-stripped.wav";

            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("shntool (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}shntool{pluginExt} strip -q -O always \"%INPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            if os.stat(sTmpOutputFile).st_size > 0 and os.stat(sTmpOutputFile).st_size < KI_GRID_OPTIMIZED:
               shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False);
               KI_GRID_OPTIMIZED = os.stat(sInputFile).st_size;
            if not settings.getboolean('Options','Debug'):
               os.remove(sTmpOutputFile);
            if settings.getboolean('Options','WAVStripSilence'):
               sTmpOutputFile = sInputFile.replace(".wav", "-trimmed.wav");
               # Prevent a bug in shntool with no lowercase extensions
               if sTmpOutputFile == sInputFile:
                  sTmpOutputFile += "-trimmed.wav";

               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("shntool (2/2)",
                         f"{winePrefixForced}{sPluginsDirectory}shntool{pluginExt} trim -q -O always \"%INPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
               if os.stat(sTmpOutputFile).st_size > 0 and os.stat(sTmpOutputFile).st_size < KI_GRID_OPTIMIZED:
                  shutil.copy2(sTmpOutputFile, sInputFile, follow_symlinks=False);
                  KI_GRID_OPTIMIZED = os.stat(sInputFile).st_size;
               if not settings.getboolean('Options','Debug'):
                  os.remove(sTmpOutputFile);
      # XML: Leanify
      if set(Extension) & set(KS_EXTENSION_XML):
         thisExt = list(set(Extension) & set(KS_EXTENSION_XML))[0];
         if settings.getboolean('Options','XMLEnableLeanify'):
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
            # Overwrite Leanify iterations
            if settings.getint('Options','LeanifyIterations') != -1:
               iLevel = settings.getint('Options','LeanifyIterations');
            else:
               iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/2)",
                      f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Minify (2/2)",
                      f"{winePrefixForced}{sPluginsDirectory}minify.exe \"%INPUTFILE%\" --output \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # WEBP: pingo, dwebp + cwebp, ImageWorsener
      if set(Extension) & set(KS_EXTENSION_WEBP):
         thisExt = list(set(Extension) & set(KS_EXTENSION_WEBP))[0];
         sFlags = "";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8);
         sFlags += f"-s{iLevel} ";
         if settings.getboolean('Options','WEBPAllowLossy'):
            sFlags += "-webp ";
         else:
            sFlags += "-webp-lossless ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("pingo (1/3)",
                   f"{winePrefix}{sPluginsDirectory}pingo.exe {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         iLevel = min(settings.getint('Options','Level') * 5 // 9, 5) + 1;
         sFlags += f"-m {iLevel} ";

         acTmpFileWebp = f"{os.path.splitext(sInputFile)[0]}.png";
         acTmpFileWebp = GetShortName(acTmpFileWebp);

         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("dwebp (2/3)",
                      f"{winePrefixForced}{sPluginsDirectory}dwebp{pluginExt} -mt \"%INPUTFILE%\" -o \"{acTmpFileWebp}\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         if iError == 0:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("cwebp (3/3)",
                      f"{winePrefixForced}{sPluginsDirectory}cwebp{pluginExt} -mt -quiet -lossless {sFlags}\"{acTmpFileWebp}\" -o \"%INPUTFILE%\" -o \"{acTmpFileWebp}\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            if os.stat(acTmpFileWebp).st_size < os.stat(sInputFile).st_size:
               shutil.copy2(acTmpFileWebp, sInputFile, follow_symlinks=False);
         if not settings.getboolean('Options','Debug'):
            os.remove(acTmpFileWebp);

         # iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageWorsener",
         #           f"{winePrefixForced}{sPluginsDirectory}imagew{pluginExt} -noresize -zipcmprlevel 9 \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
         #           sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # ZIP: Leanify, ect, advzip, deflopt, defluff, deflopt
      if set(Extension) & set(KS_EXTENSION_ZIP):
         thisExt = list(set(Extension) & set(KS_EXTENSION_ZIP))[0];
         bIsEXESFX = IsEXESFX(sInputFile);

         sFlags = "";
         if settings.getboolean('Options','ZIPCopyMetadata'):
            sFlags += "--keep-exif ";
         # iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Overwrite Leanify iterations
         if settings.getint('Options','LeanifyIterations') != -1:
            iLevel = settings.getint('Options','LeanifyIterations');
         else:
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
         sFlags += f"-i {iLevel} ";
         # Limit ZIP no recurse to ZIP extension
         if not settings.getboolean('Options','ZIPRecurse') and (set(Extension) & {".zip"}):
            sFlags += "-d 1 ";
            # sFlags += "-f ";
         sFlags += "--zip-deflate ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("Leanify (1/6)",
                   f"{winePrefixForced}{sPluginsDirectory}leanify{pluginExt} -q -p {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if not settings.getboolean('Options','ZIPCopyMetadata'):
            sFlags += "-strip ";
         iLevel = min(settings.getint('Options','Level') * 8 // 9, 8) + 1;
         # Convert level 9 to level 90032 because it is faster and usually with higher savings
         if iLevel == 9:
            iLevel = 90032;
         sFlags += f"-{iLevel} ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ECT (2/6)",
                   f"{winePrefixForced}{sPluginsDirectory}ECT{pluginExt} -quiet --mt-deflate -zip {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         # AdvZip strips header on ZIP files
         if not bIsEXESFX:
            sFlags = "";
            # iLevel = min(settings.getint('Options','Level') * 7 // 9, 7) + 1;
            iLevel = settings.getint('Options','Level') ** 3 // 25 + 1; # 1, 1, 2, 3, 6, 9, 14, 21, 30
            sFlags += f"-i {iLevel} ";
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("advzip (3/6)",
                      f"{winePrefixForced}{sPluginsDirectory}advzip.exe -z -q -4 {sFlags}\"%TMPINPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

         sFlags = "";
         if settings.getboolean('Options','ZIPCopyMetadata'):
            sFlags += "/c ";
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (4/6)",
                   f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         if sys.platform == "win32" or winePrefixForced: # defluff run from .bat
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (5/6)",
                      f"{winePrefixForced}{sPluginsDirectory}defluff.bat \"%INPUTFILE%\" \"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         else:
            iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("defluff (5/6)",
                      f"{sPluginsDirectory}defluff <\"%INPUTFILE%\" >\"%TMPOUTPUTFILE%\"",
                      sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
         iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("DeflOpt (6/6)",
                   f"{winePrefix}{sPluginsDirectory}deflopt.exe /a /b /s {sFlags}\"%TMPINPUTFILE%\"",
                   sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # 7Z: m7zRepacker
      if set(Extension) & set(KS_EXTENSION_7Z):
         thisExt = list(set(Extension) & set(KS_EXTENSION_7Z))[0];
         # Very slow, use it only in high compression profiles
         if settings.getint('Options','Level') > 7:
            if IsWindows64():
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("m7zRepacker (1/1)",
                         f"{winePrefix}{sPluginsDirectory}m7zrepacker.exe -m1 -d1024 -mem2048 \"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("m7zRepacker (1/1)",
                         f"{winePrefix}{sPluginsDirectory}m7zrepacker.exe -m1 -d128 -mem512 \"%TMPINPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
      # MISC: ImageMagick
      if set(Extension) & set(KS_EXTENSION_MISC):
         thisExt = list(set(Extension) & set(KS_EXTENSION_MISC))[0];
         if not settings.getboolean('Options','MiscDisable'):
            sFlags = "";
            if not settings.getboolean('Options','MiscCopyMetadata'):
               sFlags += "-strip ";
            if sys.platform == "win32" or winePrefixForced:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                         f"{winePrefixForced}{sPluginsDirectory}magick.exe convert \"%INPUTFILE%\" -quiet {sFlags}\"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);
            else:
               iError, KI_GRID_OPTIMIZED, KI_GRID_STATUS = RunPlugin("ImageMagick (1/1)",
                         f"{sPluginsDirectory}convert \"%INPUTFILE%\" -quiet {sFlags}\"%TMPOUTPUTFILE%\"",
                         sInputFile, "", 0, 0, Extension=thisExt, KI_GRID_ORIGINAL=KI_GRID_ORIGINAL, KI_GRID_OPTIMIZED=KI_GRID_OPTIMIZED, KI_GRID_STATUS=KI_GRID_STATUS, silentMode=silentMode);

      if settings.getboolean('Options','KeepAttributes'):
         # Restore timestamp if we were able to get it
         if udtFileCreated != (0, 0):
            os.utime(sInputFile, times=udtFileCreated);
         if FileAttributes is not None:
            SetFileAttributes(GetShortName(sInputFile), FileAttributes);

   # If file was not processed, mark it as skipped because not supported extension, or skipped because user preference (do not process JS for instance)
   if    KI_GRID_STATUS == "Pending" \
      or KI_GRID_STATUS == "Copying to Recyclebin..." \
      or KI_GRID_STATUS == "Creating backup...":
            KI_GRID_STATUS = "Skipped";
            iPercentBytes = 1.0;
            acTime = 0.0;
   elif KI_GRID_STATUS != "Optimized":
      iPercentBytes = KI_GRID_OPTIMIZED / KI_GRID_ORIGINAL;

      # Required indirection
      iEndTicks = time.perf_counter();
      acTime = iEndTicks - iStartTicks;
      sTime = time.gmtime(acTime);
      sTime = ":".join(f"{t}" for t in (sTime.tm_mday-1, sTime.tm_hour, sTime.tm_min, sTime.tm_sec) if t);
      if not sTime:
         sTime = f"0 sec";
      elif ":" not in sTime:
         sTime = f"{sTime} sec";

      sCaption = f"Done {iPercentBytes:.2%} in {sTime}";
      KI_GRID_STATUS = sCaption;

   if not silentMode:
      print(f"{SetCellFileValue(sInputFile)} ", f" {thisExt} ", f" {KI_GRID_ORIGINAL} ", f" {KI_GRID_OPTIMIZED} ", f" {KI_GRID_STATUS} ", sep="\t", end="\n");
   res.update({"InputFile": os.path.abspath(sInputFile),
               "Extension": thisExt,
               "Original": KI_GRID_ORIGINAL,
               "Optimized": KI_GRID_OPTIMIZED,
               "Status": "Done" if "Done" in KI_GRID_STATUS else KI_GRID_STATUS,
               "PercentBytes": iPercentBytes,
               "Time": acTime});
   return res

def optimiseDir(dirName, silentMode=False):
   '''Optimisation all file in directory.

   `dirName` is a path of directory.

   `silentMode` is a flag of running without output print.

   Returns list of results optimisation.
   '''
   result_list = [];
   if os.path.isdir(dirName):
      for elem in os.scandir(dirName):
         result_list.extend(optimiseDir(elem.path, silentMode=silentMode));
   else:
      result_list.append(optimise(dirName, silentMode=silentMode));
   return result_list;

class FileOptimiser:
   """Class for manage files and order before optimisation and using parallelism of processes.

   `filelist` is iterable contains files to convert to list of Path objects as self.files.
   """
   def __init__(self,filelist=None):
      if filelist:
         self.getFiles(filelist);
      else:
         self.files = ();

   def recursiveFilesFromDir(self, filelist):
      '''Recursive yielding files as Path object in directory.

      `filelist` is Path object, path string or iterable of strings.
      '''
      if hasattr(filelist, 'stat'):
         if filelist.is_dir():
            for path in filelist.iterdir():
               for f in self.recursiveFilesFromDir(path):
                  yield f
         else:
            if hasattr(filelist,'resolve'):
               yield filelist.resolve();
            else:
               yield os.path.abspath(filelist.path);
      elif isinstance(filelist, str):
         for f in self.recursiveFilesFromDir(pathlib.Path(filelist)):
            yield f
      else:
         for path in filelist:
            for f in self.recursiveFilesFromDir(path):
               yield f

   def getFiles(self,filelist):
      '''Rewriting self.files to new filelist.

      `filelist` is Path object, path string or iterable of strings.
      '''
      self.files = list(self.recursiveFilesFromDir(filelist));

   def optimise(self,silentMode=False,processes=None):
      '''Optimisation all files from self.file.

      `silentMode` is a flag of running without output print.

      `processes` is a count processes for parallel running.
      '''
      # We should use optimise_parallel() if processes more then one
      if processes and processes>1:
         return self.optimise_parallel(silentMode=silentMode,processes=processes);
      else:
         result_list = [];
         for elem in self.files:
            result_list.append(optimise(f"{elem}", silentMode=silentMode));
         return result_list;

   def optimize(self, *args, **kwargs):
      return self.optimise(*args, **kwargs);

   def optimise_parallel(self,silentMode=False,processes=4):
      '''Parallel optimisation all files from self.file.

      `silentMode` is a flag of running without output print.

      `processes` is a count processes for parallel running.
      '''
      result_list = [];
      process_list = [];
      running_processes = [];
      # Pre-creating processes for every file
      manager = multiprocessing.Manager();
      for elem in self.files:
         res = manager.dict();
         process_list.append(multiprocessing.Process(target=optimise,
                                                     args=(f"{elem}",),
                                                     kwargs={'silentMode': silentMode,
                                                             'res': res}
                                                    )
                            );
         result_list.append(res);

      next_process = 0;
      closed_processes_count = 0;
      while next_process<len(process_list):
         # Run pre-created processes
         if len(running_processes)<processes:
            running_processes.append(process_list[next_process]);
            process_list[next_process].start();
            next_process += 1;
         # Wait for closing any running process
         else:
            for running_process in running_processes:
               if not running_process.is_alive():
                  running_processes.remove(running_process);
                  closed_processes_count += 1;
      # Wait for closing processes
      for running_process in running_processes:
         running_process.join();

      if settings.getboolean('Options','BeepWhenDone'):
         print("\a");

      return list(map(dict,result_list));

   def optimize_parallel(self, *args, **kwargs):
      return self.optimise_parallel(*args, **kwargs);

   def filter(self,filter_func):
      '''Filtering files which True in funnction.
      '''
      self.files = filter(filter_func, list(self.files));

   def sort(self,sort_func, reverse=False):
      '''Sorting file in the order which they will be optimised.

      `sort_func` is sorting function.

      `reverse` is reversin flag.
      '''
      self.files = sorted(list(self.files), key=sort_func, reverse=reverse);

# Synonyms with -ize
def optimize(*args, **kwargs):
   return optimise(*args, **kwargs);
def optimizeDir(*args, **kwargs):
   return optimiseDir(*args, **kwargs);
class FileOptimizer(FileOptimiser):
   pass;
