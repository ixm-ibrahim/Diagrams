#NoEnv

#Warn All, MsgBox			; show all warnings by a popup message box (both are active by default)

SendMode Input				; reliably buffer any physical keyboard or mouse activity during the send (makes every Send call equavelent to SendInput, which is active by default)
SetWorkingDir A_ScriptDir	; ensures consistent working directory regardless of how the script is executed or where it is called from

; Note that the brackets after the HotIfs don't actually do anything functionally, it's just for readabiliy purposes
; Note that the order does not matter (except for < and >) as long as the hotkey appears at the end
; # - windows key
; ! - alt key
; ^ - ctrl key
; + - shift key
; < - specify the left button
; > - specify the right button

#If IsEnglish() and !IsCapsLockOn()
{
	; Vowels
	<!a::Send  "{U+0101}"	; ā - ا
	<!i::Send  "{U+012B}"	; ī - ي
	<!u::Send  "{U+016B}"	; ū - و
	
	; Consonants (hard letters, left ALT)
	<!d::Send  "{U+1E0D}"	; ḍ - ض
	<!h::Send  "{U+1E25}"	; ḥ - ح
	<!s::Send  "{U+1E63}"	; ṣ - ص
	<!t::Send  "{U+1E6D}"	; ṭ - ط
	<!z::Send  "{U+1E93}"	; ẓ - ظ
	<!`::Send  "{U+02BF}"	; ʿ - ع

	; Consonants (easy letters, right ALT - avoids the awkward transliteration of shaddahs like "dhdh", "ghgh", "shsh", etc.)
	>!d::Send  "{U+1E0F}"	; ḏ - ذ
	>!g::Send  "{U+1E21}"	; ḡ - غ
	>!k::Send  "{U+1E35}"	; ḵ - خ
	>!s::Send  "{U+015F}"	; ş - ش
	>!t::Send  "{U+1E6F}"	; ṯ - ث

	; Fix for uppercase letters without Caps Lock (ALT+SHIFT is also the Windows shortcut for changing languages in Windows, which will conflict with these shortcuts)
	; Note that this will prevent multiple uppercase letters to be typed at once (these shouldn't be used often anyways, but use Caps Lock if this is necessary)
	;	Fixed, now Caps Lock is not necessary to type multiple uppercase characters: old solution was adding "{Alt down}{Shift}{Alt up}"
	<!+a::Send "{U+0100}{Alt}{Shift down}"	; Ā - ا
	<!+i::Send "{U+012A}{Alt}{Shift down}"	; Ī - ي
	<!+u::Send "{U+016A}{Alt}{Shift down}"	; Ū - و

	<!+d::Send "{U+1E0C}{Alt}{Shift down}"	; Ḍ - ض
	<!+h::Send "{U+1E24}{Alt}{Shift down}"	; Ḥ - ح
	<!+s::Send "{U+1E62}{Alt}{Shift down}"	; Ṣ - ص
	<!+t::Send "{U+1E6C}{Alt}{Shift down}"	; Ṭ - ط
	<!+z::Send "{U+1E92}{Alt}{Shift down}"	; Ẓ - ظ
	<!+`::Send "{U+02BF}{Alt}{Shift down}"	; ʿ - ع

	>!+d::Send "{U+1E0E}{Alt}{Shift down}"	; Ḏ - ذ
	>!+g::Send "{U+1E20}{Alt}{Shift down}"	; Ḡ - غ
	>!+k::Send "{U+1E34}{Alt}{Shift down}"	; Ḵ - خ
	>!+s::Send "{U+015E}{Alt}{Shift down}"	; Ş - ش
	>!+t::Send "{U+1E6E}{Alt}{Shift down}"	; Ṯ - ث
}
#If IsEnglish() and IsCapsLockOn()
{
	; Holding shift while in Caps Lock will generate lowercase letters
	; Vowels
	<!+a::Send "{U+0101}{Alt}{Shift down}"	; ā - ا
	<!+i::Send "{U+012B}{Alt}{Shift down}"	; ī - ي
	<!+u::Send "{U+016B}{Alt}{Shift down}"	; ū - و
	
	; Consonants (hard letters, left ALT)
	<!+d::Send "{U+1E0D}{Alt}{Shift down}"	; ḍ - ض
	<!+h::Send "{U+1E25}{Alt}{Shift down}"	; ḥ - ح
	<!+s::Send "{U+1E63}{Alt}{Shift down}"	; ṣ - ص
	<!+t::Send "{U+1E6D}{Alt}{Shift down}"	; ṭ - ط
	<!+z::Send "{U+1E93}{Alt}{Shift down}"	; ẓ - ظ
	<!+`::Send "{U+02BF}{Alt}{Shift down}"	; ʿ - ع

	; Consonants (easy letters, right ALT)
	>!+d::Send "{U+1E0F}{Alt}{Shift down}"	; ḏ - ذ
	>!+g::Send "{U+1E21}{Alt}{Shift down}"	; ḡ - غ
	>!+k::Send "{U+1E35}{Alt}{Shift down}"	; ḵ - خ
	>!+s::Send "{U+015F}{Alt}{Shift down}"	; ş - ش
	>!+t::Send "{U+1E6F}{Alt}{Shift down}"	; ṯ - ث

	; Uppercase letters
	<!a::Send  "{U+0100}"	; Ā - ا
	<!i::Send  "{U+012A}"	; Ī - ي
	<!u::Send  "{U+016A}"	; Ū - و

	<!d::Send  "{U+1E0C}"	; Ḍ - ض
	<!h::Send  "{U+1E24}"	; Ḥ - ح
	<!s::Send  "{U+1E62}"	; Ṣ - ص
	<!t::Send  "{U+1E6C}"	; Ṭ - ط
	<!z::Send  "{U+1E92}"	; Ẓ - ظ
	<!`::Send  "{U+02BF}"	; ʿ - ع

	>!d::Send  "{U+1E0E}"	; Ḏ - ذ
	>!g::Send  "{U+1E20}"	; Ḡ - غ
	>!k::Send  "{U+1E34}"	; Ḵ - خ
	>!s::Send  "{U+015E}"	; Ş - ش
	>!t::Send  "{U+1E6E}"	; Ṯ - ث
}
#If IsArabic()	; Arabic Symbols and Letters
{
	<!a::Send  "{U+0671}"	; hamzah al-waslah	- ٱ
	<!n::Send  "{U+0670}"	; alif maqsūrah		- ٰ
	<!q::Send  "{U+06D6}"	; good stop			- ۖ
	<!w::Send  "{U+06D7}"	; sufficient stop	- ۗ
	<!e::Send  "{U+06DA}"	; equally stop		- ۚ
	<!r::Send  "{U+06D8}"	; compulsary stop	- ۘ
	<!t::Send  "{U+06D9}"	; prohibited stop	- ۙ
}
#If

; Abbreviations
<!p::Send  "{U+FDFA}"			; Ṣalla Allahu `Alayhi wa Sallam - ﷺ
<!j::Send  "{U+FDFB}"			; Jalla Jalāluhu - ﷻ
<!+j::Send "ﷻ{Alt}{Shift down}"	; Subḥānahu wa Ta`āla - ﷻ


; Helper Functions

IsCapsLockOn()
{
	return GetKeyState("Capslock", "T")  ; 1 if CapsLock is ON, 0 otherwise.
}

IsArabic()
{
	LangID := GetKeyboardLanguage()

	return LangID == 0x0001	; "Arabic", 				ar
	    or LangID == 0x1401	; "Arabic (Algeria)",		ar-DZ
	    or LangID == 0x3C01	; "Arabic (Bahrain)",		ar-BH
	    or LangID == 0x0C01	; "Arabic (Egypt)",			ar-EG
	    or LangID == 0x0801	; "Arabic (Iraq)",			ar-IQ
	    or LangID == 0x2C01	; "Arabic (Jordan)",		ar-JO
	    or LangID == 0x3401	; "Arabic (Kuwait)",		ar-KW
	    or LangID == 0x3001	; "Arabic (Lebanon)",		ar-LB
	    or LangID == 0x1001	; "Arabic (Libya)",			ar-LY
	    or LangID == 0x1801	; "Arabic (Morocco)",		ar-MA
	    or LangID == 0x2001	; "Arabic (Oman)",			ar-OM
	    or LangID == 0x4001	; "Arabic (Qatar)",			ar-QA
	    or LangID == 0x0401	; "Arabic (Saudi Arabia)",	ar-SA
	    or LangID == 0x2801	; "Arabic (Syria)",			ar-SY
	    or LangID == 0x1C01	; "Arabic (Tunisia)",		ar-TN
	    or LangID == 0x3801	; "Arabic (UAE)",			ar-AE
	    or LangID == 0x2401	; "Arabic (Yemen)",			ar-YE
}

IsEnglish()
{
	LangID := GetKeyboardLanguage()

	return LangID == 0x0009	; "English", 						en
	    or LangID == 0x0C09	; "English (Australia)",			en-AU
	    or LangID == 0x2809	; "English (Belize)",				en-BZ
	    or LangID == 0x1009	; "English (Canada)",				en-CA
	    or LangID == 0x2409	; "English (Caribbean)",			en-029
	    or LangID == 0x3C09	; "English (Hong Kong SAR)",		en-HK
	    or LangID == 0x4009	; "English (India)",				en-IN
	    or LangID == 0x3809	; "English (Indonesia)",			en-ID
	    or LangID == 0x1809	; "English (Ireland)",				en-IE
	    or LangID == 0x2009	; "English (Jamaica)",				en-JM
	    or LangID == 0x4409	; "English (Malaysia)",				en-MY
	    or LangID == 0x1409	; "English (New Zealand)",			en-NZ
	    or LangID == 0x3409	; "English (Philippines)",			en-PH
	    or LangID == 0x4809	; "English (Singapore)",			en-SG
	    or LangID == 0x1C09	; "English (South Africa)",			en-ZA
	    or LangID == 0x2C09	; "English (Trinidad & Tobago)",	en-TT
	    or LangID == 0x4C09	; "English (United Arab Emirates)",	en-AE
	    or LangID == 0x0809	; "English (United Kingdom)",		en-GB
	    or LangID == 0x0409	; "English (United States)",		en-US
	    or LangID == 0x3009	; "English (Zimbabwe)",				en-ZW
}

GetKeyboardLanguage()
{
	if !ThreadId := DllCall("user32.dll\GetWindowThreadProcessId", "Ptr", WinActive("A"), "UInt", 0, "UInt")
		return false

	if !KBLayout := DllCall("user32.dll\GetKeyboardLayout", "UInt", ThreadId, "UInt")
		return false

	return KBLayout & 0xFFFF
}