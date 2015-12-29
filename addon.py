import xbmcaddon
import xbmcgui
#import xbmc
import sys
import urllib
import string



_addon_       = xbmcaddon.Addon()
_lang_        = _addon_.getLocalizedString
_addonname_   = _addon_.getAddonInfo('name')
_icon_        = _addon_.getAddonInfo('icon')
_out_path_    = _addon_.getSetting('out_path')
_url_config_  = "http://pastebin.com/raw/aKd1JnNx"
_name_config_ = "xmltv-updater.conf"
_url_xmltv_   = ""
_name_xmltv_  = ""


# extract info from config file
def __parse_config_file():
    global _url_xmltv_
    global _name_xmltv_
    
    # read all config file
    file = open(_out_path_ + '/' + _name_config_, "r")
    cfg_file = file.read()
    file.close()
    
    # generate list with config file rows
    rows = cfg_file.split("\n")
    
    # loop for all rows in config file
    for row in rows:
        row = row.strip()
        # remove empty rows
        if len(row) > 0:
            row = row.replace('\n', '').replace('\r', '').strip()
            
            # check for xmltv url
            pos = string.find(row, '# URL:')
            if pos == 0:
                _url_xmltv_ = row.replace('# URL:', '').strip()
                
            # check for xmltv name
            pos = string.find(row, '# NAME:')
            if pos == 0:
                _name_xmltv_ = row.replace('# NAME:', '').strip()

    # check for data presence
    if (_url_xmltv_ == "") or (_name_xmltv_ == ""):
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)








# show main dialog before start update process
dialog = xbmcgui.Dialog().yesno(_addonname_, _lang_(30001), "", _lang_(30002))

# check for exit
if dialog:
    # update request

    dlfile = urllib.URLopener()
    
    
    try:
        # update gui
        pbar = xbmcgui.DialogProgress()
        pbar.create(_addonname_, _lang_(30006))
        pbar.update(40)
        
        # try to get config file
        dlfile.retrieve(_url_config_, _out_path_ + '/' + _name_config_)
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30005), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)
    
    
    # get info from config file
    pbar.update(60)
    __parse_config_file()
    
    
    try:
        pbar.update(70, _lang_(30008))

        # try to get xmltv file
        dlfile.retrieve(_url_xmltv_, _out_path_ + '/' + _name_xmltv_)
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)
    
    pbar.close()
    
    # update successful
    xbmcgui.Dialog().ok(_addonname_, _lang_(30007))
    
    
else:
    # exit without perform update
    xbmcgui.Dialog().ok(_addonname_, _lang_(30003))
    sys.exit(0)



















