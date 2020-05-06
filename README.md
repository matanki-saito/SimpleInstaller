# Simple Installer

![run](resource/image.png)

Install game mods to your computer.
 
 - For [Europa Universalis IV](https://store.steampowered.com/app/236850/Europa_Universalis_IV/)
   - [eu4dll](https://github.com/matanki-saito/EU4dll) : Multi-byte patch
   - [EUIV Main 1: Fonts and UI](https://github.com/matanki-saito/EU4JPModCore)
   - [EUIV Main 2: Text](https://github.com/matanki-saito/EU4JPModAppendixI)
   - [JPMOD Font Gothic](https://github.com/oooFUNooo/eu4-font-gothic)
   - [EUIV Sub 2: Character/history](https://github.com/matanki-saito/EU4JPModAppendixII)
   - [auto updater](https://github.com/matanki-saito/moddownloader)
 - For [Crusader Kings II](https://store.steampowered.com/app/203770/Crusader_Kings_II/)
   - [ck2dll](https://github.com/matanki-saito/CK2dll) : Multi-byte patch
   - [CKII Mod Core](https://github.com/matanki-saito/CK2JPModCore)
   - [CKII Mod Appendix I](https://github.com/matanki-saito/CK2JPModAppendixI)
   - [CKII Mod Appendix II](https://github.com/matanki-saito/CK2JPModAppendixII)
   - [CKII Mod Appendix III](https://github.com/matanki-saito/CK2JPModAppendixIII)
   - [CKII Mod Font Gothic](https://github.com/oooFUNooo/ck2-font-gothic)
   - [CKII Mod Font Aoyagi](https://github.com/matanki-saito/CK2JPModAppendixV)
   - [auto updater](https://github.com/matanki-saito/moddownloader)
 - For [Imperator:Rome](https://store.steampowered.com/app/859580/Imperator_Rome)
   - [irdll](https://github.com/matanki-saito/irdll) : Change mm/dd/yyyy to yyyy/mm/dd
   - [UI fix mod](https://github.com/matanki-saito/ImperatorRomeJPAppI)
   - [auto updater](https://github.com/matanki-saito/moddownloader)

## How to use
 Just click the button !

> ### NOTICE 
> - Steam Only
> - **Windows Only**
> - Cannot run under Windows 7. 
> - Cannot run on x86 machine.
> - **Administrator User** Login Required
> - **Windows Defender only**. Installer will not work properly under other antivirus software.
> - Requires [.Net 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48) or later.
> - User name must **not contain spaces**. OK) HakureiReimu , NG) Hakurei Reimu

## Sequence
TBD

## Build
### Requirement

 - windows 10 or later
 - python 3.7 or later
 - pyinstaller ```pip install pyinstaller```
 
### command

```
pyinstaller ./angelica.py -n installer --onefile --noconsole --icon=./icon.ico
```

## Licence
 - [MIT](https://github.com/tcnksm/tool/blob/master/LICENCE)
