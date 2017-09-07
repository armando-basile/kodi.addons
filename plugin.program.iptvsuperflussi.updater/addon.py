import xbmcaddon
import xbmcgui
import xbmc
import sys
import os
import glob
import string
import urllib
import zipfile
import contextlib


_addon_      = xbmcaddon.Addon()
_lang_       = _addon_.getLocalizedString
_addonname_  = _addon_.getAddonInfo('name')
_icon_       = _addon_.getAddonInfo('icon')
_out_path_   = _addon_.getSetting('out_path')
_is_adult_   = _addon_.getSetting('is_adult')
_username_   = _addon_.getSetting('username')
_password_   = _addon_.getSetting('password')

_url_m3u_    = ""
_url_config_ = "http://pastebin.com/raw/APQPPBxy"
_logos_url_  = "https://codeload.github.com/armando-basile/tv-logos/zip/master"
_logos_name_ = "tv-logos.zip"

_main_orig_name_  = "orig.iptvsuperflussi.m3u"
_live_orig_name_  = "orig.iptvsuperflussi-live.m3u"
_live_name_       = "iptvsuperflussi-live.m3u"
_vod_prefix_      = "iptvsuperflussi-vod-"
_vod_name_        = "iptvsuperflussi-vod.m3u"
_xxx_name_        = "iptvsuperflussi-xxx.m3u"
_conf_name_       = "iptvsuperflussi.conf"
_xxx_title_       = "= ADULT"
_vod_title_       = "FILM IN SALA"

output_list = list()
output_list_cid = list()





# read config file
def __parse_config_file():
    global _url_m3u_
    
    # update local var with config file content
    file = open(_out_path_ + '/' + _conf_name_, "r")
    cfg_file = file.read()
    file.close()
    
    # generate list with config file rows
    rows = cfg_file.split("\n")
    
    # loop for all rows in config file
    for row in rows:
        row = row.replace('\n', '').replace('\r', '').strip()
        # remove empty rows
        if len(row) > 0:
            # remove comments
            if row[0:1] != "#":
                
                subrow = row.split(";")
                
                # update vars with file content
                output_list.append(subrow[0])

                if len(subrow) > 1:
                    output_list_cid.append(subrow[1].strip())
                    
                else:
                    # error detected
                    xbmcgui.Dialog().notification(_addonname_, _lang_(30006) + subrow[0], xbmcgui.NOTIFICATION_ERROR, 10000)
                    sys.exit(0)
                    
            else:
                # check for url m3u path
                pos = string.find(row, '# URL:')
                if pos == 0:
                    _url_m3u_ = row.replace('# URL:', '').strip()

    # check for url m3u presence    
    if _url_m3u_ == "":
        # no url m3u present
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004) + '(url m3u)', xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)




def __split_orig():
    # split original m3u file into live, vod and xxx file lists
    
    content_type = "live"
    content_xxx = False
    
    file_live = open(_out_path_ + '/' + _live_orig_name_, "w")
    file_vod = open(_out_path_ + '/' + _vod_name_, "w")
    file_vod.write("#EXTM3U\n")
    
    if _is_adult_ == "true":
        file_xxx = open(_out_path_ + '/' + _xxx_name_, "w")
        file_xxx.write("#EXTM3U\n")
    
    # open original m3u file and read all lines (line by line)
    with open(_out_path_ + '/' + _main_orig_name_, "r") as file_orig:
        for line in file_orig:
            
            # detect content type
            if ((string.find(line, '#EXTINF:') == 0) and (string.find(line, _vod_title_) > 0)):
                content_type = "vod"
                content_xxx = False

            if ((string.find(line, '#EXTINF:') == 0) and (string.find(line, _xxx_title_) > 0)):
                content_xxx = True
                
            if content_type == "vod":
                if ((content_xxx == True) and (_is_adult_ == "true")):
                    file_xxx.write(line)

                elif (content_xxx == False):
                    file_vod.write(line)

            elif content_type == "live":
                file_live.write(line)
        
        file_live.close()
        file_vod.close()
        if _is_adult_ == "true":
            file_xxx.close()
        file_orig.close()




# add epg info into channels list file
def __update_content(channels_list, is_live):
    # init string for output content
    o_file = ""
    
    # open input file and read all lines
    file = open(_out_path_ + '/' + channels_list, "r")
    lines = file.readlines()
    file.close()

    # loop for each line in file
    for line in lines:
        # remove line feed and carriage return
        line = line.replace("\r", "").replace("\n", "")
        
        # check for channel header line
        if string.find(line, '#EXTINF:') == 0:
            # extract channel name
            c_pos = string.find(line, ',')
            c_name = line[c_pos+1:].strip()

            # check for channels group
            if string.find(c_name, '====') == 0:
                # channels group detected
                c_group = c_name.replace('-','').strip()
                c_group = c_group.replace('=','').strip()
                
                o_file += line.replace('#EXTINF:-1', 
                                       '#EXTINF:-1 ' +
                                       'group-title="' + c_group + '"') + "\n"
            
            else:
                # check for live list only
                if is_live == True:
                    # check for channel presence
                    if c_name in output_list:
                        # get cid from config file
                        s_pos = output_list.index(c_name)
                        c_cid = output_list_cid[s_pos]
                        
                        # update line
                        o_file += line.replace('#EXTINF:-1', 
                                               '#EXTINF:-1 ' + 
                                               'tvg-id="' + c_cid + '" ' +
                                               'tvg-logo="' + c_cid + '.png"') + "\n"
                 
                    else:
                        # channel not in list, adding
                        o_file += line + "\n"
                        
                else:
                    # not in live list, adding
                    o_file += line + "\n"
                
                
        else:
            # no channel header, update file extension from .ts to .m3u8
            line = line.replace('.ts', '.m3u8')
            o_file += line + "\n"
            
    
    return o_file






# create more m3u list with group name as filename
def __update_vod_content(channels_list):
    # init string for output content
    o_file = "#EXTM3U\n"
    out_file = None
    
    # open input file and read all lines
    file = open(_out_path_ + '/' + channels_list, "r")
    lines = file.readlines()
    file.close()

    # loop for each line in file
    for line in lines:
        # remove line feed and carriage return
        line = line.replace("\r", "").replace("\n", "")
        
        # check for channel header line
        if string.find(line, '#EXTINF:') == 0:
            # extract channel name
            c_pos = string.find(line, ',')
            c_name = line[c_pos+1:].strip()

            # check for channels group
            if string.find(c_name, '====') == 0:
                # channels group detected
                c_group = c_name.replace('-','').strip()
                c_group = c_group.replace('=','').strip()
                c_group = c_group.replace(' ','_').strip()
                
                # detect if there is a file opened
                if o_file != "#EXTM3U\n":
                    # close old file
                    out_file.write(o_file)
                    out_file.close()
                    o_file = "#EXTM3U\n"
                
                # write new file
                out_file = open(_out_path_ + '/' + _vod_prefix_ + c_group + '.m3u', "w")
                

            # append 
            o_file += line + "\n"
                
        elif string.find(line, '#EXTM3U') == 0:
            # do nothing
            do_nothing=1
            
        else:
            # no channel header, update file extension from .ts to .m3u8
            line = line.replace('.ts', '.m3u8')
            o_file += line + "\n"
            

    # detect if there is a file opened
    if o_file != "":
        # close old file
        out_file.write(o_file)
        out_file.close()
        o_file = ""





# unzip file with python 2.6 
def __unzip(source, target):
    with contextlib.closing(zipfile.ZipFile(source , "r")) as z:
        z.extractall(target)



# ==== Entry Point ====

# check for default destination path 
if (_out_path_ == "/tmp") or (_out_path_ == "/tmp/"):
    # destination path set required
    xbmcgui.Dialog().ok(_addonname_, _lang_(30012))
    xbmcaddon.Addon().openSettings()
    sys.exit(0)



# downloader
dlfile = urllib.URLopener()


# show main dialog before start update process
dialog = xbmcgui.Dialog().yesno(_addonname_, _lang_(30001), "", _lang_(30002))

# check for no list update
if dialog:
    # update request

    # create progress bar
    pbar = xbmcgui.DialogProgress()
    pbar.create(_addonname_, _lang_(30008))
    pbar.update(10)

    try:
        # try to get config file
        dlfile.retrieve(_url_config_, _out_path_ + '/' + _conf_name_)
        pbar.update(25)
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)

    # get config content from file
    __parse_config_file()
    pbar.update(40)


    # update m3u url with user data
    _url_main_ = _url_m3u_.replace('{USERNAME}', _username_)
    _url_main_ = _url_main_.replace('{PASSWORD}', _password_)
    
    
    try:
        # try to get m3u files
        dlfile.retrieve(_url_main_, _out_path_ + '/' + _main_orig_name_)
        
        # remove adult content
        if os.path.exists(_out_path_ + '/' + _xxx_name_):
            os.remove(_out_path_ + '/' + _xxx_name_)

        
        pbar.update(62)

        # detect file size
        file = open(_out_path_ + '/' + _main_orig_name_, "r")
        filesize_ = 1
        if (file.read(1) == ""):
            _filesize_ = 0
        file.close()
        
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30005), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)
    

    # check for file size = 0 (wrong username password)
    if (_filesize_ == 0):
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30005), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)


    # split orig into live, vod and xxx files list
    __split_orig()

    pbar.update(70, _lang_(30009))


    # update live content
    _new_content_ = __update_content(_live_orig_name_, True)
    # write new file
    file = open(_out_path_ + '/' + _live_name_, "w")
    file.write(_new_content_)
    file.close()


    # remove old vod files
    for fl in glob.glob(_out_path_ + '/' + _vod_prefix_ + '*.m3u'):        
        os.remove(fl)

    # update vod content
    __update_vod_content(_vod_name_)
    
    
    pbar.update(90)

    
    pbar.close()
    xbmc.executebuiltin('StartPVRManager')

    # update successful
    xbmcgui.Dialog().ok(_addonname_, _lang_(30007))
    
    




# show main dialog before start update logos process
dialog = xbmcgui.Dialog().yesno(_addonname_, _lang_(30010))

# check for no logos update
if dialog:
    # update request

    # create progress bar
    pbar = xbmcgui.DialogProgress()
    pbar.create(_addonname_, _lang_(30008))
    pbar.update(50)
    
    try:
        # try to get logos
        dlfile.retrieve(_logos_url_, _out_path_ + '/' + _logos_name_)
        pbar.update(75)
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30011), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)
    
    # unzip logo folder
    __unzip(_out_path_ + '/' + _logos_name_, _out_path_)
    
    
    pbar.close()

    # update successful
    xbmcgui.Dialog().ok(_addonname_, _lang_(30007))
    
else:
    # exit without perform update
    xbmcgui.Dialog().ok(_addonname_, _lang_(30003))
    sys.exit(0)












