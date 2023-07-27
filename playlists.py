import pytube


def get_playlist_urls(source):
    '''
    This function takes in a link to a youtube video in a playlist
    and returns the urls of all videos in the playlist after and including that video.
    ''' 
    urls = []

    playlist = pytube.Playlist(source)

    print(playlist.title)

    #If source is the direct link to a playlist
    if "?list" in source:
        for vid in playlist.videos:
            urls.append(vid.watch_url)
    #Otherwise, it's a song in a playlist
    else:
        video = pytube.YouTube(source)
        seen_source = False
        for vid in playlist.videos:
            if vid.video_id == video.video_id:
                seen_source = True
            if seen_source:
                urls.append(vid.watch_url)

    return urls


'''
This function determines if a URL is to a playlist or just a normal video. 
Returns True if playlist link, False Otherwise.
'''
def is_playlist(source):
    if "&list" in source or "?list" in source:
        return True
    return False
