import xbmc
import xbmcgui
import xbmcaddon
import json

# log: /Users/chrisbevan/Library/Logs
# tail -f kodi.log | grep "debug <general>: script.quickfind:"

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
CWD = ADDON.getAddonInfo('path')

def log(txt):
    message = '%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class GUI(xbmcgui.WindowXML):
    searchString = ""    
    
    def __init__(self, *args, **kwargs):
        self.params = kwargs['params']   
    
    def onInit(self):
        self.getControl(4).setLabel("Quickfind [COLOR highlight]"+self.params["media"]+"[/COLOR]") 
        #set initial search input list (all titles)        
        self.setSearchList()

    def setOutputList(self,list):
        self.outputList = self.getControl(200)
        self.outputList.reset()
        self.outputList.addItems(list)
        
    
    def setSearchList(self):
        self.inputList = self.getControl(100)
        self.inputList.reset()
        self.inputList.addItems(self.getSearchList(self.params["media"],self.searchString))
        xbmc.executebuiltin("SetFocus(100)")
        
    
    def getSearchList(self,mediaType,limiter):
        json_response = []
        unique_vals = []
        initial_list = []
        output_list = []
                
        if mediaType == "movies":
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter":{"field": "title", "operator": "startswith", "value": "%s"}, "properties": ["title", "art", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": false } }, "id": 1}' % (limiter))
        if mediaType == "tvshows":
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "filter":{"field": "title", "operator": "startswith", "value": "%s"}, "properties": ["title", "art", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": false } }, "id": 2}' % (limiter))
        if mediaType == "albums":
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": { "filter":{"field": "album", "operator": "startswith", "value": "%s"}, "properties": ["title", "artist", "thumbnail", "fanart", "art", "type", "artistid"], "sort": { "order": "ascending", "method": "label", "ignorearticle": false } }, "id": 3}' % (limiter))
        
        json_response = json.loads(json_query)
                                            
        for item in json_response['result'][mediaType]:    
            #get available initials for subsequent filters
            initial = item['label'][len(self.searchString)].upper()
            if initial not in unique_vals:
                unique_vals.append(initial)
                initial_list.append(xbmcgui.ListItem(initial))
                
            #add available titles to the output list
            output_list.append(self.getItem(mediaType,item))
            
        self.setOutputList(output_list)
        
        return initial_list
        
    def getItem(self,mediaType,item):
        if mediaType == "movies":
            listItem = xbmcgui.ListItem(label=item['label'])
            listItem.setPath(item['file'])
            listItem.setInfo("video",{"mediatype":"movie"})
            listItem.setInfo("video",{"dbid":item['movieid']})
            listItem.setArt({'poster':item['art']['poster'],'fanart':item['art']['fanart']})
        if mediaType == "tvshows":
            listItem = xbmcgui.ListItem(label=item['label'])
            listItem.setPath(item['file'])
            listItem.setInfo("video",{"mediatype":"tvshow"})
            listItem.setInfo("video",{"dbid":item['tvshowid']})
            listItem.setArt({'poster':item['art']['poster'],'fanart':item['art']['fanart']})
        if mediaType == "albums":
            listItem = xbmcgui.ListItem(label=item['title'],label2=str(item['artist'][0]))
            musicInfoTag = listItem.getMusicInfoTag()
            musicInfoTag.setMediaType("album")
            musicInfoTag.setDbId(item['albumid'],"album")
            listItem.setProperty('artistid', str(item['artistid'][0]))
            listItem.setArt({'thumb':item['art']['thumb']})
            listItem.setArt({'fanart':item['fanart']})
        return listItem
    
    def updateSearch(self,addToSearchTerm):
        self.searchString += addToSearchTerm
        self.getControl(3).setLabel(self.searchString)
        self.setSearchList()
    
    def onClick(self, controlID):
        if controlID == 1:
            self.searchString = self.searchString[:-1]
            self.getControl(3).setLabel(self.searchString)
            self.setSearchList()
            return
        
        control = self.getControl(controlID)
        selectedItem = control.getListItem(control.getSelectedPosition())
        
        if controlID == 100:   
            self.updateSearch(selectedItem.getLabel())
            return
        
        if controlID == 200:
            #get mediatype
            if selectedItem.getVideoInfoTag().getMediaType():
                media = selectedItem.getVideoInfoTag().getMediaType()
            if selectedItem.getMusicInfoTag().getMediaType():
                media = selectedItem.getMusicInfoTag().getMediaType()           
            #handle player by media type
            if media == 'movie':                
                movieid = selectedItem.getVideoInfoTag().getDbId()                  
                self.playItem('movieid', movieid, selectedItem)
            if media == 'tvshow':
                tvshowid = selectedItem.getVideoInfoTag().getDbId()
                xbmc.executebuiltin("activatewindow(Videos,videodb://tvshows/titles/%s)" % tvshowid)
            if media == 'album':
                albumid = selectedItem.getMusicInfoTag().getDbId()
                xbmc.executebuiltin("activatewindow(Music,musicdb://albums/%s/-1)" % albumid)
      
               
            
            
    def playItem(self, key, value, listitem=None):
        if key == 'movieid':
            xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open", "params":{"item":{"%s":%d}}, "id":1}' % (key, int(value)))

if (__name__ == '__main__'):
    try:
        params = dict(arg.split('=') for arg in sys.argv[1].split('&'))
    except:
        params = {}
    ui = GUI('script-quickfind.xml', CWD, 'default', '1080i', params=params)
    ui.doModal()
    del ui